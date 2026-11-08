#!/usr/bin/env python3
"""Prepare additional final-pass kill tests without changing the frozen proof."""
import copy
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'fpga/experiments/cu66-v108-outtile'
SRC=ROOT/'fpga/experiments/cu66-v108-outtile-kill-collisions'
AREA=ROOT/'experiments/python-gamebub-v108/outtile-kill-collisions'
HERE=Path(__file__).parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    prior=ROOT/'experiments/python-gamebub-v108/outtile/results.json';old=json.loads(prior.read_text());assert old['status']=='PASS' and old['actual_RTL_run']
    assert sha(BASE/'cu66_idct8x8.sv')==old['candidate']['sha256']=='3a30e2c527755ee5e34480274a7998795a773e23fef6cec8471fdd89c31a7808'
    SRC.mkdir(parents=True,exist_ok=True);AREA.mkdir(parents=True,exist_ok=True)
    for name in ('idct_original.sv','idct_candidate.sv','idct_probe.sv'):(SRC/name).write_bytes((BASE/name).read_bytes())
    body=(BASE/'tb_idct.cpp').read_text();edits=[]
    def edit(before,after):
        nonlocal body
        assert body.count(before)==1,before;body=body.replace(before,after,1);edits.append(dict(before=before,after=after))
    needle='unsigned directed=0,abort_mask=0;'
    edit(needle,needle+'unsigned boundary_cases=0,boundary_groups=0,boundary_guards=0,boundary_matrix=0,boundary_retries=0;')
    needle=' need(abort_mask==1023&&b.states==1023,"all FSM states coverage");'
    extra=''' // All original fixtures finish before this additional matrix; their RNG sequence is unchanged.
 for(unsigned group=0;group<4;++group)for(unsigned guards=1;guards<=3;++guards){
  b.flush(1);b.send(*ac);unsigned watchdog=0;
  while(!(b.d.verify_state==4&&b.d.verify_k==7&&b.d.verify_group==group)){need(++watchdog<=130,"final-pass write boundary unreachable");b.tick();}
  uint64_t selected=0;for(unsigned row=0;row<8;++row)for(unsigned col=group*2;col<group*2+2;++col)selected|=uint64_t(1)<<(row*8+col);
  b.d.clk=0;b.d.eval();need(b.d.verify_payload_write==selected&&__builtin_popcountll(selected)==16,"target actual sixteen-word AC write collision");
  const uint64_t old_collisions=b.kill_payload_collisions,old_outputs=b.outputs;
  b.d.in_valid=1;b.d.in_id=b.rng();for(unsigned i=0;i<40;++i)b.d.in_tile[i]=b.rng();b.flush(guards);
  need(b.kill_payload_collisions==old_collisions+1&&b.d.verify_written==0,"targeted kill must hide every concurrently written word");
  for(unsigned i=0;i<48;++i)need(b.d.out_tile[i]==0,"targeted kill public output zero even invalid");
  ++boundary_cases;boundary_groups|=1U<<group;boundary_guards|=1U<<(guards-1);boundary_matrix|=1U<<(group*3+guards-1);
  b.run(*ac);need(b.outputs==old_outputs+1,"targeted kill good golden retry did not complete");++boundary_retries;
 }
 need(boundary_cases==12&&boundary_groups==15&&boundary_guards==7&&boundary_matrix==4095&&boundary_retries==12,"all twelve AC write-boundary kill/golden-retry cases");
'''
    edit(needle,extra+needle)
    needle='  trace<<",\\\"products\\\":[";'
    extra='''  bool public_zero_after=true;for(unsigned word=0;word<64;++word)public_zero_after&=bits(d.out_tile,word*24,24)==0;
  trace<<",\\\"written_mask_after\\\":"<<d.verify_written<<",\\\"payload_write_mask\\\":"<<writes<<",\\\"public_zero_after\\\":"<<(public_zero_after?"true":"false");
'''
    edit(needle,extra+needle)
    needle='<<b.outputs<<"}\\n";'
    after='<<b.outputs<<",\\\"write_boundary_collision_cases\\\":"<<boundary_cases<<",\\\"write_boundary_group_mask\\\":"<<boundary_groups<<",\\\"write_boundary_guard_mask\\\":"<<boundary_guards<<",\\\"write_boundary_matrix_mask\\\":"<<boundary_matrix<<",\\\"write_boundary_good_retries\\\":"<<boundary_retries<<"}\\n";'
    edit(needle,after)
    (SRC/'tb_idct.cpp').write_text(body)
    a=copy.deepcopy(json.loads((BASE/'adapters.json').read_text()))
    for entry in a['adapters']:
        entry['path']=str((SRC/Path(entry['path']).name).relative_to(ROOT));entry['sha256']=sha(ROOT/entry['path'])
    a.update(schema='v108-outtile-additional-kill-lossless-adapters-v1',probe_original=str((BASE/'idct_probe.sv').relative_to(ROOT)),probe_original_sha256=sha(BASE/'idct_probe.sv'),bench_original=str((BASE/'tb_idct.cpp').relative_to(ROOT)),bench_original_sha256=sha(BASE/'tb_idct.cpp'),bench_edits=edits,frozen_prior_result=str(prior.relative_to(ROOT)),frozen_prior_result_sha256=sha(prior))
    (SRC/'adapters.json').write_text(json.dumps(a,indent=2,sort_keys=True)+'\n')
    # The existing finite model is unchanged; this is a separate actual-RTL coverage extension.
    (AREA/'preparation.json').write_bytes((ROOT/'experiments/python-gamebub-v108/outtile/preparation.json').read_bytes())
    runner=(HERE.parent/'outtile/qualify.py').read_text()
    replacements=[('from model import verify_recipe','import sys\nsys.path.insert(0,str(Path(__file__).resolve().parents[1]/"outtile"))\nfrom model import verify_recipe'),("SRC=ROOT/'fpga/experiments/cu66-v108-outtile'","SRC=ROOT/'fpga/experiments/cu66-v108-outtile-kill-collisions'"),("AREA=ROOT/'experiments/python-gamebub-v108/outtile'","AREA=ROOT/'experiments/python-gamebub-v108/outtile-kill-collisions'"),("('v108-outtile-'+stamp)","('v108-outtile-kill-'+stamp)"),("container='gamebub-v108-outtile-'","container='gamebub-v108-outtile-kill-'"),("schema='v108-outtile-exact-public-word-focused-proof-v1'","schema='v108-outtile-kill-collisions-focused-proof-v1'"),('ROOT/recipe[\'original_path\'],vectors','ROOT/recipe[\'original_path\'],ROOT/recipe[\'candidate_path\'],ROOT/"experiments/python-gamebub-v108/outtile/results.json",vectors'),("print('OUTTILE_QUALIFICATION'","print('OUTTILE_KILL_QUALIFICATION'")]
    for before,after in replacements:assert runner.count(before)==1,before;runner=runner.replace(before,after,1)
    needle='    recipe=verify_recipe();a=json.loads((SRC/\'adapters.json\').read_text())'
    after=needle+'\n    prior=ROOT/a["frozen_prior_result"];assert sha(prior)==a["frozen_prior_result_sha256"];prior_record=json.loads(prior.read_text());assert prior_record["status"]=="PASS" and prior_record["actual_RTL_run"] and prior_record["candidate"]["sha256"]==recipe["candidate_sha256"]'
    assert runner.count(needle)==1;runner=runner.replace(needle,after,1)
    needle="and v['exposed_word_commits']>1000"
    after=needle+" and v['write_boundary_collision_cases']==12 and v['write_boundary_group_mask']==15 and v['write_boundary_guard_mask']==7 and v['write_boundary_matrix_mask']==4095 and v['write_boundary_good_retries']==12 and v['kill_payload_write_collisions']==15"
    assert runner.count(needle)==1;runner=runner.replace(needle,after,1)
    needle='            products=[0]*8;rows=mul=0'
    after=needle+';boundary={}'
    assert runner.count(needle)==1;runner=runner.replace(needle,after,1)
    needle="                assert row['products']==products;rows+=1"
    after='''                assert row['products']==products;rows+=1
                if row['kill'] and row['state']==4 and row['k']==7:
                    group=row['group'];guards=row['rst']+2*row['abort'];assert 0<=group<4 and guards in (1,2,3)
                    selected=sum(1<<(r*8+c) for r in range(8) for c in (group*2,group*2+1));assert row['payload_write_mask']==selected and row['written_mask_after']==0 and row['public_zero_after']
                    key=group*3+guards-1;boundary[key]=boundary.get(key,0)+1'''
    assert runner.count(needle)==1;runner=runner.replace(needle,after,1)
    needle="            assert rows==v['clock_edges'] and mul==v['multiply_edges']"
    after=needle+'\n            assert boundary=={i:1 for i in range(12)}'
    assert runner.count(needle)==1;runner=runner.replace(needle,after,1)
    needle="trace_replay=dict(status='PASS',rows=rows,multiply_edges=mul,raw_sha256=sha(trace))"
    after="trace_replay=dict(status='PASS',rows=rows,multiply_edges=mul,raw_sha256=sha(trace),write_boundary_matrix_mask=sum(1<<i for i in boundary),write_boundary_collisions=sum(boundary.values()))"
    assert runner.count(needle)==1;runner=runner.replace(needle,after,1)
    (HERE/'qualify.py').write_text(runner)
    print('OUTTILE_KILL_PREPARED',sha(SRC/'tb_idct.cpp'))
if __name__=='__main__':main()
