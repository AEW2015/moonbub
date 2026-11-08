#!/usr/bin/env python3
"""Stream pinned canonical traces; report behavioral component-cycle distributions."""
import collections,gzip,hashlib,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'experiments/python-gamebub-v107/latency'
SELECT=ROOT/'experiments/python-gamebub-v107/elastic-pipeline/results.json'
BENCH=ROOT/'fpga/experiments/cu66-v107-elastic/verification/bench.cpp'
INVERSE=ROOT/'fpga/experiments/cu66-v107-value-check/cu66_inverse_stream_v91j.sv'
IDCT=ROOT/'fpga/experiments/cu66-v106-idct-area/cu66_idct8x8.sv'

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def stats(counter):
 n=sum(counter.values());assert n
 def rank(at):
  total=0
  for value,count in sorted(counter.items()):
   total+=count
   if total>=at:return value
  raise AssertionError('rank')
 median=(rank(n//2)+rank(n//2+1))/2 if n%2==0 else rank(n//2+1)
 return {'n':n,'min':min(counter),'median':median,'p95_nearest_rank':rank(math.ceil(.95*n)),'max':max(counter),'sum':sum(v*c for v,c in counter.items())}
def main():
 selection=json.loads(SELECT.read_text());receipt=ROOT/selection['selected_report'];r=json.loads(receipt.read_text());assert r['status']=='PASS'
 pinned={str(p.relative_to(ROOT)):sha(p) for p in [SELECT,receipt,BENCH,INVERSE,IDCT,Path(__file__)]}
 assert sha(BENCH)==r['source_sha256'][str(BENCH.relative_to(ROOT))]
 assert sha(INVERSE)==r['source_sha256'][str(INVERSE.relative_to(ROOT))]
 assert sha(IDCT)==r['source_sha256'][str(IDCT.relative_to(ROOT))]
 case_hist=collections.defaultdict(collections.Counter);tile_hist=collections.defaultdict(collections.Counter);case_rows=[];trace_checks=[];peak_pending=0
 for run in r['runs']:
  seed=run['seed'];success={(c['id'],c['memory_profile']) for c in run['case_latency'] if c['error']==0}
  for variant in ['baseline','candidate']:
   logfile=receipt.parent/f'{variant}-{seed}-simulation.jsonl';assert sha(logfile)==r['artifacts_sha256'][logfile.name];pinned[str(logfile.relative_to(ROOT))]=sha(logfile)
   with logfile.open() as source:
    for line in source:
     c=json.loads(line)
     if c['type']!='case' or c['error']!=0:continue
     profile=c['memory_profile'];case_hist[(variant,profile)][c['cycles']]+=1
     case_rows.append({'variant':variant,'seed':seed,'id':c['id'],'memory_profile':profile,'cycles':c['cycles'],'ms_at_hypothetical100mhz':c['cycles']/100000,'strict_under_1000000':c['cycles']<1000000,'strict_under_3333000':c['cycles']<3333000,'full_frame_publication':c['full_frame_publication']})
   record=run['variants'][variant]['events'];path=receipt.parent/record['path'];digest=sha(path);assert digest==record['sha256'];pinned[str(path.relative_to(ROOT))]=digest
   raw=hashlib.sha256();rows=accepted_tiles=0;pending={};previous_residual={}
   with gzip.open(path,'rb') as source:
    for line in source:
     raw.update(line);rows+=1;e=json.loads(line)
     group=(e.get('id'),e.get('memory_profile'))
     if group not in success or e['type']!='transform':continue
     key=(*group,e['token']);histgroup=(variant,group[1]);stage=e['stage']
     if stage=='assemble':
      assert key not in pending and e['samples']==64 and e['complete']
      pending[key]={'assemble':e['first_cycle'],'identity':(e['plane'],e['block'],e['tile'],e['qcell'],e['qscale'],e['frame_epoch'],e['child_epoch'])}
      if group in previous_residual:
       gap=e['first_cycle']-previous_residual[group]['last'];assert gap>0
       tile_hist[(*histgroup,'next_assemble_after_prior_last_residual_cycles')][gap]+=1
     elif stage=='dequant':
      owner=pending[key];assert 'dequant' not in owner;owner['dequant']=e['first_cycle']
      wait=e['first_cycle']-owner['assemble'];assert wait>=0
      tile_hist[(*histgroup,'assemble_to_dequant_handshake_cycles')][wait]+=1
     else:
      assert stage=='residual' and e['samples']==64 and e['complete'];owner=pending.pop(key)
      identity=(e['plane'],e['block'],e['tile'],e['qcell'],e['qscale'],e['frame_epoch'],e['child_epoch']);assert identity==owner['identity']
      interval=e['first_cycle']-owner['dequant'];span=e['last_cycle']-e['first_cycle']+1;assert interval>=0 and span>=64
      tile_hist[(*histgroup,'dequant_handshake_to_first_accepted_residual_cycles')][interval]+=1
      tile_hist[(*histgroup,'residual64_acceptance_span_cycles')][span]+=1
      tile_hist[(*histgroup,'residual64_span_excess_over64_cycles')][span-64]+=1
      tile_hist[(*histgroup,'assemble_to_last_accepted_residual_inclusive_cycles')][e['last_cycle']-owner['assemble']+1]+=1
      if group in previous_residual:
       prev=previous_residual[group];assert e['token']==prev['token']+1
       gap=e['first_cycle']-prev['last']-1;assert gap>=0
       tile_hist[(*histgroup,'between_tile_residual_acceptance_gap_cycles')][gap]+=1
      previous_residual[group]={'token':e['token'],'last':e['last_cycle']};accepted_tiles+=1
     peak_pending=max(peak_pending,len(pending))
   assert not pending and rows==record['records'] and raw.hexdigest()==record['raw_sha256']
   trace_checks.append({'variant':variant,'seed':seed,'events':rows,'successful_complete_transform_tiles':accepted_tiles,'compressed_sha256':digest,'raw_sha256':raw.hexdigest()})
 case_summary=[]
 for (variant,profile),h in sorted(case_hist.items()):
  subset=[x for x in case_rows if x['variant']==variant and x['memory_profile']==profile]
  case_summary.append({'variant':variant,'memory_profile':profile,'cycles':stats(h),'strict_under1000000':sum(x['strict_under_1000000'] for x in subset),'strict_under3333000':sum(x['strict_under_3333000'] for x in subset)})
 tile_summary=[{'variant':variant,'memory_profile':profile,'metric':metric,'cycles':stats(h)} for (variant,profile,metric),h in sorted(tile_hist.items())]
 report={'status':'PASS_PINNED_READ_ONLY_LATENCY_PROFILE','canonical_receipt':str(receipt.relative_to(ROOT)),'canonical_receipt_sha256':sha(receipt),'pinned_reads_sha256':pinned,'case_summary':case_summary,'successful_case_runs':case_rows,'tile_interval_summary':tile_summary,'trace_checks':trace_checks,'streaming_peak_pending_transform_owners':peak_pending,'percentile_definition':'p95 nearest rank ceil(0.95*N); median averages the two middle values for evenN. Repeated caseids/seeds are distinct declared runs, not independent workload sampling.','bench_boundary':'cycles=cycle-begin_cycle, beginning with accepted frame-start tick after optional qcache preload; ends after done/error checks and ownership settle ticks. Includes packet-byte offers, admission, scratch service, transforms, reconstruction/reference modeled service, output acceptance and fixed settle ticks. Optional qcache preload, host transport, HUD/C2/accepted-frame publication and hardware are outside.','frequency_assumption':'Hypothetical100MHz only. Strict budgets <1000000cycles(10ms), <3333000cycles(33.33ms approximate30fps). No measured/qualified clock, generic30fpshardware or completeE2E publication claim.','interval_scope':'Handshake timestamps only: DQ interval includes dequant service and readiness wait; dequant→first residual includes IDCT service plus control/output wait;64sample span and between-tile gaps include consumer stalls/backpressure. Do not infer AC/DC from latency or sum overlapping metric categories as case cycles.'}
 AREA.mkdir(parents=True,exist_ok=True);(AREA/'results.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({'status':report['status'],'case_summary':case_summary,'trace_checks':trace_checks,'peak_pending_owners':peak_pending},sort_keys=True))
if __name__=='__main__':main()
