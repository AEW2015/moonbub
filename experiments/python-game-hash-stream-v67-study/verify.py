#!/usr/bin/env python3
"""Independently replay V67 ordered canonical hashes from archived CS38 frames."""
from pathlib import Path
import hashlib
import importlib.util
import json
import struct
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
QUAL_DIR = HERE.parent / 'python-game-filter-qual-v67-study'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    sys.modules[name] = obj
    spec.loader.exec_module(obj)
    return obj


qual = module('hash67_independent_qual_helper', QUAL_DIR / 'helpers.py')
model = module('hash67_component_under_test', HERE / 'model.py')
DOMAINS = ('CS66_i16', 'CU66_u8')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def direct_full_hash(planes, domain):
    preimage = bytearray(struct.pack('<HH', 720, 480))
    for plane in planes:
        if domain == 'CS66_i16':
            preimage.extend(np.asarray(plane).astype('<i2', copy=False).tobytes(order='C'))
        elif domain == 'CU66_u8':
            arr = np.asarray(plane)
            assert arr.dtype == np.uint8 and arr.flags.c_contiguous
            preimage.extend(arr.tobytes(order='C'))
        else:
            raise AssertionError(domain)
    return hashlib.sha256(preimage).digest()[:16]


def main():
    data = json.loads((HERE / 'results.json').read_text())
    assert data['schema'] == 'gamebub-hash-stream-v67'
    pins = data['source_sha256']
    for name, digest in pins.items():
        path = Path(name)
        assert not path.is_absolute() and '..' not in path.parts
        assert sha(ROOT / path) == digest, ('source pin', name)

    qualification = json.loads((QUAL_DIR / 'results.json').read_text())
    assert len(qualification['cases']) == len(data['cases']) == 4
    assert sum(len(c['rows']) for c in qualification['cases']) == 457
    before = {name: sha(ROOT / name) for name in pins}
    all_frames = 0
    total_pause_checks = 0
    source_inputs = set()
    for source_case, result_case in zip(qualification['cases'], data['cases'], strict=True):
        assert source_case['scene'] == result_case['scene']
        assert len(source_case['rows']) == len(result_case['rows'])
        rx = qual.direct.Receiver()
        for source, retained in zip(source_case['rows'], result_case['rows'], strict=True):
            assert source['id'] == retained['id']
            packet = qual.raw(source['source_packet'], qual.PACKETS)
            source_inputs.add(source['source_packet']['raw_sha256'])
            canonical, _hud, metadata, _extra = rx.receive(packet)
            assert bool(metadata['key']) == bool(source['key'])
            legacy_tag = qual.h.m.C.reference_tag(canonical)
            assert legacy_tag.hex() == source['canonical_tag']

            normalized = []
            for plane in canonical:
                arr = np.asarray(plane)
                assert arr.dtype == np.int16 and arr.shape in ((480, 720), (240, 360))
                assert int(arr.min()) >= 0 and int(arr.max()) <= 255
                u8 = arr.astype(np.uint8)
                u8.setflags(write=False)
                normalized.append(u8)
            assert tuple(x.shape for x in normalized) == ((480, 720), (240, 360), (240, 360))

            expected_tags = {
                'CS66_i16': direct_full_hash(canonical, 'CS66_i16'),
                'CU66_u8': direct_full_hash(normalized, 'CU66_u8'),
            }
            assert expected_tags['CS66_i16'] == legacy_tag
            subjects = {domain: model.TileHash(domain) for domain in DOMAINS}
            pause_checks = 0
            for plane_index, plane in enumerate(normalized):
                for y in range(0, plane.shape[0], 8):
                    for x in range(0, plane.shape[1], 8):
                        tile = plane[y:y + 8, x:x + 8]
                        assert tile.shape == (8, 8) and tile.dtype == np.uint8
                        for subject in subjects.values():
                            subject.feed(plane_index, y, x, tile)
                            assert subject.work()['maximum_strip_data_bytes'] == 5760
                        if (plane_index + y // 8 + x // 8) % 19 == 0:
                            for subject in subjects.values():
                                pending = subject.work()
                                # No feed occurs during this simulated consumer pause.
                                assert subject.work() == pending
                            pause_checks += 1
            assert pause_checks == retained['deterministic_pause_checks']
            total_pause_checks += pause_checks
            assert set(retained['domains']) == set(DOMAINS)
            for domain, subject in subjects.items():
                tag = subject.finish()
                assert tag == expected_tags[domain]
                assert subject.finish() == tag
                work = subject.work()
                assert work['tiles'] == 8100 and work['canonical_samples'] == 518400
                assert work['rows_serialized'] == 960
                assert work['serialized_bytes'] == (1036804 if domain == 'CS66_i16' else 518404)
                assert work['maximum_strip_data_bytes'] == 5760
                assert work['maximum_serialized_row_bytes'] == (1440 if domain == 'CS66_i16' else 720)
                assert work['retained_strip_data_bytes'] == 0
                assert work['finished'] and not work['failed'] and not work['full_frame_staged']
                row = retained['domains'][domain]
                assert row['tag'] == tag.hex() and row['work'] == work
            all_frames += 1
            if all_frames % 64 == 0:
                print(json.dumps(dict(frames_checked=all_frames, pause_checks=total_pause_checks)), flush=True)

    assert all_frames == 457
    assert total_pause_checks == data['summary']['deterministic_pause_checks'] == 190569
    assert data['summary']['domain_results'] == 914
    assert data['summary']['tiles_per_domain'] == 3701700
    assert data['summary']['canonical_samples_per_domain'] == 236908800
    assert len(source_inputs) == 457
    assert {name: sha(ROOT / name) for name in pins} == before
    print(json.dumps(dict(frames=all_frames, domains=914, source_packets=len(source_inputs),
                          full_frame_hashlib_oracle=True, exact_old43_reference_hashes=True,
                          pause_checks=total_pause_checks, maximum_strip_data_bytes=5760,
                          maximum_transient_row_bytes={'CS66_i16': 1440, 'CU66_u8': 720},
                          source_pins=len(pins), hardware_cycles_or_fit_proven=False)))


if __name__ == '__main__':
    main()
