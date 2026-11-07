#!/usr/bin/env python3
"""Compare the guarded rate-optimized EC94 packets in the complete CS94 path."""
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
AREA = ROOT/'experiments/python-gamebub-v94/optimized-wire'
BASE_AREA = ROOT/'experiments/python-gamebub-v94/wire'
CONTAINER = 'gamebub-cu66-v69-build'
POLICIES = ('rate_ans2_s10', 'rate_byte_min')
VARIANT = {'rate_ans2_s10': 1, 'rate_byte_min': 2}
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


def selected_work(masks, variant):
    row = masks[variant]
    result = {}
    for key in WORK_KEYS:
        values = row[key]
        assert len(values) == 4, ('optimized EC94 metric shape', variant, key)
        result[key] = sum(map(int, values))
    return result


def build_packet(frame, original, commitment, qblock, wire, old88, oldmap, groupmap, variant):
    flat = [chunk for plane in frame['variants']['65536'] for chunk in plane]
    assert len(flat) == 3 and all(len(p) == 1 for p in frame['variants']['65536'])
    planes = []
    for chunk in flat:
        packets = chunk['ec94_opt']
        assert len(packets) == 3 and variant < len(packets)
        planes.append([dict(blocks=chunk['blocks'], data=packets[variant])])
    source = dict(frame, variants={'65536': planes})
    packet, _, _ = wire.frame_packet(source, original, commitment,
                                     dict(kind='copy_group', cap=65536), oldmap, groupmap)
    packet = old88.cs88(packet, qblock)
    body = b'CS94'+packet[4:-4]
    return body+struct.pack('>I', zlib.crc32(body))


