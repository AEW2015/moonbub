#!/usr/bin/env python3
"""Analyze only explicit completed traces. Gaps are observations, not service time."""
import csv,gzip,hashlib,json,math,statistics,time
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'fpga/experiments/cu66-v80/trace-analysis'
SELECTED=[
 'cohort0-frames4-fixed30-prefetch1-tac2/attempt-20261106T030655746424Z-141613e5',
 'cohort0-frames4-fixed30-prefetch2-tac2/attempt-20261106T030655747062Z-b09884e7',
 'cohort3-frames4-fixed30-prefetch1-tac2/attempt-20261106T030843168800Z-4dd9f4ad',
 'cohort3-frames4-fixed30-prefetch2-tac2/attempt-20261106T030843166027Z-20c80927',
 'cohort3-frames4-fixed30-prefetch0-tac2/attempt-20261106T030134407860Z-7748ea67',
 'cohort0-frames2-fixed30-prefetch0-tac2/attempt-20261106T025752304461Z-a968d9d3',
]
HEADER=['cycle','ps','frame_generation','event','owner_generation','client','write','address','bank','plane','tile_index']
CLIENTS={0:'tile_write_or_legacy_reference',1:'HUD',2:'LCD',3:'prefetch_reference'}
EVENTS={'command','ref_request','ref_response','tile_write_request','tile_write_done','prefetch_fill','prefetch_epoch_done','prefetch_epoch_aborted'}

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def dump(p,o):p.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')
def summary(h):
 if not h:return {'n':0}
 n=sum(h.values());total=sum(x*c for x,c in h.items());items=sorted(h.items())
 def q(p):
  target=max(1,math.ceil(n*p));acc=0
  for x,c in items:
   acc+=c
   if acc>=target:return x
 return {'n':n,'min':items[0][0],'p50_nearest_rank':q(.5),'p90_nearest_rank':q(.9),'p99_nearest_rank':q(.99),'max':items[-1][0],'sum':total,'mean':total/n,'negative':sum(c for x,c in items if x<0),'zero':h.get(0,0),'positive':sum(c for x,c in items if x>0)}
def ordinal(plane,tile):return (0 if plane==0 else 5400 if plane==1 else 6750)+tile
def coords(n):return (0,n) if n<5400 else (1,n-5400) if n<6750 else (2,n-6750)
def hidden(p,t):
 x,y=t%(90 if p==0 else 45),t//(90 if p==0 else 45)
 return ((3<=x<22 and (7<=y<9 or 11<=y<13)) or (21<=x<61 and 45<=y<48) or (21<=x<51 and 49<=y<51)) if p==0 else 11<=x<30 and y==23

def canonical(address):
 for bank,base in enumerate((0x080000,0x480000,0x880000)):
  offset=address-base
  if 0<=offset<259200:
   plane=0 if offset<172800 else 1 if offset<216000 else 2
   local=offset-(0 if plane==0 else 172800 if plane==1 else 216000)
   return bank,plane,local//32,(local%32)//8
 return None

