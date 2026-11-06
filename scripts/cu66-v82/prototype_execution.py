#!/usr/bin/env python3
"""Run COPY-aware memory/hash/metadata accounting with actual native tile bytes."""
from __future__ import annotations
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import sys
import tarfile
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v82'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def stats(values):
    return dict(min=min(values), median=statistics.median(values), max=max(values), total=sum(values))


def main():
    started = time.monotonic()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA / 'execution' / f'attempt-{stamp}-{uuid.uuid4().hex[:8]}'
    out.mkdir(parents=True)
    paths = [Path(__file__).resolve(), AREA / 'execution.py', AREA / 'native/data.py',
             AREA / 'native/index.json', ROOT / 'scripts/cu66-v82/prototype_commitment.py',
             ROOT / 'fpga/experiments/cu66-v81/residency/model.py']
    paths += list((AREA / 'native/data').glob('*.gz'))
    paths = sorted(set(paths))
    pins = {str(p.relative_to(ROOT)): sha(p) for p in paths}
    archive = out / 'sources.tar.gz'
    with tarfile.open(archive, 'w:gz') as tar:
        for p in paths:
            if p.suffix != '.gz':
                tar.add(p, arcname=str(p.relative_to(ROOT)), recursive=False)
    report = dict(schema='cu82-copy-aware-execution-v1', status='FAIL',
                  source_sha256=pins,
                  source_snapshot=dict(path=str(archive.relative_to(ROOT)), sha256=sha(archive)),
                  native_only=True, timing_is_measured=False, rtl_changed=False,
                  limitations=['Counts and conditional bounds, not a cycle-accurate pipeline.',
                               'All hash inputs available at t=0 for isolated schedules; memory data dependencies omitted.',
                               'Complete shadow-tree cloning is priced; a persistent/versioned alternative is not assumed.',
                               'External tree traffic assumes aligned digest objects; masks remain on chip.',
                               'No 30fps/under10ms/transport/fit proof.'])
    try:
        native = load('cu82_execution_native', AREA / 'native/data.py')
        commitment = load('cu82_execution_commitment', ROOT / 'scripts/cu66-v82/prototype_commitment.py')
        residency = load('cu82_execution_residency', ROOT / 'fpga/experiments/cu66-v81/residency/model.py')
        execution = load('cu82_execution_costs', AREA / 'execution.py')
        summaries = []
        for granularity in (1, 4, 16, 64):
            rows = []
            old_cohort = None
            with (out / f'g{granularity}-frames.jsonl').open('w') as stream:
                for original in native.iter_frames():
                    frame = dict(original, generation=original['ordinal'] + 1)
                    if frame['cohort'] != old_cohort:
                        model = residency.Residency(8100)
                        tree = commitment.CommitmentTree(granularity=granularity)
                        old_cohort = frame['cohort']
                    candidate = 0 if model.reference is None else (model.reference + 1) % 3
                    elided = [not frame['key'] and bool(frame['same_mask'][i]) and
                              bool(model.masks[i] & (1 << candidate)) for i in range(8100)]
                    plan = tree.plan(frame, frame['copy_ref_mask'])
                    full = tree.full(frame)
                    assert (plan['root'], plan['seal']) == (full['root'], full['seal'])
                    identity = frame['packet_sha256']
                    model.begin(frame['fid'], identity, candidate, frame['key'], frame['tiles'], frame['same_mask'])
                    model.step()
                    assert model.tx.elisions == sum(elided)
                    tx = model.commit(authenticated=True)
                    tree.commit(plan)
                    model.present()
                    assert model.banks[model.reference] == frame['tiles']
                    assert tx.writes + tx.elisions == 8100
                    row = execution.account(frame, elided, plan)
                    row['granularity'] = granularity
                    row['root'] = plan['root'].hex()
                    row['seal'] = plan['seal'].hex()
                    stream.write(json.dumps(row, separators=(',', ':')) + '\n')
                    rows.append(row)
            assert len(rows) == 457 and sum(r['key'] for r in rows) == 20
            assert sum(r['resident_store_elisions'] for r in rows) * 4 == 6740876
            assert sum(r['controls']['v81_full_store_writes'] for r in rows) == 16013280
            for key in (True, False):
                group = [r for r in rows if r['key'] == key]
                summaries.append(dict(
                    granularity=granularity, key=key, sources=len(group),
                    reference_BL8_reads=sum(r['logical_BL8']['reference_reads'] for r in group),
                    canonical_BL8_writes=sum(r['logical_BL8']['canonical_writes'] for r in group),
                    data_and_HUD_BL8=sum(r['logical_BL8']['total'] for r in group),
                    mixed_hash_only_reference_tiles=sum(r['mixed_leaf_hash_only_reference_tiles'] for r in group),
                    SHA_blocks=stats([r['hash_compression_blocks'] for r in group]),
                    conditional_data_service_ms=stats([r['conditional_data_service_floor_cycles'] * 1e-5 for r in group]),
                    external_tree_scenario_service_ms=stats([r['external_tree_scenario']['conditional_service_floor_cycles'] * 1e-5 for r in group]),
                    hash_isolated_1lane_ms=stats([r['hash_isolated_list_schedule_cycles']['1'] * 1e-5 for r in group]),
                    hash_isolated_4lane_ms=stats([r['hash_isolated_list_schedule_cycles']['4'] * 1e-5 for r in group]),
                    onchip_tree_port_floor_ms=stats([r['metadata']['onchip_tree_port_floor_cycles'] * 1e-5 for r in group]),
                    tree_and_maps_bytes=group[0]['memory']['total_tree_and_maps_bytes'],
                    group_buffer_bytes=max(r['group_payload_buffer_bytes'] for r in group)))
            print('EXECUTION_GRANULARITY_PASS', granularity, len(rows), flush=True)
        assert pins == {p: sha(ROOT / p) for p in pins}, 'executed sources/data changed during run'
        report.update(status='PASS_NATIVE_COPY_AWARE_ACCOUNTING', summaries=summaries,
                      packet_CU66_profile_unchanged_in_native_oracle=True,
                      proposed_content_profile=commitment.PROFILE,
                      encoded_residual_payload_reencoded=False,
                      direct_flat_SHA_oracle='Frozen native collector and loader verification retain full CU66 canonical/HUD/display digests.',
                      per_frame_artifacts={p.name: sha(p) for p in sorted(out.glob('g*-frames.jsonl'))})
    except Exception as exc:
        report['failure'] = repr(exc)
        raise
    finally:
        report['wall_seconds'] = time.monotonic() - started
        (out / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(dict(status=report['status'], results_path=str((out / 'results.json').relative_to(ROOT)))), flush=True)


if __name__ == '__main__':
    main()
