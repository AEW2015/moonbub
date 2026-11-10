#!/usr/bin/env python3
"""Reversible selected-V122 scratch rank-mask derivation; no simulator."""
import hashlib
import json
import re
from pathlib import Path
R=Path(__file__).resolve().parents[3]
OLD=R/'fpga/experiments/cu66-v119-scratch'
S=R/'fpga/experiments/cu66-v123-rank'
V=S/'verification'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return str(p.relative_to(R))
def write(p,x):p.write_text(json.dumps(x,sort_keys=True,indent=2)+'\n')
def main():
 V.mkdir(parents=True,exist_ok=True)
 original=OLD/'packed_scratch_v91g2.sv'
 assert sha(original)=='49a1731b2259dc089ca8d5e24b17e162b8c7bbd94c983cea938a793d3fdbda72'
 text=original.read_text();edits=[]
 def edit(before,after,why):
  nonlocal text
  assert text.count(before)==1,before
  text=text.replace(before,after,1);edits.append(dict(before=before,after=after,reason=why))
 edit('    logic input_raster_bad,input_dc_bad,input_ac_bad;','''    logic input_raster_bad,input_dc_bad,input_ac_bad;
    // V123: APPEND prepares only the six-bit rank relation. The live full32
    // high/block terms preserve generic previous-position semantics.
    logic [63:0] rank_threshold_mask;
    logic input_sparse_order_bad;
    assign input_sparse_order_bad=(previous_position[31:22]!=0) ||
        (coef_block<previous_position[21:6]) ||
        ((coef_block==previous_position[21:6]) && rank_threshold_mask[coef_index]);
`ifndef SYNTHESIS
    logic rank_owner_valid=0;
    logic [5:0] rank_owner_threshold;
    logic [2:0] rank_owner_phase;
    logic [31:0] rank_owner_epoch;
    always_ff @(posedge clk)begin
        if(cancel || state==BEGIN_COMMIT || state==NEXT_BAND)rank_owner_valid<=0;
        else if(tile_case_eligible && state==APPEND)begin
            rank_owner_valid<=1;rank_owner_threshold<=pending_position[5:0];
            rank_owner_phase<=phase;rank_owner_epoch<=active_epoch;
        end
    end
    always_ff @(posedge clk)if(tile_case_eligible && state==INGEST &&
        coef_valid && previous_valid && !raw_mode)begin
        assert(rank_owner_valid && rank_owner_threshold==previous_position[5:0] &&
            rank_owner_phase==phase && rank_owner_epoch==active_epoch)
            else $fatal(1,"V123 sparse rank threshold mixed owner");
        for(integer rank_index=0;rank_index<64;rank_index=rank_index+1)
            assert(rank_threshold_mask[rank_index]==
                (zigzag(6'(rank_index))<=previous_position[5:0]))
                else $fatal(1,"V123 rank mask differs from literal zigzag threshold");
        assert(input_sparse_order_bad==(input_sparse_position<=previous_position))
            else $fatal(1,"V123 generic full32 sparse ordering mismatch");
    end
`endif''','Add one unreset 64-bit threshold mask and verification-only low6/phase/epoch ownership; live high/block terms stay full-width.')
 edit('        (previous_valid && input_sparse_position<=previous_position);',
      '        (previous_valid && input_sparse_order_bad);',
      'Replace only sparse order subpredicate; retain all scalar full32 reference assertions.')
 edit('                APPEND: begin\n','''                APPEND: begin
                    // Same original edge and outer priority as previous_position.
                    for(integer rank_index=0;rank_index<64;rank_index=rank_index+1)
                        rank_threshold_mask[rank_index]<=
                            zigzag(6'(rank_index))<=pending_position[5:0];
''','Capture the complete threshold from pending_position on the original previous_position write; no new phase or payload reset.')
 candidate=S/'packed_scratch_v91g2.sv';candidate.write_text(text)
 for block in re.findall(r'`ifndef SYNTHESIS(.*?)`endif',original.read_text(),re.S):assert block in text
 recipes=[dict(original=rel(original),original_sha256=sha(original),candidate=rel(candidate),candidate_sha256=sha(candidate),edits=edits)]
 oldmeta=json.loads((OLD/'edit-recipes.json').read_text());adapters=[]
 for label,source in [('original',original),('candidate',candidate)]:
  body=source.read_text();ae=[]
  for e in oldmeta['adapters'][1]['edits']:
   before=e['before'];after=e['after'].replace('module observed_candidate ','module observed_'+label+' ')
   assert body.count(before)==1;body=body.replace(before,after,1);ae.append(dict(before=before,after=after))
  target=V/('observed_'+label+'.sv');target.write_text(body)
  adapters.append(dict(original=rel(source),original_sha256=sha(source),candidate=rel(target),candidate_sha256=sha(target),edits=ae))
 body=original.read_text();before='module packed_scratch_v91g2 (';after='module packed_scratch_reference ('
 target=V/'packed_scratch_reference.sv';target.write_text(body.replace(before,after,1))
 adapters.append(dict(original=rel(original),original_sha256=sha(original),candidate=rel(target),candidate_sha256=sha(target),edits=[dict(before=before,after=after)]))
 unchanged=[]
 for source in (OLD/'verification').iterdir():
  if source.name in ['observed_original.sv','observed_candidate.sv','packed_scratch_reference.sv','tb_ac.cpp','tb_slot.cpp','tb_ac_base.cpp']:continue
  target=V/source.name;target.write_bytes(source.read_bytes());unchanged.append(dict(original=rel(source),candidate=rel(target),sha256=sha(source)))
 source=OLD/'verification/tb_ac.cpp';body=source.read_text();ae=[]
 for before,after in [('#include "tb_ac_base.cpp"\n','#include "tb_ac_base.cpp"\n#include "rank_priming.hpp"\n'),('   record_context(d,phase,raw!=0,37);','   if(previous)prime_rank_threshold(d,c,phase,(order==0?uint32_t((raw?block*64U+index:phase==0?block:block*64U+ranks[index])-1U):order==1?(raw?block*64U+index:phase==0?block:block*64U+ranks[index]):order==2?uint32_t((raw?block*64U+index:phase==0?block:block*64U+ranks[index])+1U):0xffffffffU)&63U);\n   record_context(d,phase,raw!=0,37);'),('int main(int argc,char**argv)','int inherited_v119_rank_main(int argc,char**argv)')]:
  assert body.count(before)==1,before
  body=body.replace(before,after,1);ae.append(dict(before=before,after=after))
 target=V/'tb_ac.cpp';target.write_text(body)
 fixtures=[dict(original=rel(source),original_sha256=sha(source),candidate=rel(target),candidate_sha256=sha(target),edits=ae)]
 for name,before in [('tb_slot.cpp','\n}\nstatic void raw_fixtures'),('tb_ac_base.cpp',' NEW(ac_lane_fetch)=1U<<(band-1);NEW(ac_lane_apply)=0;')]:
  source=OLD/'verification'/name;body=source.read_text()
  mirror=' OLD(ac_lane_fetch)=NEW(ac_lane_fetch);OLD(ac_lane_apply)=NEW(ac_lane_apply);\n'
  after=mirror+before if name=='tb_slot.cpp' else before+'\n'+mirror
  assert body.count(before)==1
  target=V/name;target.write_text(body.replace(before,after,1))
  fixtures.append(dict(original=rel(source),original_sha256=sha(source),candidate=rel(target),candidate_sha256=sha(target),edits=[dict(before=before,after=after,reason='The selected V122 reference also owns V118 lane caches; bind both halves of this pre-existing deposited fixture to its same original poststate.')]))
 write(S/'edit-recipes.json',dict(schema='v123-append-rank-mask-recipe-v1',recipes=recipes,adapters=adapters,fixture_adapters=fixtures,unchanged_verification=unchanged,added_payload_bits=64,old_assertions_removed=0,old_require_checks_removed=0,declared_public_cycle_delta=0,unchanged_caller=oldmeta['unchanged_caller']))
 write(S/'packaging.json',dict(schema='v123-rank-single-module-packaging-v1',production_sha256=sha(candidate),fragments=[dict(filename=candidate.name,bytes=len(candidate.read_bytes()),sha256=sha(candidate))],split_byte_offsets=[]))
 print('V123_RANK_PREPARED',sha(candidate))
if __name__=='__main__':main()
