#!/usr/bin/env python3
"""Read-only V81 profile/physical-address reuse screening, not a latency model."""
from collections import OrderedDict,Counter
from pathlib import Path
import csv,gzip,hashlib,json
ROOT=Path(__file__).resolve().parents[2];AREA=ROOT/'fpga/experiments/cu66-v81/profile-analysis'
CASES=[(0,2,'20261106T040008432888Z-fc9416e1'),(0,3,'20261106T040008437496Z-ba7bcff7'),(3,2,'20261106T040203665199Z-0587ad4a'),(3,3,'20261106T040203665461Z-19047fa1')]
LINES=[8,32,128,512,2048,8192]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 AREA.mkdir(parents=True,exist_ok=True);runs=[];pins={}
 for cohort,mode,attempt in CASES:
  path=ROOT/f'fpga/experiments/cu66-v81/system/cohort{cohort}-frames4-fixed30-prefetch{mode}-tac2/attempt-{attempt}/results.json';d=json.loads(path.read_text())
  assert d['status']=='PASS_ACTUAL_DECODE_CANONICAL_AND_NATIVE_DISPLAY' and len(d['frames'])==4
  pins[str(path.relative_to(ROOT))]=sha(path);trace=ROOT/d['trace']['path'];assert sha(trace)==d['trace']['sha256'];pins[str(trace.relative_to(ROOT))]=sha(trace)
  caches={n:OrderedDict() for n in LINES};hits={n:Counter() for n in LINES};cross={n:Counter() for n in LINES};read_counts=Counter();writes=0
  previous_command=None;command_gaps={0:Counter(),1:Counter()};address_sets={2:set(),3:set()};bank_last={};row_changes=Counter();row_comparisons=Counter();raw=hashlib.sha256();raw_bytes=0;commands=Counter()
  with gzip.open(trace,'rb') as f:
   for chunk in iter(lambda:f.read(1024*1024),b''):raw.update(chunk);raw_bytes+=len(chunk)
  assert raw.hexdigest()==d['trace']['raw_sha256'] and raw_bytes==d['trace']['raw_bytes']
  with gzip.open(trace,'rt') as f:
   for row in csv.DictReader(f):
    if row['event']!='command':continue
    client=int(row['client']);address=int(row['address']);writing=int(row['write']);assert address%8==0
    cycle=int(row['cycle'])
    if previous_command is not None:
     previous_cycle,previous_write=previous_command;gap=cycle-previous_cycle
     assert gap>=(16 if previous_write else 18),(cohort,mode,previous_command,cycle)
     command_gaps[previous_write][gap]+=1
    previous_command=(cycle,writing)
    commands[(client,writing)]+=1
    physical_bank=(address>>22)&3;physical_row=(address>>9)&8191
    if physical_bank in bank_last:
     old_row,old_client=bank_last[physical_bank];row_comparisons[(old_client,client)]+=1
     if physical_row!=old_row:row_changes[(old_client,client)]+=1
    bank_last[physical_bank]=(physical_row,client)
    if writing:
     writes+=1
     for cache in caches.values():cache.pop(address,None)
    elif client in [2,3]:
     read_counts[client]+=1;address_sets[client].add(address)
     for n,cache in caches.items():
      if address in cache:
       previous_client=cache.pop(address);hits[n][client]+=1
       if previous_client!=client:cross[n][client]+=1
      cache[address]=client
      if len(cache)>n:cache.popitem(last=False)
  frames=[]
  for frame,timing,cmd in zip(d['frames'],d['timings'],d['command_frames']):
   assert frame['generation']==timing['generation']==cmd['generation']
   joint={f'{b}{t}{a}':frame[f'base{b}_tile{t}_aux{a}_cycles'] for b in [0,1] for t in [0,1] for a in [0,1]}
   assert sum(joint.values())==frame['cycles'];assert sum(frame[f'stage{s}_cycles'] for s in range(16))==frame['cycles']
   phy_commands=sum(cmd[f'client{c}_{rw}'] for c in range(4) for rw in ['reads','writes'])
   assert sum(cmd[f'client{c}_writes'] for c in range(4))==35040
   frames.append(dict(fid=frame['fid'],key=frame['key'],generation=frame['generation'],validated_ms=timing['validated_decode_model_cycles']*1e-5,queue_ms=timing['queue_cycles']*1e-5,transaction_cycles=frame['cycles'],receiver_stage_cycles={str(s):frame[f'stage{s}_cycles'] for s in range(16)},joint_busy_cycles=joint,base_busy_percent=100*sum(v for k,v in joint.items() if k[0]=='1')/frame['cycles'],tile_busy_percent=100*sum(v for k,v in joint.items() if k[1]=='1')/frame['cycles'],base_and_tile_busy_percent=100*sum(v for k,v in joint.items() if k[:2]=='11')/frame['cycles'],p0_read_service_cycles=frame['p0_read_service_cycles'],p0_all_service_cycles=frame['p0_service_cycles'],p0_read_wait_cycles=frame['p0_read_wait_cycles'],physical_commands=phy_commands,physical_payload_bytes=phy_commands*16,per_client_commands=cmd,p0_read_cache_hits=frame['p0_cache_hits'],p0_read_cache_misses=frame['p0_cache_misses']))
  runs.append(dict(cohort=cohort,mode=mode,result=str(path.relative_to(ROOT)),trace_scope='entire recorded context windows including post-ACK LCD tail; not admission-through-ACK command counts',frames=frames,recorded_command_counts={f'client{c}_{"writes" if w else "reads"}':count for (c,w),count in sorted(commands.items())},physical_command_predecessor_gaps=[dict(predecessor_write=bool(w),min_cycles=min(h),observations=sum(h.values()),all_at_least_cycles=16 if w else 18) for w,h in sorted(command_gaps.items())],writes_invalidating_all_screening_caches=writes,same_bank_address_row_transitions=[dict(previous_client=a,next_client=b,comparisons=row_comparisons[(a,b)],row_changes=row_changes[(a,b)]) for a,b in sorted(row_comparisons)],lcd_prefetch_read_counts={str(c):read_counts[c] for c in [2,3]},unique_lcd_blocks=len(address_sets[2]),unique_prefetch_blocks=len(address_sets[3]),physical_address_intersection=len(address_sets[2]&address_sets[3]),bounded_shared_read_cache_address_screen=[dict(lines=n,data_bytes=n*16,associativity='fully associative LRU',lcd_hits=hits[n][2],prefetch_hits=hits[n][3],lcd_cross_client_hits=cross[n][2],prefetch_cross_client_hits=cross[n][3]) for n in LINES]))
 diagnostics=[]
 for cohort,attempt in [(0,'20261106T041017230632Z-0d141ad0'),(3,'20261106T041254915582Z-c42d78b3')]:
  path=ROOT/f'fpga/experiments/cu66-v81/profile/cohort{cohort}-frames4-fixed30-prefetch3-tac2/attempt-{attempt}/results.json';d=json.loads(path.read_text())
  assert d['status']=='PASS_ACTUAL_DECODE_CANONICAL_AND_NATIVE_DISPLAY' and len(d['profile_frames'])==4
  pins[str(path.relative_to(ROOT))]=sha(path)
  control=ROOT/d['control_equivalence']['path'];assert sha(control)==d['control_equivalence']['sha256'];original=json.loads(control.read_text())
  for name in ['frames','timings']:
   for a,b in zip(d[name],original[name]):assert {k:v for k,v in a.items() if k!='native_hud_prepare_wall_ns'}=={k:v for k,v in b.items() if k!='native_hud_prepare_wall_ns'}
  assert d['summary']=={**original['summary'],'trace_rows':d['summary']['trace_rows']}
  rows=[]
  for frame,q in zip(d['frames'],d['profile_frames']):
   for prefix,n in [('fs',16),('ts',16),('idct',16),('controller',16),('bridge',8),('hash_fill',8),('hash_core',4),('ts_wp',32),('idct_wp',32)]:assert sum(q[f'{prefix}{i}'] for i in range(n))==frame['cycles']
   rows.append(dict(fid=frame['fid'],generation=frame['generation'],transaction_cycles=frame['cycles'],base_wait_idct_cycles=q['ts5'],inverse_arithmetic_state_cycles=sum(q[f'idct{i}'] for i in range(1,9)),inverse_output_state_cycles=q['idct9'],inverse_output_valid_not_ready_cycles=q['flag5'],write_stage_with_prior_write_pending_cycles=q['flag8'],write_stage_rows_not_ready_cycles=q['flag9'],controller_idle_cycles=q['controller5'],controller_waiting_cycles=q['controller4'],bridge_idle_cycles=q['bridge0'],raw_profile=q))
  diagnostics.append(dict(cohort=cohort,result=str(path.relative_to(ROOT)),control_equivalence=d['control_equivalence'],frames=rows))
 for rel in ['fpga/experiments/cu66-v74/memory/cu74_word_bridge.sv','fpga/experiments/cu66-v74/memory/cu74_tile_memory.sv','fpga/experiments/cu66-v72/memory/cu72_sdram_controller.sv','fpga/experiments/cu66-v69/integration/cu66_base_pipeline.sv','fpga/experiments/cu66-v69/inverse/cu66_idct8x8.sv','fpga/experiments/cu66-v69/inverse/cu66_reconstruct_tile.sv']:
  pins[rel]=sha(ROOT/rel)
 pins[str(Path(__file__).relative_to(ROOT))]=sha(Path(__file__))
 report=dict(schema='cu81-observed-profile-and-address-reuse-v1',source_sha256=pins,runs=runs,readonly_diagnostic_runs=diagnostics,conditional_serialized_delta_floor=dict(physical_reads=35040,physical_writes=35040,min_next_accept_after_read_cycles=18,min_next_accept_after_write_cycles=16,all_but_last_command_lower_bound_cycles=35040*18+35040*16-18,assumed_clock_mhz=100,lower_bound_ms=(35040*18+35040*16-18)*1e-5,scope='Only the unchanged frozen bridge/controller with the observed no-hit fixed traffic; excludes LCD/refresh/row misses and is not formal proof or physical timing signoff.'),screening_contract=dict(block_bytes=16,fill_clients=[2,3],all_physical_writes_invalidate=True,cache_reset='once per recorded run, not per source',replayed_command_times='unchanged; no work removed or retimed',address_hits='address/order screening only; metadata, replacement, fill/lookup latency and arbitration are not implemented',owner='raw command owner generation unknown; only physical address and recorded context used'),limitations=['Busy predicates overlap and are not stalls or exclusive stage service.','Cache-address hits do not establish a speedup or predict rerun command order.','Same-bank address row changes do not include refresh invalidation and are not actual controller row-hit counters.','Whole-window read reuse includes native repeated rasters and post-ACK tail.','No memory fit, target clock, physical throughput or shared cache RTL is established.'])
 (AREA/'results.json').write_text(json.dumps(report,indent=2)+'\n');print('V81_PROFILE_SCREEN_PASS runs',len(runs))
 for r in runs:print('REUSE',r['cohort'],r['mode'],json.dumps(r['bounded_shared_read_cache_address_screen']))
if __name__=='__main__':main()
