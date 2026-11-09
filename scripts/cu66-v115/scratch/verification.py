#!/usr/bin/env python3
"""Reversible logical-cycle pair, plus checked three-edge candidate preparation."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[3];SRC=ROOT/'fpga/experiments/cu66-v115-scratch';V=SRC/'verification';OLD=ROOT/'fpga/experiments/cu66-v114-prefetch/verification'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 recipes=[]
 def derive(source,target,edits):
  s=source.read_text()
  for before,after in edits:assert s.count(before)==1,(str(source),before[:70]);s=s.replace(before,after,1)
  target.write_text(s);r=s
  for before,after in reversed(edits):assert r.count(after)==1;r=r.replace(after,before,1)
  assert r==source.read_text()
  recipes.append(dict(source=str(source.relative_to(ROOT)),source_sha256=sha(source),path=str(target.relative_to(ROOT)),sha256=sha(target),edits=edits))
 oldad=json.loads((OLD/'adapters.json').read_text()) if (OLD/'adapters.json').exists() else json.loads((SRC.parent/'cu66-v114-prefetch/verification/adapters.json').read_text())
 view=oldad['adapters'][0]['edits']
 for source,name in [(ROOT/'fpga/experiments/cu66-v114-prefetch/packed_scratch_v91g2.sv','observed_original'),(SRC/'packed_scratch_v91g2.sv','observed_candidate')]:
  edits=[list(e)for e in view];edits[0][1]='module '+name+' '
  derive(source,V/(name+'.sv'),edits)
 p=OLD/'scratch_probe.sv';s=p.read_text();pos=s.index('    observed_original original (');clk=s.index('.clk(clk)',pos)
 edits=[['input logic clk, reset,','input logic clk, reference_clk, pair_enable, reset,'],['output logic mismatch,','output logic mismatch,\n    output logic verify_preparing, verify_prepare_cancel,']]
 # Replace only the old instance clock by anchoring the complete declaration.
 edits.append(['observed_original original (\n        .clk(clk),','observed_original original (\n        .clk(reference_clk),'])
 edits.append(['always_ff @(posedge clk)begin\n        assert(old_debug_state', 'always_ff @(posedge reference_clk)if(pair_enable)begin\n        assert(old_debug_state'])
 edits.append(['    assign mismatch=!(','''    assign verify_preparing=candidate.preparing_begin;
    assign verify_prepare_cancel=candidate.cancel;
    always_ff @(posedge clk)if(!pair_enable && verify_preparing && !reset && !abort_valid && !mem_rsp_valid)
        assert(busy && !begin_ready && !coef_ready && !band_end_ready && !seal_ready &&
            !dense_valid && !mem_req_valid && !debug_outstanding && !sealed && !done && error==0)
            else $fatal(1,"paired scratch prepare interval leaked public work");
    assign mismatch=pair_enable && !('''])
 derive(p,V/'scratch_probe.sv',edits)
 for name in ['tb_scratch.cpp','tb_bank.cpp','historical_hazards.cpp']:
  edits=[['outputs=0;epoch=1;d.begin_epoch=epoch;','outputs=0;epoch=epoch+1;d.begin_epoch=epoch;']] if name=='tb_scratch.cpp' else ([['int main(int argc,char**argv)','int inherited_bank_main(int argc,char**argv)']] if name=='tb_bank.cpp' else [])
  derive(OLD/name,V/name,edits)
 (V/'adapters.json').write_text(json.dumps(dict(schema='v115-private-prepare-logical-cycle-pair-v1',contract='IV115.S1: original logical-cycle checks execute outside exactly three candidate-only preparation edges after each accepted descriptor. Every extra edge is checked for no public data/request/debt. Original files and checks remain unchanged.',adapters=recipes),indent=2)+'\n')
 print('PREPARED_VERIFICATION',len(recipes))
if __name__=='__main__':main()
