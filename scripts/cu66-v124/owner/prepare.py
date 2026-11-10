#!/usr/bin/env python3
"""Reversible compare-before-mux owner lanes; preparation only."""
import hashlib,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[3]
OLD=R/'fpga/experiments/cu66-v119-owner'
S=R/'fpga/experiments/cu66-v124-owner'
V=S/'verification'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return str(p.relative_to(R))
def write(p,j):p.write_text(json.dumps(j,sort_keys=True,indent=2)+'\n')
def main():
 V.mkdir(parents=True,exist_ok=True)
 original=OLD/'cs88_coefficients_v91k.sv'
 assert sha(original)=='3517bda5016d7c2920e20fbc0767bbb1146e091cea4a5216db9a8b9a6532ee30'
 text=original.read_text();edits=[]
 def edit(before,after,reason):
  nonlocal text
  assert text.count(before)==1,before
  text=text.replace(before,after,1);edits.append(dict(before=before,after=after,reason=reason))
 before='    assign child_out_ready=state==DISPATCH&&out_ready&&child_out_epoch==current_child_epoch&&out_block==expected_block&&!reset&&!abort_packet;'
 after='''    // V124: full-width owner comparison precedes the one-bit bank selector.
    // KEEP is restricted to these two combinational result bits; no placement,
    // hierarchy, reset, new FF, or timing exception is introduced.
    (* keep = "true" *) logic [1:0] tile_owner_match;
    logic child_owner_match;
    for(genvar owner_bank=0;owner_bank<2;owner_bank=owner_bank+1)begin: owner_lanes
        assign tile_owner_match[owner_bank]=
            dbg_bank_epoch[owner_bank]==current_child_epoch &&
            dbg_bank_block[owner_bank]==expected_block;
    end
    assign child_owner_match=dbg_tile_mode ? tile_owner_match[dbg_emit_bank] :
        (child_out_epoch==current_child_epoch && out_block==expected_block);
`ifndef SYNTHESIS
    // Unconditional tile cycles, including invalid/unready/reset/abort cycles.
    // Raw views, not bank validity or presumed current ownership, certify this.
    always_ff @(posedge clk)begin
        if(dbg_tile_mode)begin
            assert(child_out_epoch==dbg_bank_epoch[dbg_emit_bank] &&
                out_block==dbg_bank_block[dbg_emit_bank])
                else $fatal(1,"V124 tile bank raw views differ from selected fields");
        end
        for(integer owner_bank=0;owner_bank<2;owner_bank=owner_bank+1)
            assert(tile_owner_match[owner_bank]==
                (dbg_bank_epoch[owner_bank]==current_child_epoch &&
                 dbg_bank_block[owner_bank]==expected_block))
                else $fatal(1,"V124 complete full32/full16 owner lane mismatch");
        assert(child_owner_match==(child_out_epoch==current_child_epoch &&
            out_block==expected_block))
            else $fatal(1,"V124 generic selected owner identity mismatch");
    end
`endif
    assign child_out_ready=state==DISPATCH&&out_ready&&child_owner_match&&!reset&&!abort_packet;'''
 edit(before,after,'Prepare two full32 epoch/full16 block combinational equality lanes before one-bit selection; preserve non-tile scalar fallback and every invalid-cycle owner value.')
 edit('    assign out_valid=state==DISPATCH&&child_out_valid&&child_out_epoch==current_child_epoch&&out_block==expected_block&&!reset&&!abort_packet;',
      '    assign out_valid=state==DISPATCH&&child_out_valid&&child_owner_match&&!reset&&!abort_packet;',
      'Use the same exact owner predicate for public valid; no bank-ready or child-valid assumption added.')
 edit('                        if(child_out_valid&&(child_out_epoch!=current_child_epoch||out_block!=expected_block))begin',
      '                        if(child_out_valid&&!child_owner_match)begin',
      'Preserve same-edge error67 priority using the exact complement of the common owner predicate.')
 candidate=S/original.name;candidate.write_text(text)
 for block in re.findall(r'`ifndef SYNTHESIS(.*?)`endif',original.read_text(),re.S):assert block in text
 recipe=dict(original=rel(original),original_sha256=sha(original),candidate=rel(candidate),candidate_sha256=sha(candidate),edits=edits)
 adapters=[]
 for label,source in [('original',original),('candidate',candidate)]:
  before='module cs88_coefficients_v91k #';after='module ready_'+label+' #'
  body=source.read_text();assert body.count(before)==1
  target=V/('ready_'+label+'.sv');target.write_text(body.replace(before,after,1))
  adapters.append(dict(original=rel(source),original_sha256=sha(source),candidate=rel(target),candidate_sha256=sha(target),edits=[dict(before=before,after=after)]))
 unchanged=[]
 for name in ['tb_ready.cpp']:
  source=OLD/'producer-verification'/name;target=V/name;target.write_bytes(source.read_bytes());unchanged.append(dict(original=rel(source),candidate=rel(target),sha256=sha(source)))
 fixtures=[]
 for name in ['tb_owner.cpp','ready_probe.sv']:
  source=OLD/'producer-verification'/name;body=source.read_text()
  if name=='tb_owner.cpp':before='int main(int argc,char**argv)';after='int inherited_owner_main(int argc,char**argv)'
  else:
   before='assign probe_internal_equal=';after='assign probe_internal_equal=(old_dut.child_out_ready==new_dut.child_out_ready)&&'
  assert body.count(before)==1
  target=V/name;target.write_text(body.replace(before,after,1));fixtures.append(dict(original=rel(source),original_sha256=sha(source),candidate=rel(target),candidate_sha256=sha(target),edits=[dict(before=before,after=after)]))
 source=R/'fpga/experiments/cu66-v91i2b/tb_pipeline.cpp';body=source.read_text();fe=[]
 for before,after in [('#include "Vcs88_pipeline_v91i2b.h"','#include "caller_pair.hpp"'),('int main(int argc,char **argv)','int inherited_controller_main(int argc,char **argv)')]:
  assert body.count(before)==1;body=body.replace(before,after,1);fe.append(dict(before=before,after=after))
 target=V/'tb_controller.cpp';target.write_text(body);fixtures.append(dict(original=rel(source),original_sha256=sha(source),candidate=rel(target),candidate_sha256=sha(target),edits=fe))
 write(S/'edit-recipes.json',dict(schema='v124-spatial-owner-lanes-recipe-v1',production=recipe,adapters=adapters,fixture_adapters=fixtures,unchanged=unchanged,added_registers=0,added_public_cycles=0,old_assertions_removed=0,old_require_checks_removed=0,synthesis_attribute=dict(name='keep',value='true',exact_target='tile_owner_match[1:0]',bit_count=2,other_directives_added=False)))
 write(S/'packaging.json',dict(schema='v124-owner-single-module-packaging-v1',production_sha256=sha(candidate),fragments=[dict(filename=candidate.name,bytes=len(candidate.read_bytes()),sha256=sha(candidate))],split_byte_offsets=[]))
 print('V124_OWNER_PREPARED',sha(candidate))
if __name__=='__main__':main()
