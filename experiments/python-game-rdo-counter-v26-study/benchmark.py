#!/usr/bin/env python3
"""Paid native GM25 parity and exact isolated CP02 probe count benchmark."""
from pathlib import Path
import hashlib
import importlib.util
import json
import platform
import sys
import time
import zlib
import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
V25=HERE.parent/'python-game-capped-key-v25-study'
V24=HERE.parent/'python-game-standard-v24-study'
ROIS=((16,48,192,80),(160,352,400,80))
spec=importlib.util.spec_from_file_location('counter26_fast_adapter',HERE/'fast_model.py')
fast=importlib.util.module_from_spec(spec);sys.modules[spec.name]=fast;spec.loader.exec_module(fast)
b=fast.base
c=fast.counter
USED=set()

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def load(path):USED.add(Path(path));return json.loads(Path(path).read_text())

def raw(desc,directory):
    p=Path(desc['path'])
    assert not p.is_absolute() and '..' not in p.parts
    path=directory/p;USED.add(path);data=path.read_bytes()
    assert hashlib.sha256(data).hexdigest()==desc['stored_sha256']
    d=zlib.decompressobj();out=d.decompress(data,desc['raw_bytes']+1)
    assert d.eof and not d.unused_data and not d.unconsumed_tail
    assert len(out)==desc['raw_bytes'] and hashlib.sha256(out).hexdigest()==desc['raw_sha256']
    return out

def source(row):
    # Both retained original RGB565 and common YUV source artifacts are checked.
    raw(row['original_rgb565'],V24)
    a=np.frombuffer(raw(row['common_yuv420_u8'],V24),np.uint8)
    return tuple(x.astype(np.int16) for x in (a[:345600].reshape(480,720),a[345600:432000].reshape(240,360),a[432000:].reshape(240,360)))

def fixtures():
    old=load(V25/'results.json');inputs=load(V24/'results.json')
    return [x for x in old['cases'] if x['profile']=='capped_key_zero_rdo1'],{x['scene']:x for x in inputs['inputs']}

def native_samples(cases):
    chunks=[];manifest=[];general=[]
    for case in cases:
        for row in case['rows']:
            if row['id'] not in (0,1,24,25):continue
            packet=raw(row['base_packet'],V25);meta=b.parse(packet,expected_epoch=25)
            for plane,coeff in enumerate(meta['coefficients']):
                bw=90 if plane==0 else 45
                actual=len(c.oracle.encode_coefficients(coeff,bw));count=c.count_packets(coeff,bw)
                assert actual==count
                general.append(dict(scene=case['scene'],id=row['id'],plane=plane,blocks=len(coeff),bytes=actual))
            # The real RDO CP02 path probes full blocks, not zeros or DC-only.
            coeff=meta['coefficients'][0];_,_,full=b.sr.classifications(coeff)
            indices=np.flatnonzero(full)
            indices=indices[np.linspace(0,len(indices)-1,min(512,len(indices)),dtype=int)]
            selected=coeff[indices];chunks.append(selected)
            manifest.append(dict(scene=case['scene'],id=row['id'],plane=0,packet=row['base_packet'],indices=indices.tolist(),coefficient_sha256=digest(selected)))
    return np.concatenate(chunks),manifest,general

def time_call(fn):
    start=time.perf_counter_ns();result=fn();return result,(time.perf_counter_ns()-start)/1e6

def counter_campaign(cases):
    a,manifest,general=native_samples(cases)
    want=np.array([len(c.oracle.encode_coefficients(x[None],1)) for x in a],np.int64)
    np.testing.assert_array_equal(c.isolated_packet_bytes(a),want)
    serial=[];counter=[]
    for repeat in range(5):
        order=('counter','serial') if repeat%2 else ('serial','counter')
        for kind in order:
            fn=(lambda:c.isolated_packet_bytes(a)) if kind=='counter' else (lambda:np.array([len(c.oracle.encode_coefficients(x[None],1)) for x in a],np.int64))
            result,elapsed=time_call(fn);np.testing.assert_array_equal(result,want)
            (counter if kind=='counter' else serial).append(elapsed)
    return dict(blocks=len(a),coefficient_sha256=digest(a),exact_packet_bytes=int(want.sum()),sizes_sha256=digest(want),oracle_ms=serial,counter_ms=counter,oracle_median_ms=float(np.median(serial)),counter_median_ms=float(np.median(counter)),speedup_median=float(np.median(serial)/np.median(counter)),counter_constructed_packets=0,manifest=manifest,general_packets=general)

