#!/usr/bin/env python3
"""Bounded strict behavioral CDC fabric regression; independent trace replay."""
import argparse,datetime,gzip,hashlib,json,os,shutil,signal,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'fpga/experiments/cu66-v107-cdc'
AREA=ROOT/'experiments/python-gamebub-v107/cdc'
CONTAINER='gamebub-cu66-v69-build'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def resources():
    mem={x.split(':')[0]:int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines() if ':' in x}
    line=next(x for x in Path('/proc/pressure/memory').read_text().splitlines() if x.startswith('full '))
    return dict(available_bytes=mem['MemAvailable'],psi_full_avg10=float(line.split('avg10=')[1].split()[0]))
def replay(path):
    queues=[[] for _ in range(5)];accepted=delivered=discarded=epochs=0
    with gzip.open(path,'rt') as f:
        for line in f:
            t,op,ch,ep,*words=line.strip().split(',');ch=int(ch);words=tuple(map(int,words))
            if op=='E':
                discarded+=sum(map(len,queues));queues=[[] for _ in range(5)];epochs+=1;assert int(ep)==epochs
            elif op=='W':queues[ch].append((int(ep),words));accepted+=1
            else:
                assert op=='R' and queues[ch] and queues[ch].pop(0)==(int(ep),words),(t,ch)
                delivered+=1
    assert not any(queues) and accepted==delivered+discarded and epochs==6
    return dict(status='PASS',accepted=accepted,delivered=delivered,reset_discarded=discarded,reset_epochs=epochs)
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--replay',type=Path);args=parser.parse_args()
    if args.replay:print(json.dumps(replay(args.replay)));return
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/stamp;out.mkdir(parents=True)
    build=Path('/home/lori/gamebub-build/cu66-v69')/('v107-cdc-'+stamp);build.mkdir();mapped='/build/'+build.name
    files=[*sorted(SRC.glob('*.sv')),*sorted(SRC.glob('*.cpp')),Path(__file__).resolve()]
    receipt=dict(schema='v107-cdc-behavioral-v1',status='FAIL',actual_RTL_run=False,mode='behavioral-two-state',source_sha256={str(p.relative_to(ROOT)):sha(p) for p in files},commands=[],runs=[],strict_warning_policy='Verilator -Wall --assert; C++ -Wall -Wextra -Werror; no suppression',build_directory=str(build),scope='Experimental five-channel fabric only; actual board parent adapters, physical CDC signoff, metastability and hardware are not verified.')
    def command(argv,name,timeout):
        entry=dict(argv=argv,timeout_seconds=timeout,resource_before=resources());receipt['commands'].append(entry)
        gate=entry['resource_before'];assert gate['available_bytes']>=8*1024**3 and gate['psi_full_avg10']<1,gate
        with (out/name).open('w') as log:
            p=subprocess.Popen(argv,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);start=time.monotonic()
            while p.poll() is None:
                if time.monotonic()-start>timeout+10:os.killpg(p.pid,signal.SIGTERM);p.wait();raise TimeoutError(name)
                gate=resources()
                if gate['available_bytes']<4*1024**3 or gate['psi_full_avg10']>=5:
                    os.killpg(p.pid,signal.SIGTERM);p.wait();raise RuntimeError('resource stop '+str(gate))
                time.sleep(.25)
            entry.update(exit_code=p.returncode,wall_seconds=time.monotonic()-start,resource_after=resources())
            assert p.returncode==0,name
    try:
        for p in files:
            dst=out/'sources'/p.relative_to(ROOT);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dst)
        paths=[str(out/'sources'/p.relative_to(ROOT)) for p in files if p.suffix in ('.sv','.cpp')]
        command(['docker','exec',CONTAINER,'verilator','--version'],'version.log',30)
        command(['docker','exec',CONTAINER,'timeout','--kill-after=5s','180s','verilator','--cc','--exe','--build','-j','2','--assert','-Wall','--language','1800-2017','--top-module','v107_cdc_fabric','--Mdir',mapped,'-CFLAGS','-std=c++17 -O2 -Wall -Wextra -Werror',*paths],'compile.log',180)
        assert '%Warning-' not in (out/'compile.log').read_text()
        receipt['binary_sha256']=sha(build/'Vv107_cdc_fabric')
        for seed in (107001,107002,107003):
            trace=out/f'{seed}.csv';name=f'{seed}.log'
            command(['docker','exec',CONTAINER,'timeout','--kill-after=5s','30s',mapped+'/Vv107_cdc_fabric',str(seed),str(trace)],name,30)
            assert f'TEST_PASS_CDC seed={seed}' in (out/name).read_text()
            with trace.open('rb') as src,(out/f'{seed}.csv.gz').open('wb') as dst:
                with gzip.GzipFile(filename='',mode='wb',fileobj=dst,mtime=0) as z:shutil.copyfileobj(src,z)
            trace.unlink();receipt['runs'].append(dict(seed=seed,replay=replay(out/f'{seed}.csv.gz')))
        receipt['actual_RTL_run']=True;receipt['status']='PASS_BEHAVIORAL_CDC_FABRIC'
        assert receipt['source_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in files}
    except BaseException as e:receipt.update(error_class=type(e).__name__,error=str(e));raise
    finally:
        receipt['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
        (out/'receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
        (AREA/'results.json').write_text(json.dumps(dict(status=receipt['status'],selected_receipt=str((out/'receipt.json').relative_to(ROOT)),sha256=sha(out/'receipt.json')),indent=2)+'\n')
        print(receipt['status'],out,flush=True)
if __name__=='__main__':main()
