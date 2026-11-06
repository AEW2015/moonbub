#!/usr/bin/env python3
"""Independently replay bank certificates and recompute V82 execution accounting."""
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import statistics
import tarfile

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v82'
COMMITMENT = AREA / 'commitment/attempt-20261106T052142Z'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def stats(values):
    return dict(min=min(values), median=statistics.median(values), max=max(values), total=sum(values))


def main():
    # Exact retained artifacts first; historical C1 has its own captured source.
    manifest = read(AREA / 'native/artifact-manifest.json')
    for name, pin in manifest['files'].items():
        p = ROOT / name
        assert p.stat().st_size == pin['bytes'] and sha(p) == pin['sha256'], name
    for folder in sorted((AREA / 'commitment').glob('attempt-*')):
        for name, expected in read(folder / 'sha256.json').items():
            assert sha(folder / name) == expected, (folder, name)
    c = read(COMMITMENT / 'report.json')
    assert c['status'] == 'PASS' and c['profile_id'].endswith('TREE-2')
    assert len(c['synthetic_tests']) == 113 and all(t['status'] == 'PASS' for t in c['synthetic_tests'])
    assert c['native']['frames'] == 457 and c['native']['full_rebuilds'] == 3656
    assert sha(COMMITMENT / 'prototype_commitment.py') == sha(ROOT / 'scripts/cu66-v82/prototype_commitment.py')
    assert c['claims']['sender_authentication'] is False and c['claims']['rtl_or_hls'] is False
    proof = read(AREA / 'execution-input-verification.json')
    assert proof['status'] == 'PASS' and proof['sources'] == 457
    assert proof['native_index_sha256'] == sha(AREA / 'native/index.json')
    assert proof['script_sha256'] == sha(ROOT / 'scripts/cu66-v82/verify_execution_inputs.py')
    vectors = read(AREA / 'compact-message-vectors.json')
    assert vectors['status'] == 'PASS' and len(vectors['vectors']) == 8
    for name, digest in vectors['source_sha256'].items():
        assert sha(ROOT / name) == digest, name
    for vector in vectors['vectors']:
        message = bytes.fromhex(vector['message_hex'])
        assert len(message) == vector['bytes']
        assert hashlib.sha256(message).hexdigest() == vector['SHA256']
        assert vector['compression_blocks'] == (len(message)+9+63)//64

    runs = []
    for path in sorted((AREA / 'execution').glob('attempt*/results.json')):
        d = read(path)
        if d['status'] == 'PASS_NATIVE_COPY_AWARE_ACCOUNTING':
            runs.append((path, d))
    assert runs, 'no qualified execution result'
    path, report = runs[-1]
    for name, pin in report['source_sha256'].items():
        assert sha(ROOT / name) == pin, name
    archive = ROOT / report['source_snapshot']['path']
    assert sha(archive) == report['source_snapshot']['sha256']
    with tarfile.open(archive, 'r:gz') as tar:
        for member in tar.getmembers():
            assert not Path(member.name).is_absolute() and '..' not in Path(member.name).parts
            if member.isfile():
                assert hashlib.sha256(tar.extractfile(member).read()).hexdigest() == report['source_sha256'][member.name]
    assert report['rtl_changed'] is False and report['timing_is_measured'] is False
    host_rows = {(r['granularity'], r['cohort'], r['fid']): r
                 for line in (COMMITMENT / 'frames.jsonl').read_text().splitlines()
                 if (r := json.loads(line))['policy'] == 'conservative-zero-coefficient'}
    expected = {}
    for g in (1, 4, 16, 64):
        p = path.parent / f'g{g}-frames.jsonl'
        assert sha(p) == report['per_frame_artifacts'][p.name]
        rows = [json.loads(line) for line in p.read_text().splitlines()]
        assert len(rows) == 457
        expected[g] = {(r['cohort'], r['fid']): r for r in rows}
    spec = importlib.util.spec_from_file_location('v82_audit_native', AREA / 'native/data.py')
    native = importlib.util.module_from_spec(spec); spec.loader.exec_module(native)

    accepted = None; old_cohort = None; ref = None
    frames = keys = elisions = 0
    for f in native.iter_frames():
        if f['cohort'] != old_cohort:
            accepted = None; ref = None; masks = [0] * 8100
            banks = [[None] * 8100 for _ in range(3)]; old_cohort = f['cohort']
        candidate = 0 if ref is None else (ref + 1) % 3
        assert candidate != ref
        shadow = []; skip = []
        for i, tile in enumerate(f['tiles']):
            same = accepted is not None and tile == accepted[i]
            assert same == bool(f['same_mask'][i])
            bit = 1 << candidate
            reuse = not f['key'] and same and bool(masks[i] & bit)
            if reuse:
                assert banks[candidate][i] == accepted[i] == tile
                shadow.append(masks[i])
            else:
                masks[i] &= ~bit
                banks[candidate][i] = tile
                shadow.append((masks[i] if same and not f['key'] else 0) | bit)
            skip.append(reuse)
        assert banks[candidate] == f['tiles']
        stores = 8100 - sum(skip)
        for g, by_source in expected.items():
            r = by_source[f['cohort'], f['fid']]; h = host_rows[g, f['cohort'], f['fid']]
            assert (r['root'], r['seal'], r['hash_compression_blocks']) == (h['content_root'], h['seal'], h['blocks'])
            assert r['hash_isolated_list_schedule_cycles'] == h['lane_cycles']
            assert r['resident_store_elisions'] == sum(skip) and r['physical_store_tiles'] == stores
            hash_needed = set()
            offset = 0
            for count in (5400, 1350, 1350):
                for start in range(0, count, g):
                    group = range(offset + start, offset + min(start + g, count))
                    if f['key'] or any(not(f['copy_ref_mask'][i] or f['hidden_mask'][i]) for i in group):
                        hash_needed.update(group)
                offset += count
            residual = sum(not f['key'] and not f['hidden_mask'][i] and not f['copy_ref_mask'][i] for i in range(8100))
            materialize = sum(not f['key'] and f['copy_ref_mask'][i] and not skip[i] for i in range(8100))
            hash_only = sum(not f['key'] and f['copy_ref_mask'][i] and skip[i] and i in hash_needed for i in range(8100))
            assert (r['decode_reference_tiles'], r['materialize_copy_reference_tiles'], r['mixed_leaf_hash_only_reference_tiles']) == (residual, materialize, hash_only)
            R = (residual + materialize + hash_only) * 4 + 2640; W = stores * 4 + 2640
            assert r['logical_BL8'] == dict(reference_reads=R-2640, canonical_writes=W-2640, HUD_reads=2640, HUD_writes=2640, total=R+W)
            assert r['conditional_data_service_floor_cycles'] == R*18 + W*16 - 18
            L = 1 << (sum((n+g-1)//g for n in (5400,1350,1350))-1).bit_length(); nodes = 2*L-1
            jobs = h['hash_jobs']; old_compare = 0 if f['key'] else sum(v for k,v in jobs.items() if k != 'seal')*8
            clone = 0 if f['key'] else nodes*8
            mr = clone + jobs.get('internal',0)*16 + old_compare + 8
            mw = clone + sum(v for k,v in jobs.items() if k != 'seal')*8
            assert (r['metadata']['tree_read_words32'], r['metadata']['tree_write_words32']) == (mr,mw)
            assert r['memory']['total_tree_and_maps_bytes'] == 2*nodes*32+6075
            assert r['metadata']['onchip_tree_port_floor_cycles'] == max(mr,mw)
            ext = r['external_tree_scenario']; assert ext['reads'] == R+mr//4 and ext['writes'] == W+mw//4
            assert ext['conditional_service_floor_cycles'] == ext['reads']*18+ext['writes']*16-18
            for lane in (1,2,4):
                bound = r['hash_necessary_compute_bound_cycles'][str(lane)]
                assert math.ceil(h['blocks']*64/lane) <= bound <= h['lane_cycles'][str(lane)]
        accepted = f['tiles']; masks = shadow; ref = candidate
        frames += 1; keys += f['key']; elisions += sum(skip)
    assert (frames,keys,elisions*4) == (457,20,6740876)
    # Recompute every published execution summary from audited per-source rows.
    for s in report['summaries']:
        rows = [r for r in expected[s['granularity']].values() if r['key'] == s['key']]
        assert s['sources'] == len(rows)
        for output, field in [('reference_BL8_reads','reference_reads'),('canonical_BL8_writes','canonical_writes'),('data_and_HUD_BL8','total')]:
            assert s[output] == sum(r['logical_BL8'][field] for r in rows)
        assert s['SHA_blocks'] == stats([r['hash_compression_blocks'] for r in rows])
        for output, values in [
            ('conditional_data_service_ms',[r['conditional_data_service_floor_cycles']*1e-5 for r in rows]),
            ('external_tree_scenario_service_ms',[r['external_tree_scenario']['conditional_service_floor_cycles']*1e-5 for r in rows]),
            ('hash_isolated_1lane_ms',[r['hash_isolated_list_schedule_cycles']['1']*1e-5 for r in rows]),
            ('hash_isolated_4lane_ms',[r['hash_isolated_list_schedule_cycles']['4']*1e-5 for r in rows]),
            ('onchip_tree_port_floor_ms',[r['metadata']['onchip_tree_port_floor_cycles']*1e-5 for r in rows])]:
            assert s[output] == stats(values), output
    print('V82_EVIDENCE_AUDIT_PASS native=457 execution_rows=1828 commitment_checks=3656 synthetic=113 vectors=8')
    print('Python semantic/accounting evidence only; no timing, transport, RTL, fit, 30fps or under10ms qualification.')


if __name__ == '__main__':
    main()
