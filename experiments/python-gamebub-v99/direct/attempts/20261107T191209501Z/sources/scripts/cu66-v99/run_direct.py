#!/usr/bin/env python3
"""Measure direct fresh q16 RGB->CS88 construction with native causal ACKs."""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v99'
sys.path.insert(0, str(AREA / 'encoder'))
import direct_cs88 as direct


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def distribution(values):
    ordered = sorted(values)
    return dict(n=len(values), min=min(values), median=float(np.median(values)),
                p95_nearest_rank=ordered[(95 * len(values) + 99) // 100 - 1], max=max(values))


def resource_gate():
    memory = {line.split(':')[0]: int(line.split()[1]) for line in Path('/proc/meminfo').read_text().splitlines()}
    pressure = Path('/proc/pressure/memory').read_text()
    full = float(next(line for line in pressure.splitlines() if line.startswith('full ')).split()[1].split('=')[1])
    if memory['MemAvailable'] < 8 * 1024 * 1024 or full >= 1:
        raise RuntimeError('direct case requires available RAM>=8GiB and full PSI avg10<1')
    return dict(available_kib=memory['MemAvailable'], full_psi_avg10=full)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--control-report', type=Path, default=AREA / 'cs88/attempts/20261107T190043503Z/results.json')
    parser.add_argument('--source-manifest', type=Path, default=ROOT / 'experiments/python-gamebub-v98/sources/manifest.json')
    parser.add_argument('--output', type=Path, required=True, help='new immutable output directory')
    parser.add_argument('--container', default=direct.cs88.CONTAINER)
    parser.add_argument('--clip', help='optional single source clip for bounded smoke')
    parser.add_argument('--limit-frames', type=int, help='optional first N frames per selected clip for smoke only')
    parser.add_argument('--synthetic32', action='store_true', help='separate deterministic32-frame key0/key30/P31 control')
    args = parser.parse_args()
    if args.limit_frames is not None and not 1 <= args.limit_frames <= 30:
        parser.error('limit-frames must be1..30')
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    report = dict(schema='v99-direct-fresh-q16-CS88-v1', status='FAIL', argv=sys.argv,
                  started_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                  python=sys.version, numpy=np.__version__, platform=platform.platform(),
                  quant_scale=16, key_interval=30, block_size=32, packet_cap=49152,
                  profile='v91-group3 key0/P3 QM87run2/cache6 allBR88 C2group16',
                  timing_scope='unpaced prevalidated fresh RGB->complete packet; verification, golden render/hash, packet IO and native ACK excluded',
                  BR88_timing_scope='persistent native helper encode+self-decode exact check plus Docker stdio IPC',
                  native_ack_scope='Docker stdio request through full independent native reconstruction/hash/publication response, not isolated decode benchmark',
                  physical_30fps_proven=False, capture_to_display_measured=False,
                  cases=[], commands=[], source_sha256={}, selected_control_report=str(args.control_report.resolve()),
                  selected_control_report_sha256=sha(args.control_report), source_manifest_sha256=sha(args.source_manifest))
    dense = receiver = None
    started = time.perf_counter_ns()
    try:
        control = json.loads(args.control_report.read_text())
        if control['status'] != 'PASS_FRESH_NATIVE_CS88_PARITY' or control['profile'] != 'v91-group3':
            raise ValueError('require completed selected actual V91-subset CS88 control')
        for name, pin in control['source_sha256'].items():
            if sha(ROOT / name) != pin:
                raise ValueError('frozen control source changed: ' + name)
        rows_path = args.control_report.parent / 'frames.jsonl'
        if sha(rows_path) != control['artifacts_sha256']['frames.jsonl']:
            raise ValueError('authoritative control frame ledger hash')
        controls = {}
        for line in rows_path.read_text().splitlines():
            row = json.loads(line)
            if row['quant_scale'] == 16:
                identity = (row['clip_id'], row['frame_id'])
                if identity in controls:
                    raise ValueError('duplicate q16 control identity')
                controls[identity] = row
        report['selected_control_ledger_sha256'] = sha(rows_path)
        inspect_command = ['docker', 'inspect', args.container]
        result = subprocess.run(inspect_command, capture_output=True, check=True)
        identity = json.loads(result.stdout)[0]
        sanitized = dict(Id=identity['Id'], Image=identity['Image'], Name=identity.get('Name'),
            State=dict(Running=identity.get('State', {}).get('Running')),
            Mounts=[{key: mount.get(key) for key in ('Source', 'Destination', 'Type', 'RW')}
                    for mount in identity.get('Mounts', [])],
            HostConfig={key: identity.get('HostConfig', {}).get(key)
                        for key in ('Memory', 'NanoCpus', 'CpusetCpus')})
        dump(out / 'container-inspect-sanitized.json', sanitized)
        if identity['Id'] != control['container']['id'] or identity['Image'] != control['container']['image_id']:
            raise ValueError('selected frozen native container identity changed')
        report['container'] = control['container']
        report['compiler_version'] = control['compiler_version']
        report['binaries'] = control['binaries']
        report['commands'].append(inspect_command)
        for name, binary in control['binaries'].items():
            command = ['docker', 'exec', args.container, 'sha256sum', binary['path']]
            result = subprocess.run(command, capture_output=True, check=True)
            (out / (name + '-binary-sha256.log')).write_bytes(result.stdout)
            report['commands'].append(command)
            if result.stdout.decode().split()[0] != binary['sha256']:
                raise ValueError('selected native binary changed: ' + name)
        direct.fresh.dependencies()
        pins = direct.fresh.source_pins()
        pins.update(control['source_sha256'])
        for path in (Path(__file__).resolve(), Path(direct.__file__).resolve(), args.source_manifest.resolve()):
            pins[str(path.relative_to(ROOT))] = sha(path)
        report['source_sha256'] = pins
        for name, pin in pins.items():
            if sha(ROOT / name) != pin:
                raise ValueError('source snapshot changed: ' + name)
            destination = out / 'sources' / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, destination)
        dump(out / 'receipt.json', report)
        manifest = json.loads(args.source_manifest.read_text())
        clips = [c for c in manifest['clips'] if args.clip is None or c['clip_id'] == args.clip]
        if not clips:
            raise ValueError('source clip selection empty')
        dense_command = ['docker', 'exec', '-i', args.container, control['binaries']['encode_dense']['path']]
        report['commands'].append(dense_command)
        dense = direct.cs88.DenseEncoder(dense_command, out / 'dense.stderr')
        all_rows = []
        with (out / 'frames.jsonl').open('w') as ledger:
            for clip in clips:
                report.setdefault('resource_gates', []).append(resource_gate())
                source_path = args.source_manifest.parent / clip['npz_path']
                if sha(source_path) != clip['npz_sha256']:
                    raise ValueError('fresh compressed source NPZ pin')
                with np.load(source_path, allow_pickle=False) as source:
                    frames = source['rgb']
                if frames.shape != (30, 480, 720, 3) or frames.dtype != np.uint8:
                    raise ValueError('fresh 30frame RGB corpus geometry')
                if [direct.digest(frame.tobytes()) for frame in frames] != clip['frame_sha256']:
                    raise ValueError('fresh input frame hash list')
                frames.setflags(write=False)
                count = args.limit_frames or len(frames)
                clip_id = clip['clip_id'] + '-q16'
                case_out = out / clip_id
                case_out.mkdir()
                receiver_command = ['docker', 'exec', '-i', args.container, control['binaries']['receiver']['path']]
                report['commands'].append(receiver_command)
                receiver = direct.cs88.Native(receiver_command, case_out / 'native.stderr')
                sender = direct.DirectSender(dense, receiver, clip_id=clip_id)
                clip_rows = []
                print('DIRECT_START', clip_id, count, flush=True)
                for fid, rgb in enumerate(frames[:count]):
                    oracle = controls[(clip_id, fid)]
                    oracle_path = args.control_report.parent / oracle['packet_path']
                    row = sender.send(rgb, fid, expected_source_sha256=clip['frame_sha256'][fid],
                        control_row=oracle, control_packet_path=oracle_path,
                        packet_path=case_out / f'f{fid:06d}.cs88')
                    row['source_npz_sha256'] = clip['npz_sha256']
                    row['source_npz_path'] = str(source_path.resolve())
                    ledger.write(json.dumps(row, sort_keys=True) + '\n')
                    ledger.flush()
                    clip_rows.append(row)
                    all_rows.append(row)
                receiver.close()
                receiver = None
                if sha(source_path) != clip['npz_sha256']:
                    raise ValueError('source NPZ changed during direct run')
                case = dict(clip_id=clip_id, input_frames=count, accepted_frames=len(clip_rows),
                    all_inputs_admitted=len(clip_rows) == count, complete_30frame_clip=count == 30,
                    actual_packets_equal_authoritative_control=True,
                    packet_ready_ms=distribution([r['packet_ready_ms'] for r in clip_rows]),
                    native_ack_roundtrip_ms=distribution([r['native_ack_roundtrip_ms'] for r in clip_rows]),
                    phases={key: distribution([r['phases'][key] for r in clip_rows]) for key in clip_rows[0]['phases']},
                    packet_bytes=sum(r['packet_bytes'] for r in clip_rows),
                    max_packet_bytes=max(r['packet_bytes'] for r in clip_rows))
                report['cases'].append(case)
                print('DIRECT_DONE', json.dumps(case), flush=True)
                dump(out / 'results.json', report)
            if args.synthetic32:
                report.setdefault('resource_gates', []).append(resource_gate())
                case_out = out / 'synthetic-cross-key32'
                case_out.mkdir()
                command = ['docker', 'exec', '-i', args.container, control['binaries']['receiver']['path']]
                report['commands'].append(command)
                receiver = direct.cs88.Native(command, case_out / 'native.stderr')
                sender = direct.DirectSender(dense, receiver, clip_id='synthetic-cross-key32')
                synthetic_rows = []
                with (case_out / 'frames.jsonl').open('w') as synthetic_ledger:
                    for fid in range(32):
                        rgb = direct.synthetic_rgb(fid)
                        row = sender.send(rgb, fid, expected_source_sha256=direct.digest(rgb.tobytes()),
                                          packet_path=case_out / f'f{fid:06d}.cs88')
                        synthetic_ledger.write(json.dumps(row, sort_keys=True) + '\n')
                        synthetic_ledger.flush()
                        synthetic_rows.append(row)
                receiver.close()
                receiver = None
                if [r['frame_id'] for r in synthetic_rows if r['key']] != [0, 30]:
                    raise AssertionError('synthetic exact key0/key30 cadence')
                if synthetic_rows[31]['reference_id'] != 30:
                    raise AssertionError('synthetic P31 must use ACKed key30')
                if any(r['qmap_method'] != (2 if r['key'] else 6) for r in synthetic_rows):
                    raise AssertionError('synthetic exact QM87 keyrun2/Pcache6')
                report['synthetic_cross_key_control'] = dict(input_frames=32, native_exact_ACKs=32,
                    key_ids=[0, 30], final_P31_reference=30, source='deterministic synthetic_rgb code and per-frame hashes',
                    physical_FPS_or_gameplay_qualification=False,
                    packet_ready_ms=distribution([r['packet_ready_ms'] for r in synthetic_rows]),
                    ledger_path=str(case_out / 'frames.jsonl'))
        dense.close()
        dense = None
        if pins != {name: sha(ROOT / name) for name in pins}:
            raise ValueError('direct measured sources changed')
        report.update(status='PASS_DIRECT_FRESH_NATIVE_CS88_EXACT', frames=len(all_rows),
                      actual_packets_equal_control=len(all_rows), native_exact_ACKs=len(all_rows),
                      complete_120frame_campaign=len(clips) == 4 and len(all_rows) == 120 and all(c['complete_30frame_clip'] for c in report['cases']),
                      packet_ready_ms=distribution([r['packet_ready_ms'] for r in all_rows]),
                      phases={key: distribution([r['phases'][key] for r in all_rows]) for key in all_rows[0]['phases']},
                      source_frame_hashes_bound=True, historical_coefficients_as_input=False,
                      AB38_encoded=False, CS38_CU66_wrappers_constructed=False)
    except BaseException as error:
        report['error'] = repr(error)
        raise
    finally:
        if receiver:
            receiver.abort()
        if dense:
            dense.abort()
        report['wall_ms_including_verify_IO_ACK'] = (time.perf_counter_ns() - started) / 1e6
        report['artifact_sha256'] = {str(p.relative_to(out)): sha(p) for p in sorted(out.rglob('*'))
            if p.is_file() and p.name != 'results.json'}
        dump(out / 'results.json', report)
        print('DIRECT_REPORT', out / 'results.json', report['status'], flush=True)
        if report['status'] == 'PASS_DIRECT_FRESH_NATIVE_CS88_EXACT' and report.get('complete_120frame_campaign'):
            index = AREA / 'direct/index.json'
            index.parent.mkdir(parents=True, exist_ok=True)
            dump(index, dict(attempt_json=str((out / 'results.json').relative_to(ROOT)), sha256=sha(out / 'results.json')))


if __name__ == '__main__':
    main()
