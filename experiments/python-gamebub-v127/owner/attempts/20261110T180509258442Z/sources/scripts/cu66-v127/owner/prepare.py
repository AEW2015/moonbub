#!/usr/bin/env python3
"""Derive V127 direct scalar views and exact three-lane owner selection; no build."""
import hashlib
import json
import re
from pathlib import Path

R=Path(__file__).resolve().parents[3]
S=R/'fpga/experiments/cu66-v127-owner'
BASES=[
 ('fpga/experiments/cu66-v91g2/packed_scratch_v91g2.sv','fpga/experiments/cu66-v123-rank/packed_scratch_v91g2.sv','12ad772136053d040d09770e0e98df6a49889757919993e3725c3ac70bafc5d7'),
 ('fpga/experiments/cu66-v91h/br88_pipeline_v91h.sv','fpga/experiments/cu66-v116b-control/br88_pipeline_v91h.sv',None),
 ('fpga/experiments/cu66-v91k/cs88_coefficients_v91k.sv','fpga/experiments/cu66-v126-producer/cs88_coefficients_v91k.sv','5dec7454e6bfae4f7a9d7f64ecfbef8568665ddaa2dc00d4a76de1167a3c7292')]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return str(p.relative_to(R))
def save(p,v):p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
def main():
 card=json.loads((R/'experiments/python-gamebub-v126/integration/results.json').read_text())
 assert len(card['source_origins'])==18
 assert all(sha(R/v['path'])==v['sha256'] for v in card['source_origins'].values())
 S.mkdir(parents=True,exist_ok=True);recipes=[];mapping={}
 for alias,old,expected in BASES:
  original=R/old;candidate=S/original.name;before=original.read_text();text=before;edits=[]
  assert card['source_origins'][alias]['path']==old
  assert sha(original)==(expected or card['source_origins'][alias]['sha256'])
  def edit(b,a,reason,kind='interface-only'):
   nonlocal text
   assert text.count(b)==1,b;text=text.replace(b,a,1);edits.append(dict(before=b,after=a,reason=reason,classification=kind))
  if original.name=='packed_scratch_v91g2.sv':
   edit('    output logic [31:0] debug_bank_epoch [0:1],','    output logic [31:0] debug_bank_epoch [0:1],\n    output logic [31:0] debug_scalar_epoch,\n    output logic [15:0] debug_scalar_block,','Direct raw scalar register views, independent of tile mode/emit selector.')
   edit('    assign debug_tile_mode=tile_mode;','    assign debug_tile_mode=tile_mode;\n    assign debug_scalar_epoch=active_epoch;\n    assign debug_scalar_block=output_block;','No state, validity, reset or ready gate on scalar metadata views.')
  elif original.name=='br88_pipeline_v91h.sv':
   edit('    output logic [31:0] dbg_bank_epoch [0:1],','    output logic [31:0] dbg_bank_epoch [0:1],\n    output logic [31:0] dbg_scalar_epoch,\n    output logic [15:0] dbg_scalar_block,','Forward internal scratch scalar views without changing pipeline behavior.')
   edit('.debug_bank_epoch(dbg_bank_epoch),','.debug_bank_epoch(dbg_bank_epoch), .debug_scalar_epoch(dbg_scalar_epoch), .debug_scalar_block(dbg_scalar_block),','Explicit new internal output connections; all old connections unchanged.')
  else:
   edit('    logic child_owner_match;','    logic child_owner_match;\n    logic [31:0] raw_scalar_epoch;\n    logic [15:0] raw_scalar_block;\n    logic scalar_owner_match;','Private direct scalar view wires; producer public port list remains byte-identical.')
   edit('    assign child_owner_match=dbg_tile_mode ? tile_owner_match[dbg_emit_bank] :\n        (child_out_epoch==current_child_epoch && out_block==expected_block);','    // V127: scalar and both bank comparisons precede mode/bank bit selection.\n    assign scalar_owner_match=raw_scalar_epoch==current_child_epoch &&\n        raw_scalar_block==expected_block;\n    assign child_owner_match=dbg_tile_mode ? tile_owner_match[dbg_emit_bank] :\n        scalar_owner_match;','Exact full32/full16 third lane removes mode-selected scalar fields from comparison inputs.','functional-comparator-factor')
   edit('        .dbg_bank_epoch(dbg_bank_epoch),','        .dbg_bank_epoch(dbg_bank_epoch),\n        .dbg_scalar_epoch(raw_scalar_epoch),\n        .dbg_scalar_block(raw_scalar_block),','Connect raw scalar views privately; no public top ports or state changes.')
   marker='''        assert(child_owner_match==(child_out_epoch==current_child_epoch &&
            out_block==expected_block))'''
   added='''        assert(scalar_owner_match==(raw_scalar_epoch==current_child_epoch &&
            raw_scalar_block==expected_block))
            else $fatal(1,"V127 full32/full16 scalar owner lane mismatch");
        if(!dbg_tile_mode)begin
            assert(child_out_epoch==raw_scalar_epoch && out_block==raw_scalar_block)
                else $fatal(1,"V127 non-tile raw scalar views differ from selected fields");
        end
'''
   edit(marker,added+marker,'Additional unconditional scalar lane/view identities; all original assertion bodies retained.','verification-only')
  for block in re.findall(r'`ifndef SYNTHESIS(.*?)`endif',before,re.S):
   if original.name!='cs88_coefficients_v91k.sv':assert block in text
  for statement in re.findall(r'assert(?:\s+property)?\s*\(.*?;',before,re.S):assert statement in text,statement[:90]
  assert re.findall(r'\(\*.*?\*\)',before,re.S)==re.findall(r'\(\*.*?\*\)',text,re.S)
  reverse=text
  for e in reversed(edits):assert reverse.count(e['after'])==1;reverse=reverse.replace(e['after'],e['before'],1)
  assert reverse==before
  if original.name=='cs88_coefficients_v91k.sv':assert text.split(');',1)[0]==before.split(');',1)[0]
  candidate.write_text(text)
  recipes.append(dict(alias=alias,original=old,original_sha256=sha(original),candidate=rel(candidate),candidate_sha256=sha(candidate),edits=edits,added_registers=0,old_assertions_removed=0,added_synthesis_attributes=0,added_public_cycles=0))
  pack=S/(candidate.stem+'-packaging.json')
  save(pack,dict(schema='v127-owner-single-module-packaging-v1',production_sha256=sha(candidate),fragments=[dict(filename=candidate.name,bytes=candidate.stat().st_size,sha256=sha(candidate))],split_byte_offsets=[]))
  mapping[alias]=dict(path=rel(candidate),sha256=sha(candidate),packaging=rel(pack),packaging_sha256=sha(pack))
 save(S/'edit-recipe.json',dict(schema='v127-owner-three-lane-production-derivation-v1',baseline_index='experiments/python-gamebub-v126/integration/results.json',baseline_index_sha256=sha(R/'experiments/python-gamebub-v126/integration/results.json'),sources=recipes,unchanged_other_origins=15,added_registers=0,added_public_cycles=0,added_synthesis_attributes=0))
 save(S/'source-map.json',dict(schema='v127-owner-source-map-v1',source_origins=mapping))
 print('V127_OWNER_PREPARED',json.dumps({a:v['sha256'] for a,v in mapping.items()},sort_keys=True))
if __name__=='__main__':main()
