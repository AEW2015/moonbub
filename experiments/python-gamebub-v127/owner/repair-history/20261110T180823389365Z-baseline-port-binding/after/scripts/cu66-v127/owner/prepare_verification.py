#!/usr/bin/env python3
"""Prepare V127 lossless pair adapters and source-extracted scalar comparison."""
import hashlib
import json
import re
from pathlib import Path
R=Path(__file__).resolve().parents[3]
S=R/'fpga/experiments/cu66-v127-owner';V=S/'verification'
OLD=R/'fpga/experiments/cu66-v126-producer';OV=OLD/'verification'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return str(p.relative_to(R))
def save(p,x):p.write_text(json.dumps(x,sort_keys=True,indent=2)+'\n')
def main():
 V.mkdir(parents=True,exist_ok=True);adapters=[];unchanged=[]
 def derive(source,target,edits):
  before=source.read_text();body=before
  for e in edits:assert body.count(e['before'])==1,e['before'];body=body.replace(e['before'],e['after'],1)
  reverse=body
  for e in reversed(edits):assert reverse.count(e['after'])==1;reverse=reverse.replace(e['after'],e['before'],1)
  assert reverse==before
  target.write_text(body);adapters.append(dict(original=rel(source),original_sha256=sha(source),candidate=rel(target),candidate_sha256=sha(target),edits=edits))
 def e(b,a):return dict(before=b,after=a)
 for kind,source in [('original',OLD/'cs88_coefficients_v91k.sv'),('candidate',S/'cs88_coefficients_v91k.sv')]:
  edits=[e('module cs88_coefficients_v91k #','module ready_'+kind+' #')]
  if kind=='original':
   edits.append(e('    logic child_owner_match;','    logic child_owner_match;\n    logic [31:0] raw_scalar_epoch;\n    logic [15:0] raw_scalar_block;'))
   edits.append(e('        .dbg_bank_epoch(dbg_bank_epoch),','        .dbg_bank_epoch(dbg_bank_epoch),\n        .dbg_scalar_epoch(raw_scalar_epoch),\n        .dbg_scalar_block(raw_scalar_block),'))
  derive(source,V/('ready_'+kind+'.sv'),edits)
 for name in ['tb_ready.cpp','tb_controller.cpp','successor_monitor.hpp','successor_priming.hpp']:
  source=OV/name;target=V/name;target.write_bytes(source.read_bytes());unchanged.append(dict(original=rel(source),candidate=rel(target),sha256=sha(source)))
 derive(OV/'tb_successor_scalar.cpp',V/'tb_successor_scalar.cpp',[e('int main(int argc,char**argv)','int inherited_successor_scalar_main(int argc,char**argv)')])
 derive(OV/'tb_successor.cpp',V/'tb_successor.cpp',[e('int main(int argc,char**argv)','int inherited_successor_main(int argc,char**argv)')])
 source=OV/'ready_probe.sv'
 ports='''output logic probe_refill_overlap,
    output logic probe_factor_equal,probe_factor_scalar_match,probe_factor_selected,
    output logic [1:0] probe_factor_mode,probe_factor_bank_matches);'''
 extra='''
assign probe_factor_mode={new_dut.child.scratch.tile_overlap_mode,new_dut.child.scratch.raw_mode};
assign probe_factor_scalar_match=new_dut.scalar_owner_match;
assign probe_factor_selected=new_dut.child_owner_match;
assign probe_factor_bank_matches=new_dut.tile_owner_match;
assign probe_factor_equal=
    old_dut.raw_scalar_epoch==old_dut.child.scratch.active_epoch &&
    old_dut.raw_scalar_block==old_dut.child.scratch.output_block &&
    new_dut.raw_scalar_epoch==new_dut.child.scratch.active_epoch &&
    new_dut.raw_scalar_block==new_dut.child.scratch.output_block &&
    new_dut.raw_scalar_epoch==old_dut.child.scratch.active_epoch &&
    new_dut.raw_scalar_block==old_dut.child.scratch.output_block &&
    new_dut.child_owner_match==old_dut.child_owner_match &&
    new_dut.scalar_owner_match==(old_dut.child.scratch.active_epoch==old_dut.current_child_epoch &&
                                old_dut.child.scratch.output_block==old_dut.expected_block);
'''
 derive(source,V/'ready_probe.sv',[e('output logic probe_refill_overlap);',ports),e('\nendmodule',extra+'\nendmodule')])
 derive(OV/'tb_owner.cpp',V/'tb_owner.cpp',[
  e('#include "successor_monitor.hpp"','#include "successor_monitor.hpp"\n#include "owner_factor_monitor.hpp"'),
  e('static void equal(Vready_probe&d){d.eval();','static void equal(Vready_probe&d){d.eval();factor_observe(d,true,d.clk);')])
 derive(OV/'tb_owner_lanes.cpp',V/'tb_owner_lanes.cpp',[])
 derive(OV/'caller_pair.hpp',V/'caller_pair.hpp',[
  e('#include "successor_monitor.hpp"','#include "successor_monitor.hpp"\n#include "owner_factor_monitor.hpp"'),
  e('        Vready_probe::eval();','        Vready_probe::eval();\n        factor_observe(*this,false,rising);')])
 # Keep the entire original source-extracted stage probe and append only owner
 # ports/assignments. Bind its existing source recipe rather than copying logic.
 source=OV/'producer_scalar_probe.sv';body=source.read_text();prod=(S/'cs88_coefficients_v91k.sv').read_text()
 fragments=[re.search(r'    for\(genvar owner_bank=0;.*?    end\n',prod,re.S).group(),re.search(r'    assign scalar_owner_match=.*?        scalar_owner_match;',prod,re.S).group()]
 mode_fragment='    assign tile_mode=tile_overlap_mode && !raw_mode;'
 assert mode_fragment in (S/'packed_scratch_v91g2.sv').read_text()
 original_expression='    assign original_owner_match=(selected_epoch==current_child_epoch && selected_block==expected_block);'
 owner_ports='''    input logic [31:0] raw_scalar_epoch,owner_expected_epoch,bank_epoch0,bank_epoch1,
    input logic [15:0] raw_scalar_block,expected_block,bank_block0,bank_block1,
    input logic raw_mode,tile_overlap_mode,dbg_emit_bank,
    output logic [1:0] tile_owner_match,
    output logic scalar_owner_match,child_owner_match,original_owner_match,
'''
 owner_tail='''    wire tile_mode;
    wire dbg_tile_mode=tile_mode;
'''+mode_fragment+'\n'+'''    wire [31:0] dbg_bank_epoch[0:1];
    wire [15:0] dbg_bank_block[0:1];
    assign dbg_bank_epoch[0]=bank_epoch0;assign dbg_bank_epoch[1]=bank_epoch1;
    assign dbg_bank_block[0]=bank_block0;assign dbg_bank_block[1]=bank_block1;
    wire [31:0] selected_epoch=dbg_tile_mode ? dbg_bank_epoch[dbg_emit_bank] : raw_scalar_epoch;
    wire [15:0] selected_block=dbg_tile_mode ? dbg_bank_block[dbg_emit_bank] : raw_scalar_block;
'''+''.join(fragments)+'\n'+original_expression+'\n'
 owner_tail=owner_tail.replace('current_child_epoch','owner_expected_epoch')
 edits=[e('    input logic clk,reset,abort_packet,accepted_start,',owner_ports+'    input logic clk,reset,abort_packet,accepted_start,'),e('\nendmodule','\n'+owner_tail+'endmodule')]
 derive(source,V/source.name,edits)
 original_recipe=json.loads((OLD/'verification-recipe.json').read_text())
 for f in original_recipe['scalar_extraction']['fragments']+original_recipe['scalar_extraction']['call_fragments']:assert f in prod
 # Every older check body is retained in all adapters, including renamed mains.
 for item in adapters:
  before=(R/item['original']).read_text();after=(R/item['candidate']).read_text()
  for req in re.findall(r'(?:require_owner|successor_need|need)\(.*?;',before,re.S):assert req in after
 authored=[dict(path=rel(V/name),sha256=sha(V/name)) for name in ['owner_factor_monitor.hpp','tb_owner_scalar.cpp','tb_owner_factor.cpp'] if (V/name).exists()]
 save(S/'verification-recipe.json',dict(schema='v127-owner-selection-verification-derivation-v1',adapters=adapters,unchanged=unchanged,scalar_extraction=dict(source=rel(S/'cs88_coefficients_v91k.sv'),source_sha256=sha(S/'cs88_coefficients_v91k.sv'),target=rel(V/'producer_scalar_probe.sv'),target_sha256=sha(V/'producer_scalar_probe.sv'),fragments=fragments,bindings={'current_child_epoch':'owner_expected_epoch'},mode_source=rel(S/'packed_scratch_v91g2.sv'),mode_source_sha256=sha(S/'packed_scratch_v91g2.sv'),mode_fragment=mode_fragment,wrapper_ports=owner_ports,wrapper_tail=owner_tail,baseline_stage_recipe=rel(OLD/'verification-recipe.json'),baseline_stage_recipe_sha256=sha(OLD/'verification-recipe.json'),original_owner_expression=original_expression),new_verification_inputs=authored,old_require_checks_removed=0,new_payload_or_owner_forces=0,added_public_cycles=0))
 print('V127_OWNER_VERIFICATION_PREPARED',len(adapters),len(unchanged),len(authored))
if __name__=='__main__':main()
