"""Correlate bounded direct-display reference-copy controls within each simulation clock."""
from pathlib import Path
import argparse,csv,hashlib,json,re
r=Path(__file__).resolve().parents[3];a=argparse.ArgumentParser();a.add_argument('--output',required=True);a.add_argument('proofs',nargs='+');args=a.parse_args();o=(r/args.output).resolve();o.mkdir(parents=True,exist_ok=False);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();results=[]
for name in args.proofs:
 p=(r/name).resolve();q=json.loads((p/'result.json').read_text());log=(p/'simulation.log').read_text();events=[];times={}
 for row in csv.reader((p/'trace.csv').open()):
  if row and row[0]=='LINE_TIMES':times[int(row[1])]=dict(request=int(row[2]),admit=int(row[3]),fill=int(row[4]),deadline=int(row[5]))
  elif len(row)==21 and row[1].isdigit():events.append(dict(event=row[0],cycle=int(row[1]),line=int(row[3]),context=int(row[4]),requested_u=int(row[5]),Y_ready=int(row[6]),C_ready=int(row[7]),halo_ready=int(row[8]),cache_ready=int(row[9]),front_job=int(row[10]),kind=int(row[11]),group=int(row[12]),prepare=int(row[13]),prepare_phase=int(row[14]),lcd_busy=int(row[15]),max_backend_wait=int(row[16])))
 miss=next((e for e in events if e['event']=='FIRST_UNDERRUN'),None);first=None
 if miss:
  line=miss['line'];t=times[line];yg=(line-40)//8;start=next(e for e in reversed(events)if e['event']=='PAGE_START'and e['kind']==0 and e['group']==yg and e['cycle']<=miss['cycle']);end=next(e for e in events if e['event']=='PAGE_DONE'and e['kind']==0 and e['group']==yg and e['cycle']>start['cycle']);previous_start=next((e for e in reversed(events)if e['event']=='PAGE_START'and e['cycle']<start['cycle']),None);first=dict(panel_line=line,Y_group=yg,line_times_memcycles=t,Y_page_start=start,Y_page_done=end,Y_page_latency_cycles=end['cycle']-start['cycle'],Y_page_deadline_budget_cycles=t['deadline']-start['cycle'],line_fill_lateness_cycles=t['fill']-t['deadline'],previous_page_start=previous_start,nearby_events=[e for e in events if start['cycle']-14000<=e['cycle']<=t['fill']+2000])
 counts={}
 for pattern,key in [(r'DIRECT_REFERENCE_CONTROL (.*)','reference'),(r'DIRECT_BACKGROUND (.*)','background'),(r'CU71_DIRECT_PIN_FUNCTIONAL_PASS (.*)','panel'),(r'DIRECT_PHYSICAL_COUNTERS (.*)','physical')]:
  m=re.search(pattern,log)
  if m:counts[key]=m[1]
 results.append(dict(proof=str(p.relative_to(r)).replace('\\','/'),status=q['status'],configuration={k:q.get(k,'not_recorded_in_older_runner')for k in ['owner_variant','front_bank','reference_bank','candidate_bank','hud_candidate_bank']},counts=counts,first_failure=first,source_freeze_sha256=sha(p/'source-freeze.json'),trace_sha256=sha(p/'trace.csv'),fixture_sha256=sha(p/'canonical.hex')))
(o/'correlation.json').write_text(json.dumps(dict(scope='Isolated actual pin-model reference-copy workload; preloaded fixture, no full owner lease/decoder or hardware claim',clock_unit='memory cycles at10ns; only compare event differences within the same run',results=results),indent=2)+'\n');print('REFERENCE_CONTROL_CORRELATION_WRITTEN',o)
