#!/usr/bin/env python3
"""Prepare or run bounded read-only V129/V130 DCP path observations.

No route, implementation, constraint change or hardware access occurs here.
Matching names show physical netlist path identity only, not logical equivalence.
"""
import argparse, csv, datetime, hashlib, json, math, re, shutil, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
AREA=ROOT/'experiments/python-gamebub-v130/spec-read/checkpoint-inspect'
RECEIPTS={
 'v129':ROOT/'experiments/python-gamebub-v129/native/20261111T003938700577Z/receipt.json',
 'v130':ROOT/'experiments/python-gamebub-v130/spec-read/native/20261111T024750249700Z/receipt.json'}
AUDITS={
 'v129':ROOT/'experiments/python-gamebub-v129/audit/native-post-route-independent.json',
 'v130':ROOT/'experiments/python-gamebub-v130/spec-read/audit/native-post-route-independent.json'}
RECEIPT_SHA={'v129':'5576fa6e190f82f0583d3e1b5e94b50757d31e11822dcc2d62590a071f1f3ab1',
             'v130':'f7af8110cf6883175c144f02a26549862c1f95e9c919b091997b8a2a1d306273'}
IMAGE='sha256:dd51b5dd44148c23bb0059b929697243797022172d5efb01ffdd8b8dd7a89742'
SCRIPT=HERE/'inspect.tcl'
G=1024**3

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for x in iter(lambda:f.read(1024*1024),b''):h.update(x)
 return h.hexdigest()
def load(p):return json.loads(Path(p).read_text())
def write(p,d):Path(p).write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
def need(ok,msg):
 if not ok:raise ValueError(msg)
def rel(p):return str(Path(p).resolve().relative_to(ROOT))
def memory():
 m={x.split(':')[0]:int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()}
 line=next(x for x in Path('/proc/pressure/memory').read_text().splitlines() if x.startswith('full '))
 return dict(available_bytes=m['MemAvailable'],psi_full_avg10=float(line.split('avg10=')[1].split()[0]),combined_used_fraction=(m['MemTotal']-m['MemAvailable']+m['SwapTotal']-m['SwapFree'])/(m['MemTotal']+m['SwapTotal']))

def source_contract():
 data={}
 for label,p in RECEIPTS.items():
  need(sha(p)==RECEIPT_SHA[label],label+' receipt hash')
  d=load(p);aud=load(AUDITS[label]);need(aud['status']=='PASS_'+label.upper()+'_INDEPENDENT_POST_ROUTE_EVIDENCE' and aud['candidate_receipt']['sha256']==sha(p),label+' audit chain')
  need(d['status']=='COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN' and d['component_route_finished'] and d['clock_period_ns']==8.0 and d['part']=='xc7a100tcsg324-1' and d['source_snapshot_unchanged'] and d['recipe_unchanged'] and d['image_id']==IMAGE,label+' route identity')
  for alias,meta in d['source_contract']['source_origins'].items():
   need(sha(ROOT/meta['path'])==meta['sha256']==sha(p.parent/'source-snapshot'/alias),label+' source '+alias)
  cp=d['external_artifacts']['route.dcp']; need(Path(cp['external_path']).is_file() and sha(cp['external_path'])==cp['sha256'],label+' checkpoint hash')
  data[label]=dict(native_receipt=rel(p),native_receipt_sha256=sha(p),audit=rel(AUDITS[label]),audit_sha256=sha(AUDITS[label]),checkpoint=cp,source_origins=d['source_contract']['source_origins'],source_order=d['source_contract']['source_order'],recipe_sha256=d['recipe_sha256'])
 a,b=data['v129'],data['v130'];need(a['source_order']==b['source_order'] and all(a['recipe_sha256'][x]==b['recipe_sha256'][x] for x in ('run.tcl','report.tcl','component.xdc')),'recipe/source order differs')
 diff={k for k in a['source_origins'] if a['source_origins'][k]!=b['source_origins'][k]};need(diff=={'fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv'},'source delta')
 return data