def native_campaign(cases,inputs,verify_rows=None):
    rows=[]
    for case in cases:
        reference=None
        for row,original in zip(case['rows'],inputs[case['scene']]['rows']):
            key=row['key'];src=source(original)
            (prepared,analysis_ms)=time_call(lambda:b.analyze_planes(src,None if key else reference,epoch=25,frame_id=row['id'],reference_id=b.NO_REF if key else row['reference_id'],block_size=16,motion_mode='zero',penalty=0))
            attempts=[]
            for attempt in row['attempts']:
                mapped=b.roi.declared_map(720,480,ROIS,8,attempt['background'])
                stored=raw(attempt['packet'],V25)
                lam=0 if key else 1
                outputs={};elapsed={}
                order=('fast','frozen') if row['id']%2 else ('frozen','fast')
                if verify_rows is not None:order=('fast',)
                for kind in order:
                    method=fast.encode_prepared if kind=='fast' else b.encode_prepared
                    outputs[kind],elapsed[kind]=time_call(lambda:method(prepared,mapped,rdo_lambda=lam))
                    assert outputs[kind][0]==stored,(case['scene'],row['id'],attempt['background'],kind)
                packet,rebuilt,work=outputs['fast']
                parsed=b.parse(packet,expected_epoch=25)
                if 'frozen' in outputs:
                    old_packet,old_rebuilt,old_work=outputs['frozen']
                    assert old_packet==packet
                    for x,y in zip(rebuilt,old_rebuilt):np.testing.assert_array_equal(x,y)
                    for name,value in old_work['rdo'].items():
                        if name not in ('cp02_probe_calls','cp02_probe_bytes'):assert work['rdo'][name]==value,name
                    assert work['rdo']['cp02_logical_probe_calls']==old_work['rdo']['cp02_probe_calls']
                    assert work['rdo']['cp02_logical_probe_bytes']==old_work['rdo']['cp02_probe_bytes']
                attempts.append(dict(background=attempt['background'],packet=attempt['packet'],packet_sha256=hashlib.sha256(packet).hexdigest(),packet_bytes=len(packet),coefficient_sha256=[digest(x) for x in parsed['coefficients']],reconstructed_sha256=[digest(x) for x in rebuilt],order=list(order),wall_ms=elapsed,rdo_ms={kind:out[2]['rdo_ms'] for kind,out in outputs.items()},rdo=work['rdo']))
            # Advance from the retained accepted decoded GM25 only. Never use
            # original source or a losing attempt as the next reference.
            accepted=raw(row['base_packet'],V25)
            reference,meta=b.decode(accepted,None if key else reference,expected_epoch=25,expected_reference_id=None if key else row['reference_id'])
            assert accepted==packet
            for x,y in zip(reference,rebuilt):np.testing.assert_array_equal(x,y)
            record=dict(scene=case['scene'],id=row['id'],key=key,reference_id=row['reference_id'],selected_background=row['selected_background'],analysis_ms=analysis_ms,attempts=attempts)
            rows.append(record)
            print(json.dumps(dict(scene=case['scene'],id=row['id'],attempts=len(attempts),fast_ms=sum(x['wall_ms']['fast'] for x in attempts),frozen_ms=sum(x['wall_ms'].get('frozen',0) for x in attempts))),flush=True)
    return rows

def summarize(rows):
    out=dict(sources=len(rows),attempts=sum(len(x['attempts']) for x in rows),all_packet_coefficient_reconstruction_equal=True,all_packet_bytes_equal_retained_v25=True,actual_probe_packets=0)
    for kind in ('frozen','fast'):
        walls=[sum(a['wall_ms'][kind] for a in r['attempts']) for r in rows]
        rdo=[sum(a['rdo_ms'][kind] for a in r['attempts']) for r in rows]
        paid=[r['analysis_ms']+wall for r,wall in zip(rows,walls)]
        out[kind]=dict(total_encode_prepared_ms=sum(walls),mean_encode_prepared_ms=float(np.mean(walls)),total_rdo_ms=sum(rdo),mean_rdo_ms=float(np.mean(rdo)),total_analysis_plus_attempts_ms=sum(paid),mean_analysis_plus_attempts_ms=float(np.mean(paid)))
    out['encode_prepared_speedup']=out['frozen']['total_encode_prepared_ms']/out['fast']['total_encode_prepared_ms']
    out['rdo_speedup']=out['frozen']['total_rdo_ms']/out['fast']['total_rdo_ms']
    out['logical_probe_calls']=sum(a['rdo']['cp02_logical_probe_calls'] for r in rows for a in r['attempts'])
    out['logical_probe_bytes']=sum(a['rdo']['cp02_logical_probe_bytes'] for r in rows for a in r['attempts'])
    return out

def pins():
    paths=set(USED)
    paths|={HERE/x for x in ('model.py','fast_model.py','benchmark.py','test_model.py','verify.py','README.md','SCHEMA.md')}
    for module in list(sys.modules.values()):
        path=Path(getattr(module,'__file__','') or '.')
        if path.is_file() and ROOT in path.resolve().parents and path.suffix=='.py':paths.add(path.resolve())
    return {p.resolve().relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}

def main():
    cases,inputs=fixtures();counter=counter_campaign(cases);rows=native_campaign(cases,inputs)
    data=dict(schema='gamebub-rdo-counter-v26',host=dict(python=sys.version,numpy=np.__version__,platform=platform.platform()),geometry=dict(coded=[720,480],active=[720,405]),counter=counter,rows=rows,summary=summarize(rows),source_sha256=pins(),scope='Host Python only; same prepared analysis for alternating frozen/fast calls; source loading, retained reference decode, parity assertions and HUD excluded from encoder clocks; no hardware FPS claim.')
    (HERE/'results.json').write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps(data['summary'],indent=2))

if __name__=='__main__':main()
