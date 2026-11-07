#!/usr/bin/env python3
"""Append the actual optimized EC94 winner to a frozen RV94 vector set."""
import argparse
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import signal
import struct
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v94/optimized-rtl-vectors'
BASE_INDEX = ROOT / 'experiments/python-gamebub-v94/rtl-vectors/index.json'
OPT = ROOT / 'experiments/python-gamebub-v94/native/optimized'
CODEC = ROOT / 'experiments/python-gamebub-v94/python/codec.py'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--timeout', type=int, default=180)
    args = parser.parse_args()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA / 'attempts' / (stamp + '-' + uuid.uuid4().hex[:8])
    out.mkdir(parents=True)
    pins, cases = {}, []
    report = dict(schema='cu66-v94-optimized-winner-rtl-vectors-v1', status='FAIL',
                  source_sha256=pins, cases=cases, watchdog_seconds=args.timeout,
                  physical_timing_proven=False, hardware_tested=False,
                  scope='Frozen 54 category streams plus one actual optimized winning DC context. Packet/literal parsing and frame publication remain outside the RTL kernel.')
    started = time.monotonic()
    prior = signal.getsignal(signal.SIGALRM)
    def timeout(signum, frame):
        raise TimeoutError('optimized EC94 RTL export watchdog expired')
    signal.signal(signal.SIGALRM, timeout)
    signal.alarm(args.timeout)
    def pin(path):
        path = path.resolve()
        name = str(path.relative_to(ROOT))
        digest = sha(path)
        assert name not in pins or pins[name] == digest, 'pinned source changed'
        pins[name] = digest
        dest = out / 'sources' / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(path.read_bytes())
    try:
        for path in (Path(__file__).resolve(), CODEC, BASE_INDEX, OPT/'index.json', OPT/'data.py'):
            pin(path)
        base_pointer = json.loads(BASE_INDEX.read_text())
        base_report_path = ROOT / base_pointer['selected_report']
        base = json.loads(base_report_path.read_text())
        base_binary_path = base_report_path.with_name(base['vectors_path'])
        pin(base_report_path); pin(base_binary_path)
        assert base['status'] == 'PASS_INDEPENDENT_RANS_RTL_VECTORS'
        assert (base['case_count'], base['actual_case_count'], base['actual_symbols'], base['total_symbols']) == (54, 18, 30012, 66876)
        assert sha(base_binary_path) == base['vectors_sha256']
        for name, digest in base['source_sha256'].items():
            assert sha(ROOT/name) == digest, ('stale parent vector source', name)
        original = base_binary_path.read_bytes()
        assert original[:4] == b'RV94' and struct.unpack_from('<I', original, 4)[0] == 54
        for index, case in enumerate(base['cases']):
            cases.append(dict(name=case['name'], kind=case['kind'], symbols=case['symbols'],
                              scale=case['scale'], lanes=case['lanes'], model_count=case['model_count'],
                              renorm_bytes=case['renorm_bytes'], renorm_counts=case['renorm_counts'],
                              parent_report=str(base_report_path.relative_to(ROOT)),
                              parent_report_sha256=sha(base_report_path), parent_case_index=index))
        opt_index = json.loads((OPT/'index.json').read_text())
        assert opt_index['status'] == 'PASS_NATIVE_ALL_3_INDEPENDENT_PYTHON_ALL_3'
        pin(OPT/opt_index['data']['path'])
        if 'selected_report' in opt_index:
            pin(ROOT/opt_index['selected_report'])
        codec = load('ec94_optimized_vector_reader', CODEC)
        corpus = load('ec94_optimized_vector_corpus', OPT/'data.py')
        target, winners, frames = None, [], 0
        for frame in corpus.iter_frames():
            frames += 1
            for axis, plane in enumerate(frame['variants']['65536']):
                for chunk_number, chunk in enumerate(plane):
                    packet = chunk['ec94_opt'][2]
                    flags, selector, streams, counts = codec.parse_header(packet, chunk['blocks'])
                    if not flags:
                        for context in range(4):
                            if ((selector >> (2*context)) & 3) in (2,3):
                                identity = (frame['cohort'],frame['fid'],axis,chunk_number,context)
                                winners.append(identity)
                                if identity == (0,12,1,0,0):
                                    assert target is None
                                    target = (frame,chunk,packet,streams,selector,counts)
        assert frames == 457 and winners == [(0,12,1,0,0)], ('optimized winner identities', winners)
        assert target is not None
        frame,chunk,packet,streams,selector,counts = target
        stats = chunk['ec94_opt_stats']
        assert chunk['blocks'] == stats['blocks'] == 797
        observation = stats['masks'][2]
        packet_sha = hashlib.sha256(packet).hexdigest()
        assert packet_sha == observation['sha256'] and len(packet) == observation['bytes']
        values = codec.decode(packet,chunk['blocks'])
        packed = struct.pack('<'+'h'*len(values),*values)
        coefficient_sha = hashlib.sha256(packed).hexdigest()
        assert coefficient_sha == stats['coefficient_sha256'] == chunk['coefficient_sha256']
        method = selector & 3
        assert method == 2
        trace = codec.inspect_rans(streams[0],0,method,797)
        assert (trace['k0'],trace['k1'],trace['scale'],trace['lanes'],len(trace['models'])) == (0,255,10,2,1)
        assert [codec.signed(v) for v in trace['values']] == values[::64]
        rate_header = codec.parse_header(chunk['ec94_opt'][1],797)
        assert not rate_header[0] and streams[0] == rate_header[2][0], 'actual rate-search stream composition'
        assert len(streams[0]) == stats['method_stream_bytes'][3][0] < min(stats['method_stream_bytes'][0][0],stats['method_stream_bytes'][1][0])
        assert trace['symbol_count'] == observation['ans_symbols'][0] == 797
        assert len(trace['renorm_bytes']) == observation['ans_renorm_bytes'][0]
        assert all(state == codec.RANS_L for state in trace['final_states'])
        name = 'actual_optimized_c0f12_p1_chunk0_context0_N2S10_k0'
        packet_path = out/(name+'.ec94'); packet_path.write_bytes(packet)
        context_path = out/(name+'.context'); context_path.write_bytes(streams[0])
        trace_path = out/(name+'.trace.json')
        trace_path.write_text(json.dumps(trace,separators=(',',':'))+'\n')
        stats_path = out/(name+'.native-stats.json')
        stats_path.write_text(json.dumps(stats,indent=2)+'\n')
        table_bytes = streams[0][20:52]
        assert zlib_crc32(table_bytes) == trace['model_id']
        case = dict(name=name,kind='actual_corpus',study='optimized_rice_rate',
                    context=0,method=method,cohort=0,fid=12,plane=1,chunk=0,blocks=797,
                    variant=2,selector=selector,k0=trace['k0'],k1=trace['k1'],
                    scale=trace['scale'],lanes=trace['lanes'],model_count=1,
                    symbols=797,renorm_bytes=len(trace['renorm_bytes']),literal_bits=trace['literal_bits'],
                    model_id=trace['model_id'],model_frequency_bytes_sha256=hashlib.sha256(table_bytes).hexdigest(),
                    models=trace['models'],initial_states=trace['initial_states'],final_states=trace['final_states'],
                    renorm_counts=sorted(set(f['renorm_count'] for f in trace['fields'])),
                    packet_path=packet_path.name,packet_sha256=packet_sha,
                    stream_path=context_path.name,stream_sha256=sha(context_path),
                    trace_path=trace_path.name,trace_sha256=sha(trace_path),
                    native_stats_path=stats_path.name,native_stats_sha256=sha(stats_path),
                    baseline_chunk_coefficient_sha256=coefficient_sha,
                    baseline_frame_bindings={k:frame[k] for k in
                        ('ordinal','key','refid','packet_path','packet_sha256','canonical_sha256',
                         'hud_sha256','display_sha256','canonical_coefficients_sha256','component_sha256')},
                    source_index=str((OPT/'index.json').relative_to(ROOT)),source_index_sha256=sha(OPT/'index.json'))
        cases.append(case)
        suffix = bytearray(struct.pack('<5I',10,2,1,797,len(trace['renorm_bytes'])))
        suffix += struct.pack('<4I',*(trace['initial_states']+[codec.RANS_L]*2))
        suffix += struct.pack('<32H',*(trace['models'][0]['freq']+[64]*16))
        suffix += bytes(trace['renorm_bytes'])
        for field in trace['fields']:
            suffix += struct.pack('<4I',field['q'],field['lane'],field['state_after'],field['cursor'])
        binary = original[:4]+struct.pack('<I',55)+original[8:]+suffix
        assert binary[8:len(original)] == original[8:] and binary[:4] == original[:4]
        vector_path = out/'vectors.bin'; vector_path.write_bytes(binary)
        assert pins == {name:sha(ROOT/name) for name in pins}, 'executed sources changed'
        coverage = sorted({n for case in cases for n in case['renorm_counts']})
        report.update(status='PASS_INDEPENDENT_RANS_RTL_VECTORS',case_count=55,
                      actual_case_count=19,actual_symbols=30809,total_symbols=67673,
                      renorm_count_coverage=coverage,uncovered_renorm_counts=sorted({0,1,2}-set(coverage)),
                      parent_report=str(base_report_path.relative_to(ROOT)),parent_report_sha256=sha(base_report_path),
                      parent_vectors_sha256=sha(base_binary_path),parent_cases_preserved_byte_exact=True,
                      appended_case_index=54,appended_symbols=797,optimized_winner_context_count=len(winners),
                      corpus_frames_verified=frames,vectors_path='vectors.bin',vectors_sha256=sha(vector_path),
                      empty_cases=base['empty_cases'])
    except BaseException as error:
        report['error'] = repr(error)
        raise
    finally:
        signal.alarm(0);signal.signal(signal.SIGALRM,prior)
        report['wall_seconds'] = time.monotonic()-started
        report['artifacts_sha256'] = {str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()}
        (out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
        print(report['status'],out/'manifest.json',flush=True)
    (AREA/'index.json').write_text(json.dumps(dict(report,selected_report=str((out/'manifest.json').relative_to(ROOT))),indent=2)+'\n')


def zlib_crc32(data):
    import zlib
    return zlib.crc32(data)


if __name__ == '__main__':
    main()
