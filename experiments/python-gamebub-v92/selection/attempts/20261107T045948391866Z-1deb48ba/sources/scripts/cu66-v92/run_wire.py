#!/usr/bin/env python3
"""Exact bounded context selection and actual complete CS92 reconstruction.

Work counts are measured entropy operations, not FPGA cycle estimates.
"""
import datetime
import gzip
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import statistics
import struct
import subprocess
import sys
import time
import uuid
import zlib

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v92/wire'
CONTAINER = 'gamebub-cu66-v69-build'
POLICIES = ('context_byte_min', 'context_work5', 'context_work15', 'whole_plane_work15')


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stats(values):
    return dict(min=min(values), median=statistics.median(values), max=max(values), total=sum(values))


def pareto(planes, fixed):
    """At most 16 choices/plane, 4096 terminal combinations; exact pruning.

    Keep the best lexicographic (AB decisions, renorm, BR bits, mask) at each
    byte count, then discard states dominated in both bytes and that objective.
    Nonnegative additive work makes this pruning exact, including tie breaks.
    """
    states = [(fixed, 0, 0, 0, 0)]
    expanded = peak = 0
    for axis, choices in enumerate(planes):
        proposed = [(s[0]+c['bytes'], s[1]+c['ab_decisions'], s[2]+c['ab_renorm'],
                     s[3]+c['br_bits'], s[4] | (c['requested_mask'] << (4*axis)))
                    for s in states for c in choices]
        expanded += len(proposed)
        peak = max(peak, len(proposed))
        best = None
        states = []
        for item in sorted(proposed):
            if best is None or item[1:] < best:
                states.append(item)
                best = item[1:]
    return states, expanded, peak


def exhaustive(planes, fixed):
    return [(fixed+sum(c['bytes'] for c in choice),
             sum(c['ab_decisions'] for c in choice), sum(c['ab_renorm'] for c in choice),
             sum(c['br_bits'] for c in choice), sum(c['requested_mask'] << (4*a) for a, c in enumerate(choice)))
            for choice in itertools.product(*planes)]


def pick(states, budget, byte_min=False):
    feasible = [s for s in states if s[0] <= budget]
    assert feasible, ('no admissible candidate', budget)
    return min(feasible, key=(lambda s: (s[0], *s[1:])) if byte_min else (lambda s: (*s[1:], s[0])))


