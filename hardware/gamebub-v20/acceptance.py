#!/usr/bin/env python3
"""Compile and replay the portable C11 inverse against retained golden vectors."""
import argparse,ctypes,hashlib,json,os,platform,re,shutil,subprocess,tempfile,zlib
from pathlib import Path
import numpy as np
import reference as ref
HERE=Path(__file__).resolve().parent
FIELDS=('nonzero_coefficients','nonzero_intermediates','first_products','second_products','constant_products','classification')
class Work(ctypes.Structure):_fields_=[(name,ctypes.c_uint32) for name in FIELDS]
PTR=ctypes.POINTER(ctypes.c_int32)
def load_array(desc):
    path=HERE/desc['path'];stored=path.read_bytes();assert hashlib.sha256(stored).hexdigest()==desc['stored_sha256']
    raw=zlib.decompress(stored);assert len(raw)==desc['raw_bytes'] and hashlib.sha256(raw).hexdigest()==desc['raw_sha256']
    return np.frombuffer(raw,dtype='<i4').reshape(desc['shape']).astype(np.int32,copy=True)
def compile_library(folder,sanitized=True):
    cc=shutil.which('cc') or shutil.which('gcc') or shutil.which('clang')
    output=Path(folder)/'libgb_v20_inverse.so'
    flags=['-std=c11','-O2','-Wall','-Wextra','-Werror','-fPIC','-shared']
    if sanitized:flags+=['-fsanitize=undefined','-fno-sanitize-recover=undefined']
    mode='host'
    if cc is not None:
        command=[cc,*flags,'-I',str(HERE/'include'),str(HERE/'src/gb_inverse.c'),'-o',str(output)]
        subprocess.run(command,check=True,capture_output=True,text=True)
        version=subprocess.run([cc,'--version'],check=True,capture_output=True,text=True).stdout.splitlines()[0]
    else:
        container=os.environ.get('GB_V20_COMPILER_CONTAINER','gamebub-esp32-dev')
        if shutil.which('docker') is None or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*',container):raise RuntimeError('Install a C11 compiler and UBSan, or set GB_V20_COMPILER_CONTAINER to an existing x86-64 development container')
        mode='existing-container:'+container
        tmp=subprocess.run(['docker','exec',container,'mktemp','-d','/tmp/gb-v20-ref-XXXXXXXX'],check=True,capture_output=True,text=True).stdout.strip()
        if not tmp.startswith('/tmp/gb-v20-ref-') or '/' in tmp[len('/tmp/'):]:raise RuntimeError('unexpected compiler temporary directory')
        try:
            for name,src in [('gb_inverse.c',HERE/'src/gb_inverse.c'),('gb_inverse.h',HERE/'include/gb_inverse.h')]:
                subprocess.run(['docker','cp',str(src),container+':'+tmp+'/'+name],check=True,capture_output=True,text=True)
            # Carry UBSan in the result so the newer host needs no matching runtime package.
            if sanitized:flags+=['-static-libubsan']
            command=['docker','exec',container,'cc',*flags,'-I',tmp,tmp+'/gb_inverse.c','-o',tmp+'/libgb_v20_inverse.so']
            built=subprocess.run(command,capture_output=True,text=True)
            if built.returncode:raise RuntimeError(built.stdout+built.stderr)
            subprocess.run(['docker','cp',container+':'+tmp+'/libgb_v20_inverse.so',str(output)],check=True,capture_output=True,text=True)
            version=subprocess.run(['docker','exec',container,'cc','--version'],check=True,capture_output=True,text=True).stdout.splitlines()[0]
        finally:
            subprocess.run(['docker','exec',container,'rm','-rf','--',tmp],check=True,capture_output=True,text=True)
    lib=ctypes.CDLL(str(output));fn=lib.gb_v20_inverse_block;fn.argtypes=[PTR,PTR,ctypes.POINTER(Work)];fn.restype=ctypes.c_int
    return lib,fn,dict(compiler=version,compiler_mode=mode,flags=flags,platform=platform.platform(),sanitized=sanitized)
def check_errors(fn):
    original=np.arange(64,dtype=np.int32);output=np.full(64,987654,np.int32);work=Work(*([777]*6))
    assert fn(None,output.ctypes.data_as(PTR),ctypes.byref(work))==-1
    assert np.all(output==987654) and all(getattr(work,k)==777 for k in FIELDS)
    for bad in (-522241,522241):
        a=original.copy();a[-1]=bad
        assert fn(a.ctypes.data_as(PTR),output.ctypes.data_as(PTR),ctypes.byref(work))==-2
        assert np.all(output==987654) and all(getattr(work,k)==777 for k in FIELDS)
    assert fn(original.ctypes.data_as(PTR),None,ctypes.byref(work))==-1
    return 4

def run(sanitized=True):
    index=json.loads((HERE/'golden-index.json').read_text())
    for raw,h in index['source_sha256'].items():assert ref.sha(ref.ROOT/raw)==h,raw
    rows=[]
    with tempfile.TemporaryDirectory(prefix='gb-v20-c11-') as folder:
        lib,fn,toolchain=compile_library(folder,sanitized);errors=check_errors(fn)
        for dataset in index['datasets']:
            values=load_array(dataset['arrays']['dequantized']);expected=load_array(dataset['arrays']['residual'])
            output=np.empty_like(values);totals={k:0 for k in FIELDS[:-1]};modes=[0,0,0]
            for i in range(len(values)):
                work=Work();assert fn(values[i].ctypes.data_as(PTR),output[i].ctypes.data_as(PTR),ctypes.byref(work))==0
                modes[work.classification]+=1
                for name in totals:totals[name]+=getattr(work,name)
            np.testing.assert_array_equal(output,expected)
            assert totals=={k:dataset['work'][k] for k in totals}
            assert modes==[dataset['work'][k] for k in ('zero','dc','general')]
            rows.append(dict(name=dataset['name'],blocks=len(values),exact_residual_samples=int(output.size),
                residual_sha256=hashlib.sha256(output.astype('<i4').tobytes()).hexdigest(),work=totals,classification_counts=modes))
    return dict(schema='gamebub-v20-c11-acceptance-v1',source_sha256=ref.source_pins(),golden_index_sha256=ref.sha(HERE/'golden-index.json'),
        toolchain=toolchain,invalid_input_checks=errors,datasets=rows,blocks=sum(r['blocks'] for r in rows),
        exact_residual_samples=sum(r['exact_residual_samples'] for r in rows),
        scope='Native host C11 scalar arithmetic replay with undefined-behavior sanitizer; not ESP32 execution, RTL simulation, resource/Fmax proof, full codec or physical30fps.')
def main():
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');p.add_argument('--no-sanitize',action='store_true');args=p.parse_args();data=run(not args.no_sanitize)
    if args.write:(HERE/'results.json').write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps(dict(blocks=data['blocks'],exact_residual_samples=data['exact_residual_samples'],invalid_input_checks=data['invalid_input_checks'],sanitized=data['toolchain']['sanitized'],hardware_30fps_proven=False),indent=2))
if __name__=='__main__':main()
