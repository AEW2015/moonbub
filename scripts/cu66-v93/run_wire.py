#!/usr/bin/env python3
"""Actual CS93 prefix/suffix and small-group Rice complete-frame comparison."""
import datetime
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import signal
import statistics
import struct
import subprocess
import sys
import time
import uuid
import zlib

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT/'experiments/python-gamebub-v93/wire'
CONTAINER = 'gamebub-cu66-v69-build'
POLICIES = ('all_AB', 'all_BR', 'prefix_suffix', 'small_group', 'byte_min',
            'v92_byte_min', 'v92_work15', 'work5', 'work15')
WORK_KEYS = ('ab_decisions', 'ab_renorm', 'plain_bits', 'arithmetic_inits', 'group_headers')


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stats(values):
    return dict(min=min(values), median=statistics.median(values), max=max(values), total=sum(values))


def split(packet):
    assert packet[:5] == b'EC93\x01' and packet[5] == 0, 'coded corpus only'
    lengths = struct.unpack_from('<4I', packet, 16)
    streams = []
    at = 44
    for size in lengths:
        streams.append(packet[at:at+size])
        at += size
    assert at+4 == len(packet) and zlib.crc32(packet[:-4]) == int.from_bytes(packet[-4:], 'little')
    return streams


def assemble(packets, selector):
    """Compose actual encoded streams, never re-encode or alter coefficients."""
    sources = [split(p) for p in packets[:4]]
    streams = [sources[(selector >> (2*c)) & 3][c] for c in range(4)]
    head = bytearray(packets[0][:44])
    head[6] = selector
    struct.pack_into('<4I', head, 16, *map(len, streams))
    assert sum(map(len, streams)) < 128*struct.unpack_from('<I', head, 8)[0], 'requires RAW fallback'
    result = bytes(head)+b''.join(streams)
    return result+struct.pack('<I', zlib.crc32(result))


def work_key(state):
    return state[1], state[2], state[3], state[0], state[4]


def beam(choices, fixed, budget, width=128):
    """Finite approximate host search; no global optimality claim.

    State=(bytes, decisions, renorm, plainbits, selector). Preserve low-byte
    and low-work Pareto extremes at each step. At most 512 proposals/stage.
    """
    assert len(choices) == 12 and width >= 2
    remaining = [0]*13
    for i in range(11, -1, -1):
        remaining[i] = remaining[i+1]+min(c[0] for c in choices[i])
    states = [(fixed, 0, 0, 0, 0)]
    expanded = peak = truncations = 0
    for index, options in enumerate(choices):
        proposed = [(s[0]+c[0], s[1]+c[1], s[2]+c[2], s[3]+c[3], s[4] | (m << (2*index)))
                    for s in states for m, c in enumerate(options)
                    if s[0]+c[0]+remaining[index+1] <= budget]
        expanded += len(proposed)
        peak = max(peak, len(proposed))
        states = []
        best = None
        for state in sorted(proposed):
            if best is None or state[1:4] < best:
                states.append(state)
                best = state[1:4]
        if len(states) > width:
            truncations += 1
            half = width//2
            keep = set(states[:half]+sorted(states, key=work_key)[:width-half])
            states = sorted(keep)
        if not states:
            raise ValueError('no feasible CS93 beam candidate')
    return min(states, key=work_key), dict(expanded=expanded, peak=peak, truncations=truncations)


def expand92(mask):
    return sum(((mask >> bit) & 1) << (2*bit) for bit in range(4))


