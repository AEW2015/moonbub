"""Actual retained CU66 gameplay coefficients and independent FT01 goldens.

Quantizer code is inferred ONLY by exact equality against the packet parser's
per-block normative table; unsupported tables fail rather than invent a code.
"""
from pathlib import Path
import hashlib,importlib.util,json,sys
import numpy as np
r=Path(__file__).resolve().parents[3];out=r/'fpga/experiments/cu66-v71/dequant'
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
e=module('cu71_pinned_inverse_export',r/'fpga/experiments/cu66-v69/inverse/export.py')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pack=lambda a,b:''.join(f'{int(x)&((1<<b)-1):0{b//4}x}'for x in np.asarray(a).reshape(-1)[::-1])
def line(ident,a,chroma,code):
    bad=code==3 or bool(np.any(a < -2048)or np.any(a>2048))
    golden=np.zeros((8,8),np.int64)if bad else a.astype(np.int64)*e.ft.qtable((8,16,32)[code],bool(chroma))
    return f'{ident} {int(chroma)} {code} {pack(a,16)} {pack(golden,20)} {int(bad)}\n'
records=[];packets={};lines=[];source=r/'experiments/python-game-binary-qual-v40-study';data=e.h.load(source/'results.json');rng=np.random.default_rng(710069)
for c in data['cases']:
    for fid in(0,1,24,len(c['rows'])-1):
        row=c['rows'][fid];raw=e.h.raw(row['packet'],source);parsed=e.rx.parse(raw);packet_key=c['scene']+'/'+str(fid);packets[packet_key]=hashlib.sha256(raw).hexdigest()
        for axis,coeff in enumerate(parsed['coefficients']):
            tables=e.h.m.roi.block_tables(parsed['qmap'],720,480,axis)
            indices=sorted(set(range(min(8,len(coeff))))|set(map(int,rng.choice(len(coeff),64,replace=False))))
            for index in indices:
                matches=[i for i,s in enumerate((8,16,32))if np.array_equal(tables[index],e.ft.qtable(s,axis!=0))]
                assert len(matches)==1,(packet_key,axis,index,matches)
                lines.append(line(len(lines)+1,coeff[index],axis!=0,matches[0]));records.append([packet_key,axis,index,matches[0]])
(out/'gameplay.hex').write_text(''.join(lines))
directed=[]
for chroma in(0,1):
    for code in range(4):
        for value in(0,-2048,2048,-2049,2049,-32768,32767):
            a=np.full((8,8),value,np.int64);directed.append(line(len(directed)+1,a,chroma,code))
        for index in range(64):
            for value in(-2048,2048,-2049,2049):
                a=np.zeros((8,8),np.int64);a.flat[index]=value;directed.append(line(len(directed)+1,a,chroma,code))
(out/'directed.hex').write_text(''.join(directed))
sources={}
for m in list(sys.modules.values()):
    f=getattr(m,'__file__',None)
    if f:
        p=Path(f).resolve()
        if p.is_relative_to(r)and p.is_file():sources[p.relative_to(r).as_posix()]=sha(p)
for p in(Path(__file__),source/'results.json'):sources[p.relative_to(r).as_posix()]=sha(p)
report=dict(gameplay_cases=len(lines),directed_cases=len(directed),seed=710069,packet_sha256=packets,source_sha256=sources,records=records,files={n:sha(out/n)for n in('gameplay.hex','directed.hex')},scope='All 64 words per sampled actual gameplay block; independent FT01 qtable multiplication; not all frames or hardware')
(out/'vectors.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in('gameplay_cases','directed_cases','files')}))
