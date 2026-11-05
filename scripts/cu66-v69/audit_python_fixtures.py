#!/usr/bin/env python3
"""Replay native v69 CU66 packet fixtures with the frozen Python V66 receiver."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
NATIVE = ROOT / 'experiments/cu66-native-v69'
V66 = ROOT / 'experiments/python-game-canonical-tag-v66-study'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    helper = load('cu66_v69_audit_helpers', V66 / 'helpers.py')
    previous = sys.modules.get('helpers')
    sys.modules['helpers'] = helper
    try:
        receiver_module = load('cu66_v69_audit_receiver', V66 / 'receiver.py')
    finally:
        if previous is None:
            sys.modules.pop('helpers', None)
        else:
            sys.modules['helpers'] = previous

    manifest = json.loads((NATIVE / 'manifest.json').read_text())
    assert manifest['schema'] == 'cu66-native-v69-fixtures'
    assert manifest['capabilities']['wire'] == 'CU66/GU66'
    total = 0
    for case in manifest['cases']:
        receiver = receiver_module.Receiver(profile='CU66')
        rows = case['rows']
        assert rows, f"empty case: {case['scene']}"
        for expected_id, row in enumerate(rows):
            packet_path = NATIVE / row['packet']['path']
            packet = packet_path.read_bytes()
            assert len(packet) == row['packet']['bytes']
            assert sha(packet) == row['packet']['sha256']

            planes, hud, meta, _ = receiver.receive(packet)
            assert meta['frame_id'] == row['id'] == expected_id
            assert meta['reference_id'] == row['reference_id']
            assert bool(meta['key']) is row['key']

            canonical = b''.join(np.asarray(plane, dtype=np.uint8).tobytes()
                                 for plane in planes)
            hud_words = b''.join(patch['words'].astype('<u2').tobytes()
                                 for patch in hud)
            rgb565 = helper.m.C.corpus.rgb565(
                helper.m.ft.planes_to_rgb(planes))
            displayed = helper.f.f.n.overlay(
                rgb565, tuple(patch['words'] for patch in hud)
            ).astype('<u2').tobytes()
            checks = {
                'canonical_yuv_u8_sha256': sha(canonical),
                'hud_words_u16le_sha256': sha(hud_words),
                'display_rgb565_u16le_sha256': sha(displayed),
                'canonical_tag': meta['output_tag'].hex(),
            }
            for field, actual in checks.items():
                assert row[field] == actual, (
                    case['scene'], row['id'], field, row[field], actual)
        print(f"{case['scene']} {len(rows)} PASS")
        total += len(rows)
    assert total == 457, f'expected 457 archived frames; found {total}'
    print(f'independent_frozen_V66_CU66_replay {total} PASS')


if __name__ == '__main__':
    main()
