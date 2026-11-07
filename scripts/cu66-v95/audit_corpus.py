#!/usr/bin/env python3
"""Read every archived V95 palette independently against frozen V82 U8 tiles.

The V95 archive loader verifies its compressed/raw/plane hashes. This audit
does not decode residual coefficients or time generation of predecoded targets.
"""

import argparse
from collections import Counter
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import signal
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v95/python'
NATIVE = ROOT / 'experiments/python-gamebub-v95/native'


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--index', type=Path, default=NATIVE / 'index.json')
    parser.add_argument('--timeout', type=int, default=600)
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error('--timeout must be positive')
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA / 'corpus-attempts' / (stamp + '-' + uuid.uuid4().hex[:8])
    out.mkdir(parents=True)
    pins, archive_pins, observations = {}, {}, []
    totals = [Counter() for _ in range(6)]
    report = dict(schema='cu66-v95-independent-python-corpus-v1', status='FAIL',
                  watchdog_seconds=args.timeout, physical_timing_proven=False,
                  predecoded_pixel_generation_cost_measured=False,
                  raw_capture_coverage_claim=False, source_sha256=pins,
                  archive_sha256=archive_pins, profiles=[], observations=observations)
    started = time.monotonic()

    def pin(path, *, archive=False):
        path = path.resolve()
        name = str(path.relative_to(ROOT))
        digest = sha(path)
        target = archive_pins if archive else pins
        if name in target:
            assert target[name] == digest, ('input changed', name)
        else:
            target[name] = digest
            if not archive:
                dest = out / 'sources' / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(path.read_bytes())
        return path

    def timeout(signum, frame):
        raise TimeoutError('V95 independent corpus watchdog expired')

    signal.signal(signal.SIGALRM, timeout)
    signal.alarm(args.timeout)
    try:
        pin(Path(__file__))
        pin(AREA / 'codec.py')
        index_path = pin(args.index)
        native_index = json.loads(index_path.read_text())
        # Retain exact loader/index sources; retain archive SHA pins by reference
        # rather than duplicating the already immutable frozen binary corpora.
        for version, sub in ((95, 'native'), (88, 'entropy'), (85, 'residual'), (82, 'native')):
            source = ROOT / ('experiments/python-gamebub-v%d/%s' % (version, sub))
            pin(source / 'data.py')
            selected_index = index_path if version == 95 else source / 'index.json'
            pin(selected_index)
            index = json.loads(selected_index.read_text())
            if 'data' in index:
                pin(source / index['data']['path'], archive=True)
            if isinstance(index.get('chunks'), list):
                for chunk in index['chunks']:
                    pin(source / chunk['path'], archive=True)
            for shard in index.get('shards', []):
                pin(source / shard['path'], archive=True)
        codec = module('v95_corpus_independent', AREA / 'codec.py')
        native = module('v95_corpus_loader', NATIVE / 'data.py')
        assert len(native.PROFILES) == 6
        targets = module('v95_frozen_v82_target', ROOT / 'experiments/python-gamebub-v82/native/data.py')
        frames, planes, records, reused, cohorts = 0, 0, 0, 0, Counter()
        all_pixels, all_targets = hashlib.sha256(), hashlib.sha256()
        for frame, original in zip(native.iter_frames(index_path=index_path), targets.iter_frames(), strict=True):
            for key in ('cohort', 'ordinal', 'fid', 'refid', 'key', 'canonical_sha256'):
                assert frame[key] == original[key], ('frozen identity', key)
            assert len(frame['plane_variants']) == len(frame['palette_stats']) == 3
            offset = 0
            for axis, tile_count in enumerate((5400, 1350, 1350)):
                active = [position for position in range(tile_count)
                          if not original['hidden_mask'][offset + position] and
                          (frame['key'] or frame['zero_mask'][offset + position] == '0')]
                assert len(active) == frame['residual_counts'][axis], 'original mode2 count'
                assert len(active) == sum(chunk['blocks'] for chunk in frame['variants']['65536'][axis])
                variants, stats = frame['plane_variants'][axis], frame['palette_stats'][axis]
                assert len(variants) == len(stats) == 6
                for profile, (packet, native_stats) in enumerate(zip(variants, stats, strict=True)):
                    decoded = codec.parse_plane(packet, active)
                    pixels_hash, targets_hash = hashlib.sha256(), hashlib.sha256()
                    kinds = Counter()
                    for entry in decoded['palettes']:
                        target = original['planes'][axis][entry['position']]
                        assert entry['pixels'] == target, ('pixel mismatch', frames, axis, profile, entry['position'])
                        pixels_hash.update(entry['pixels'])
                        targets_hash.update(target)
                        all_pixels.update(entry['pixels'])
                        all_targets.update(target)
                        kinds[str(entry['record'][0])] += 1
                    assert pixels_hash.hexdigest() == targets_hash.hexdigest()
                    assert pixels_hash.hexdigest() == native_stats['palette_pixel_sha256'], 'native target digest'
                    count = len(decoded['palettes'])
                    for key in ('palette_records', 'palette_count', 'avoided_tiles'):
                        if key in native_stats:
                            assert count == native_stats[key]
                    if 'pal_positions' in native_stats:
                        assert [entry['position'] for entry in decoded['palettes']] == native_stats['pal_positions']
                    if 'record_kind_counts' in native_stats:
                        assert [kinds[str(kind)] for kind in range(5)] == native_stats['record_kind_counts']
                    if 'residual_blocks' in native_stats:
                        assert decoded['residual_blocks'] == native_stats['residual_blocks']
                    total = totals[profile]
                    total.update(planes=1, palette_records=count,
                                 palette_pixels=count * 64, residual_blocks=decoded['residual_blocks'],
                                 plane_bytes=len(packet), reuse_records=kinds['4'])
                    for kind, value in kinds.items():
                        total['kind_' + kind] += value
                    observations.append(dict(cohort=frame['cohort'], ordinal=frame['ordinal'],
                                             fid=frame['fid'], axis=axis, profile=profile,
                                             profile_name=native.PROFILES[profile],
                                             plane_sha256=hashlib.sha256(packet).hexdigest(),
                                             records=count, residual_blocks=decoded['residual_blocks'],
                                             palette_pixel_sha256=pixels_hash.hexdigest(), kinds=dict(kinds)))
                    planes += 1
                    records += count
                    reused += kinds['4']
                offset += tile_count
            frames += 1
            cohorts[frame['cohort']] += 1
            if frames % 50 == 0:
                print('audited', frames, 'frames', records, 'palette records', flush=True)
        assert frames == native_index['native_sources'] == 457
        assert planes == 457 * 3 * 6
        assert all_pixels.hexdigest() == all_targets.hexdigest()
        assert records > 0 and reused > 0, 'archive must exercise actual palette/reuse records'
        for mapping in (pins, archive_pins):
            assert mapping == {name: sha(ROOT / name) for name in mapping}, 'pinned inputs changed'
        report.update(status='PASS_ALL_V95_ARCHIVE_PALETTE_PIXELS_MATCH_FROZEN_V82',
                      frames=frames, cohorts=dict(cohorts), planes=planes, palette_records=records,
                      reuse_records=reused, palette_pixel_sha256=all_pixels.hexdigest(),
                      profiles=[dict(profile=index, profile_name=native.PROFILES[index], **dict(values))
                                for index, values in enumerate(totals)],
                      scope='Every six-profile palette record independently decoded and compared byte-for-byte to the frozen V82 target tile. Opaque EC92 residuals are checked separately by native/full-frame tests. Frozen predecoded target generation cost is unmeasured. No physical timing or new raw-capture coverage claim.')
    except BaseException as error:
        report['error'] = repr(error)
        raise
    finally:
        signal.alarm(0)
        report['wall_seconds'] = time.monotonic() - started
        report['artifacts_sha256'] = {str(p.relative_to(out)): sha(p) for p in out.rglob('*') if p.is_file()}
        (out / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
        print(report['status'], out / 'results.json', flush=True)
    (AREA / 'corpus-index.json').write_text(json.dumps(dict(report, selected_report=str((out / 'results.json').relative_to(ROOT))), indent=2) + '\n')


if __name__ == '__main__':
    main()
