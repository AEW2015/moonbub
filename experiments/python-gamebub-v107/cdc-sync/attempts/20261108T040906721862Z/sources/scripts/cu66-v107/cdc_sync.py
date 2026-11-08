#!/usr/bin/env python3
"""Prepare/run the isolated synchronous-BRAM-control CDC prototype."""
import argparse,datetime,gzip,hashlib,importlib.util,json,os,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'fpga/experiments/cu66-v107-cdc-sync'
AREA=ROOT/'experiments/python-gamebub-v107/cdc-sync'
BUILD=Path('/home/lori/gamebub-build/cu66-v69')
CONTAINER='gamebub-cu66-v69-build'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def module(p,name):
    spec=importlib.util.spec_from_file_location(name,p);result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result
OLD=module(ROOT/'scripts/cu66-v107/cdc.py','original_cdc')
def prepare():
    selected=json.loads((ROOT/'experiments/python-gamebub-v107/cdc/results.json').read_text());prior=ROOT/selected['selected_receipt'];assert sha(prior)==selected['sha256'];baseline=json.loads(prior.read_text())
    assert baseline['status']=='PASS_BEHAVIORAL_CDC_FABRIC'
    bench=SRC/'tb_cdc.cpp';assert sha(bench)==baseline['source_sha256']['fpga/experiments/cu66-v107-cdc/tb_cdc.cpp']
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/stamp;out.mkdir(parents=True)
    build=BUILD/('v107-cdc-sync-'+stamp);build.mkdir();mapped='/build/'+build.name
    files=[*sorted(SRC.glob('*.sv')),bench,SRC/'reset_contract.py',ROOT/'scripts/cu66-v107/cdc.py',Path(__file__).resolve()]
    for p in files:
        dst=out/'sources'/p.relative_to(ROOT);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dst)
    model=module(SRC/'reset_contract.py','reset_contract').model();write(out/'reset-model.json',model)
    r=dict(schema='v107-cdc-sync-behavioral-v1',status='PREPARED',source_sha256={str(p.relative_to(ROOT)):sha(p) for p in files},baseline_behavioral_receipt=dict(path=str(prior.relative_to(ROOT)),sha256=sha(prior)),build_external=str(build),mapped_build=mapped,container=CONTAINER,actual_RTL_run=False,unchanged_scoreboard_sha256=sha(bench),capacity='8 reserved RAM slots including write stage +1 read output',reset_contract='Coordinated async public inhibit and dedicated up notifications; >=3local reset edges; RAM pointers/addresses/issues/Gray/valid reset synchronously',physical_read_write_commit=True,strict_warning_policy='Verilator -Wall --assert and C++ -Wall -Wextra -Werror; no suppression',interface_comparison='Each seed checked against its own accepted stream and identical replay oracle; added staging changes ready/valid timing and accepted workload, no cycle/bitwise A/B claim',commands=[],runs=[])
    write(out/'inputs.json',r);print('V107_CDC_SYNC_PREPARED',out.relative_to(ROOT),flush=True);return out

def run(out):
    out=out.resolve();out.relative_to(AREA);assert not (out/'receipt.json').exists(),'attempt already executed'
    r=json.loads((out/'inputs.json').read_text());assert r['status']=='PREPARED'
    for name,h in r['source_sha256'].items():assert sha(out/'sources'/name)==h,(name,'snapshot')
    r['status']='FAIL';start=time.monotonic();build=Path(r['build_external']);mapped=r['mapped_build']
    def command(argv,name,timeout):
        gate=OLD.resources();assert gate['available_bytes']>=8*1024**3 and gate['psi_full_avg10']<1,gate
        entry=dict(argv=argv,timeout_seconds=timeout,resource_before=gate);r['commands'].append(entry)
        with (out/name).open('w') as log:
            proc=subprocess.Popen(argv,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT);began=time.monotonic()
            while proc.poll() is None:
                gate=OLD.resources()
                if time.monotonic()-began>timeout+10 or gate['available_bytes']<4*1024**3 or gate['psi_full_avg10']>=5:
                    # Stop ONLY the timeout supervisor for this unique build.
                    script='import os,signal; target='+repr(mapped)+''';
for item in os.listdir('/proc'):
 if not item.isdigit(): continue
 try:
  data=open('/proc/'+item+'/cmdline','rb').read().split(b'\\0')
  if data and data[0].endswith(b'timeout') and any(target.encode() in x for x in data):os.kill(int(item),signal.SIGTERM)
 except (FileNotFoundError,ProcessLookupError,PermissionError): pass
'''
                    subprocess.run(['docker','exec',CONTAINER,'python3','-c',script],timeout=10,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                    proc.wait(timeout=15);raise RuntimeError('owned job time/resource stop '+str(gate))
                time.sleep(.25)
            entry.update(exit_code=proc.returncode,wall_seconds=time.monotonic()-began,resource_after=OLD.resources());assert proc.returncode==0,name
    try:
        files=[out/'sources'/name for name in r['source_sha256'] if name.endswith(('.sv','.cpp'))]
        command(['docker','exec',CONTAINER,'verilator','--version'],'version.log',30)
        command(['docker','exec',CONTAINER,'timeout','--signal=TERM','--kill-after=5s','180s','verilator','--cc','--exe','--build','-j','2','--assert','-Wall','--language','1800-2017','--top-module','v107_cdc_fabric','--Mdir',mapped,'-CFLAGS','-std=c++17 -O2 -Wall -Wextra -Werror',*map(str,files)],'compile.log',180)
        assert '%Warning-' not in (out/'compile.log').read_text();r['binary_sha256']=sha(build/'Vv107_cdc_fabric')
        prior=json.loads((ROOT/r['baseline_behavioral_receipt']['path']).read_text());old={v['seed']:v['replay'] for v in prior['runs']}
        for seed in (107001,107002,107003):
            trace=out/f'{seed}.csv';name=f'{seed}.log'
            command(['docker','exec',CONTAINER,'timeout','--signal=TERM','--kill-after=5s','30s',mapped+'/Vv107_cdc_fabric',str(seed),str(trace)],name,30)
            assert f'TEST_PASS_CDC seed={seed}' in (out/name).read_text()
            with trace.open('rb') as src,(out/f'{seed}.csv.gz').open('wb') as dst:
                with gzip.GzipFile(filename='',mode='wb',fileobj=dst,mtime=0) as z:shutil.copyfileobj(src,z)
            trace.unlink();replay=OLD.replay(out/f'{seed}.csv.gz');r['runs'].append(dict(seed=seed,replay=replay,original_same_scoreboard_replay=old[seed]))
        assert all(sha(out/'sources'/name)==h for name,h in r['source_sha256'].items())
        r['actual_RTL_run']=True;r['status']='PASS_BEHAVIORAL_SYNC_BRAM_CONTROL'
    except BaseException as e:r.update(error_class=type(e).__name__,error=str(e));raise
    finally:
        r['wall_seconds']=time.monotonic()-start;r['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='receipt.json'}
        write(out/'receipt.json',r);write(AREA/'results.json',dict(status=r['status'],selected_receipt=str((out/'receipt.json').relative_to(ROOT)),sha256=sha(out/'receipt.json')));print('V107_CDC_SYNC',r['status'],out.relative_to(ROOT),flush=True)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,help='Run a previously prepared attempt after heavy-slot grant');p.add_argument('--replay',type=Path);a=p.parse_args()
    if a.run:run(a.run)
    elif a.replay:print(json.dumps(OLD.replay(a.replay),sort_keys=True))
    else:prepare()
if __name__=='__main__':main()
