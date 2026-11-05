#!/usr/bin/env python3
"""Replay v31 cycles, project bank overlap, and inspect v32 residual schedules."""
from pathlib import Path
import hashlib,importlib.util,json,sys,zlib
import numpy as np
import model as scheduling
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('schedule32_runtime',HERE.parent/'python-game-runtime-v28-study/model.py')
codec=importlib.util.module_from_spec(spec);sys.modules[spec.name]=codec;spec.loader.exec_module(codec)

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(desc,folder):
    p=folder/desc['path'];packed=p.read_bytes();assert hashlib.sha256(packed).hexdigest()==desc['stored_sha256']
    dc=zlib.decompressobj();raw=dc.decompress(packed,desc['raw_bytes']+1)
    assert dc.eof and not dc.unused_data and not dc.unconsumed_tail and len(raw)==desc['raw_bytes'] and hashlib.sha256(raw).hexdigest()==desc['raw_sha256'];return raw,p

def main():
    old=HERE.parent/'rtl-game-inverse-v31-study';vectors=json.loads((old/'vectors.json').read_text());rtl=json.loads((old/'results/results.json').read_text())
    d=vectors['files']['kind'];packed=(old/d['path']).read_bytes();assert hashlib.sha256(packed).hexdigest()==d['stored_sha256']
    raw=zlib.decompress(packed);assert hashlib.sha256(raw).hexdigest()==d['raw_sha256']
    kinds=[int(v,16) for v in raw.split()];controls=[]
    for group in vectors['groups']:
        if 'scene' not in group:continue
        frame=kinds[group['start_block']:group['start_block']+8100]
        measured=next(f for c in rtl['simulations'] if c['bypass']==1 and c['stalls']==0 for f in c['frames'] if (f['scene'],f['frame_id'])==(group['scene'],group['frame_id']))
        points=[]
        for banks in (1,2,3):
            result=scheduling.schedule(frame,banks);assert scheduling.validate(result)
            if banks==1:assert result['done_cycles']==measured['service_cycles']
            points.append({k:v for k,v in result.items() if k!='rows'})
        controls.append(dict(scene=group['scene'],frame_id=group['frame_id'],points=points,old_RTL_cycles=measured['service_cycles']))
    campaign=HERE.parent/'python-game-controller-v32-study';data=json.loads((campaign/'results.json').read_text());cases=[];objects=set()
    assert len(data['cases'])==6
    for case in data['cases']:
        rows=[]
        for row in case['rows']:
            packet,path=read(row['base_packet'],campaign);objects.add(path);meta=codec.parse(packet)
            frame=[]
            for c in meta['coefficients']:
                k=np.where(np.any(c.reshape(-1,64)[:,1:]!=0,axis=1),2,np.where(c[:,0,0]!=0,1,0));frame.extend(int(v) for v in k)
            assert len(frame)==8100
            points=[]
            for banks in (1,2,3):
                result=scheduling.schedule(frame,banks);assert scheduling.validate(result)
                points.append(dict(banks=banks,cycles=result['done_cycles'],projection_ms_at_unclosed_100MHz=result['done_cycles']/100000,payload_storage_bits=result['payload_storage_bits']))
            rows.append(dict(id=row['id'],base_packet=row['base_packet'],kinds=dict(zero=frame.count(0),dc=frame.count(1),general=frame.count(2)),points=points))
        summary={str(b):dict(mean_projection_ms_at_unclosed_100MHz=sum(r['points'][b-1]['cycles'] for r in rows)/48/100000,
                            worst_projection_ms_at_unclosed_100MHz=max(r['points'][b-1]['cycles'] for r in rows)/100000,
                            payload_storage_bits=b*scheduling.PAYLOAD_BITS_PER_BANK) for b in (1,2,3)}
        cases.append(dict(scene=case['scene'],policy=case['policy'],rows=rows,summary=summary))
    paths={HERE/'model.py',HERE/'benchmark.py',HERE/'test_model.py',HERE/'verify.py',old/'vectors.json',old/'results/results.json',old/d['path'],campaign/'results.json'}|objects
    paths|={Path(v.__file__).resolve() for v in list(sys.modules.values()) if getattr(v,'__file__',None) and Path(v.__file__).resolve().is_relative_to(ROOT)}
    output=dict(schema='gamebub-banked-schedule-v32',source_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)},
                controls=controls,cases=cases,stage_cycles=dict(load=64,zero_compute=0,dc_compute=4,general_compute=132,output=64),
                clock_MHz_assumed=100,new_RTL_implemented=False,physical_30fps_proven=False,
                scope=['One-bank controls exactly reproduce measured v31 no-stall cycles; two/three-bank points are new architecture projections.',
                       'Independent load/compute/output resources, ordered service, separate bank memory/ports and no external stalls are assumptions.',
                       'Logical payload bits exclude control, DSP registers, RAM port replication and physical memory mapping.',
                       'No entropy/dequant/reference-memory/color/HUD/CRC/network/QSPI/publication/LCD service or routed clock included.'])
    (HERE/'results.json').write_text(json.dumps(output,separators=(',',':'))+'\n')
    print(json.dumps(dict(controls=controls,summaries=[{k:c[k] for k in ('scene','policy','summary')} for c in cases]),indent=2))

if __name__=='__main__':main()
