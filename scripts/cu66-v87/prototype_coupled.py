#!/usr/bin/env python3
"""Actual CS86 context work in a consumer-backpressured reconstruction DAG."""
from __future__ import annotations
import argparse,datetime,gzip,hashlib,importlib.util,json,statistics,subprocess,sys,tarfile,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];AREA=ROOT/'experiments/python-gamebub-v87/coupled'
CTX=ROOT/'experiments/python-gamebub-v86/contexts';NATIVE=ROOT/'experiments/python-gamebub-v82/native'
WIRE=ROOT/'experiments/python-gamebub-v86/wire-attempts/20261106T135235884295Z-2a73a26a/frames.jsonl'
CONTROL=ROOT/'experiments/python-gamebub-v82/execution/attempt-20261106T052617072164Z-c382bb87/g16-frames.jsonl'
LOW=dict(decisions=2,renorm=2,stream_bytes=2,rice_values=1,events=1,raw_bytes=2,header_bytes=2,crc_bytes=2,emits=1,raw_bits=1,prob_init=1)
HIGH=dict(decisions=4,renorm=4,stream_bytes=4,rice_values=1,events=1,raw_bytes=4,header_bytes=4,crc_bytes=4,emits=1,raw_bits=2,prob_init=1)
ZERO={k:0 for k in LOW}
RESERVED=dict(period=10000,blocked=[(0,2000)])
CONFIGS=[dict(name='zero_front_control',weights=ZERO,lanes=1,dequant=0,windows=None),
 dict(name='low_lanes1',weights=LOW,lanes=1,dequant=64,windows=None),
 dict(name='low_lanes2',weights=LOW,lanes=2,dequant=64,windows=None),
 dict(name='high_lanes1',weights=HIGH,lanes=1,dequant=64,windows=None),
 dict(name='high_lanes2',weights=HIGH,lanes=2,dequant=64,windows=None),
 dict(name='low_lanes2_reserved20',weights=LOW,lanes=2,dequant=64,windows=RESERVED)]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def stats(v):return dict(min=min(v),median=statistics.median(v),max=max(v),total=sum(v))