def main():
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA/'attempts'/(stamp+'-'+uuid.uuid4().hex[:8])
    out.mkdir(parents=True)
    data = load('v94_opt_data', ROOT/'experiments/python-gamebub-v94/native/optimized/data.py')
    wire = load('v94_opt_frame', ROOT/'scripts/cu66-v86/run_wire.py')
    old88 = load('v94_opt_qframe', ROOT/'scripts/cu66-v88/run_wire.py')
    qcodec = load('v94_opt_qmap', ROOT/'scripts/cu66-v87/quantizer_codec.py')
    native = load('v94_opt_original', ROOT/'experiments/python-gamebub-v82/native/data.py')
    oldmap = load('v94_opt_oldmap', ROOT/'scripts/cu66-v84/prototype_mode_map_v2.py')
    groupmap = load('v94_opt_groupmap', ROOT/'scripts/cu66-v86/prototype_maps.py')

    baseline_summary_path = BASE_AREA/'results.json'
    baseline_summary = json.loads(baseline_summary_path.read_text())
    baseline_report_path = Path(baseline_summary['selected_report'])
    if not baseline_report_path.is_absolute():
        baseline_report_path = ROOT/baseline_report_path
    baseline_report = json.loads(baseline_report_path.read_text())
    baseline_frames_path = baseline_report_path.with_name('frames.jsonl')
    baseline_rows = {(row['policy'], row['cohort'], row['fid']): row
                     for row in map(json.loads, baseline_frames_path.read_text().splitlines())}
    attempt_dir = baseline_report_path.parent
    receiver_path = attempt_dir/'receiver.bin'
    research_receiver_path = attempt_dir/'research.bin'
    receiver_sha = sha(receiver_path)
    research_receiver_sha = sha(research_receiver_path)
    assert baseline_report['artifacts_sha256']['receiver.bin'] == receiver_sha
    assert baseline_report['artifacts_sha256']['research.bin'] == research_receiver_sha
    assert baseline_report['status'] == 'PASS_NATIVE_CS94_FULL_FRAME_PARITY'
    c2_path = wire.C2_CONTROL
    commitments = {(row['cohort'], row['fid']): row
                   for row in map(json.loads, c2_path.read_text().splitlines())}

    source_paths = [Path(__file__).resolve(),
                    ROOT/'experiments/python-gamebub-v94/native/optimized/data.py',
                    ROOT/'experiments/python-gamebub-v94/native/optimized/index.json',
                    ROOT/'experiments/python-gamebub-v94/native/optimized/codec.hpp',
                    ROOT/'experiments/python-gamebub-v94/native/data.py',
                    ROOT/'experiments/python-gamebub-v94/native/index.json',
                    ROOT/'experiments/python-gamebub-v94/native/codec.hpp',
                    ROOT/'experiments/python-gamebub-v94/wire/receiver.cpp',
                    baseline_summary_path, baseline_report_path, baseline_frames_path,
                    receiver_path, research_receiver_path, c2_path,
                    ROOT/'scripts/cu66-v86/run_wire.py', ROOT/'scripts/cu66-v88/run_wire.py',
                    ROOT/'scripts/cu66-v87/quantizer_codec.py', ROOT/'scripts/cu66-v84/prototype_mode_map_v2.py',
                    ROOT/'scripts/cu66-v86/prototype_maps.py',
                    ROOT/'experiments/python-gamebub-v82/native/data.py',
                    ROOT/'experiments/python-gamebub-v82/native/index.json',
                    ROOT/'experiments/python-gamebub-v88/entropy/data.py',
                    ROOT/'experiments/python-gamebub-v88/entropy/index.json',
                    ROOT/'experiments/python-gamebub-v88/entropy/codec.hpp',
                    ROOT/'experiments/python-gamebub-v85/residual/encode.hpp',
                    ROOT/'experiments/python-gamebub-v85/residual/data.py',
                    ROOT/'experiments/python-gamebub-v85/residual/index.json']
    source_paths += sorted((ROOT/'experiments/cu66-native-v69').glob('*.hpp'))
    source_paths += sorted((ROOT/'experiments/python-gamebub-v94/native/optimized/data').glob('*.gz'))
    pins = {str(path.relative_to(ROOT)): sha(path) for path in source_paths}
    for path in source_paths:
        dest = out/'sources'/path.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(path.read_bytes())

    report = dict(schema='cu66-v94-optimized-full-wire-v1', status='FAIL', source_sha256=pins,
                  baseline_wire_report=str(baseline_report_path.relative_to(ROOT)),
                  baseline_receiver_sha256=receiver_sha,
                  baseline_research_receiver_sha256=research_receiver_sha,
                  baseline_wire_report_sha256=sha(baseline_report_path), policies=list(POLICIES),
                  target_cap_bytes=49152, research_packet_cap_bytes=2097152,
                  physical_30fps_proven=False, validated_under10ms_proven=False,
                  promoted_to_RTL=False, commands=[],
                  scope=['Optimized EC94 alternatives are actual native packets, assembled in the qualified CS94 envelope.',
                         'rate_ans2_s10 is diagnostic-receiver only; rate_byte_min uses the strict receiver.',
                         'Anchor byte count and guarded/local-min full-path bounds are checked against the qualified base V94 results.',
                         'Full native coefficient, pixel, reference, HUD, root and seal parity; no FPGA timing claim.'])
    processes = {}
    archives = {}
    rows = []
    started = time.monotonic()
    prior = signal.getsignal(signal.SIGALRM)
    signal.signal(signal.SIGALRM, lambda _s, _f: (_ for _ in ()).throw(TimeoutError('optimized CS94 watchdog')))
    signal.setitimer(signal.ITIMER_REAL, 1200)
    try:
        receiver_full = str(receiver_path.resolve())
        research_full = str(research_receiver_path.resolve())
        for policy in POLICIES:
            log = (out/(policy+'.stderr')).open('wb')
            executable = research_full if policy == 'rate_ans2_s10' else receiver_full
            command = ['docker', 'exec', '-i', CONTAINER, executable]
            report['commands'].append(dict(argv=command, receiver_sha256=sha(Path(executable))))
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log)
            processes[policy] = (process, log)
        archives.update({policy: gzip.open(out/f'packets-{policy}.bin.gz', 'wb') for policy in POLICIES})

        qcache = {}
        with (out/'frames.jsonl').open('w') as output:
            for frame, original in zip(data.iter_frames(), native.iter_frames(), strict=True):
                ident = frame['cohort'], frame['fid']
                assert all(frame[key] == original[key] for key in ('cohort', 'fid', 'ordinal', 'key'))
                flat = [chunk for plane in frame['variants']['65536'] for chunk in plane]
                assert len(flat) == 3 and all(len(p) == 1 for p in frame['variants']['65536'])
                operations = [1 if hidden else 0 if not frame['key'] and zero == '1' else 2
                              for hidden, zero in zip(original['hidden_mask'], frame['zero_mask'], strict=True)]
                previous = None if frame['key'] else qcache.get(frame['cohort'])
                qblock = qcodec.encode(qcodec.unpacked(frame['qmap'], 1350), operations, previous)
                qcache[frame['cohort']] = qcodec.decode(qblock, operations, previous)
                baseline_anchor = baseline_rows[('rans2_s10', *ident)]['wire_bytes']
                baseline_minimum = baseline_rows[('byte_min', *ident)]['wire_bytes']
                anchor_packet = build_packet(frame, original, commitments[ident], qblock, wire, old88,
                                             oldmap, groupmap, 0)
                if len(anchor_packet) != baseline_anchor:
                    raise AssertionError(('rANS2 S10 anchor byte-count drift', ident,
                                          len(anchor_packet), baseline_anchor))
                for policy in POLICIES:
                    packet = build_packet(frame, original, commitments[ident], qblock, wire, old88,
                                          oldmap, groupmap, VARIANT[policy])
                    if policy == 'rate_ans2_s10' and len(packet) > len(anchor_packet):
                        raise AssertionError(('guarded uniform candidate grew beyond anchor', ident,
                                              len(packet), len(anchor_packet)))
                    if policy == 'rate_byte_min':
                        if len(packet) > 49152:
                            raise AssertionError(('strict optimized packet exceeds target cap', ident, len(packet)))
                        if len(packet) > baseline_minimum:
                            raise AssertionError(('local min grew beyond qualified byte_min', ident,
                                                  len(packet), baseline_minimum))
                    if frame['cohort'] == 0 and frame['fid'] in (0, 1, 2):
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
                    variant = VARIANT[policy]
                    work = {key: sum(selected_work(chunk['ec94_opt_stats']['masks'], variant)[key]
                                     for chunk in flat) for key in WORK_KEYS}
                    row = dict(policy=policy, cohort=frame['cohort'], fid=frame['fid'],
                               ordinal=frame['ordinal'], key=frame['key'], variant=variant,
                               wire_bytes=len(packet), fits_49152=len(packet) <= 49152,
                               anchor_wire_bytes=len(anchor_packet),
                               baseline_rans2_s10_wire_bytes=baseline_anchor,
                               baseline_byte_min_wire_bytes=baseline_minimum,
                               packet_sha256=hashlib.sha256(packet).hexdigest(), decoded=decoded, **work)
                    output.write(json.dumps(row, separators=(',', ':'))+'\n')
                    rows.append(row)
                    meta = json.dumps(row, separators=(',', ':')).encode()
                    archives[policy].write(struct.pack('<II', len(meta), len(packet))+meta+packet)
                if len(rows) % (len(POLICIES)*50) == 0:
                    print('V94_OPT_WIRE_PROGRESS', len(rows)//len(POLICIES), flush=True)
        for archive in archives.values():
            archive.close()
        for policy, (process, log) in processes.items():
            process.stdin.close()
            assert process.wait(timeout=30) == 0, policy
            log.close()
        assert len(rows) == 457*len(POLICIES)
        assert pins == {path: sha(ROOT/path) for path in pins}, 'source changed during optimized campaign'
        summaries = []
        for policy in POLICIES:
            group = [row for row in rows if row['policy'] == policy]
            summaries.append(dict(policy=policy, frames=457,
                                  wire_bytes=stats([row['wire_bytes'] for row in group]),
                                  fits_49152=sum(row['fits_49152'] for row in group),
                                  **{key: sum(row[key] for row in group) for key in WORK_KEYS}))
        report.update(status='PASS_NATIVE_CS94_OPTIMIZED_FULL_FRAME_PARITY', frames=457,
                      packets=len(rows), summaries=summaries)
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
        report['artifacts_sha256'] = {str(path.relative_to(out)): sha(path)
                                      for path in out.rglob('*') if path.is_file()}
        (out/'results.json').write_text(json.dumps(report, indent=2)+'\n')
        print('V94_OPT_WIRE_REPORT', out/'results.json', report['status'], flush=True)
    (AREA/'results.json').write_text(json.dumps(
        dict(report, selected_report=str((out/'results.json').relative_to(ROOT))), indent=2)+'\n')


if __name__ == '__main__':
    main()
