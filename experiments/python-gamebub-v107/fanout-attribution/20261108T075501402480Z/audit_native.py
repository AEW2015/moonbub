#!/usr/bin/env python3
"""Portable audit/grouping of exact read-only PAYLOAD primitive-pin attribution."""
import argparse,collections,csv,hashlib,json,re
from pathlib import Path

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,sort_keys=True,indent=2)+'\n')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--area',type=Path,default=Path(__file__).resolve().parents[2]/'experiments/python-gamebub-v107/fanout-attribution');args=ap.parse_args();area=args.area
 selected=json.loads((area/'results.json').read_text());out=area/Path(selected['selected_receipt']).parent.name;r=json.loads((out/'receipt.json').read_text());assert sha(out/'receipt.json')==selected['sha256'];assert r['status']=='PASS_READONLY_LOAD_EXTRACTION' and r['exit_code']==0
 assert r['checkpoint_sha256_before']==r['checkpoint_sha256_after'];assert r['parent_receipt_sha256']==r['parent_receipt_sha256_after']==sha(out/'parent-receipt.json')
 for n,h in r['retained_sha256'].items():assert sha(out/n)==h,n
 parent=json.loads((out/'parent-receipt.json').read_text());assert parent['artifacts']['route.dcp']['sha256']==r['checkpoint_sha256_before'];assert sha(out/'parent-inputs.json')==parent['source_manifest_sha256']
 for n,h in parent['retained_source_snapshot_sha256'].items():assert sha(out/'sources'/n)==h,n
 settings=list(csv.DictReader((out/'reports/settings.csv').open()));assert len(settings)==1 and settings[0]['part']=='xc7a100tcsg324-1' and float(settings[0]['period_ns'])==10 and int(settings[0]['max_threads'])==2
 for n in ['route-high-fanout.rpt','route-timing-summary.rpt']:assert sha(out/n)==parent['artifacts'][n]['sha256']
 targets=[('coefficients/child/scratch/cancelled',7141,-1.340),('transform/inverse/reset_0',2354,-1.180),('coefficient_boundary/running14_out',2242,-1.753)]
 summary=[]
 for i,(name,total,reported_slack) in enumerate(targets):
  rows=list(csv.DictReader((out/f'reports/net{i}-pins.csv').open()));assert all(x['net']==name for x in rows);assert len({x['pin'] for x in rows})==len(rows)
  loads=[x for x in rows if x['direction']=='IN'];drivers=[x for x in rows if x['direction']=='OUT'];assert len(loads)==total and len(drivers)==1
  parents=collections.Counter(x['parent'] for x in loads);types=collections.Counter((x['primitive'],x['ref_pin']) for x in loads)
  groups=collections.Counter((x['parent'],x['primitive'],x['ref_pin']) for x in loads)
  with (out/f'net{i}-groups.csv').open('w') as f:
   w=csv.writer(f);w.writerow(['actual_parent','primitive','ref_pin','load_pins']);w.writerows([list(k)+[n] for k,n in sorted(groups.items())])
  stems=collections.Counter((re.sub(r'\[\d+\]','[]',x['cell']),x['primitive'],x['ref_pin']) for x in loads)
  with (out/f'net{i}-register-stems.csv').open('w') as f:
   w=csv.writer(f);w.writerow(['actual_cell_with_numeric_indices_normalized','primitive','ref_pin','load_pins']);w.writerows([list(k)+[n] for k,n in sorted(stems.items())])
  setup=(out/f'reports/net{i}-setup.rpt').read_text();hold=(out/f'reports/net{i}-hold.rpt').read_text();extract=lambda t:[float(x) for x in re.findall(r'Slack \([^)]*\)\s*:\s*([-+0-9.]+)ns',t)]
  ss,hs=extract(setup),extract(hold);assert ss and hs and abs(ss[0]-reported_slack)<.0001
  ff=[x for x in loads if x['primitive'] in ('FDRE','FDSE')];assert all(x['ref_pin'] in ('R','S') for x in ff)
  row=dict(net=name,load_pins=len(loads),unique_load_cells=len({x['cell'] for x in loads}),driver=drivers,actual_parent_loads=dict(parents),primitive_pin_loads=[dict(primitive=k[0],pin=k[1],count=n) for k,n in sorted(types.items())],slice_SR_pins=len(ff),setup_slacks_ns=ss,hold_slacks_ns=hs,retained_parent_high_fanout_worst_slack_ns=reported_slack)
  if i==0:
   operational=[x for x in ff if x['cell'] in ['coefficients/child/allocation_reg','coefficients/child/done_reg','coefficients/child/seal_sent_reg']];assert len(operational)==3
   observation=[x for x in ff if x not in operational];assert len(observation)==7125 and all(Path(x['cell']).name.startswith(('count_','ts_','max_','stage_buffer_highwater')) for x in observation)
   row['explicit_slice_SR_attribution']=dict(named_telemetry_FFs=len(observation),operational_FFs=operational)
  elif i==1:
   exact=lambda p:len([x for x in ff if x['cell'].startswith('transform/inverse/'+p)])
   row['explicit_slice_SR_attribution']=dict(public_out_tile=exact('out_tile_reg['),even_sum=exact('even_sum_reg['),odd_sum=exact('odd_sum_reg['),public_out_id=exact('out_id_reg['),state_and_replicas=exact('state_reg['));assert sum(row['explicit_slice_SR_attribution'].values())==len(ff)
  else:
   residual=len([x for x in ff if x['cell'].startswith('reconstruction/residual_reg[')]);reference=len([x for x in ff if x['cell'].startswith('reconstruction/reference_pixels_reg[')]);assert residual==1536 and reference==512
   row['explicit_slice_SR_attribution']=dict(residual=residual,reference_pixels=reference,other_controls=len(ff)-residual-reference)
  summary.append(row)
 result=dict(status='PASS_EXACT_MAPPED_PIN_ATTRIBUTION',parent_receipt_sha256=sha(out/'parent-receipt.json'),raw_receipt_sha256=sha(out/'receipt.json'),checkpoint_sha256=r['checkpoint_sha256_before'],source_snapshot_files=len(parent['retained_source_snapshot_sha256']),settings=settings,nets=summary,warnings=[x for x in (out/'tool.log').read_text().splitlines() if 'WARNING:' in x],scope='Exact physical loads/pins and name-normalized stem counts only. No logical RTL equivalence, reset-removal safety, new source activation, board timing or closure proof.')
 write(out/'summary.json',result)
 index={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='evidence-index.json'};write(out/'evidence-index.json',dict(status=result['status'],retained_sha256=index,external_DCP_hash_only=parent['artifacts']['route.dcp']))
 print(result['status']);print('SLICE_SR_COUNTS',[x['slice_SR_pins'] for x in summary])
if __name__=='__main__':main()
