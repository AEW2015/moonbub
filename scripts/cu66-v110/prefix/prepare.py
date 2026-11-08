#!/usr/bin/env python3
"""Prepare guarded parallel PREFIX rank/take simplification; no cycle added."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];SRC=ROOT/'fpga/experiments/cu66-v110-prefix';AREA=ROOT/'experiments/python-gamebub-v110/prefix';OLD=ROOT/'fpga/experiments/cu66-v110-rice/br88_rice_elastic.sv';HASH='dfa58d806ce93ab273f0eb4a2d45b391198ab4bee9ce33aea324d5285d1cc5df'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def main():
 assert sha(OLD)==HASH;s=OLD.read_text();edits=[]
 def edit(before,after):
  nonlocal s
  assert s.count(before)==1,(before,s.count(before));s=s.replace(before,after,1);edits.append(dict(before=before,after=after,expected_occurrences=1))
 edit("                      (zeros==15 ? 6'd15 : (found_one ? 6'(zeros)+1'b1 : window));", "                      (found_one ? 6'(prefix_rank)+6'd1 : window);")
 edit('                            quotient<=zeros; suffix_left<=zeros==15 ? escape_width : k;', "                            quotient<=5'(prefix_rank); suffix_left<=prefix_rank==15 ? escape_width : k;")
 extra='''`ifndef SYNTHESIS
    // All PREFIX take values agree, even when the current cycle cannot consume.
    always_ff @(posedge clk)if(state==PREFIX)begin
        assert(take_bits==(serial ? 6'd1 : (zeros==15 ? 6'd15 : (found_one ? 6'(zeros)+6'd1 : window))))
            else $fatal(1,"parallel prefix take identity mismatch");
    end
    // Existing outer priority reaches this write only when not truncated.
    always_ff @(posedge clk)if(!reset&&!stream_start&&active&&state==PREFIX&&!out_valid&&
        !(req_valid&&req_ready)&&!(in_valid&&in_ready)&&failed==0&&!prefix_empty&&can_step&&
        !serial&&(found_one||window==15))begin
        assert(zeros==5'(prefix_rank) && (zeros==15)==(prefix_rank==15))
            else $fatal(1,"selected parallel prefix rank identity mismatch");
    end
`endif
'''
 edit('endmodule',extra+'endmodule');p=SRC/'br88_rice_elastic.sv';p.write_text(s);reverse=s
 for e in reversed(edits):assert reverse.count(e['after'])==1;reverse=reverse.replace(e['after'],e['before'],1)
 assert reverse==OLD.read_text()
 entry=dict(original=str(OLD.relative_to(ROOT)),original_sha256=HASH,candidate=str(p.relative_to(ROOT)),candidate_sha256=sha(p),edits=edits)
 write(SRC/'edit-recipe.json',dict(schema='v110-parallel-prefix-guarded-rank-v1',status='PREPARED_NOT_RTL_QUALIFIED',production={p.name:entry},added_public_cycles=0,scope='Take expression exact for every reachable combinational window/rank including stalled/inactive cycles. Rank load equivalence only in original parallel PREFIX nontruncated write branch. Original guards, zeros/reference, assertions, public/invalid/counters and all raw registers retained.'))
 previous=ROOT/'fpga/experiments/cu66-v110-rice/verification';out=SRC/'verification';a=json.loads((previous/'adapters.json').read_text());adapters=[]
 for suffix,path in [('original',OLD),('candidate',p)]:
  before='module br88_rice_elastic (';after='module rice_'+suffix+' (';dest=out/('rice_'+suffix+'.sv');dest.write_text(path.read_text().replace(before,after,1));adapters.append(dict(source=str(path.relative_to(ROOT)),source_sha256=sha(path),path=str(dest.relative_to(ROOT)),sha256=sha(dest),renames=[[before,after]]))
 a['adapters']=adapters;a['schema']='v110-parallel-prefix-complete-lossless-adapters-v1';write(out/'adapters.json',a)
 for n in ('historical_rice.cpp','tb_rice.cpp','rice_probe.sv'):(out/n).write_bytes((previous/n).read_bytes())
 s=(previous/'tb_rice_v110.cpp').read_text();old='   if(OLD(prefix_rank)!=NEW(prefix_rank))++differing_unused_ranks;';new='''   require(OLD(prefix_rank)==NEW(prefix_rank),"both full unmasked parser ranks equal");
   unsigned independently_masked_rank=15;
   for(unsigned p=0;p<15&&p<available;++p)if((raw>>(63-p))&1U){independently_masked_rank=p;break;}
   if(independently_masked_rank!=NEW(prefix_rank))++differing_unused_ranks;'''
 assert s.count(old)==1;s=s.replace(old,new,1);(out/'tb_prefix.cpp').write_text(s)
 write(out/'fixture-adapter.json',dict(original=str((previous/'tb_rice_v110.cpp').relative_to(ROOT)),sha256=sha(previous/'tb_rice_v110.cpp'),edits=[dict(before=old,after=new)],reason='Both miter bodies now begin at qualified unmasked V110 Rice. Preserve unused-unowned-bit coverage metric against independent masked linear reference, additionally require original/candidate unmasked ranks equal. Every inherited golden/public/raw/counter assertion remains.'))
 write(AREA/'preparation.json',dict(status='PASS_PREPARATION_NOT_RTL',original_sha256=HASH,candidate_sha256=sha(p),added_public_cycles=0,all_old_assertions_retained=True))
 print('PREFIX_PREPARED_NOT_RUN',sha(p))
if __name__=='__main__':main()
