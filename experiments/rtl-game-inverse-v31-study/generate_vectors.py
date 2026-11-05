#!/usr/bin/env python3
"""Q14 goldens: directed/random blocks plus four full real codec frames."""
from pathlib import Path
import hashlib, importlib.util, json, sys, zlib
import numpy as np
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]

def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
m=module('inverse31_runtime',HERE.parent/'python-game-runtime-v28-study/model.py')

def sha(data):return hashlib.sha256(data).hexdigest()
def raw(desc,folder):
    q=Path(desc['path']);assert not q.is_absolute() and '..' not in q.parts
    p=folder/q;packed=p.read_bytes();assert sha(packed)==desc['stored_sha256']
    dc=zlib.decompressobj();out=dc.decompress(packed,desc['raw_bytes']+1)
    assert dc.eof and not dc.unused_data and not dc.unconsumed_tail and len(out)==desc['raw_bytes'] and sha(out)==desc['raw_sha256']
    return out,p

def blocks(plane):
    h,w=plane.shape;assert h%8==0 and w%8==0
    return plane.reshape(h//8,8,w//8,8).transpose(0,2,1,3).reshape(-1,8,8)

def scalar_inverse(a):
    q=m.ft.Q14.tolist();a=a.tolist();mid=[[0]*8 for _ in range(8)];out=[[0]*8 for _ in range(8)]
    for r in range(8):
        for c in range(8):mid[r][c]=(sum(a[r][k]*q[k][c] for k in range(8))+8192)//16384
    for r in range(8):
        for c in range(8):out[r][c]=(sum(q[k][r]*mid[k][c] for k in range(8))+8192)//16384
    return np.array(out,np.int64)

def main():
    rng=np.random.default_rng(31004);inputs=[];preds=[];groups=[];paths=set()
    def add(label,a,p=None):
        start=len(inputs);a=np.asarray(a,np.int64).reshape(-1,8,8)
        p=rng.integers(0,256,a.shape,dtype=np.int16) if p is None else np.asarray(p,np.int16).reshape(a.shape)
        inputs.extend(a);preds.extend(p);groups.append(dict(label=label,start_block=start,blocks=len(a)))
    directed=[np.zeros((8,8),np.int64)]
    for v in (1,-1,7,-7,8192,-8192,16384,-16384,522240,-522240):
        a=np.zeros((8,8),np.int64);a[0,0]=v;directed.append(a)
    for position in range(64):
        for v in (1,-1,8192,-8192,522240,-522240):
            a=np.zeros((8,8),np.int64);a.flat[position]=v;directed.append(a)
    directed += [np.full((8,8),522240,np.int64),np.full((8,8),-522240,np.int64),np.where(np.indices((8,8)).sum(axis=0)%2,522240,-522240)]
    add('directed-boundaries-bases-rounding',np.array(directed))
    a=rng.integers(-522240,522241,(128,8,8),dtype=np.int64);add('seeded-dense',a)
    a=rng.integers(-522240,522241,(128,8,8),dtype=np.int64);a[rng.random(a.shape)<.95]=0;add('seeded-sparse',a)
    directed_count=len(inputs)
    study=HERE.parent/'python-game-controller-v30-study';path=study/'results.json';paths.add(path)
    data=json.loads(path.read_text())
    for case in data['cases']:
        if case['policy']!='band_strict':continue
        ref=None
        for row in case['rows']:
            if row['key']:ref=None
            packet,source=raw(row['base_packet'],study);paths.add(source)
            out,meta=m.decode(packet,ref,expected_epoch=25,expected_reference_id=None if row['key'] else row['reference_id'])
            if row['id'] in (0,12):
                prediction=tuple(np.full_like(p,128) for p in out) if row['key'] else m.taps.predict(ref,meta['vectors'],32)
                start=len(inputs)
                for plane,c in enumerate(meta['coefficients']):
                    a=c.astype(np.int64)*m.roi.block_tables(meta['scale_map'],720,480,plane)
                    inputs.extend(a);preds.extend(blocks(prediction[plane]))
                assert len(inputs)-start==8100
                groups.append(dict(label=case['scene']+'-frame'+str(row['id']),scene=case['scene'],frame_id=row['id'],start_block=start,blocks=8100))
            ref=out
    coeff=np.array(inputs,np.int64);pred=np.array(preds,np.int16)
    assert np.abs(coeff).max()<=522240
    residual=m.ft.inverse(coeff)
    for i in range(directed_count):np.testing.assert_array_equal(residual[i],scalar_inverse(coeff[i]))
    pixels=np.clip(residual+pred,0,255).astype(np.uint8)
    kind=np.where(np.any(coeff.reshape(-1,64)[:,1:]!=0,axis=1),2,np.where(coeff[:,0,0]!=0,1,0))
    target=HERE/'fixtures';target.mkdir(exist_ok=True);files={}
    for name,array,bits in (('coeff',coeff,20),('prediction',pred,8),('residual',residual,24),('pixel',pixels,8),('kind',kind,4)):
        mask=(1<<bits)-1;width=(bits+3)//4
        text=('\n'.join(f'{int(v)&mask:0{width}x}' for v in array.reshape(-1))+'\n').encode()
        packed=zlib.compress(text,9);rel='fixtures/'+name+'.mem.zlib';(HERE/rel).write_bytes(packed)
        files[name]=dict(path=rel,raw_bytes=len(text),raw_sha256=sha(text),stored_sha256=sha(packed))
    q=m.ft.Q14;col_l1=int(np.abs(q).sum(axis=0).max());mid_bound=(522240*col_l1+8192)//16384;out_bound=(mid_bound*col_l1+8192)//16384
    assert mid_bound<(1<<23) and out_bound<(1<<23)
    paths|={Path(v.__file__).resolve() for v in list(sys.modules.values()) if getattr(v,'__file__',None) and Path(v.__file__).resolve().is_relative_to(ROOT)}
    manifest=dict(schema='gamebub-q14-rtl-v31-vectors',blocks=len(coeff),samples=len(coeff)*64,directed_random_blocks=directed_count,
        groups=groups,files=files,source_sha256={p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in sorted(paths)},
        kinds=dict(zero=int((kind==0).sum()),dc=int((kind==1).sum()),general=int((kind==2).sum())),
        arithmetic=dict(input_signed_bits=20,intermediate_signed_bits=24,product_signed_bits=38,accumulator_signed_bits=48,output_residual_signed_bits=24,
                        maximum_dequantized_abs=522240,matrix_column_abs_sum_max=col_l1,proven_intermediate_abs_bound=mid_bound,proven_output_abs_bound=out_bound,
                        observed_output_abs_max=int(np.abs(residual).max()),rounding='(sum+8192) arithmetic_shift_right14 at both stages; ties toward positive infinity'),
        limitations=['Dequantized inverse/predict/clip kernel vectors only, not entropy/QSPI/SDRAM/full decoder tests.','Four real complete component frames; other accepted reference frames decoded on Python to establish their histories.'])
    (HERE/'vectors.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in manifest.items() if k not in ('files','source_sha256','groups')}))

if __name__=='__main__':main()
