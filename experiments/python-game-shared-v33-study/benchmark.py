#!/usr/bin/env python3
"""Rotated paid old-pair/shared-pair timing on 24 retained v32 source frames."""
import argparse
import gc
import json
import platform
import statistics
import time
import tracemalloc
import numpy as np
import helpers as h


def elapsed(fn):
    start = time.perf_counter_ns()
    out = fn()
    return out, (time.perf_counter_ns()-start)/1e6


def signature(value):
    packet, pixels, _ = value
    return dict(packet_sha256=h.digest(packet), packet_bytes=len(packet),
        plane_packet_sha256=[h.digest(p) for p in h.packet_planes(packet)],
        output_plane_sha256=[h.digest(a.astype('<i2').tobytes()) for a in pixels])


def parity(old, new):
    assert old[0] == new[0]
    assert h.packet_planes(old[0]) == h.packet_planes(new[0])
    for a, b in zip(old[1], new[1]): np.testing.assert_array_equal(a, b)


def peak(fn):
    gc.collect(); tracemalloc.start()
    result = fn()
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak_bytes, result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repeats', type=int, default=3)
    args = parser.parse_args()
    assert args.repeats >= 2
    before = h.pins()
    rows, memory = [], []
    for case, inp in h.cases():
        ref = None
        for prior, srcrow in zip(case['rows'][:12], inp['rows'][:12]):
            source = h.n.source(srcrow)
            assert h.digest(b''.join(a.astype('u1').tobytes() for a in source)) == srcrow['common_yuv420_u8_sha256']
            preparations = {}
            for old_attempt in prior['attempts']:
                kind = old_attempt['kind']
                if kind.endswith('_band'): continue
                bg = old_attempt['background']
                if kind not in preparations: preparations[kind] = h.prepare(source, ref, prior, kind)
                prepared = preparations[kind]
                assert prepared.reference_tag.hex() == prior['reference_tag']
                q = h.m.roi.declared_map(720, 480, h.n.ROIS, 8, bg)
                functions = dict(old=lambda:h.old_pair(prepared, q),
                                 shared=lambda:h.shared.encode_pair(h.m, prepared, q))
                times = dict(old=[], shared=[])
                # No hidden warmup: every measured call builds its private cache.
                for repeat in range(args.repeats):
                    results = {}
                    order = ('old','shared') if (prior['id']+repeat)%2 == 0 else ('shared','old')
                    for name in order:
                        results[name], wall = elapsed(functions[name]); times[name].append(wall)
                    for old, new in zip(results['old'], results['shared']): parity(old, new)
                old, new = results['old'], results['shared']
                band_attempt = next(a for a in prior['attempts'] if a['kind'] == kind+'_band' and a['background'] == bg)
                for value, attempt in zip(old, (old_attempt, band_attempt)):
                    assert value[0] == h.raw(attempt['base_packet'], h.V32)
                if prior['id'] == 0 and kind == 'zero' and bg == 16:
                    mem = dict(scene=case['scene'], frame_id=0, kind=kind, background=bg)
                    for name in ('old','shared'):
                        mem[name+'_tracemalloc_peak_bytes'], measured = peak(functions[name])
                        for a, b in zip(measured, old): parity(a, b)
                    memory.append(mem)
                records = []
                for label, value in zip(('incumbent','band_strict'), new):
                    records.append(dict(kind=label, packet=h.blob(value[0]), signature=signature(value), work=value[2]))
                old_inverse = 3+3+6+3+3 + 2*int(old[0][2]['rdo'].get('baseline_inverse_plane_calls',0))
                rows.append(dict(scene=case['scene'], frame_id=prior['id'], motion_kind=kind, background=bg,
                    source_sha256=srcrow['common_yuv420_u8_sha256'], reference_tag=prior['reference_tag'],
                    reference_id=prior['reference_id'], timing_ms=times,
                    paired_speedups=[a/b for a,b in zip(times['old'],times['shared'])],
                    old_work=[v[2] for v in old], records=records,
                    old_pair_calls=dict(quantize_calls=2,rdo_calls=2,inverse_plane_calls=old_inverse),
                    exact_packet_plane_and_output_parity=True))
            retained = h.raw(prior['base_packet'], h.V32)
            ref, _ = h.m.decode(retained, ref, expected_epoch=25,
                expected_reference_id=None if prior['key'] else prior['reference_id'])
            print(json.dumps(dict(scene=case['scene'], frame=prior['id'], pairs=len(rows))), flush=True)
    old_total = sum(sum(r['timing_ms']['old']) for r in rows)
    shared_total = sum(sum(r['timing_ms']['shared']) for r in rows)
    counts = [r['records'][0]['work']['shared_pair'] for r in rows]
    old_legacy_calls = sum(r['old_work'][0]['legacy_size_counter_calls'] +
        sum(sum(p['size_counter_calls'] for p in detail['incumbent_legacy_trials']) +
            sum(c['plan']['legacy']['size_counter_calls'] for c in detail['candidate_plans'])
            for detail in r['old_work'][1]['planes']) for r in rows)
    summary = dict(source_frames=24, pairs=len(rows), output_packets=2*len(rows), repeats=args.repeats,
        mean_old_pair_ms=old_total/(len(rows)*args.repeats),
        mean_shared_pair_ms=shared_total/(len(rows)*args.repeats), aggregate_speedup=old_total/shared_total,
        median_paired_speedup=statistics.median(v for r in rows for v in r['paired_speedups']),
        old_quantize_calls=2*len(rows), shared_quantize_calls=len(rows),
        old_rdo_calls=2*len(rows), shared_rdo_calls=len(rows),
        reused_incumbent_plane_payloads=sum(c['reused_incumbent_plane_payloads'] for c in counts),
        old_legacy_size_counter_calls=old_legacy_calls,
        shared_legacy_size_counter_calls=sum(c['legacy_size_counter_calls'] for c in counts),
        old_ec26_construct_calls=sum(w['ec26_construct_calls'] for r in rows for w in r['old_work']),
        shared_ec26_construct_calls=sum(c['ec26_construct_calls'] for c in counts),
        old_cp02_construct_calls=sum(w['actual_cp02_encode_calls'] for r in rows for w in r['old_work']),
        shared_cp02_construct_calls=sum(c['actual_cp02_encode_calls'] for c in counts),
        shared_ec26_plan_calls=sum(c['ec26_plan_calls'] for c in counts),
        shared_inverse_plane_calls=sum(c['inverse_plane_calls'] for c in counts),
        old_inverse_plane_calls=sum(r['old_pair_calls']['inverse_plane_calls'] for r in rows),
        exact_packet_plane_and_output_parity=True)
    assert h.pins() == before
    data = dict(schema='gamebub-shared-v33', parent_commit='293b8b2e3a58db733eddd10c635ec7df29789f70',
        source_sha256=before, environment=dict(python=platform.python_version(),numpy=np.__version__,platform=platform.platform()),
        summary=summary, memory=memory, rows=rows, unchanged_GM27_wire=True, physical_30fps_proven=False,
        scope=['First 12 frames of each v32 band_control accepted causal history; all backgrounds and motion variants actually attempted.',
            'Pair timing includes validation, private plan setup, quantization, RDO, all band candidates, winning serialization and both output packets.',
            'Rotated paired repeats; no hidden warmup or persistent cache. Timing excludes analysis/search, fixture read, parity decode, artifact I/O, HUD, RGB scoring, networking and display.',
            'tracemalloc separately measures first bg16 key pair per scene; tracing overhead is excluded from timings.',
            'Private coefficient byte counters are conservative sums and may double-count aliased arrays; tracemalloc measures transient allocation peak.'])
    (h.HERE/'results.json').write_text(json.dumps(data,separators=(',',':'),allow_nan=False)+'\n')
    print(json.dumps(summary), flush=True)


if __name__ == '__main__': main()
