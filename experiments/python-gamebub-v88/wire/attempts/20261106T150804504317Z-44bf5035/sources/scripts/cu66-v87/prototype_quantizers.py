#!/usr/bin/env python3
"""Actual CS87 packets with independently parsed quantizers and native pixels."""
import datetime
import hashlib
import importlib.util
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
AREA = ROOT / 'experiments/python-gamebub-v87/quantizers'
OLD = ROOT / 'experiments/python-gamebub-v86'
QUALIFIED = OLD / 'wire-attempts/20261106T135235884295Z-2a73a26a'
CONTAINER = 'gamebub-cu66-v69-build'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stats(values):
    return dict(min=min(values), median=statistics.median(values), max=max(values), total=sum(values))


def replace_quantizers(packet, block):
    header = bytearray(packet[:128])
    header[:4] = b'CS87'
    mode_bytes = int.from_bytes(header[36:40], 'big')
    struct.pack_into('>I', header, 40, len(block))
    begin = 128 + mode_bytes
    content = bytes(header) + packet[128:begin] + block + packet[begin + 338:-4]
    return content + struct.pack('>I', zlib.crc32(content))


def main():
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA / 'attempts' / (stamp + '-' + uuid.uuid4().hex[:8])
    out.mkdir(parents=True)
    wire = load('q87_wire', ROOT / 'scripts/cu66-v86/run_wire.py')
    codec = load('q87_codec', ROOT / 'scripts/cu66-v87/quantizer_codec.py')
    residual = load('q87_residual', ROOT / 'experiments/python-gamebub-v85/residual/data.py')
    controls_data = load('q87_controls', OLD / 'controls/data.py')
    native = load('q87_native', ROOT / 'experiments/python-gamebub-v82/native/data.py')
    old_codec = load('q87_old_map', ROOT / 'scripts/cu66-v84/prototype_mode_map_v2.py')
    group_codec = load('q87_group_map', ROOT / 'scripts/cu66-v86/prototype_maps.py')
    sources = [Path(__file__).resolve(), ROOT/'scripts/cu66-v87/quantizer_codec.py', AREA/'receiver.cpp',
               ROOT/'scripts/cu66-v86/run_wire.py', QUALIFIED/'results.json', QUALIFIED/'frames.jsonl',
               ROOT/'experiments/python-gamebub-v85/residual/index.json', OLD/'controls/index.json',
               ROOT/'experiments/python-gamebub-v82/native/index.json', wire.C2_CONTROL]
    sources += sorted((ROOT/'experiments/cu66-native-v69').glob('*.hpp'))
    pins = {str(p.relative_to(ROOT)): sha(p) for p in sources}
    for path in sources:
        if path.suffix in ('.py', '.cpp', '.hpp'):
            dest = out/'sources'/path.relative_to(ROOT)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(path.read_bytes())
    qualified = {(r['configuration'], r['cohort'], r['fid']): r
                 for r in map(json.loads, (QUALIFIED/'frames.jsonl').read_text().splitlines())}
    commitments = {(r['cohort'], r['fid']): r for r in map(json.loads, wire.C2_CONTROL.read_text().splitlines())}
    configs = [dict(name=kind+'_cap65536', kind=kind, cap=65536) for kind in ('copy_group', 'all_visible')]
    report = dict(schema='cu66-v87-actual-quantizers-v1', status='FAIL', source_sha256=pins,
                  configurations=configs, commands=[], physical_30fps_proven=False,
                  validated_under10ms_proven=False, scope='Actual new-profile packets and native pixel parity; no target timing or resource qualification.')
    binary = '/build/v87-quantizers-' + stamp
    processes, prior, rows = {}, {}, []
    started = time.monotonic()
    try:
        command = ['docker', 'exec', CONTAINER, 'g++', '-std=c++17', '-O2', '-Wall', '-Wextra', '-Werror', str(AREA/'receiver.cpp'), '-o', binary]
        result = subprocess.run(command, text=True, capture_output=True)
        report['commands'].append(dict(argv=command, observed_exit_code=result.returncode))
        (out/'compile.log').write_text(result.stdout + result.stderr)
        assert result.returncode == 0, result.stderr
        command = ['docker', 'cp', CONTAINER+':'+binary, str(out/'receiver.bin')]
        result = subprocess.run(command, text=True, capture_output=True)
        report['commands'].append(dict(argv=command, observed_exit_code=result.returncode))
        (out/'copy.log').write_text(result.stdout + result.stderr)
        assert result.returncode == 0
        for c in configs:
            log = (out/(c['name']+'.stderr')).open('wb')
            command = ['docker', 'exec', '-i', CONTAINER, binary]
            report['commands'].append(dict(argv=command))
            processes[c['name']] = (subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log), log)
        with (out/'frames.jsonl').open('w') as output:
            for i, (frame, control_frame, original) in enumerate(zip(residual.iter_frames(), controls_data.iter_frames(), native.iter_frames(), strict=True)):
                assert all(frame[k] == control_frame[k] == original[k] for k in ('cohort','fid','ordinal','key'))
                for c in configs:
                    name = c['name']
                    source = control_frame if c['kind'] == 'all_visible' else frame
                    packet, components, _ = wire.frame_packet(source, original, commitments[(frame['cohort'],frame['fid'])], c, old_codec, group_codec)
                    old_row = qualified[(name, frame['cohort'], frame['fid'])]
                    assert hashlib.sha256(packet).hexdigest() == old_row['packet_sha256']
                    operations = [1 if hidden else 0 if c['kind'] != 'all_visible' and not frame['key'] and zero == '1' else 2
                                  for hidden, zero in zip(original['hidden_mask'], frame['zero_mask'], strict=True)]
                    values = codec.unpacked(frame['qmap'], 1350)
                    previous = None if frame['key'] else prior.get((name,frame['cohort']))
                    block = codec.encode(values, operations, previous)
                    scales = codec.decode(block, operations, previous)
                    needed = codec.needed_cells(operations)
                    assert all(not n or a == b for n,a,b in zip(needed, values, scales))
                    candidate = replace_quantizers(packet, block)
                    assert len(candidate) == len(packet) - 338 + len(block)
                    process = processes[name][0]
                    process.stdin.write(struct.pack('>II',frame['cohort'],len(candidate))+candidate)
                    process.stdin.flush()
                    decoded = json.loads(process.stdout.readline())
                    assert decoded['accepted'] and not decoded['replayed'], decoded
                    for key in ('canonical_sha256','hud_sha256','display_sha256','coefficient_sha256','root','seal','generation','fid'):
                        assert decoded[key] == old_row['decoded'][key], (name,frame['fid'],key)
                    assert decoded['wire_bytes'] == len(candidate)
                    prior[(name,frame['cohort'])] = scales
                    new_components = dict(components, qmap=len(block))
                    assert sum(new_components.values()) == len(candidate)
                    row = dict(configuration=name,cohort=frame['cohort'],fid=frame['fid'],ordinal=frame['ordinal'],key=frame['key'],
                               q_method=block[5],needed_cells=sum(needed),q_block_bytes=len(block),qmap_sha256=hashlib.sha256(block).hexdigest(),
                               original_packet_bytes=frame['packet_bytes'],CS86_wire_bytes=len(packet),wire_bytes=len(candidate),
                               packet_sha256=hashlib.sha256(candidate).hexdigest(),components=new_components,decoded=decoded)
                    output.write(json.dumps(row,separators=(',',':'))+'\n')
                    rows.append(row)
                    if frame['cohort'] in (0,3) and frame['ordinal'] in (0,1,2):
                        (out/f"c{frame['cohort']}-f{frame['fid']}-{name}.cs87").write_bytes(candidate)
                if i % 50 == 0:
                    print('V87_QUANTIZER_PROGRESS',i+1,flush=True)
        report['receiver_exit_codes'] = {}
        for name, (process, log) in processes.items():
            process.stdin.close()
            code = process.wait()
            log.close()
            report['receiver_exit_codes'][name] = code
            assert code == 0
        assert len(rows) == 914
        summaries = []
        for c in configs:
            selected = [r for r in rows if r['configuration'] == c['name']]
            summaries.append(dict(configuration=c['name'],sources=len(selected),wire_bytes=stats([r['wire_bytes'] for r in selected]),
                                  CS86_wire_bytes=stats([r['CS86_wire_bytes'] for r in selected]),
                                  q_block_bytes=stats([r['q_block_bytes'] for r in selected]),
                                  saved_vs_CS86=sum(r['CS86_wire_bytes']-r['wire_bytes'] for r in selected),
                                  saved_vs_original=sum(r['original_packet_bytes']-r['wire_bytes'] for r in selected),
                                  method_counts={str(m):sum(r['q_method']==m for r in selected) for m in range(7)},
                                  fits_49152=sum(r['wire_bytes']<=49152 for r in selected)))
        assert pins == {p:sha(ROOT/p) for p in pins}, 'executed sources changed'
        report.update(status='PASS_ACTUAL_PACKETS_NATIVE_PARITY',sources=457,received_packets=914,summaries=summaries,binary=binary)
    finally:
        for process, log in processes.values():
            if process.poll() is None:
                process.terminate()
                process.wait()
            if not log.closed:
                log.close()
        report['wall_seconds'] = time.monotonic() - started
        report['artifacts_sha256'] = {str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()}
        (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
        print('V87_QUANTIZER_REPORT',out/'results.json',report['status'],flush=True)
    (AREA/'results.json').write_text(json.dumps(dict(report,selected_report=str((out/'results.json').relative_to(ROOT))),indent=2)+'\n')


if __name__ == '__main__':
    main()