def analyze(name,tile_writer):
 p=ROOT/'fpga/experiments/cu66-v80/system'/name;meta=json.loads((p/'results.json').read_text())
 assert meta['status']=='PASS_ACTUAL_DECODE_CANONICAL_AND_NATIVE_DISPLAY'
 trace=p/'trace.csv.gz';assert sha(trace)==meta['trace']['sha256']
 timing={int(x['generation']):x for x in meta['timings']};frames={int(x['generation']):x for x in meta['frames']}
 declared={int(x['generation']):x for x in meta['command_frames']}
 traces=defaultdict(Counter);events=Counter();tiles={};commands=defaultdict(list);command_counts=Counter();previous={};gaps=defaultdict(Counter)
 command_matching=defaultdict(list);previous_pref={};same_tile_pref_gaps=defaultdict(Counter);no_other_command_pref_gaps=defaultdict(Counter);previous_any_command={};global_prev={};row_count=0
 with gzip.open(trace,'rt',newline='') as f:
  reader=csv.reader(f);assert next(reader)==HEADER
  for row in reader:
   row_count+=1
   cycle,ps,context,event,owner,client,write,address,bank,plane,tile=row
   cycle=int(cycle);context=int(context);owner=int(owner);client=int(client);write=int(write);address=int(address);bank=int(bank);plane=int(plane);tile=int(tile)
   assert event in EVENTS and context in timing
   events[event]+=1;traces[context][event]+=1
   if event=='command':
    assert owner==0 # Raw command ownership is deliberately unspecified.
    assert client in CLIENTS and address%8==0
    in_transaction=timing[context]['admission_cycle']<=cycle<=timing[context]['commit_ack_cycle']
    scopes=['context_window']+(['admission_through_ACK'] if in_transaction else [])
    for scope in scopes:
     for group in (f'client{client}_{"write" if write else "read"}',f'client{client}_all','all_clients'):
      k=(context,scope,group);command_counts[k]+=1
      if k in previous:gaps[k][cycle-previous[k]]+=1
      previous[k]=cycle
     if scope=='admission_through_ACK':
      if context in global_prev:
       prev_cycle,prev_client,prev_write=global_prev[context]
       gaps[(context,scope,f'endpoint_pair_{prev_client}{"W" if prev_write else "R"}_to_{client}{"W" if write else "R"}')][cycle-prev_cycle]+=1
      global_prev[context]=(cycle,client,write)
    co=canonical(address)
    # This is a coordinate join inside a context window, NOT raw-owner proof.
    if co and in_transaction and ((client==0 and write) or (client==3 and not write)):
     cb,cp,ct,block=co;command_matching[(context,client,cb,cp,ct)].append((cycle,block))
    if client==3 and not write and in_transaction:
     if context in previous_pref:
      prev_cycle,prev_co=previous_pref[context]
      if co and prev_co and co[:3]==prev_co[:3] and co[3]==prev_co[3]+1:
       same_tile_pref_gaps[context][cycle-prev_cycle]+=1
       if previous_any_command.get(context)==prev_cycle:no_other_command_pref_gaps[context][cycle-prev_cycle]+=1
     previous_pref[context]=(cycle,co)
    previous_any_command[context]=cycle
   elif event in ('ref_request','ref_response','tile_write_request','tile_write_done','prefetch_fill'):
    assert owner==context and 0<=plane<3 and 0<=tile<(5400 if plane==0 else 1350)
    k=(owner,plane,tile);t=tiles.setdefault(k,{})
    assert event not in t,(name,k,event)
    t[event]=cycle;t[event+'_bank']=bank
 for event,count in meta['trace']['event_counts'].items():assert events[event]==count,(name,event,count,events[event])
 observations=[];histograms=[];banks={};metric_hists=defaultdict(Counter)
 for generation,fr in frames.items():
  candidate={t['tile_write_request_bank'] for (g,p,tile),t in tiles.items() if g==generation and 'tile_write_request' in t}
  references={t['ref_request_bank'] for (g,p,tile),t in tiles.items() if g==generation and 'ref_request' in t}
  fills={t['prefetch_fill_bank'] for (g,p,tile),t in tiles.items() if g==generation and 'prefetch_fill' in t}
  assert len(candidate)==1 and len(references)<=1 and len(fills)<=1
  cb=next(iter(candidate));rb=next(iter(references),None)
  assert not fills or fills==references
  assert fr['key'] or rb!=cb
  banks[generation]={'candidate_bank':cb,'reference_bank':rb,'explicit_translation':None if rb is None else f'reference bank {rb} -> candidate bank {cb}; generation/plane/index retained'}
  d=declared[generation]
  for client in range(4):
   for writing in (0,1):
    group=f'client{client}_{"write" if writing else "read"}'
    assert command_counts[(generation,'admission_through_ACK',group)]==d[f'client{client}_{"writes" if writing else "reads"}'],(name,generation,group)
  for event,key in [('ref_request','ref_requests'),('ref_response','ref_responses'),('tile_write_request','tile_write_requests'),('tile_write_done','tile_write_done'),('prefetch_fill','prefetch_fill_events')]:assert traces[generation][event]==d[key]
  for n in range(8100):
   plane,tile=coords(n);t=tiles[(generation,plane,tile)];W=t['tile_write_request'];D=t['tile_write_done'];assert W<D
   assert t['tile_write_done_bank']==cb and t['tile_write_request_bank']==cb
   F=t.get('prefetch_fill');Q=t.get('ref_request');R=t.get('ref_response');prevD=None if n==0 else tiles[(generation,*coords(n-1))]['tile_write_done']
   assert (Q is None)==(R is None)
   if Q is not None:assert t['ref_response_bank']==rb and t['ref_request_bank']==rb and Q<R<=W
   if F is not None:assert t['prefetch_fill_bank']==rb and (Q is None or F<Q)
   pc=command_matching[(generation,3,rb,plane,tile)] if rb is not None else []
   wc=command_matching[(generation,0,cb,plane,tile)]
   assert [b for c,b in wc]==[0,1,2,3] and W<wc[0][0]<=wc[-1][0]<D
   if meta['prefetch'] and not fr['key']:assert [b for c,b in pc]==[0,1,2,3]
   m={'write_accept_to_receiver_done':D-W,'write_accept_to_first_context_matched_write_command':wc[0][0]-W,'last_context_matched_write_command_to_receiver_done':D-wc[-1][0]}
   if Q is not None:m.update({'accepted_ref_request_to_response':R-Q,'ref_response_to_write_accept':W-R})
   if F is not None:
    m['fill_to_write_accept']=W-F
    if Q is not None:m['fill_to_accepted_lookup']=Q-F
    if prevD is not None:m['fill_minus_previous_candidate_done']=F-prevD
   if prevD is not None:
    m['write_accept_minus_previous_candidate_done']=W-prevD
    if Q is not None:m['accepted_lookup_minus_previous_candidate_done']=Q-prevD
   if pc:
    m['last_context_matched_prefetch_command_to_fill']=F-pc[-1][0]
    m['first_context_matched_prefetch_command_to_fill']=F-pc[0][0]
   for metric,value in m.items():metric_hists[(generation,metric)][value]+=1
   tile_writer.writerow([name,meta['cohort'],meta['prefetch'],generation,fr['fid'],cb,'' if rb is None else rb,plane,tile,int(hidden(plane,tile)),F or '',Q or '',R or '',W,D,prevD or '',pc[0][0] if pc else '',pc[-1][0] if pc else '',wc[0][0],wc[-1][0]])
  observations.append({'generation':generation,'fid':fr['fid'],'key':fr['key'],'events':dict(traces[generation]),'admission_through_ACK_command_counts':{str(c):{'reads':command_counts[(generation,'admission_through_ACK',f'client{c}_read')],'writes':command_counts[(generation,'admission_through_ACK',f'client{c}_write')]}for c in range(4)},'context_window_command_counts':{str(c):{'reads':command_counts[(generation,'context_window',f'client{c}_read')],'writes':command_counts[(generation,'context_window',f'client{c}_write')]}for c in range(4)},'bank_translation':banks[generation],'validated_from_packet_cycles':timing[generation]['validated_decode_model_cycles'],'validated_from_packet_ms':timing[generation]['validated_decode_model_cycles']*meta['clocks']['memory_period_ps']/1e9,'queue_cycles':timing[generation]['queue_cycles'],'measured_stream_counters':next((x for x in meta.get('stream_frames',[]) if x['generation']==generation),None),'tile_metrics_cycles':{metric:summary(h) for (g,metric),h in metric_hists.items() if g==generation},'same_tile_prefetch_interaccept_cycles':summary(same_tile_pref_gaps[generation]),'same_tile_prefetch_interaccept_no_intervening_command_cycles':summary(no_other_command_pref_gaps[generation])})
 for key,count in sorted(command_counts.items()):
  generation,scope,group=key
  histograms.append({'generation':generation,'scope':scope,'group':group,'commands':count,'interaccept_cycles':summary(gaps[key])})
 # Preserve exact integer histograms separately from compact report quantiles.
 for (generation,scope,group),h in sorted(gaps.items()):
  for delta,count in sorted(h.items()):hist_writer.writerow([name,generation,scope,group,delta,count])
 for (generation,metric),h in sorted(metric_hists.items()):
  for delta,count in sorted(h.items()):hist_writer.writerow([name,generation,'tile_metric',metric,delta,count])
 for generation,h in same_tile_pref_gaps.items():
  for delta,count in sorted(h.items()):hist_writer.writerow([name,generation,'prefetch_coordinate_sequence','same_tile_successive_block_accept',delta,count])
 for generation,h in no_other_command_pref_gaps.items():
  for delta,count in sorted(h.items()):hist_writer.writerow([name,generation,'prefetch_coordinate_sequence','same_tile_successive_block_accept_no_intervening_command',delta,count])
 bound={}
 for filename in ('results.json','source-manifest.json','sources.tar.gz','run.log','binary-check.log','binary.log','build.log'):
  if (p/filename).exists():bound[str((p/filename).relative_to(ROOT))]=sha(p/filename)
 bound[str(trace.relative_to(ROOT))]=sha(trace)
 assert bound[str((p/'sources.tar.gz').relative_to(ROOT))]==meta['source_snapshot']['sha256']
 raw_hash=hashlib.sha256()
 with gzip.open(trace,'rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):raw_hash.update(block)
 assert raw_hash.hexdigest()==meta['trace']['raw_sha256']
 return {'run':name,'cohort':meta['cohort'],'mode':meta['prefetch'],'status':meta['status'],'trace_rows':row_count,'trace_event_counts':dict(events),'trace_header':HEADER,'trace_raw_sha256_verified':raw_hash.hexdigest(),'bound_files_sha256':bound,'producer_source_sha256':meta['source_sha256'],'frames':observations,'command_groups':histograms},meta

if __name__=='__main__':
 start=time.monotonic();AREA.mkdir(parents=True,exist_ok=True)
 with gzip.open(AREA/'tiles.csv.gz','wt',newline='') as tf,gzip.open(AREA/'histograms.csv.gz','wt',newline='') as hf:
  tile_writer=csv.writer(tf);tile_writer.writerow(['run','cohort','mode','owner_generation','fid','candidate_bank','reference_bank','plane','tile_index','hidden','fill_cycle_postedge','lookup_accept_cycle_preedge','ref_response_accept_cycle_preedge','write_accept_cycle_preedge','receiver_done_accept_cycle_preedge','previous_ordinal_receiver_done_cycle','first_context_matched_pref_command_cycle','last_context_matched_pref_command_cycle','first_context_matched_write_command_cycle','last_context_matched_write_command_cycle'])
  hist_writer=csv.writer(hf);hist_writer.writerow(['run','generation','scope','group','delta_cycles','count'])
  analyzed=[analyze(name,tile_writer) for name in SELECTED]
 pairs=[]
 for cohort in (0,3):
  control,overlap=[(r,m) for r,m in analyzed if r['cohort']==cohort and r['mode'] in (1,2)]
  rc,mc=control;ro,mo=overlap;assert mc['prefetch']==1 and mo['prefetch']==2
  assert mc['source_sha256']==mo['source_sha256'],'mode1/2 producer source mismatch'
  assert [(x['fid'],x['packet_complete_cycle'])for x in mc['timings']]==[(x['fid'],x['packet_complete_cycle'])for x in mo['timings']]
  pairs.append({'cohort':cohort,'mode1_run':rc['run'],'mode2_run':ro['run'],'identical_producer_source_pins':True,'source_pin_count':len(mc['source_sha256']),'identical_packet_release_cycles':True,'frames':[{'fid':a['fid'],'generation':a['generation'],'mode1_validated_cycles':a['validated_decode_model_cycles'],'mode2_validated_cycles':b['validated_decode_model_cycles'],'mode2_minus_mode1_cycles':b['validated_decode_model_cycles']-a['validated_decode_model_cycles']}for a,b in zip(mc['timings'],mo['timings'])]})
 separate_validation=[]
 for rel in ('fpga/experiments/cu66-v80/integration/results.json','fpga/experiments/cu66-v80/memory/overlap-results.json','fpga/experiments/cu66-v80/system/faults/attempt-20261106T032224482435Z-1b8e74f4/results.json'):
  evidence=json.loads((ROOT/rel).read_text());separate_validation.append({'path':rel,'sha256':sha(ROOT/rel),'status':evidence['status'],'cases_or_configurations':evidence.get('cases') if isinstance(evidence.get('cases'),int) else len(evidence.get('cases',evidence.get('runs',[]))),'pending_lookup_coincident_abort_claimed':False})
 report={'schema':'cu80-completed-trace-analysis-v1','script_sha256':sha(Path(__file__)),'data_artifact_counts':{'runs':len(analyzed),'trace_rows':sum(r['trace_rows']for r,m in analyzed),'tile_records':sum(len(m['frames'])*8100 for r,m in analyzed),'event_totals':dict(sum((Counter(r['trace_event_counts'])for r,m in analyzed),Counter()))},'selected_completed_attempts':SELECTED,'separate_validation_evidence':separate_validation,'runs':[r for r,m in analyzed],'paired_actual_validated_milestones':pairs,'clock_period_ps':10000,'semantics':{'raw_command_owner_generation':'0 means UNKNOWN; context window is not transaction owner','event_cycles':'tile handshakes sampled preedge; fill sampled postedge of that numbered edge','interaccept_gaps':'observed controller-acceptance separations; include other clients, refresh, idle and demand timing; not controller service or recoverable critical path','lookup':'accepted handshake, not first valid assertion; F-to-Q alone cannot prove fill latency was hidden','stream_counters':'actual RTL predicates; candidate_wait includes accepted cycles, idle_candidate_wait also does not imply an unserved request; do not label them controller blockage or predicted savings','write_interval':'accepted candidate write to accepted receiver completion; includes physical work and any held retirement; backend terminal completion is not separately traced','physical_command_tile_join':'address coordinate joined within matching context window and checked against explicit bank map; raw owner remains unknown'},'artifact_sha256':{n:sha(AREA/n)for n in ('tiles.csv.gz','histograms.csv.gz')},'limits':['No first-valid lookup, raw logical request/response, bridge snapshot-capture or beat events exist in these traces.','No interaccept-count subtraction is a speedup prediction.','Only explicit completed bounded attempts analyzed; no active full-history files read.','Component overlap/reference checks and full system fault campaign PASS separately; no combined pending-lookup/write coincidence fault case asserted here.'],'wall_seconds':time.monotonic()-start}
 dump(AREA/'results.json',report)
 print('TRACE_ANALYSIS_PASS runs=',len(analyzed),'rows=',sum(r['trace_rows']for r,m in analyzed),'seconds=',round(time.monotonic()-start,2))
