"""Independent NumPy goldens for dequantization and canonical reconstruction."""
from pathlib import Path
import hashlib,importlib.util,json,sys
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
p=ROOT/'experiments/python-transform-study/fixed_codec.py';s=importlib.util.spec_from_file_location('math69_frozen_ft',p);ft=importlib.util.module_from_spec(s);sys.modules[s.name]=ft;s.loader.exec_module(ft)
def packed(a,bits):return ''.join(f'{int(x)&((1<<bits)-1):0{bits//4}x}'for x in np.asarray(a).reshape(-1)[::-1])
def main():
    rng=np.random.default_rng(690046);dq=[];rc=[]
    for i in range(1536):
        scale=i%4;chroma=(i//4)%2
        a=rng.integers(-2048,2049,(8,8),dtype=np.int64)
        if i%7==0:a[:]=0
        if i%11==0:a[:]=0;a[0,0]=int(rng.choice([-2048,-1,1,2048]))
        if i%23==0:a[2,5]=int(rng.choice([-32768,-2049,2049,32767]))
        bad=scale==3 or bool(np.any(np.abs(a)>2048))
        expected=np.zeros_like(a) if bad else a*ft.qtable((8,16,32)[scale],bool(chroma))
        dq.append(f'{i+1} {chroma} {scale} {packed(a,16)} {packed(expected,20)} {int(bad)}\n')
        residual=rng.integers(-(1<<23),1<<23,64,dtype=np.int64)
        if i%5==0:residual=rng.choice([-257,-256,-255,-129,-128,-1,0,1,127,128,255,256],64)
        reference=rng.integers(0,256,64,dtype=np.uint8);key=i%3==0;hidden=i%7==0
        reference_id=i+1 if i%13 else i+2
        result=np.full(64,128,np.uint8) if hidden else np.clip(residual+(128 if key else reference.astype(np.int64)),0,255).astype(np.uint8)
        error=not key and not hidden and reference_id!=i+1
        rc.append(f'{i+1} {int(key)} {int(hidden)} {reference_id} {packed(residual,24)} {packed(reference,8)} {packed(result,8)} {int(error)}\n')
    for name,lines in [('dequant.hex',dq),('reconstruct.hex',rc)]: (HERE/name).write_text(''.join(lines))
    result={'schema':'cu66-math-v69-fixtures','seed':690046,'dequant_cases':len(dq),'reconstruct_cases':len(rc),
            'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest(),str(Path(__file__).relative_to(ROOT)):hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
            'files':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['dequant.hex','reconstruct.hex']},
            'scope':'Normative/invalid coefficient and quantizer cases; signed residual clipping, key and hidden normalization, tile address mismatch. No memory throughput proof.'}
    (HERE/'math-fixtures.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'dequant':len(dq),'reconstruct':len(rc)}))
if __name__=='__main__':main()
