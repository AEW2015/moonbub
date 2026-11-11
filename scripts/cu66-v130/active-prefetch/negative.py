#!/usr/bin/env python3
"""Run out-of-range scan injection as a separately recorded expected failure."""
from pathlib import Path
import datetime,hashlib,json,re,subprocess,time
R=Path(__file__).resolve().parents[3];AREA=R/'experiments/python-gamebub-v130/active-prefetch';BASE=Path('/home/lori/gamebub-build/cu66-v69');G=1024**3
IMAGE='sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def mem():
 m={x.split(':')[0]:int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()};q=next(x for x in Path('/proc/pressure/memory').read_text().splitlines() if x.startswith('full '))
 return {'available':m['MemAvailable'],'psi_full_avg10':float(q.split('avg10=')[1].split()[0]),'combined_used':(m['MemTotal']-m['MemAvailable']+m['SwapTotal']-m['SwapFree'])/(m['MemTotal']+m['SwapTotal'])}
def write(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def main():
 sel=json.loads((AREA/'results.json').read_text());positive=R/sel['path'];assert sel['status']=='PASS' and sha(positive)==sel['sha256'];p=json.loads(positive.read_text());assert p['actual_RTL_run']
 build=BASE/('v130-active-prefetch-'+positive.parent.name);binary=build/'obj/Vadmission_pair';assert sha(binary)==p['binary_sha256'];fixture=positive.parent/'sources/experiments/python-gamebub-v91i/vectors/vectors.txt';assert sha(fixture)==p['source_sha256']['experiments/python-gamebub-v91i/vectors/vectors.txt']
 m=mem();assert m['available']>=8*G and m['psi_full_avg10']<1 and m['combined_used']<.85,m
 assert sum(bool(re.match(r'^gamebub-v\d+-',n)) for n in subprocess.check_output(['docker','ps','--format','{{.Names}}'],text=True).splitlines())<2
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'negative'/stamp;out.mkdir(parents=True);name='gamebub-v130-scan-negative-'+stamp.lower()
 cmd=['docker','run','--rm','--init','--name',name,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={binary},dst=/work/Vadmission_pair,readonly','--mount',f'type=bind,src={fixture},dst=/work/fixture.txt,readonly','-w','/work',IMAGE,'timeout','--kill-after=5s','600s','/work/Vadmission_pair','/work/fixture.txt','130301','bad_index']
 rec={'schema':'v130-active-prefetch-negative-v1','status':'RUNNING','positive_receipt':sel,'binary_sha256':sha(binary),'fixture_sha256':sha(fixture),'expected_detection':'scan index outside reachable range','command':cmd,'memory_samples':[]};write(out/'receipt.json',rec);print('SCAN_NEGATIVE_STARTED',str(out.relative_to(R)),flush=True)
 t=time.monotonic();last=-15;high=0;stop=None
 with (out/'simulation.log').open('w') as log:
  proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
  while proc.poll() is None:
   age=time.monotonic()-t
   if age-last>=15:
    x=mem();rec['memory_samples'].append(dict(elapsed=age,**x));last=age;high=high+1 if x['psi_full_avg10']>=5 else 0
    if x['available']<4*G or high>=2 or x['combined_used']>=.90:stop='HOST_MEMORY_PRESSURE'
   if age>630:stop='HOST_TIMEOUT'
   if stop:subprocess.run(['docker','stop','--time','10',name],capture_output=True,timeout=20);break
   time.sleep(1)
  code=proc.wait(timeout=30)
 text=(out/'simulation.log').read_text(errors='replace');detected=stop is None and code not in (0,124,137) and rec['expected_detection'] in text and sha(binary)==p['binary_sha256'] and sha(fixture)==rec['fixture_sha256']
 rec.update(status='PASS_EXPECTED_FAILURE_DETECTED' if detected else 'FAIL',observed_exit_code=code,stop_reason=stop,actual_RTL_run=True,simulation_log_sha256=sha(out/'simulation.log'));write(out/'receipt.json',rec)
 if detected:write(AREA/'negative/results.json',{'status':rec['status'],'path':str((out/'receipt.json').relative_to(R)),'sha256':sha(out/'receipt.json')})
 print('SCAN_NEGATIVE_FINISHED',rec['status'],str(out.relative_to(R)),flush=True)
 if not detected:raise SystemExit(1)
if __name__=='__main__':main()
