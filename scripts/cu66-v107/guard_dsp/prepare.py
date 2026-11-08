#!/usr/bin/env python3
"""Exact two-local-signal USE_DSP=no recipes; historical sources read-only."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'fpga/experiments/cu66-v107-guard-dsp'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 recipes=[]
 for rel,signal,arg,anchor,expression,guard in [
 ('fpga/experiments/cu66-v106-scratch/packed_scratch_v91g2.sv','begin_limit43','begin_blocks','    logic [31:0] input_position;','32\'(begin_blocks)*43',"begin_count3>32'(begin_blocks)*43"),
 ('fpga/experiments/cu66-v106-ingress/br88_packet_ingress_sync_v91h.sv','context_limit43','context_blocks','    logic [31:0] replay_bits, raw_position, replay_word;','32\'(context_blocks)*43',"3: descriptor_limit=32'(context_blocks)*43;")]:
  source=ROOT/rel;s=source.read_text();decl=f'    // Only this constant control product is kept in slice logic.\n    (* use_dsp = "no" *) logic [31:0] {signal};\n    assign {signal}={expression};\n';newguard=guard.replace(expression,signal)
  edits=[dict(before=anchor,after=decl+anchor,expected_occurrences=1),dict(before=guard,after=newguard,expected_occurrences=1)]
  for e in edits:assert s.count(e['before'])==1;s=s.replace(e['before'],e['after'],1)
  target=OUT/source.name;target.write_text(s);recipes.append(dict(original=rel,original_sha256=sha(source),candidate=str(target.relative_to(ROOT)),candidate_sha256=sha(target),edits=edits,signal=signal,operand=arg,exact_expression=expression,scope='Single combinational 32-bit product, ×43 only; no arithmetic/operator/operand-width/state/priority/cycle changes.'))
 (OUT/'edit-recipe.json').write_text(json.dumps(dict(schema='v107-guard-local-dsp-edit-v1',files=recipes),indent=2,sort_keys=True)+'\n')
 unit='''module guard_probe (
 input logic [16:0] begin_blocks,context_blocks,
 input logic [31:0] scratch_count,ingress_count,
 output logic [31:0] scratch_original,scratch_candidate,ingress_original,ingress_candidate,
 output logic scratch_old_reject,scratch_new_reject,ingress_old_reject,ingress_new_reject
);
'''
 for e,prefix,count in zip(recipes,('scratch','ingress'),('scratch_count','ingress_count')):
  unit+=f'    assign {prefix}_original={e["exact_expression"]};\n'
  s=(ROOT/e['candidate']).read_text();lines=s.splitlines(keepends=True);decl=next(x for x in lines if f'logic [31:0] {e["signal"]};' in x);assign=next(x for x in lines if x.startswith(f'    assign {e["signal"]}='));unit+=decl+assign
  unit+=f'    assign {prefix}_candidate={e["signal"]};\n    assign {prefix}_old_reject={count}>{prefix}_original;\n    assign {prefix}_new_reject={count}>{e["signal"]};\n'
 unit+='endmodule\n';(OUT/'guard_probe.sv').write_text(unit)
 print(json.dumps(recipes,indent=2))
if __name__=='__main__':main()
