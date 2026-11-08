#!/usr/bin/env python3
"""Portable audit of actual capture ownership, complete public pairs and source hashes."""
import csv,gzip,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];AREA=ROOT/'experiments/python-gamebub-v107/plan-prefix'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def replay(path):
 a=[0,0,0];p12=p123=0;edges=captures=meta=0;by_index=[0,0,0];prepared_modes={};states={0:(12,0),3:(13,0),4:(0,0),5:(1,0),6:(0,0),7:(0,0),8:(10,0),9:(8,3),10:(12,0)};mode_order=[0,3,4,5,6,7,8,9,10]
 with (gzip.open(path,'rt') if path.suffix=='.gz' else path.open()) as f:
  for row in csv.reader(f):
   edge,cap,index,count,a1,a2,a3,q12,q123,valid,state,error=map(int,row);assert edge==edges
   next12=(a[0]+a[1])&0xffffffff;next123=(p12+a[2])&0xffffffff
   if cap and index>=0:a[index]=((count*4+15)&0xffffffff)&0xfffffff0;captures+=1;by_index[index]+=1
   assert [a1,a2,a3]==a and (q12,q123)==(next12,next123),(edge,'independent exact capture/nonblocking cache replay')
   p12,p123=next12,next123;meta+=valid
   if edge>=2 and edge<=3456 and edge%2==0:
    case=edge//2-1;index_group=case//(9*64);mode=mode_order[(case//64)%9];assert (state,error)==states[mode],(edge,mode,state,error);assert cap==int(mode==0);assert index==(index_group if mode==0 else -1);prepared_modes[mode]=prepared_modes.get(mode,0)+1
   edges+=1
 assert all(n==192 for n in prepared_modes.values()) and len(prepared_modes)==9
 assert edges==8305 and captures==591 and by_index==[198,197,196] and meta==2248
 return dict(edges=edges,captures=captures,capture_indices=by_index,prepared_mode_counts=prepared_modes,postedge_owned_metadata_rows=meta,all_three_private_untouched_words_checked_every_edge=True,actual_public_comparison_assertions_retained=True)
def main():
 selected=json.loads((AREA/'results.json').read_text());assert selected['status']=='PASS' and selected['actual_RTL_run'];receipt=ROOT/selected['selected_report'];r=json.loads(receipt.read_text());out=receipt.parent
 for rel,digest in r['source_sha256'].items():assert sha(ROOT/rel)==sha(out/'sources'/rel)==digest,rel
 for rel,digest in r['artifacts_sha256'].items():assert sha(out/rel)==digest,rel
 recipe=json.loads((out/'sources/fpga/experiments/cu66-v107-plan-prefix/edit-recipe.json').read_text())
 for file in recipe['files']:
  a=(out/'sources'/file['original']).read_text();b=(out/'sources'/file['candidate']).read_text();s=a
  for e in file['edits']:assert s.count(e['before'])==1;s=s.replace(e['before'],e['after'],1)
  assert s==b
  for e in reversed(file['edits']):assert s.count(e['after'])==1;s=s.replace(e['after'],e['before'],1)
  assert s==a
 adapters=json.loads((out/'sources/fpga/experiments/cu66-v107-plan-prefix/verification/adapters.json').read_text())
 for adapter in adapters['adapters']:
  s=(out/'sources'/adapter['source']).read_text()
  for before,after in adapter['renames']:assert s.count(before)==1;s=s.replace(before,after,1)
  assert s==(out/'sources'/adapter['path']).read_text()
 tb=(out/'sources/fpga/experiments/cu66-v107-plan-prefix/verification/tb_prefix.cpp').read_text()
 original_bench=(out/'sources/fpga/experiments/cu66-v91h/tb_pipeline.cpp').read_text()
 tb=tb[tb.index('#ifdef V91E_LEGACY'):tb.index('\nstatic void prefix_pre(Vprefix_probe&d){')]
 begin=tb.index('        require(prefix_edges>1000&&metadata_edges>0,')
 end=tb.index('        return 0;',begin)
 tb=tb[:begin]+tb[end:]
 tb=tb.replace('prefix_pre(d);d.clk=1;d.eval();prefix_post(d);d.clk=0;d.eval();','d.clk=1;d.eval();d.clk=0;d.eval();',1).replace('Vprefix_probe','Vbr88_pipeline_v91h')
 assert tb==original_bench,'historical golden/interface/memory checks must be byte-identical after exactly documented wrapper hooks'
 runs=[]
 for v in r['capture_runs']:
  x=replay(out/f"capture-{v['seed']}.csv.gz");assert x['edges']==v['edges'] and x['captures']==v['captures'] and x['capture_indices']==v['capture_indices'];assert v['positive_prepared_cases']==1728 and v['actual_raw_packets']==4 and v['high32_metadata_owners']==128 and v['held_metadata_edges']==2244;runs.append(dict(seed=v['seed'],**x))
 assert len(r['negative_owner_contract_rejections'])==6
 for n in r['negative_owner_contract_rejections']:
  assert n['status']=='PASS_EXPECTED_ASSERTION_REJECTION' and not n['capture_enable'] and not n['post_rejection_recovery_claim'];log=(out/n['log']).read_text();assert 'stale staging response' in log and 'EXPECTED_ASSERTION_ARMED' in log and '"capture_enable":false' in log
 assert r['math']['status']=='TEST_PASS' and r['math']['rows']==108000 and len(r['runs'])==4
 assert {(v['sync_staging'],v['seed']) for v in r['runs']}=={(s,seed) for s in (0,1) for seed in (108041,108042)}
 for v in r['runs']:assert v['pair']['status']==v['historical']['status']=='TEST_PASS' and v['historical']['configurations']==2 and v['pair']['public_cycle_edges']>1000
 result=dict(schema='v107-plan-prefix-independent-portable-audit-v1',status='PASS_ACTUAL_CAPTURE_OWNERSHIP_AND_ALL_FOUR_BODY_PUBLIC_PAIRS',receipt=str(receipt.relative_to(ROOT)),receipt_sha256=sha(receipt),production=r['production'],capture_runs=runs,positive_prepared_cases_total=sum(v['positive_prepared_cases'] for v in r['capture_runs']),prepared_high32_metadata_owners_total=256,actual_raw_packets_total=8,capture_edge_abort_restarts_total=6,held_metadata_edges_total=4488,expected_negative_foreign_valid_assertion_rejections=6,negative_post_rejection_recovery_claim=False,math=r['math'],complete_controller_pairs=r['runs'],scope='Actual full-production prepared capture/controller ownership plus real RAW interface and historical full four-body child pipelines. Prepared high32 owners are not packet-reachability proof. No full pixel canonical/native timing claim.')
 (AREA/'audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(result['status'])
if __name__=='__main__':main()