def main():
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA/'attempts'/(stamp+'-'+uuid.uuid4().hex[:8])
    out.mkdir(parents=True)
    data = load('v93_data', ROOT/'experiments/python-gamebub-v93/native/data.py')
    wire = load('v93_frame', ROOT/'scripts/cu66-v86/run_wire.py')
    old88 = load('v93_qframe', ROOT/'scripts/cu66-v88/run_wire.py')
    qcodec = load('v93_qmap', ROOT/'scripts/cu66-v87/quantizer_codec.py')
    native = load('v93_original', ROOT/'experiments/python-gamebub-v82/native/data.py')
    oldmap = load('v93_oldmap', ROOT/'scripts/cu66-v84/prototype_mode_map_v2.py')
    groupmap = load('v93_groupmap', ROOT/'scripts/cu66-v86/prototype_maps.py')
    control_report = ROOT/json.loads((ROOT/'experiments/python-gamebub-v92/wire/results.json').read_text())['selected_report']
    controls = {(r['policy'], r['cohort'], r['fid']): r for r in map(json.loads, control_report.with_name('frames.jsonl').read_text().splitlines())}
    commitments = {(r['cohort'], r['fid']): r for r in map(json.loads, wire.C2_CONTROL.read_text().splitlines())}
    sources = [Path(__file__).resolve(), AREA/'receiver.cpp', control_report, control_report.with_name('frames.jsonl'), wire.C2_CONTROL]
    sources += [ROOT/p for p in ('experiments/python-gamebub-v93/native/codec.hpp', 'experiments/python-gamebub-v93/native/data.py',
        'experiments/python-gamebub-v93/native/index.json', 'experiments/python-gamebub-v92/native/codec.hpp',
        'experiments/python-gamebub-v88/entropy/codec.hpp', 'experiments/python-gamebub-v85/residual/encode.hpp',
        'scripts/cu66-v86/run_wire.py', 'scripts/cu66-v88/run_wire.py', 'scripts/cu66-v87/quantizer_codec.py',
        'scripts/cu66-v84/prototype_mode_map_v2.py', 'scripts/cu66-v86/prototype_maps.py',
        'experiments/python-gamebub-v82/native/data.py', 'experiments/python-gamebub-v82/native/index.json',
        'experiments/python-gamebub-v88/entropy/data.py', 'experiments/python-gamebub-v88/entropy/index.json',
        'experiments/python-gamebub-v85/residual/data.py', 'experiments/python-gamebub-v85/residual/index.json')]
    sources += sorted((ROOT/'experiments/cu66-native-v69').glob('*.hpp'))
    pins = {str(p.relative_to(ROOT)): sha(p) for p in sources}
    for p in sources:
        dest = out/'sources'/p.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(p.read_bytes())
    report = dict(schema='cu66-v93-full-wire-v1', status='FAIL', source_sha256=pins, policies=list(POLICIES),
                  target_cap_bytes=49152, diagnostic_research_cap_bytes=2097152, beam_width=128,
                  physical_30fps_proven=False, validated_under10ms_proven=False, promoted_to_RTL=False, commands=[],
                  scope=['Direct CS93/EC93 reconstruction; exact coefficients, pixels, references, semantic HUD and seals.',
                         'Homogeneous method controls may exceed target cap; diagnostic receiver acceptance is reported separately.',
                         'Beam selection is bounded and approximate; measured operation counts are not calibrated FPGA cycles.'])
    binary = '/build/v93-wire-'+stamp
    research_binary = binary+'-research'
    processes = {}
    rows = []
    searches = []
    qcache = {}
    started = time.monotonic()
    prior = signal.getsignal(signal.SIGALRM)
    signal.signal(signal.SIGALRM, lambda _s, _f: (_ for _ in ()).throw(TimeoutError('CS93 watchdog')))
    signal.setitimer(signal.ITIMER_REAL, 1200)
    try:
        for target, flags in ((binary, []), (research_binary, ['-DCS93_RESEARCH=1'])):
            command = ['docker', 'exec', CONTAINER, 'g++', '-std=c++17', '-O2', '-Wall', '-Wextra', '-Werror', *flags, str(AREA/'receiver.cpp'), '-o', target]
            result = subprocess.run(command, capture_output=True, text=True, timeout=120)
            (out/('compile-research.log' if flags else 'compile.log')).write_text(result.stdout+result.stderr)
            report['commands'].append(dict(argv=command, exit_code=result.returncode))
            assert result.returncode == 0, result.stderr
            copied = subprocess.run(['docker', 'cp', CONTAINER+':'+target, str(out/('research.bin' if flags else 'receiver.bin'))], capture_output=True, timeout=30)
            assert copied.returncode == 0
        for policy in POLICIES:
            diagnostic = policy in ('all_BR', 'prefix_suffix', 'small_group')
            log = (out/(policy+'.stderr')).open('wb')
            processes[policy] = (subprocess.Popen(['docker', 'exec', '-i', CONTAINER, research_binary if diagnostic else binary],
                                                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log), log)
        with (out/'frames.jsonl').open('w') as output, (out/'search.jsonl').open('w') as search_output, gzip.open(out/'packets.bin.gz', 'wb') as archive:
            for frame, original in zip(data.iter_frames(), native.iter_frames(), strict=True):
                ident = frame['cohort'], frame['fid']
                assert all(frame[k] == original[k] for k in ('cohort', 'fid', 'ordinal', 'key'))
                flat = [c for p in frame['variants']['65536'] for c in p]
                assert len(flat) == 3 and all(len(p) == 1 for p in frame['variants']['65536'])
                streams = [[split(p) for p in c['ec93'][:4]] for c in flat]
                observations = [c['ec93_stats']['masks'][:4] for c in flat]
                base = controls[('context_byte_min', *ident)]['old_AB38_bytes']
                fixed = base-sum(len(c['data']) for c in flat)+3*48
                choices = []
                for axis in range(3):
                    for context in range(4):
                        choices.append([(len(streams[axis][m][context]), observations[axis][m]['ab_decisions'][context],
                                         observations[axis][m]['ab_renorm'][context], observations[axis][m]['plain_bits'][context]) for m in range(4)])

                def price(selectors):
                    total = [fixed, 0, 0, 0, sum(s << (8*a) for a, s in enumerate(selectors))]
                    for index, options in enumerate(choices):
                        method = (total[4] >> (2*index)) & 3
                        for k in range(4):
                            total[k] += options[method][k]
                    return tuple(total)

                selected = {name: [m*85]*3 for name, m in (('all_AB', 0), ('all_BR', 1), ('prefix_suffix', 2), ('small_group', 3))}
                selected['byte_min'] = [sum(min(range(4), key=lambda m: (len(streams[a][m][c]), observations[a][m]['ab_decisions'][c],
                                                                   observations[a][m]['ab_renorm'][c], observations[a][m]['plain_bits'][c], m)) << (2*c)
                                                   for c in range(4)) for a in range(3)]
                for policy, old_policy in (('v92_byte_min', 'context_byte_min'), ('v92_work15', 'context_work15')):
                    selected[policy] = [expand92(m) for m in controls[(old_policy, *ident)]['plane_masks']]
                    assert price(selected[policy])[0] == controls[(old_policy, *ident)]['wire_bytes'], 'V92 matched-byte control'
                assert price(selected['all_AB'])[0] == base+6
                before = time.perf_counter_ns()
                for policy, percent in (('work5', 105), ('work15', 115)):
                    budget = min(49152, base*percent//100)
                    best, search = beam(choices, fixed, budget)
                    # Frozen controls and byte-min are always explicitly included.
                    anchors = [price(selected[n]) for n in ('byte_min', 'v92_byte_min', 'v92_work15')]
                    best = min([best]+[p for p in anchors if p[0] <= budget], key=work_key)
                    selected[policy] = [(best[4] >> (8*a)) & 255 for a in range(3)]
                    search_row = dict(policy=policy, cohort=frame['cohort'], fid=frame['fid'], **search)
                    searches.append(search_row)
                    search_output.write(json.dumps(search_row, separators=(',', ':'))+'\n')
                search_ns = time.perf_counter_ns()-before
                operations = [1 if h else 0 if not frame['key'] and frame['zero_mask'][t] == '1' else 2 for t, h in enumerate(original['hidden_mask'])]
                previous = None if frame['key'] else qcache.get(frame['cohort'])
                qblock = qcodec.encode(qcodec.unpacked(frame['qmap'], 1350), operations, previous)
                qcache[frame['cohort']] = qcodec.decode(qblock, operations, previous)
                for policy, selectors in selected.items():
                    priced = price(selectors)
                    planes = [[dict(blocks=c['blocks'], data=assemble(c['ec93'], selectors[a]))] for a, c in enumerate(flat)]
                    packet, _, _ = wire.frame_packet(dict(frame, variants={'65536': planes}), original, commitments[ident], dict(kind='copy_group', cap=65536), oldmap, groupmap)
                    packet = old88.cs88(packet, qblock)
                    body = b'CS93'+packet[4:-4]
                    packet = body+struct.pack('>I', zlib.crc32(body))
                    assert len(packet) == priced[0]
                    diagnostic = policy in ('all_BR', 'prefix_suffix', 'small_group')
                    if not diagnostic:
                        assert len(packet) <= 49152
                    budget = min(49152, base*(105 if policy == 'work5' else 115)//100) if policy in ('work5', 'work15') else None
                    if budget is not None:
                        assert len(packet) <= budget
                    process = processes[policy][0]
                    process.stdin.write(struct.pack('>II', frame['cohort'], len(packet))+packet)
                    process.stdin.flush()
                    decoded = json.loads(process.stdout.readline())
                    assert decoded['accepted'] and not decoded['replayed'], (policy, ident, decoded)
                    for k in ('canonical_sha256', 'hud_sha256', 'display_sha256'):
                        assert decoded[k] == frame[k], (policy, ident, k)
                    assert decoded['coefficient_sha256'] == frame['canonical_coefficients_sha256']
                    for k in ('root', 'seal'):
                        assert decoded[k] == commitments[ident][k]
                    assert decoded['generation'] == frame['ordinal']+1 and decoded['wire_bytes'] == len(packet)
                    work = {k: sum(observations[a][(selectors[a] >> (2*c)) & 3][k][c] for a in range(3) for c in range(4)) for k in WORK_KEYS}
                    assert (work['ab_decisions'], work['ab_renorm'], work['plain_bits']) == priced[1:4]
                    row = dict(policy=policy, cohort=frame['cohort'], fid=frame['fid'], ordinal=frame['ordinal'], key=frame['key'],
                               selectors=selectors, wire_bytes=len(packet), fits_49152=len(packet) <= 49152,
                               diagnostic_receiver=diagnostic, budget=budget, old_AB38_bytes=base, search_ns=search_ns,
                               methods=[(s >> (2*c)) & 3 for s in selectors for c in range(4)],
                               packet_sha256=hashlib.sha256(packet).hexdigest(), decoded=decoded, **work)
                    output.write(json.dumps(row, separators=(',', ':'))+'\n')
                    rows.append(row)
                    meta = json.dumps(row, separators=(',', ':')).encode()
                    archive.write(struct.pack('<II', len(meta), len(packet))+meta+packet)
                    if frame['cohort'] == 0 and frame['fid'] in (0, 1, 2):
                        (out/f'c0-f{frame["fid"]}-{policy}.cs93').write_bytes(packet)
                if len(rows)//len(POLICIES) % 50 == 0:
                    print('V93_WIRE_PROGRESS', len(rows)//len(POLICIES), flush=True)
        assert len(rows) == 457*len(POLICIES)
        for policy, (process, log) in processes.items():
            process.stdin.close()
            assert process.wait(timeout=30) == 0, policy
            log.close()
        assert pins == {p: sha(ROOT/p) for p in pins}, 'source changed during campaign'
        summaries = []
        for policy in POLICIES:
            group = [r for r in rows if r['policy'] == policy]
            summaries.append(dict(policy=policy, frames=457, wire_bytes=stats([r['wire_bytes'] for r in group]),
                                  fits_49152=sum(r['fits_49152'] for r in group), **{k: sum(r[k] for r in group) for k in WORK_KEYS},
                                  method_streams=[sum(r['methods'].count(m) for r in group) for m in range(4)]))
        report.update(status='PASS_NATIVE_CS93_FULL_FRAME_PARITY', frames=457, packets=len(rows), summaries=summaries,
                      beam_expanded=stats([r['expanded'] for r in searches]), beam_peak=max(r['peak'] for r in searches),
                      beam_truncated_stages=sum(r['truncations'] for r in searches),
                      two_search_ns=stats([r['search_ns'] for r in rows if r['policy'] == 'byte_min']),
                      binary=binary, research_binary=research_binary)
    except BaseException as error:
        report['failure'] = repr(error)
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, prior)
        for process, log in processes.values():
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=15)
            if not log.closed:
                log.close()
        report['wall_seconds'] = time.monotonic()-started
        report['artifacts_sha256'] = {str(p.relative_to(out)): sha(p) for p in out.rglob('*') if p.is_file()}
        (out/'results.json').write_text(json.dumps(report, indent=2)+'\n')
        print('V93_WIRE_REPORT', out/'results.json', report['status'], flush=True)
    (AREA/'results.json').write_text(json.dumps(dict(report, selected_report=str((out/'results.json').relative_to(ROOT))), indent=2)+'\n')


if __name__ == '__main__':
    main()