def prepare(a):
 data=source_contract();stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'prepared'/stamp;out.mkdir(parents=True)
 shutil.copyfile(SCRIPT,out/'inspect.tcl');shutil.copyfile(Path(__file__),out/'checkpoint_inspect.py')
 result=dict(schema='v130-readonly-checkpoint-preflight-v1',status='PREPARED_NOT_RUN',checkpoints=data,script_sha256=sha(SCRIPT),runner_sha256=sha(Path(__file__)),image_id=IMAGE,part='xc7a100tcsg324-1',period_ns=8.0,timeout_seconds=900,cpus=2,memory_bytes=8*G,memory_swap_bytes=8*G,hardware_contact=False,new_implementation=False,changes_constraints=False,full_parent_functionality_qualified=False,invalid_data_consumer_contract='UNKNOWN',source_selection='base_kill_valid_reg* FD Q',destination_selection='coefficients/admission/memory_reg* RAMB ENBWREN')
 write(out/'preflight.json',result);print(rel(out/'preflight.json'))

def run(a):
 p=load(a.preflight);need(p['status']=='PREPARED_NOT_RUN' and p['checkpoints']==source_contract(),'preflight source drift')
 need(p['script_sha256']==sha(SCRIPT)==sha(a.preflight.parent/'inspect.tcl') and p['runner_sha256']==sha(Path(__file__))==sha(a.preflight.parent/'checkpoint_inspect.py'),'script drift')
 need(a.license_file.is_file(),'license path')
 image=subprocess.check_output(['docker','image','inspect','--format','{{.Id}}','acorn-nexys4-ddr:2026.1'],text=True).strip();need(image==IMAGE,'image drift')
 active=subprocess.check_output(['docker','ps','--format','{{.Names}}'],text=True).splitlines();need(sum(bool(re.match(r'^gamebub-v\d+-',n)) for n in active)<2,'heavy slots')
 for label in ('v129','v130'):
  m=memory();need(m['available_bytes']>=8*G and m['psi_full_avg10']<1 and m['combined_used_fraction']<.85,'memory gate')
  cp=p['checkpoints'][label]['checkpoint'];stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/(label+'-'+stamp);out.mkdir(parents=True)
  script=a.preflight.parent/'inspect.tcl';name='gamebub-v130-checkpoint-'+label+'-'+stamp.lower()
  cmd=['docker','run','--rm','--init','--name',name,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--ulimit','core=0','--network','host','--mount','type=bind,src=/home/lori/acorn-nexys4-ddr/tools,dst=/opt/amd-tools,readonly','--mount',f"type=bind,src={cp['external_path']},dst=/input/route.dcp,readonly",'--mount',f'type=bind,src={script.resolve()},dst=/inspect/inspect.tcl,readonly','--mount',f'type=bind,src={out.resolve()},dst=/output','--mount',f'type=bind,src={a.license_file.resolve()},dst=/root/.Xilinx/license.dat,readonly','-e','LD_PRELOAD=/lib/x86_64-linux-gnu/libudev.so.1','-e','XILINXD_LICENSE_FILE=/root/.Xilinx/license.dat','-w','/output',IMAGE,'timeout','--kill-after=10s','900s','/opt/amd-tools/2026.1/Vivado/bin/vivado','-mode','batch','-nojournal','-nolog','-notrace','-source','/inspect/inspect.tcl','-tclargs','/input/route.dcp','/output']
  receipt=dict(status='RUNNING',label=label,preflight=rel(a.preflight),preflight_sha256=sha(a.preflight),checkpoint=cp,script_sha256=sha(script),command=cmd,memory_samples=[],qualification=False,new_implementation=False,hardware_contact=False,changes_constraints=False)
  write(out/'receipt.json',receipt);start=time.monotonic();last=-30;high=0;stop=None
  print('V130_CHECKPOINT_INSPECTION_STARTED',rel(out),flush=True)
  with (out/'vivado.log').open('w') as log:
   proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
   while proc.poll() is None:
    age=time.monotonic()-start
    if age-last>=15:
     m=memory();receipt['memory_samples'].append(dict(elapsed_seconds=age,**m));last=age;high=high+1 if m['psi_full_avg10']>=5 else 0
     if m['available_bytes']<4*G or high>=2 or m['combined_used_fraction']>=.90:stop='HOST_MEMORY_PRESSURE'
    if age>930:stop='HOST_WALL_TIMEOUT'
    if stop:subprocess.run(['docker','stop','--time','10',name],capture_output=True,timeout=20);break
    time.sleep(1)
   code=proc.wait(timeout=30)
  receipt.update(exit_code=code,stop_reason=stop,wall_seconds=time.monotonic()-start,checkpoint_unchanged=sha(cp['external_path'])==cp['sha256'])
  done=(out/'status.txt').is_file() and 'V130_TARGETED_CHECKPOINT_REPORT_COMPLETE' in (out/'status.txt').read_text()
  receipt['status']='PASS_READONLY_REPORT' if code==0 and stop is None and done and receipt['checkpoint_unchanged'] else 'FAIL'
  receipt['artifact_sha256']={str(f.relative_to(out)):sha(f) for f in sorted(out.rglob('*')) if f.is_file() and f.name!='receipt.json'};write(out/'receipt.json',receipt)
  print(receipt['status'],rel(out/'receipt.json'),flush=True);need(receipt['status']=='PASS_READONLY_REPORT',label+' inspection failed')
  write(AREA/(label+'-results.json'),dict(status=receipt['status'],path=rel(out/'receipt.json'),sha256=sha(out/'receipt.json')))

def compare(a):
 reports={}
 for label in ('v129','v130'):
  s=load(AREA/(label+'-results.json'));p=ROOT/s['path'];need(s['status']=='PASS_READONLY_REPORT' and sha(p)==s['sha256'],label+' selector');d=load(p)
  for name,digest in d['artifact_sha256'].items():need(sha(p.parent/name)==digest,label+' artifact')
  with (p.parent/'inventory.tsv').open() as f:inventory=list(csv.DictReader(f,delimiter='\t'))
  with (p.parent/'paths.tsv').open() as f:paths=list(csv.DictReader(f,delimiter='\t'))
  need(len({(x['source'],x['destination']) for x in paths})==len(paths),label+' duplicate paths')
  reports[label]=dict(receipt=s['path'],sources=sorted(x['name'] for x in inventory if x['kind']=='SOURCE_PIN'),destinations=sorted(x['name'] for x in inventory if x['kind']=='DEST_PIN'),paths={(x['source'],x['destination']):x for x in paths})
 x,y=reports['v129'],reports['v130']; common_sources=sorted(set(x['sources'])&set(y['sources']));common_dest=sorted(set(x['destinations'])&set(y['destinations']));pairs=[]
 for src in common_sources:
  for dst in common_dest:
   u=x['paths'].get((src,dst));v=y['paths'].get((src,dst));need(u is not None and v is not None,'missing queried pair')
   item=dict(source=src,destination=dst,v129_status=u['status'],v130_status=v['status'])
   if u['status']=='PATH' and v['status']=='PATH':
    old,new=float(u['slack_ns']),float(v['slack_ns']);need(math.isfinite(old) and math.isfinite(new),'nonfinite slack')
    item.update(v129_slack_ns=old,v130_slack_ns=new,delta_ns=new-old)
   pairs.append(item)
 query_errors={label:sum(x['status']=='QUERY_ERROR' for x in d['paths'].values()) for label,d in reports.items()}
 comparable=sum('delta_ns' in p for p in pairs)
 incomplete=not common_sources or not common_dest or not comparable or any(query_errors.values())
 result=dict(schema='v130-direct-matching-checkpoint-paths-v1',status='QUERY_INCOMPLETE' if incomplete else 'COMPARISON_ONLY',query_errors=query_errors,timed_in_both_count=comparable,no_comparable_timing_count=len(pairs)-comparable,source_only_v129=sorted(set(x['sources'])-set(y['sources'])),source_only_v130=sorted(set(y['sources'])-set(x['sources'])),destination_only_v129=sorted(set(x['destinations'])-set(y['destinations'])),destination_only_v130=sorted(set(y['destinations'])-set(x['destinations'])),source_count_v129=len(x['sources']),source_count_v130=len(y['sources']),destination_count_v129=len(x['destinations']),destination_count_v130=len(y['destinations']),common_source_count=len(common_sources),common_destination_count=len(common_dest),matched_paths=pairs,receipts={k:v['receipt'] for k,v in reports.items()},scope='Exact named physical Q-to-ENBWREN path comparison only; unmatched/no-path queries are not zero or pass. No equivalence, route closure, parent or hardware claim.')
 out=AREA/'comparison.json';write(out,result);print(rel(out),sha(out))

def main():
 p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='action',required=True);sub.add_parser('prepare');r=sub.add_parser('run');r.add_argument('--preflight',type=Path,required=True);r.add_argument('--license-file',type=Path,required=True);sub.add_parser('compare');a=p.parse_args();{'prepare':prepare,'run':run,'compare':compare}[a.action](a)
if __name__=='__main__':main()