def campaign(args):
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/f'{stamp}-{uuid.uuid4().hex[:8]}';out.mkdir(parents=True)
 index=json.loads((CTX/'index.json').read_text())
 sources=[Path(__file__).resolve(),AREA/'model.py',CTX/'prototype.py',CTX/'data.py',CTX/'index.json',CTX/index['data']['path'],NATIVE/'data.py',NATIVE/'index.json',
 ROOT/'experiments/python-gamebub-v83/workload.py',ROOT/'experiments/python-gamebub-v83/scheduler.py',ROOT/'experiments/python-gamebub-v83/audit.py',
 ROOT/'experiments/python-gamebub-v84/credits.py',ROOT/'scripts/cu66-v82/prototype_commitment.py',ROOT/'fpga/experiments/cu66-v81/residency/model.py',ROOT/'experiments/python-gamebub-v82/execution.py',WIRE,CONTROL]
 sources+=sorted((NATIVE/'data').glob('*.gz'));pins={str(p.relative_to(ROOT)):sha(p) for p in sources}
 with tarfile.open(out/'sources.tar.gz','w:gz') as tar:
  for p in sources:
   if p.suffix!='.gz':tar.add(p,arcname=str(p.relative_to(ROOT)),recursive=False)
 report=dict(schema='cu66-v87-coupled-campaign-v1',status='FAIL',source_sha256=pins,source_archive_sha256=sha(out/'sources.tar.gz'),configurations=CONFIGS,cohort=args.cohort,smoke_limit=args.limit,
 clock_mhz_assumption=100,physical_timing_proven=False,esp32_simulated=False,profile='fixed CS86 grouped COPY whole-plane',
 limitations=['Fully buffered input at release, CRC pass then metadata byte scan; not transport/streaming ingress.',
 'Per-tile batched fetch precedes context arithmetic; hypothetical LOW/HIGH primitive costs, not clock bounds.',
 '4 output groups,8 reference/inverse/coefficient slots; consumers retain actual producer credits.',
 'Dequant64, inverse64, reconstruct64 cycles per residual tile are architectural assumptions, not RTL measurements.',
 'HUD entropy and semantic HUD hashing, physical COPY/CONST ports, LCD/refresh, RAM rows/direction, abort/drain and ESP32 remain outside qualified timing.',
 'Reserved20 windows restart phase0 per frame; not a continuous display trace.',
 '457 sources from one walkthrough family, four reset histories; no sustained hardware30fps or complete validatedunder10ms proof.'])
 started=time.monotonic()
 try:
  native=load('cu87_native',NATIVE/'data.py');ctx=load('cu87_context_source',CTX/'prototype.py');coupled=load('cu87_coupled',AREA/'model.py')
  commitment=load('cu87_commitment',ROOT/'scripts/cu66-v82/prototype_commitment.py');residency=load('cu87_residency',ROOT/'fpga/experiments/cu66-v81/residency/model.py')
  cost=load('cu87_cost',ROOT/'experiments/python-gamebub-v82/execution.py');workload=load('cu87_workload',ROOT/'experiments/python-gamebub-v83/workload.py')
  scheduler=load('cu87_scheduler',ROOT/'experiments/python-gamebub-v83/scheduler.py');generic=load('cu87_generic',ROOT/'experiments/python-gamebub-v83/audit.py');credits=load('cu87_credits',ROOT/'experiments/python-gamebub-v84/credits.py')
  originals=(f for f in native.iter_frames() if f['cohort']==args.cohort)
  observed=(f for f in ctx.iter_cohort(index,args.cohort) if f['cap']==65536)
  wire={(r['cohort'],r['fid']):r for r in map(json.loads,WIRE.read_text().splitlines()) if r['configuration']=='copy_group_cap65536'}
  controls={(r['cohort'],r['fid']):r for r in map(json.loads,CONTROL.read_text().splitlines())}
  model=residency.Residency(8100);tree=commitment.CommitmentTree(granularity=16);rows=[];processed=0
  with (out/'rows.jsonl').open('w') as output:
   for original,observation in zip(originals,observed,strict=True):
    if args.limit and processed>=args.limit:break
    frame=dict(original,generation=original['ordinal']+1);identity=(frame['cohort'],frame['fid']);packet=wire[identity];control=controls[identity]
    for k in ('cohort','fid','ordinal','key','canonical_sha256','hud_sha256','display_sha256'):assert frame[k]==observation[k]
    assert observation['canonical_coefficients_sha256']==packet['decoded']['coefficient_sha256']
    candidate=0 if model.reference is None else (model.reference+1)%3
    elided=[not frame['key'] and bool(frame['same_mask'][i]) and bool(model.masks[i]&(1<<candidate)) for i in range(8100)]
    plan=tree.plan(frame,frame['copy_ref_mask']);assert (plan['root'].hex(),plan['seal'].hex())==(control['root'],control['seal'])
    account=cost.account(frame,elided,plan);assert account['logical_BL8']==control['logical_BL8']
    model.begin(frame['fid'],frame['packet_sha256'],candidate,frame['key'],frame['tiles'],frame['same_mask']);model.step();model.commit(authenticated=True);tree.commit(plan);model.present();assert model.banks[model.reference]==frame['tiles']
    base=workload.build(frame,elided,plan,inverse_cycles=64,reconstruct_cycles=64,read_gap=18,write_gap=16,group_slots=4)
    credited=credits.augment(base,[0]*8100,ref_slots=8,inverse_slots=8,coefficient_slots=8)
    metadata_bytes=sum(packet['components'][k] for k in ('header','mode_body','qmap','chunk_directory'))
    for config in CONFIGS:
     work=coupled.couple(credited,observation['shared_work'],observation['context_work'],config['weights'],wire_bytes=packet['wire_bytes'],metadata_bytes=metadata_bytes,dequant_cycles=config['dequant'])
     capacities=dict(memory=1,inverse=1,reconstruct=1,hash=1,tree_r=1,tree_w=1,map_r=1,map_w=1,fetch=1,arithmetic=config['lanes'],emit=1,dequant=1)
     result=scheduler.schedule(work['jobs'],capacities,config['windows'],retain_timeline=True)
     audited=generic.verify(work['jobs'],result['timeline'],capacities,config['windows'],work['groups'],4)
     lifetimes=credits.audit_lifetimes(work,result['timeline']);front_audit=coupled.audit(work,result,config['lanes'])
     expected_memory=(account['logical_BL8']['reference_reads']+2640)*18+(account['logical_BL8']['canonical_writes']+2640)*16
     assert audited['resource_work_cycles']['memory']==expected_memory
     assert audited['resource_work_cycles']['hash']==account['hash_compression_blocks']*64
     assert audited['resource_work_cycles'].get('dequant',0)==config['dequant']*work['counts']['inverse_tiles']
     if config['name']=='zero_front_control':
      control_result=scheduler.schedule(credited['jobs'],dict(memory=1,inverse=1,reconstruct=1,hash=1,tree_r=1,tree_w=1,map_r=1,map_w=1,entropy=1))
      assert control_result['finish_cycles']==result['finish_cycles'],('zero control',identity,control_result['finish_cycles'],result['finish_cycles'])
     row=dict(configuration=config['name'],cohort=frame['cohort'],fid=frame['fid'],ordinal=frame['ordinal'],key=frame['key'],canonical_sha256=frame['canonical_sha256'],hud_sha256=frame['hud_sha256'],display_sha256=frame['display_sha256'],context_work_sha256=observation['work_sha256'],CS86_packet_sha256=packet['packet_sha256'],wire_bytes=packet['wire_bytes'],metadata_bytes=metadata_bytes,root=plan['root'].hex(),seal=plan['seal'].hex(),finish_cycles=result['finish_cycles'],model_ms=result['finish_cycles']*1e-5,audit=audited,credits=lifetimes,frontend=front_audit,memory_work_cycles=expected_memory,timeline_sha256=hashlib.sha256(json.dumps(result['timeline'],sort_keys=True,separators=(',',':')).encode()).hexdigest())
     rows.append(row);output.write(json.dumps(row,separators=(',',':'))+'\n');output.flush()
     if (frame['cohort'],frame['fid'],config['name']) in [(0,0,'low_lanes2'),(0,1,'low_lanes2'),(3,50,'low_lanes2'),(3,50,'high_lanes2'),(3,50,'low_lanes2_reserved20')]:
      with gzip.open(out/f"witness-c{frame['cohort']}-f{frame['fid']}-{config['name']}.json.gz",'wt') as f:json.dump(dict(config=config,capacities=capacities,workload=work,result=result,audit=audited,credits=lifetimes,frontend_audit=front_audit),f,separators=(',',':'))
    processed+=1
    if processed==1 or processed%10==0:print('COUPLED_PROGRESS',args.cohort,processed,len(rows),round(time.monotonic()-started,2),flush=True)
  expected=(119,119,119,100)[args.cohort];assert processed==(args.limit or expected)
  summaries=[]
  for config in CONFIGS:
   group=[r for r in rows if r['configuration']==config['name']]
   summaries.append(dict(configuration=config['name'],sources=len(group),model_ms=stats([r['model_ms'] for r in group]),conditional_under10ms=sum(r['finish_cycles']<1000000 for r in group),conditional_within30fps_period=sum(r['finish_cycles']*30<=100000000 for r in group)))
  assert pins=={name:sha(ROOT/name) for name in pins},'executed source mutation'
  report.update(status='PASS_SMOKE_ONLY' if args.limit else 'PASS_CONDITIONAL_COHORT_COUPLING',native_sources=processed,schedules=len(rows),summaries=summaries,artifacts_sha256={p.name:sha(p) for p in out.iterdir() if p.is_file() and p.name!='results.json'})
 except BaseException as exc:report['failure']=repr(exc);raise
 finally:
  report['wall_seconds']=time.monotonic()-started;(out/'results.json').write_text(json.dumps(report,indent=2)+'\n');print('COUPLED_REPORT',out/'results.json',report['status'],flush=True)

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--cohort',type=int,choices=range(4));parser.add_argument('--limit',type=int,default=0);args=parser.parse_args()
 if args.cohort is not None:return campaign(args)
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'sessions'/f'{stamp}-{uuid.uuid4().hex[:8]}';out.mkdir(parents=True);children=[];started=time.monotonic()
 for cohort in range(4):
  command=[sys.executable,str(Path(__file__).resolve()),'--cohort',str(cohort)]+(['--limit',str(args.limit)] if args.limit else [])
  log=(out/f'cohort{cohort}.log').open('w');p=subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT);children.append((cohort,command,p,log))
 print('COUPLED_SESSION',out,flush=True);records=[];rows=[]
 for cohort,command,p,log in children:
  code=p.wait();log.close();path=out/f'cohort{cohort}.log';selected=[line.split('COUPLED_REPORT ',1)[1].rsplit(' ',1)[0] for line in path.read_text().splitlines() if line.startswith('COUPLED_REPORT ')]
  record=dict(cohort=cohort,command=command,exit_code=code,log=str(path.relative_to(ROOT)),log_sha256=sha(path),report=str(Path(selected[-1]).relative_to(ROOT)) if selected else None)
  records.append(record);print('COUPLED_COHORT_EXIT',cohort,code,flush=True)
  if code==0:rows.extend(map(json.loads,(ROOT/record['report']).with_name('rows.jsonl').read_text().splitlines()))
 summaries=[]
 for config in CONFIGS:
  group=[r for r in rows if r['configuration']==config['name']]
  if group:summaries.append(dict(configuration=config['name'],sources=len(group),model_ms=stats([r['model_ms'] for r in group]),conditional_under10ms=sum(r['finish_cycles']<1000000 for r in group),conditional_within30fps_period=sum(r['finish_cycles']*30<=100000000 for r in group)))
 result=dict(schema='cu66-v87-coupled-session-v1',status='PASS_SMOKE_ONLY' if args.limit and all(r['exit_code']==0 for r in records) else 'PASS' if all(r['exit_code']==0 for r in records) else 'FAIL',cohorts=records,native_sources=len(rows)//len(CONFIGS),schedules=len(rows),summaries=summaries,wall_seconds=time.monotonic()-started)
 (out/'results.json').write_text(json.dumps(result,indent=2)+'\n');print('COUPLED_SESSION_REPORT',out/'results.json',result['status'],flush=True)
 return 0 if result['status'].startswith('PASS') else 1
if __name__=='__main__':raise SystemExit(main())
