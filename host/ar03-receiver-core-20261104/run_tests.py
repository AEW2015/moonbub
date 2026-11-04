#!/usr/bin/env python3
"""Offline source/hash and rustc host-test runner for the AR03 receiver-core export."""
from __future__ import annotations
import argparse, hashlib, json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
EXPECTED_INVENTORY='d904373e006126480d3de5c9d2711e459a614b0ed04de1dcc2b83b602243f36d'
EXPECTED_TESTS={'ar03_lab_gateway.rs':22,'ar03_state_transcripts.rs':10}

def digest(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def write_log(out:Path,name:str,text:str):
    if out is not None:
        out.mkdir(parents=True,exist_ok=True)
        (out/name).write_text(text,encoding='utf-8',newline='\n')

def verify_snapshot():
    snap_path=HERE/'source-snapshot.json'; snap=json.loads(snap_path.read_bytes())
    if snap['source_inventory_sha256']!=EXPECTED_INVENTORY:raise RuntimeError('unexpected source inventory pin')
    if snap['copied_file_count']!=13 or len(snap['files'])!=13:raise RuntimeError('expected 13 source files')
    for rec in snap['files']:
        p=HERE/rec['export_relative_path']; raw=p.read_bytes()
        if len(raw)!=rec['bytes'] or digest(raw)!=rec['sha256']:
            raise RuntimeError(f'export source hash mismatch: {rec["export_relative_path"]}')
    fm_path=HERE/'tests/fixtures/ar03-lab/manifest.json'; fm=json.loads(fm_path.read_bytes())
    if fm['FG19_messages']!=1725 or fm['shared_state_transcripts']!={'cases':10,'steps':51,'drain_adapter':'Identity fields retained; kind normalized to GRANT for trusted physical-drain hook, not an on-wire REQUEST action.'}:
        raise RuntimeError('fixture coverage manifest differs from pinned claims')
    for rel,want in fm['files'].items():
        if digest((fm_path.parent/rel).read_bytes())!=want:raise RuntimeError(f'fixture hash mismatch: {rel}')
    shared=json.loads((fm_path.parent/'receiver-state-transcripts.json').read_bytes())
    if len(shared['cases'])!=10 or sum(len(c['steps']) for c in shared['cases'])!=51:
        raise RuntimeError('shared transcript shape mismatch')
    return {'source_inventory_sha256':snap['source_inventory_sha256'],
            'source_snapshot_sha256':digest(snap_path.read_bytes()),'copied_files':len(snap['files']),
            'fixture_files':len(fm['files']),'fg19_messages':fm['FG19_messages'],
            'shared_cases':10,'shared_steps':51}

def find_rustc():
    found=shutil.which('rustc')
    if found:return Path(found)
    candidates=[Path.home()/'.cargo/bin/rustc.exe',Path.home()/'.cargo/bin/rustc']
    for p in candidates:
        if p.is_file():return p
    raise RuntimeError('rustc not found on PATH or under ~/.cargo/bin')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--log-dir',type=Path)
    args=ap.parse_args();logdir=args.log_dir.resolve() if args.log_dir else None
    snap=verify_snapshot();rustc=find_rustc()
    probe=subprocess.run([str(rustc),'+stable','--version'],capture_output=True,text=True)
    prefix=[str(rustc),'+stable'] if probe.returncode==0 else [str(rustc)]
    version=subprocess.check_output(prefix+['--version'],text=True).strip()
    runs=[];compile_fail=[]
    with tempfile.TemporaryDirectory(prefix='ar03-receiver-core-') as td:
        tmp=Path(td)
        for name,want in EXPECTED_TESTS.items():
            src=HERE/'tests'/name;exe=tmp/(Path(name).stem+('.exe' if os.name=='nt' else ''))
            cmd=prefix+['--edition=2021','--test',str(src),'-o',str(exe)]
            build=subprocess.run(cmd,capture_output=True,text=True)
            run=subprocess.run([str(exe)],capture_output=True,text=True) if build.returncode==0 else None
            build_text=f'$ {" ".join(cmd)}\nexit_code={build.returncode}\n{build.stdout}{build.stderr}'
            write_log(logdir,Path(name).stem+'-compile.log',build_text)
            if build.returncode!=0:raise RuntimeError(f'{name} compile failed; see compile log')
            run_text=f'$ {exe}\nexit_code={run.returncode}\n{run.stdout}{run.stderr}'
            write_log(logdir,Path(name).stem+'-run.log',run_text)
            m=re.search(r'test result: ok\. (\d+) passed; 0 failed',run.stdout)
            if run.returncode!=0 or not m or int(m.group(1))!=want:
                raise RuntimeError(f'{name} expected {want} tests; got {run.stdout.strip()}')
            runs.append({'suite':name,'passed':int(m.group(1)),'exit_code':run.returncode})

        module=(HERE/'handheld/src/streaming/ar03_lab/mod.rs').resolve().as_posix()
        for typ in ['frame::Frames','packet::Gateway']:
            for operation,expected in [('copy','E0382'),('clone','E0599')]:
                body=('let _duplicate=original;drop(original);' if operation=='copy'
                      else 'let _duplicate=original.clone();')
                harness=tmp/f'{typ.split("::")[-1]}-{operation}.rs'
                harness.write_text(f'#[path="{module}"] mod ar03_lab; fn main(){{let original=ar03_lab::{typ}::cold_epoch1(true);{body}}}\n',encoding='utf-8',newline='\n')
                exe=tmp/(harness.stem+('.exe' if os.name=='nt' else ''))
                cmd=prefix+['--edition=2021',str(harness),'-o',str(exe)]
                result=subprocess.run(cmd,capture_output=True,text=True);output=result.stdout+result.stderr
                write_log(logdir,harness.stem+'.log',f'$ {" ".join(cmd)}\nexit_code={result.returncode}\n{output}')
                if result.returncode==0 or expected not in output:
                    raise RuntimeError(f'{typ} {operation} expected compiler rejection {expected}')
                compile_fail.append({'type':typ,'operation':operation,'expected_error':expected,'rejected':True})

    summary={'passed':True,'rustc':version,'source':snap,'host_tests':runs,
             'host_test_count':sum(x['passed'] for x in runs),'expected_compile_rejections':compile_fail,
             'binary_output':'temporary directory only; removed at process exit',
             'scope':'host-only tests of dormant metadata/policy core; no full firmware/backend/hardware proof'}
    raw=json.dumps(summary,indent=2,sort_keys=True)+'\n'
    if logdir is not None:
        logdir.mkdir(parents=True,exist_ok=True)
        (logdir/'summary.json').write_text(raw,encoding='utf-8',newline='\n')
        (logdir/'run.log').write_text(raw,encoding='utf-8',newline='\n')
    print(raw,end='')
if __name__=='__main__':
    try:main()
    except Exception as exc:
        print(f'FAIL: {exc}',file=sys.stderr);raise SystemExit(1)
