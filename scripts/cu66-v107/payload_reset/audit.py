#!/usr/bin/env python3
"""Portable source/snapshot audit and separately implemented public trace replay."""
import ast,csv,gzip,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];AREA=ROOT/'experiments/python-gamebub-v107/payload-reset';SRC=ROOT/'fpga/experiments/cu66-v107-payload-reset'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def replay(path,constant):
 m=re.search(r'QTABLES\[2\]\[3\]\[8\]\[8\]=(.*?);',constant.read_text());table=ast.literal_eval(m.group(1).replace('{','[').replace('}',']'))
 state='idle';group=0;identifier=0;error=0;out=[0]*64;owned=[];chroma=scale=0;counts=dict(edges=0,accepted=0,retired=0,discarded=0,multiply_edges=0,held_edges=0,kill_edges=0,idle_invalid_edges=0,owned_input_noise_edges=0);group_hits=[0]*8;kill_states={};errors=zeros=0
 with gzip.open(path,'rt') as f:
  for row in csv.reader(f):
   edge,rst,abort,take,pop,ready,postready,postvalid,inid,chr_,scale_=map(int,row[:11]);raw=row[11];outid,outerr=map(int,row[12:14]);bits=int(row[14],16);actual=[(bits>>(20*i))&0xfffff for i in range(64)]
   assert edge==counts['edges'];kill=bool(rst or abort);assert not take or state=='idle' and not kill;assert pop==int(state=='hold' and not kill and ready)
   old=state
   if kill:
    kill_states[old]=kill_states.get(old,0)+1;counts['discarded']+=state!='idle';state='idle';group=0;identifier=0;error=0;out=[0]*64;counts['kill_edges']+=1
   elif state=='idle':
    if take:
     counts['accepted']+=1;identifier=inid;chroma=chr_;scale=scale_;n=int(raw,16);owned=[(n>>(16*i))&65535 for i in range(64)];owned=[x-65536 if x>=32768 else x for x in owned];group=0;error=int(scale==3 or any(x < -2048 or x >2048 for x in owned));errors+=error;zeros+=not any(owned)
     if error or not any(owned):out=[0]*64;state='hold'
     else:state='multiply'
    else:counts['idle_invalid_edges']+=1
   elif state=='multiply':
    for i in range(group*8,(group+1)*8):out[i]=(owned[i]*table[chroma][scale][i//8][i%8])&0xfffff
    group_hits[group]+=1;counts['multiply_edges']+=1
    if group==7:state='hold'
    else:group+=1
   elif pop:state='idle';counts['retired']+=1
   else:counts['held_edges']+=1
   counts['owned_input_noise_edges']+=old!='idle'
   assert postready==int(state=='idle' and not kill),(edge,'ready')
   assert postvalid==int(state=='hold' and not kill),(edge,'valid')
   assert (outid,outerr,actual)==(identifier,error,out),(edge,'all public id/error/1280 payload bits')
   counts['edges']+=1
 assert state=='idle' and counts['accepted']==counts['retired']+counts['discarded']
 assert all(x>0 for x in group_hits) and set(kill_states)=={'idle','multiply','hold'}
 return dict(counts=counts,multiply_group_hits=group_hits,kill_states=kill_states,error_shortcuts=errors,zero_shortcuts=zeros)
def main():
 selected=json.loads((AREA/'results.json').read_text());assert selected['status']=='PASS' and selected['actual_RTL_run'];receipt=ROOT/selected['selected_report'];r=json.loads(receipt.read_text());base=receipt.parent
 for rel,digest in r['artifacts_sha256'].items():assert sha(base/rel)==digest,rel
 for rel,digest in r['source_sha256'].items():assert sha(base/'sources'/rel)==digest,rel
 candidate='fpga/experiments/cu66-v107-payload-reset/cu66_dequant.sv';assert sha(ROOT/candidate)==r['source_sha256'][candidate]
 recipe=json.loads((base/'sources/fpga/experiments/cu66-v107-payload-reset/edit-recipe.json').read_text());original=(base/'sources'/recipe['baseline']).read_text();rebuilt=original
 for e in reversed(recipe['changes']):assert rebuilt[e['start']:e['end']]==e['old'];rebuilt=rebuilt[:e['start']]+e['new']+rebuilt[e['end']:]
 assert rebuilt==(ROOT/candidate).read_text();assert recipe['private_reset_bits_removed']==1027
 runs=[]
 for run in r['runs']:
  replayed=replay(base/f"{run['seed']}.csv.gz",base/'sources/experiments/cu66-native-v69/generated_constants.hpp')
  assert replayed['counts']=={k:run[k] for k in replayed['counts']};runs.append(dict(seed=run['seed'],**replayed))
 native=AREA/'native/results.json';nr=None
 if native.exists():
  nr=json.loads(native.read_text());n=ROOT/nr['selected_receipt'];assert sha(n)==nr['sha256'];nr=json.loads(n.read_text());assert nr['candidate_sha256']==r['candidate']['sha256']
  for rel,digest in nr['artifacts_sha256'].items():assert sha(n.parent/rel)==digest,rel
 q=AREA/'native/query-results.json';qr=None
 if q.exists():
  chosen=json.loads(q.read_text());query=ROOT/chosen['selected_receipt'];assert sha(query)==chosen['sha256'];qr=json.loads(query.read_text());assert qr['status']=='PASS_EXACT_MAPPED_PAYLOAD_RESET_AND_CE_FANIN';assert qr['candidate_sha256']==r['candidate']['sha256'];assert qr['dcp_sha256_before']==qr['dcp_sha256_after'];assert qr['prior_receipt_sha256']==sha(n)
  for rel,digest in qr['artifacts_sha256'].items():assert sha(query.parent/rel)==digest,rel
  metrics={}
  for variant in ('original','candidate'):
   rows=list(csv.DictReader((query.parent/f'{variant}.tsv').open(),delimiter='\t'));assert len(rows)==1027
   assert len(set(x['cell'] for x in rows))==1027
   metrics[variant]=dict(cells=len(rows),ground_reset=sum(int(x['reset_ground']) for x in rows),reset_ports=sorted(set(x['reset_ports'] for x in rows)),ce_ports=sorted(set(x['ce_ports'] for x in rows)),ce_register_starts=sorted(set(x['ce_register_starts'] for x in rows)))
   assert metrics[variant]==qr['metrics'][variant]
  assert metrics['original']['ground_reset']==0 and metrics['candidate']['ground_reset']==1027
  assert metrics['original']['reset_ports']==['abort_i rst'] and metrics['original']['ce_ports']==['abort_i in_valid rst']
  assert metrics['candidate']['reset_ports']==[''] and metrics['candidate']['ce_ports']==[''] and metrics['candidate']['ce_register_starts']==['{FSM_onehot_state_reg[0]/C}']
  direct=list(csv.DictReader((n.parent/'reports/candidate/payload.tsv').open(),delimiter='\t'));assert all(x['ce_driver']=='FSM_onehot_state_reg[0]/Q' and x['reset_driver']=='GND/G' and x['ref']=='FDRE' for x in direct)
 out=dict(schema='v107-dequant-portable-independent-audit-v1',status='PASS_PUBLIC_CYCLE_REPLAY_SOURCE_RECIPE_AND_MAPPED_CONTROL' if qr else 'PASS_PUBLIC_CYCLE_REPLAY_AND_SOURCE_RECIPE',source_sha256=r['candidate']['sha256'],selected_report=str(receipt.relative_to(ROOT)),receipt_sha256=sha(receipt),runs=runs,private_bits=1027,public_output_bits_compared_every_edge=1315,mode='two-state behavioral; no SDF/hardware claim',native_status=qr['status'] if qr else None,native_metrics=qr.get('metrics') if qr else None,authoritative_native_query=str(query.relative_to(ROOT)) if qr else None,unvalidated_historical_columns_excluded=['ce_port_fanin','reset_port_fanin'])
 (AREA/'audit.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(out['status'],sum(x['counts']['edges'] for x in runs))
if __name__=='__main__':main()
