#!/usr/bin/env python3
"""Export whole EC94 rANS category traces for the independent RTL kernel.

RV94 binary is little endian: magic, u32 case count; per case five u32
(scale, lanes, models, symbols, renorm bytes), four initial u32 states,
32 u16 frequencies, renorm bytes, then four u32 per field
(q, lane, state after renormalization, cumulative renorm cursor).
"""
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
AREA = ROOT / 'experiments/python-gamebub-v94/rtl-vectors'
NATIVE = ROOT / 'experiments/python-gamebub-v94/native'
CODEC = ROOT / 'experiments/python-gamebub-v94/python/codec.py'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name,path)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fixtures-only',action='store_true')
    parser.add_argument('--fixtures',type=Path,default=NATIVE/'fixtures/manifest.json')
    parser.add_argument('--corpus-index',type=Path,default=NATIVE/'index.json')
    parser.add_argument('--timeout',type=int,default=900)
    parser.add_argument('--max-fields',type=int,default=4096)
    args = parser.parse_args()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA/'attempts'/(stamp+'-'+uuid.uuid4().hex[:8]); out.mkdir(parents=True)
    pins, cases = {},[]
    def pin(path):
        path=path.resolve(); name=str(path.relative_to(ROOT)); digest=sha(path)
        assert name not in pins or pins[name]==digest, 'pinned source changed'
        pins[name]=digest
        dest=out/'sources'/name; dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(path.read_bytes())
    pin(Path(__file__).resolve());pin(CODEC);pin(args.fixtures)
    report=dict(schema='cu66-v94-independent-rans-rtl-vectors-v1',status='FAIL',
                fixtures_only=args.fixtures_only,source_sha256=pins,cases=cases,
                watchdog_seconds=args.timeout,physical_timing_proven=False,
                scope='Whole rANS category streams only. No coefficient reconstruction, frame, pixel, or hardware timing claim.')
    started=time.monotonic()
    def timeout(signum,frame):
        raise TimeoutError('EC94 RTL vector export watchdog expired')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(args.timeout)
    try:
        codec=load('ec94_vector_reader',CODEC)
        def add(name,stream,context,method,metadata,expected_values=None):
            assert name not in {case['name'] for case in cases}, 'duplicate vector case identity'
            trace=codec.inspect_rans(stream,context,method)
            if expected_values is not None:
                assert trace['values']==expected_values,'native fixture unsigned fields'
            assert all(v==codec.RANS_L for v in trace['final_states'])
            path=out/'contexts'/(name+'.bin');path.parent.mkdir(exist_ok=True);path.write_bytes(stream)
            trace_path=out/'traces'/(name+'.json');trace_path.parent.mkdir(exist_ok=True)
            trace_path.write_text(json.dumps(trace,separators=(',',':'))+'\n')
            cases.append(dict(name=name,context=context,method=method,
                              scale=trace['scale'],lanes=trace['lanes'],model_count=len(trace['models']),
                              symbols=trace['symbol_count'],renorm_bytes=len(trace['renorm_bytes']),
                              model_id=trace['model_id'],initial_states=trace['initial_states'],
                              final_states=trace['final_states'],
                              renorm_counts=sorted(set(f['renorm_count'] for f in trace['fields'])),
                              stream_path=str(path.relative_to(out)),stream_sha256=sha(path),
                              trace_path=str(trace_path.relative_to(out)),trace_sha256=sha(trace_path),
                              **metadata))
            return trace
        manifest=json.loads(args.fixtures.read_text())
        assert manifest.get('context_fixtures'), 'native context fixture archive required'
        for fixture in manifest['context_fixtures']:
            path=args.fixtures.parent/fixture['path'];pin(path)
            method=fixture['method'];context=fixture['context']
            trace=add('synthetic_'+path.stem+'_'+fixture['name'],path.read_bytes(),context,method,
                      dict(kind='native_synthetic',native_source=str(path.relative_to(ROOT)),
                           native_source_sha256=sha(path)),fixture.get('fields'))
            assert trace['symbol_count']==fixture['symbol_count']
        if not args.fixtures_only:
            reader_path=NATIVE/'data.py';pin(reader_path);pin(args.corpus_index)
            index=json.loads(args.corpus_index.read_text())
            archive=NATIVE/index['data']['path'];pin(archive)
            corpus=load('ec94_vector_corpus',reader_path)
            targets={(0,0),(0,1),(3,50)};selected={};frames_checked=0
            for frame in corpus.iter_frames(index_path=args.corpus_index):
                frames_checked+=1
                identity=(frame['cohort'],frame['fid'])
                if identity not in targets:
                    continue
                options=[]
                for axis,plane in enumerate(frame['variants']['65536']):
                    for chunk_number,chunk in enumerate(plane):
                        packets=chunk['ec94']
                        assert len(packets)==9
                        # All six scales/lane variants must remain rANS coded.
                        headers=[codec.parse_header(p,chunk['blocks']) for p in packets[2:8]]
                        if any(h[0] for h in headers):
                            continue
                        for context in range(1,4):
                            fields=chunk['blocks'] if context==0 else headers[0][3][context-1]*2
                            if not 1<=fields<=args.max_fields:
                                continue
                            if any(((h[1]>>(2*context))&3) not in (2,3) for h in headers):
                                continue
                            # Prefer ~1,667 symbols: 18 cases total ~30k fields.
                            options.append((abs(fields-1667),axis,chunk_number,context,fields,chunk,headers))
                assert options,('no whole small rANS stream',identity)
                best=min(options,key=lambda value:value[:5])
                selected[identity]=(frame,best)
            assert set(selected)==targets,('missing target corpus identities',set(selected))
            for identity,(frame,option) in sorted(selected.items()):
                _,axis,chunk_number,context,fields,chunk,headers=option
                packets=chunk['ec94']
                all_coefficients=[codec.decode(p,chunk['blocks']) for p in packets]
                assert all(v==all_coefficients[0] for v in all_coefficients),'all-nine coefficient parity'
                packed=struct.pack('<'+'h'*len(all_coefficients[0]),*all_coefficients[0])
                coefficient_sha=hashlib.sha256(packed).hexdigest()
                assert coefficient_sha==chunk['coefficient_sha256'], 'frozen baseline coefficient SHA'
                for offset,header in enumerate(headers,2):
                    packet=packets[offset]
                    path=out/'packets'/('c%df%d_p%d_chunk%d_variant%d.ec94'%(*identity,axis,chunk_number,offset))
                    path.parent.mkdir(exist_ok=True);path.write_bytes(packet)
                    method=(header[1]>>(2*context))&3
                    name='actual_c%df%d_p%d_chunk%d_context%d_variant%d'%(*identity,axis,chunk_number,context,offset)
                    trace=add(name,header[2][context],context,method,
                              dict(kind='actual_corpus',cohort=identity[0],fid=identity[1],
                                   frame_key=frame['key'],ordinal=frame['ordinal'],
                                   canonical_coefficients_sha256=frame['canonical_coefficients_sha256'],
                                   baseline_chunk_coefficient_sha256=coefficient_sha,
                                   baseline_frame_bindings={k:frame[k] for k in
                                       ('packet_path','packet_sha256','canonical_sha256','hud_sha256',
                                        'display_sha256','canonical_coefficients_sha256',
                                        'component_sha256','refid') if k in frame},
                                   plane=axis,chunk=chunk_number,blocks=chunk['blocks'],variant=offset,
                                   packet_path=str(path.relative_to(out)),packet_sha256=sha(path),
                                   source_index=str(args.corpus_index.relative_to(ROOT)),source_index_sha256=sha(args.corpus_index)))
                    assert trace['symbol_count']==fields
            report['corpus_frames_verified']=frames_checked
            report['corpus_index_bindings']={k:index[k] for k in ('schema','status','source_sha256','data') if k in index}
        binary=bytearray(b'RV94'+struct.pack('<I',len(cases)))
        for case in cases:
            trace=json.loads((out/case['trace_path']).read_text())
            binary+=struct.pack('<5I',trace['scale'],trace['lanes'],len(trace['models']),trace['symbol_count'],len(trace['renorm_bytes']))
            binary+=struct.pack('<4I',*(trace['initial_states']+[codec.RANS_L]*(4-trace['lanes'])))
            models=[m['freq'] for m in trace['models']]
            if len(models)==1:
                models.append([(1<<trace['scale'])//16]*16)
            binary+=struct.pack('<32H',*(models[0]+models[1]))
            binary+=bytes(trace['renorm_bytes'])
            for field in trace['fields']:
                binary+=struct.pack('<4I',field['q'],field['lane'],field['state_after'],field['cursor'])
        vector_path=out/'vectors.bin';vector_path.write_bytes(binary)
        coverage=sorted({n for c in cases for n in c['renorm_counts']})
        assert pins=={name:sha(ROOT/name) for name in pins},'pinned inputs changed'
        report.update(status='PASS_INDEPENDENT_RANS_RTL_VECTORS',case_count=len(cases),
                      actual_case_count=sum(c['kind']=='actual_corpus' for c in cases),
                      actual_symbols=sum(c['symbols'] for c in cases if c['kind']=='actual_corpus'),
                      total_symbols=sum(c['symbols'] for c in cases),renorm_count_coverage=coverage,
                      uncovered_renorm_counts=sorted({0,1,2}-set(coverage)),
                      empty_cases=sum(c['symbols']==0 for c in cases),
                      vectors_path='vectors.bin',vectors_sha256=sha(vector_path))
    except BaseException as error:
        report['error']=repr(error)
        raise
    finally:
        signal.alarm(0);report['wall_seconds']=time.monotonic()-started
        report['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()}
        (out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
        print(report['status'],out/'manifest.json',flush=True)
    (AREA/'index.json').write_text(json.dumps(dict(report,selected_report=str((out/'manifest.json').relative_to(ROOT))),indent=2)+'\n')


if __name__=='__main__':
    main()
