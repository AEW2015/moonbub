#!/usr/bin/env python3
"""Compose actual EC94 streams into complete CS94 packets and audit receivers."""
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
AREA = ROOT/'experiments/python-gamebub-v94/wire'
CONTAINER = 'gamebub-cu66-v69-build'
POLICIES = ('all_AB', 'all_BR', 'rans2_s8', 'rans2_s9', 'rans2_s10',
            'rans4_s8', 'rans4_s9', 'rans4_s10', 'byte_min', 'v92_byte_min')
SELECTOR_METHOD = (0, 1, 2, 2, 2, 3, 3, 3)
RESEARCH_POLICIES = frozenset(('all_BR', 'rans2_s8', 'rans2_s9', 'rans2_s10',
                               'rans4_s8', 'rans4_s9', 'rans4_s10'))
WORK_KEYS = ('ab_decisions', 'ab_renorm', 'literal_bits', 'ans_symbols',
             'ans_renorm_bytes', 'model_tables', 'model_entries', 'ans_lanes')


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
    assert packet[:5] == b'EC94\x01' and packet[5] == 0, 'coded EC94 corpus required'
    lengths = struct.unpack_from('<4I', packet, 16)
    streams = []
    at = 44
    for size in lengths:
        streams.append(packet[at:at+size])
        at += size
    assert at+4 == len(packet) and zlib.crc32(packet[:-4]) == int.from_bytes(packet[-4:], 'little')
    return streams


def assemble(packets, choices):
    """Join exact context streams from the eight homogeneous EC94 encodings."""
    assert len(choices) == 4 and all(0 <= c < 8 for c in choices)
    if packets[0][5]:
        # The encoder's finite whole-chunk RAW fallback is identical for all variants.
        assert all(p[5] and p == packets[0] for p in packets)
        return packets[0]
    sources = [split(p) for p in packets[:8]]
    streams = [sources[choices[c]][c] for c in range(4)]
    head = bytearray(packets[0][:44])
    selector = sum(SELECTOR_METHOD[choices[c]] << (2*c) for c in range(4))
    head[6] = selector
    struct.pack_into('<4I', head, 16, *map(len, streams))
    result = bytes(head)+b''.join(streams)
    return result+struct.pack('<I', zlib.crc32(result))


def expand92(mask):
    """Map the frozen V92 AB/BR decision bit per context to EC94 variants."""
    return tuple((mask >> context) & 1 for context in range(4))


def metric_tuple(metrics, variant, context):
    row = metrics[variant]
    keys = ('ab_decisions', 'ans_symbols', 'literal_bits')
    for key in keys:
        assert len(row[key]) == 4, ('EC94 metric shape', variant, key)
    return tuple(int(row[key][context]) for key in keys)


def selected_work(metrics, choices):
    result = {key: 0 for key in WORK_KEYS}
    for context, variant in enumerate(choices):
        row = metrics[variant]
        for key in WORK_KEYS:
            assert len(row[key]) == 4, ('EC94 metric shape', variant, key)
            result[key] += int(row[key][context])
    return result


def policy_choices(policy, packets, metrics, v92_masks):
    if policy == 'all_AB':
        return (0, 0, 0, 0)
    if policy == 'all_BR':
        return (1, 1, 1, 1)
    if policy == 'rans2_s8':
        return (2, 2, 2, 2)
    if policy == 'rans2_s9':
        return (3, 3, 3, 3)
    if policy == 'rans2_s10':
        return (4, 4, 4, 4)
    if policy == 'rans4_s8':
        return (5, 5, 5, 5)
    if policy == 'rans4_s9':
        return (6, 6, 6, 6)
    if policy == 'rans4_s10':
        return (7, 7, 7, 7)
    if policy == 'v92_byte_min':
        return expand92(v92_masks)
    if policy == 'byte_min':
        lengths = [split(p) if not p[5] else [] for p in packets[:8]]
        return tuple(min(range(8), key=lambda variant: (
            len(packets[variant]) if packets[variant][5] else len(lengths[variant][context]),
            *metric_tuple(metrics, variant, context), variant)) for context in range(4))
    raise ValueError(f'unknown policy {policy}')