def main():
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA / 'attempts' / (stamp + '-' + uuid.uuid4().hex[:8])
    out.mkdir(parents=True)
    data = load('ec92_data', ROOT / 'experiments/python-gamebub-v92/native/data.py')
    old88 = load('ec92_old88', ROOT / 'scripts/cu66-v88/run_wire.py')
    wire = load('ec92_frame', ROOT / 'scripts/cu66-v86/run_wire.py')
    qcodec = load('ec92_qmap', ROOT / 'scripts/cu66-v87/quantizer_codec.py')
    native = load('ec92_frames', ROOT / 'experiments/python-gamebub-v82/native/data.py')
    oldmap = load('ec92_mode_old', ROOT / 'scripts/cu66-v84/prototype_mode_map_v2.py')
    groupmap = load('ec92_mode_group', ROOT / 'scripts/cu66-v86/prototype_maps.py')
    prior = json.loads((ROOT / 'experiments/python-gamebub-v88/wire/results.json').read_text())
    control_path = (ROOT / prior['selected_report']).with_name('candidates.jsonl')
    controls = {(r['cohort'], r['fid'], r['mask']): r for r in map(json.loads, control_path.read_text().splitlines())}
    commitment = {(r['cohort'], r['fid']): r for r in map(json.loads, wire.C2_CONTROL.read_text().splitlines())}
    sources = [Path(__file__).resolve(), AREA/'receiver.cpp', control_path, wire.C2_CONTROL]
    sources += [ROOT/p for p in ('scripts/cu66-v88/run_wire.py', 'scripts/cu66-v86/run_wire.py',
        'scripts/cu66-v87/quantizer_codec.py', 'scripts/cu66-v84/prototype_mode_map_v2.py',
        'scripts/cu66-v86/prototype_maps.py', 'experiments/python-gamebub-v92/native/data.py',
        'experiments/python-gamebub-v92/native/codec.hpp', 'experiments/python-gamebub-v92/native/index.json')]
    sources += sorted((ROOT/'experiments/cu66-native-v69').glob('*.hpp'))
    sources += [ROOT/'experiments/python-gamebub-v88/entropy/codec.hpp', ROOT/'experiments/python-gamebub-v85/residual/encode.hpp']
    pins = {str(p.relative_to(ROOT)): sha(p) for p in sources}
    for path in sources:
        dest = out/'sources'/path.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(path.read_bytes())
    report = dict(schema='cu66-v92-full-context-selection-v1', status='FAIL', source_sha256=pins,
                  cap_bytes=49152, physical_30fps_proven=False, validated_under10ms_proven=False,
                  v92d_promoted=False, commands=[], policies=list(POLICIES),
                  scope=['Actual EC92 bytes in CS92, native full coefficient/pixel/HUD/reference/seal reconstruction.',
                         '4096 exhaustive combinations are compared to exact bounded Pareto selection; no reencoding during search.',
                         'Adaptive decisions are a selection objective, not calibrated memory/FPGA latency. V92d remains open.'])
    binary = '/build/v92-wire-' + stamp
    processes = {}
    rows = []
    qcache = {}
    search_rows = []
    started = time.monotonic()
    try:
        command = ['docker', 'exec', CONTAINER, 'g++', '-std=c++17', '-O2', '-Wall', '-Wextra', '-Werror', str(AREA/'receiver.cpp'), '-o', binary]
        compiled = subprocess.run(command, capture_output=True, text=True, timeout=120)
        (out/'compile.log').write_text(compiled.stdout+compiled.stderr)
        report['commands'].append(dict(argv=command, observed_exit_code=compiled.returncode))
        assert compiled.returncode == 0, compiled.stderr
        copied = subprocess.run(['docker', 'cp', CONTAINER+':'+binary, str(out/'receiver.bin')], capture_output=True, text=True, timeout=30)
        assert copied.returncode == 0, copied.stderr
        for policy in POLICIES:
            log = (out/(policy+'.stderr')).open('wb')
            processes[policy] = (subprocess.Popen(['docker', 'exec', '-i', CONTAINER, binary], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log), log)
        with (out/'frames.jsonl').open('w') as output, (out/'selection.jsonl').open('w') as selections, gzip.open(out/'packets.bin.gz', 'wb') as archive:
            for frame, original in zip(data.iter_frames(), native.iter_frames(), strict=True):
                ident = frame['cohort'], frame['fid']
                assert all(frame[k] == original[k] for k in ('cohort', 'fid', 'ordinal', 'key'))
                flat = [c for plane in frame['variants']['65536'] for c in plane]
                assert len(flat) == 3 and all(len(p) == 1 for p in frame['variants']['65536'])
                choices = [[dict(m, **{k: sum(m[k]) if isinstance(m[k], list) else m[k]
                                      for k in ('ab_decisions', 'ab_renorm', 'br_bits')})
                            for m in c['ec92_stats']['masks']] for c in flat]
                assert all(len(p) == 16 for p in choices)
                # Complete old control plus the two new bytes per plane header.
                base = controls[(*ident, 0)]['wire_bytes']
                fixed = base - sum(len(c['data']) for c in flat)
                assert all(c['ec92'][0][:4] == b'EC92' for c in flat)
                # Whole-plane choices preserve each frozen AB38/BR88 stream.
                for mask in range(8):
                    size = fixed + sum(choices[a][15 if mask & (1 << a) else 0]['bytes'] for a in range(3))
                    assert size == controls[(*ident, mask)]['wire_bytes'] + 6
                before = time.perf_counter_ns()
                frontier, expanded, peak = pareto(choices, fixed)
                search_ns = time.perf_counter_ns()-before
                all_options = exhaustive(choices, fixed)
                assert len(all_options) == 4096
                whole = exhaustive([[p[0], p[15]] for p in choices], fixed)
                chosen = {}
                for policy in POLICIES:
                    budget = 49152 if policy == 'context_byte_min' else min(49152, base*(105 if policy.endswith('5') and not policy.endswith('15') else 115)//100)
                    states = whole if policy.startswith('whole') else frontier
                    selected = pick(states, budget, policy == 'context_byte_min')
                    reference = pick(whole if policy.startswith('whole') else all_options, budget, policy == 'context_byte_min')
                    assert selected == reference, ('bounded search differs', ident, policy)
                    chosen[policy] = (selected, budget)
                search = dict(cohort=frame['cohort'], fid=frame['fid'], exhaustive_combinations=4096,
                              expanded_states=expanded, peak_states=peak, final_frontier=len(frontier), search_ns=search_ns,
                              AB38_wire_bytes=base, old_plane_min_bytes=min(controls[(*ident, m)]['wire_bytes'] for m in range(8)))
                selections.write(json.dumps(search, separators=(',', ':'))+'\n')
                search_rows.append(search)
                operations = [1 if h else 0 if not frame['key'] and frame['zero_mask'][t] == '1' else 2 for t, h in enumerate(original['hidden_mask'])]
                previous = None if frame['key'] else qcache.get(frame['cohort'])
                qblock = qcodec.encode(qcodec.unpacked(frame['qmap'], 1350), operations, previous)
                qcache[frame['cohort']] = qcodec.decode(qblock, operations, previous)
                for policy, (selected, budget) in chosen.items():
                    masks = [(selected[4] >> (4*a)) & 15 for a in range(3)]
                    planes = [[dict(blocks=c['blocks'], data=c['ec92'][masks[a]])] for a, c in enumerate(flat)]
                    packet, components, _ = wire.frame_packet(dict(frame, variants={'65536': planes}), original, commitment[ident], dict(kind='copy_group', cap=65536), oldmap, groupmap)
                    packet = old88.cs88(packet, qblock)
                    packet = b'CS92'+packet[4:-4]
                    packet += struct.pack('>I', zlib.crc32(packet))
                    assert len(packet) == selected[0] <= budget <= 49152
                    process = processes[policy][0]
                    process.stdin.write(struct.pack('>II', frame['cohort'], len(packet))+packet)
                    process.stdin.flush()
                    decoded = json.loads(process.stdout.readline())
                    assert decoded['accepted'] and not decoded['replayed'], (policy, ident, decoded)
                    for k in ('canonical_sha256', 'hud_sha256', 'display_sha256'):
                        assert decoded[k] == frame[k], (policy, ident, k)
                    assert decoded['coefficient_sha256'] == frame['canonical_coefficients_sha256']
                    for k in ('root', 'seal'):
                        assert decoded[k] == commitment[ident][k], (policy, ident, k)
                    assert decoded['generation'] == frame['ordinal']+1 and decoded['wire_bytes'] == len(packet)
                    row = dict(policy=policy, cohort=frame['cohort'], fid=frame['fid'], ordinal=frame['ordinal'],
                               key=frame['key'], mask=selected[4], plane_masks=masks, wire_bytes=len(packet),
                               ab_decisions=selected[1], ab_renorm=selected[2], br_bits=selected[3], budget=budget,
                               old_AB38_bytes=base, old_plane_min_bytes=search['old_plane_min_bytes'],
                               packet_sha256=hashlib.sha256(packet).hexdigest(), decoded=decoded)
                    output.write(json.dumps(row, separators=(',', ':'))+'\n')
                    rows.append(row)
                    meta = json.dumps(row, separators=(',', ':')).encode()
                    archive.write(struct.pack('<II', len(meta), len(packet))+meta+packet)
                    if frame['cohort'] == 0 and frame['fid'] in (0, 1, 2):
                        (out/f'c0-f{frame["fid"]}-{policy}.cs92').write_bytes(packet)
                if len(search_rows) % 50 == 0:
                    print('V92_WIRE_PROGRESS', len(search_rows), flush=True)
        for policy, (process, log) in processes.items():
            process.stdin.close()
            assert process.wait(timeout=30) == 0, policy
            log.close()
        assert len(search_rows) == 457 and len(rows) == 457*len(POLICIES)
        assert pins == {p: sha(ROOT/p) for p in pins}, 'sources changed during execution'
        report['summaries'] = [dict(policy=p, frames=457, wire_bytes=stats([r['wire_bytes'] for r in rows if r['policy'] == p]),
            ab_decisions=sum(r['ab_decisions'] for r in rows if r['policy'] == p),
            ab_renorm=sum(r['ab_renorm'] for r in rows if r['policy'] == p),
            br_bits=sum(r['br_bits'] for r in rows if r['policy'] == p),
            mixed_plane_chunks=sum(m not in (0, 15) for r in rows if r['policy'] == p for m in r['plane_masks'])) for p in POLICIES]
        report.update(status='PASS_NATIVE_CS92_CONTEXT_SELECTION', frames=457, received_packets=len(rows),
                      exhaustive_combinations=457*4096, source_coding_alternatives=457*3*2,
                      pareto_expanded=stats([r['expanded_states'] for r in search_rows]),
                      pareto_peak=stats([r['peak_states'] for r in search_rows]),
                      pareto_search_ns=stats([r['search_ns'] for r in search_rows]), binary=binary)
    except BaseException as exc:
        report['failure'] = repr(exc)
        raise
    finally:
        for process, log in processes.values():
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=15)
            if not log.closed:
                log.close()
        report['wall_seconds'] = time.monotonic()-started
        report['artifact_sha256'] = {str(p.relative_to(out)): sha(p) for p in out.rglob('*') if p.is_file()}
        (out/'results.json').write_text(json.dumps(report, indent=2)+'\n')
        print('V92_WIRE_REPORT', out/'results.json', report['status'], flush=True)
    (AREA/'results.json').write_text(json.dumps(dict(report, selected_report=str((out/'results.json').relative_to(ROOT))), indent=2)+'\n')


if __name__ == '__main__':
    main()