def main():
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA/'attempts'/(stamp+'-'+uuid.uuid4().hex[:8])
    out.mkdir(parents=True)
    data = load('v94_data', ROOT/'experiments/python-gamebub-v94/native/data.py')
    wire = load('v94_frame', ROOT/'scripts/cu66-v86/run_wire.py')
    old88 = load('v94_qframe', ROOT/'scripts/cu66-v88/run_wire.py')
    qcodec = load('v94_qmap', ROOT/'scripts/cu66-v87/quantizer_codec.py')
    native = load('v94_original', ROOT/'experiments/python-gamebub-v82/native/data.py')
    oldmap = load('v94_oldmap', ROOT/'scripts/cu66-v84/prototype_mode_map_v2.py')
    groupmap = load('v94_groupmap', ROOT/'scripts/cu66-v86/prototype_maps.py')
    controls_path = ROOT/'experiments/python-gamebub-v92/wire/results.json'
    controls_report = json.loads(controls_path.read_text())
    frame_report = controls_report['selected_report']
    frame_report = ROOT/frame_report if not Path(frame_report).is_absolute() else Path(frame_report)
    controls = {(r['policy'], r['cohort'], r['fid']): r
                for r in map(json.loads, frame_report.with_name('frames.jsonl').read_text().splitlines())}
    v92_control_rows = {(r['cohort'], r['fid']): r for r in controls.values()
                        if r['policy'] == 'context_byte_min'}
    c2_path = wire.C2_CONTROL
    commitments = {(r['cohort'], r['fid']): r
                   for r in map(json.loads, c2_path.read_text().splitlines())}
    source_paths = [Path(__file__).resolve(), AREA/'receiver.cpp',
                    ROOT/'experiments/python-gamebub-v94/native/data.py',
                    ROOT/'experiments/python-gamebub-v94/native/index.json',
                    ROOT/'experiments/python-gamebub-v94/native/codec.hpp',
                    controls_path, frame_report, frame_report.with_name('frames.jsonl'), c2_path,
                    ROOT/'experiments/python-gamebub-v92/native/codec.hpp',
                    ROOT/'experiments/python-gamebub-v92/native/index.json',
                    ROOT/'experiments/python-gamebub-v92/native/data.py',
                    ROOT/'experiments/python-gamebub-v88/entropy/codec.hpp',
                    ROOT/'experiments/python-gamebub-v85/residual/encode.hpp',
                    ROOT/'scripts/cu66-v86/run_wire.py', ROOT/'scripts/cu66-v88/run_wire.py',
                    ROOT/'scripts/cu66-v87/quantizer_codec.py', ROOT/'scripts/cu66-v84/prototype_mode_map_v2.py',
                    ROOT/'scripts/cu66-v86/prototype_maps.py',
                    ROOT/'experiments/python-gamebub-v82/native/data.py',
                    ROOT/'experiments/python-gamebub-v82/native/index.json',
                    ROOT/'experiments/python-gamebub-v88/entropy/data.py',
                    ROOT/'experiments/python-gamebub-v88/entropy/index.json',
                    ROOT/'experiments/python-gamebub-v85/residual/data.py',
                    ROOT/'experiments/python-gamebub-v85/residual/index.json']
    source_paths += sorted((ROOT/'experiments/cu66-native-v69').glob('*.hpp'))
    source_paths += sorted((ROOT/'experiments/python-gamebub-v94/native/data').glob('*.gz'))
    pins = {str(path.relative_to(ROOT)): sha(path) for path in source_paths}
    for path in source_paths:
        dest = out/'sources'/path.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(path.read_bytes())
    report = dict(schema='cu66-v94-full-wire-v1', status='FAIL', source_sha256=pins,
                  policies=list(POLICIES), target_cap_bytes=49152,
                  diagnostic_research_cap_bytes=2097152, physical_30fps_proven=False,
                  validated_under10ms_proven=False, promoted_to_RTL=False, commands=[],
                  scope=['Direct EC94/CS94 reconstruction from actual homogeneous per-stream variants.',
                         'All rANS and all_BR diagnostic packets use the explicit 2 MiB research receiver; fit to 49,152 bytes is reported separately.',
                         'byte_min and v92_byte_min are strict 49,152-byte policies; byte_min is exact independent per-context packet-length minimization.',
                         'Native exact coefficient, pixel, reference, HUD, root and seal parity; no FPGA timing or board-fit claim.'])
    binary = '/build/v94-wire-'+stamp
    research_binary = binary+'-research'
    processes = {}
    rows = []
    archives = {}
    started = time.monotonic()
    prior = signal.getsignal(signal.SIGALRM)
    signal.signal(signal.SIGALRM, lambda _s, _f: (_ for _ in ()).throw(TimeoutError('CS94 watchdog')))
    signal.setitimer(signal.ITIMER_REAL, 1200)
    try:
        for target, flags in ((binary, []), (research_binary, ['-DCS94_RESEARCH=1'])):
            command = ['docker', 'exec', CONTAINER, 'g++', '-std=c++17', '-O2', '-Wall', '-Wextra', '-Werror',
                       *flags, str(AREA/'receiver.cpp'), '-o', target]
            result = subprocess.run(command, capture_output=True, text=True, timeout=120)
            (out/('compile-research.log' if flags else 'compile.log')).write_text(result.stdout+result.stderr)
            report['commands'].append(dict(argv=command, exit_code=result.returncode))
            assert result.returncode == 0, result.stderr
            copied = subprocess.run(['docker', 'cp', CONTAINER+':'+target,
                                     str(out/('research.bin' if flags else 'receiver.bin'))],
                                    capture_output=True, timeout=30)
            assert copied.returncode == 0
        for policy in POLICIES:
            log = (out/(policy+'.stderr')).open('wb')
            executable = research_binary if policy in RESEARCH_POLICIES else binary
            process = subprocess.Popen(['docker', 'exec', '-i', CONTAINER, executable],
                                       stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log)
            processes[policy] = (process, log)
        archives.update({policy: gzip.open(out/f'packets-{policy}.bin.gz', 'wb') for policy in POLICIES})
        qcache = {}
        with (out/'frames.jsonl').open('w') as output:
            for frame, original in zip(data.iter_frames(), native.iter_frames(), strict=True):
                ident = frame['cohort'], frame['fid']
                assert all(frame[k] == original[k] for k in ('cohort', 'fid', 'ordinal', 'key'))
                flat = [chunk for plane in frame['variants']['65536'] for chunk in plane]
                assert len(flat) == 3 and all(len(p) == 1 for p in frame['variants']['65536'])
                v92_masks = [v92_control_rows[ident]['plane_masks'][axis] for axis in range(3)]
                # V92 decisions are stored separately for each plane's four contexts.
                choices_by_policy = {}
                for policy in POLICIES:
                    choices_by_policy[policy] = [policy_choices(policy, c['ec94'], c['ec94_stats']['masks'], v92_masks[axis])
                                                  for axis, c in enumerate(flat)]
                operations = [1 if h else 0 if not frame['key'] and frame['zero_mask'][t] == '1' else 2
                              for t, h in enumerate(original['hidden_mask'])]
                previous = None if frame['key'] else qcache.get(frame['cohort'])
                qblock = qcodec.encode(qcodec.unpacked(frame['qmap'], 1350), operations, previous)
                qcache[frame['cohort']] = qcodec.decode(qblock, operations, previous)
                for policy in POLICIES:
                    # The wire builder accepts one actual entropy chunk per plane.
                    # Rebuild with the selected plane payloads together.
                    planes = [[dict(blocks=c['blocks'], data=assemble(c['ec94'], choices_by_policy[policy][axis]))]
                              for axis, c in enumerate(flat)]
                    source = dict(frame, variants={'65536': planes})
                    packet, _, _ = wire.frame_packet(source, original, commitments[ident],
                                                     dict(kind='copy_group', cap=65536), oldmap, groupmap)
                    packet = old88.cs88(packet, qblock)
                    body = b'CS94'+packet[4:-4]
                    packet = body+struct.pack('>I', zlib.crc32(body))
                    if policy in ('all_AB', 'byte_min', 'v92_byte_min'):
                        assert len(packet) <= 49152, (policy, ident, len(packet))
                    if policy == 'v92_byte_min':
                        assert [list(choices_by_policy[policy][axis]) for axis in range(3)] == [
                            list(expand92(m)) for m in v92_masks]
                        assert len(packet) == v92_control_rows[ident]['wire_bytes'], (
                            'frozen V92 byte-count control', ident, len(packet),
                            v92_control_rows[ident]['wire_bytes'])
                    if frame['cohort'] == 0 and frame['fid'] in (0, 1, 2) and policy in (
                            'byte_min', 'rans2_s10', 'rans4_s10'):
                        (out/f"c0-f{frame['fid']}-{policy}.cs94").write_bytes(packet)
                    process = processes[policy][0]
                    process.stdin.write(struct.pack('>II', frame['cohort'], len(packet))+packet)
                    process.stdin.flush()
                    decoded = json.loads(process.stdout.readline())
                    assert decoded['accepted'] and not decoded['replayed'], (policy, ident, decoded)
                    for key in ('canonical_sha256', 'hud_sha256', 'display_sha256'):
                        assert decoded[key] == frame[key], (policy, ident, key)
                    assert decoded['coefficient_sha256'] == frame['canonical_coefficients_sha256']
                    for key in ('root', 'seal'):
                        assert decoded[key] == commitments[ident][key]
                    assert decoded['generation'] == frame['ordinal']+1 and decoded['wire_bytes'] == len(packet)
                    work = {key: sum(selected_work(flat[axis]['ec94_stats']['masks'],
                                                   choices_by_policy[policy][axis])[key]
                                     for axis in range(3)) for key in WORK_KEYS}
                    row = dict(policy=policy, cohort=frame['cohort'], fid=frame['fid'], ordinal=frame['ordinal'],
                               key=frame['key'], choices=[list(c) for c in choices_by_policy[policy]],
                               selectors=[sum(SELECTOR_METHOD[v] << (2*i) for i, v in enumerate(c))
                                          for c in choices_by_policy[policy]],
                               wire_bytes=len(packet), fits_49152=len(packet) <= 49152,
                               diagnostic_receiver=policy in RESEARCH_POLICIES,
                               v92_plane_masks=v92_masks if policy == 'v92_byte_min' else None,
                               packet_sha256=hashlib.sha256(packet).hexdigest(), decoded=decoded, **work)
                    output.write(json.dumps(row, separators=(',', ':'))+'\n')
                    rows.append(row)
                    meta = json.dumps(row, separators=(',', ':')).encode()
                    archives[policy].write(struct.pack('<II', len(meta), len(packet))+meta+packet)
                if len(rows) % (len(POLICIES)*50) == 0:
                    print('V94_WIRE_PROGRESS', len(rows)//len(POLICIES), flush=True)
        for archive in archives.values():
            archive.close()
        for policy, (process, log) in processes.items():
            process.stdin.close()
            assert process.wait(timeout=30) == 0, policy
            log.close()
        assert len(rows) == 457*len(POLICIES)
        assert pins == {path: sha(ROOT/path) for path in pins}, 'source changed during campaign'
        summaries = []
        for policy in POLICIES:
            group = [r for r in rows if r['policy'] == policy]
            summaries.append(dict(policy=policy, frames=457,
                                  wire_bytes=stats([r['wire_bytes'] for r in group]),
                                  fits_49152=sum(r['fits_49152'] for r in group),
                                  **{key: sum(r[key] for r in group) for key in WORK_KEYS}))
        report.update(status='PASS_NATIVE_CS94_FULL_FRAME_PARITY', frames=457, packets=len(rows),
                      summaries=summaries, binary=binary, research_binary=research_binary)
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
        for archive in archives.values():
            if not archive.closed:
                archive.close()
        report['wall_seconds'] = time.monotonic()-started
        report['artifacts_sha256'] = {str(p.relative_to(out)): sha(p) for p in out.rglob('*') if p.is_file()}
        (out/'results.json').write_text(json.dumps(report, indent=2)+'\n')
        print('V94_WIRE_REPORT', out/'results.json', report['status'], flush=True)
    (AREA/'results.json').write_text(json.dumps(dict(report, selected_report=str((out/'results.json').relative_to(ROOT))), indent=2)+'\n')


if __name__ == '__main__':
    main()
