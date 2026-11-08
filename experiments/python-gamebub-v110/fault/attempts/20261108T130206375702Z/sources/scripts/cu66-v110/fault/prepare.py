#!/usr/bin/env python3
"""Prepare reversible same-edge owned unacknowledged fault pulse; no RTL run."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'fpga/experiments/cu66-v110-fault'
AREA=ROOT/'experiments/python-gamebub-v110/fault'
BASE=ROOT/'experiments/python-gamebub-v109/native/20261108T121030620057Z/receipt.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def main():
 card=json.loads(BASE.read_text());prod={};sub={};verification=OUT/'verification';verification.mkdir(parents=True,exist_ok=True)
 targets=['cu66_inverse_stream_v91j.sv','cu66_reconstruct_stream_v91k.sv','cs88_pipeline_v91k.sv']
 for name in targets:
  alias,meta=next((a,m) for a,m in card['source_origins'].items() if Path(a).name==name)
  p=ROOT/meta['path'];assert sha(p)==meta['sha256'];s=p.read_text();edits=[]
  def edit(before,after):
   nonlocal s
   assert s.count(before)==1,(name,before,s.count(before));s=s.replace(before,after,1);edits.append(dict(before=before,after=after,expected_occurrences=1))
  if name!='cs88_pipeline_v91k.sv':
   edit('    output logic fault_o,','    output logic fault_o,\n    // Pulse equals fault_o && !top acknowledgement on the original fault edge.\n    input logic fault_ack_i,\n    output logic fault_pending_o,')
   edit('error<=reason;fault_o<=(reason)!=0;', 'error<=reason;fault_o<=(reason)!=0;fault_pending_o<=(reason)!=0&&!fault_ack_i&&!fault_o;')
   marker='    always_ff @(posedge clk) begin\n        if(reset||start||cancel)begin' if name.startswith('cu66_inverse') else '    always_ff @(posedge clk)begin\n        if(reset||cancel||start)begin'
   edit(marker,marker.replace('\n        if(', '\n        // Ack observes the old fault on this edge. A held fault is acknowledged.\n        fault_pending_o<=0;\n        if(',1))
  else:
   edit('    logic inverse_fault, reconstruction_fault, coefficient_fault;', '    logic inverse_fault, reconstruction_fault, coefficient_fault;\n    logic inverse_fault_pending, reconstruction_fault_pending;')
   edit('    assign base_abort=abort_packet||(inverse_fault&&!inverse_fault_ack)||(reconstruction_fault&&!reconstruction_fault_ack);', '    assign base_abort=abort_packet||inverse_fault_pending||reconstruction_fault_pending;')
   edit('.error(inverse_error),.fault_o(inverse_fault),','.error(inverse_error),.fault_o(inverse_fault),\n        .fault_ack_i(inverse_fault_ack),.fault_pending_o(inverse_fault_pending),')
   edit('.error(reconstruct_error),.fault_o(reconstruction_fault),','.error(reconstruct_error),.fault_o(reconstruction_fault),\n        .fault_ack_i(reconstruction_fault_ack),.fault_pending_o(reconstruction_fault_pending),')
   edit('        assert(inverse_fault==(inverse_error!=0))', '        assert(inverse_fault_pending==(inverse_fault&&!inverse_fault_ack)) else $fatal(1,"inverse pending fault/ack mismatch");\n        assert(reconstruction_fault_pending==(reconstruction_fault&&!reconstruction_fault_ack)) else $fatal(1,"reconstruction pending fault/ack mismatch");\n        assert(inverse_fault==(inverse_error!=0))')
  target=OUT/name;target.write_text(s);reverse=s
  for e in reversed(edits):assert reverse.count(e['after'])==1;reverse=reverse.replace(e['after'],e['before'],1)
  assert reverse==p.read_text()
  prod[name]=dict(alias=alias,original=meta['path'],original_sha256=sha(p),candidate=str(target.relative_to(ROOT)),candidate_sha256=sha(target),edits=edits)
  sub[alias]=dict(path=str(target.relative_to(ROOT)),sha256=sha(target))
 recipe=dict(schema='v110-owned-unacknowledged-fault-recipe-v1',status='PREPARED_NOT_RTL_QUALIFIED',baseline_receipt=str(BASE.relative_to(ROOT)),baseline_receipt_sha256=sha(BASE),production=prod,source_origins={a:sub.get(a,m) for a,m in card['source_origins'].items()},added_public_cycles=0,error_assignment_policy='Existing fault/reset/start/cancel/error assignment and priority unchanged. Pending defaults zero on every edge, then fail(reason) assigns (reason!=0)&&!ack_i&&!old_fault in original task priority.')
 write(OUT/'edit-recipe.json',recipe)
 previous=ROOT/'fpga/experiments/cu66-v109-fault/verification'
 for suffix,key in [('original','original'),('candidate','candidate')]:
  s=(ROOT/prod['cu66_inverse_stream_v91j.sv'][key]).read_text().replace('module cu66_inverse_stream_v91j (','module locality_'+suffix+' (',1)
  (verification/('locality_'+suffix+'.sv')).write_text(s)
 s=(previous/'locality_probe.sv').read_text()
 s=s.replace('input logic clk, reset, start, cancel, input_done,', 'input logic clk, reset, start, cancel, input_done,\n    input logic verify_abort_packet,',1)
 s=s.replace('logic old_fault,new_fault;', 'logic old_fault,new_fault;\nlogic fault_ack,new_fault_pending;\nalways_ff @(posedge clk)begin\n    if(reset||verify_abort_packet||start)fault_ack<=0;\n    else if(old_fault)fault_ack<=1;\nend')
 s=s.replace('assign probe_fault_equal=(old_fault==new_fault);','assign probe_fault_equal=(old_fault==new_fault)&&(new_fault_pending==(old_fault&&!fault_ack));')
 s=s.replace('locality_candidate new_dut(', 'locality_candidate new_dut(.fault_ack_i(fault_ack),.fault_pending_o(new_fault_pending),',1)
 (verification/'locality_probe.sv').write_text(s)
 for name in ('tb_inverse.cpp','historical_inverse.cpp'):
  s=(previous/name).read_text()
  if name=='tb_inverse.cpp':
   s=s.replace('NEW(fault_o)=0;', 'BOTH(fault_o,0U);NEW(fault_pending_o)=0;')
   s=s.replace('static void locality_pre(Vlocality_probe&d){', 'static void locality_pre(Vlocality_probe&d){\n // The standalone start is an admitted parent start; cancel includes either peer kill or external abort.\n d.verify_abort_packet=d.cancel&&((oracle.clocks&1U)!=0);',1)
  (verification/name).write_text(s)
 adapter=json.loads((ROOT/'fpga/experiments/cu66-v104-control/adapter.json').read_text())
 for suffix,key in [('original','original'),('candidate','candidate')]:
  s=(ROOT/prod['cu66_reconstruct_stream_v91k.sv'][key]).read_text().replace('module cu66_reconstruct_stream_v91k (','module control_'+suffix+' (',1)
  s=s.replace('\n);',adapter['extra_ports'],1).replace('endmodule',adapter['assignments']['candidate']+'endmodule',1)
  (verification/('control_'+suffix+'.sv')).write_text(s)
 s=(previous/'control_probe.sv').read_text()
 s=s.replace('    input logic  cancel,','    input logic  cancel,\n    input logic verify_abort_packet,',1)
 s=s.replace('    logic original_fault,candidate_fault;', '    logic original_fault,candidate_fault;\n    logic fault_ack,candidate_fault_pending;\n    always_ff @(posedge clk)begin\n        if(reset||verify_abort_packet||start)fault_ack<=0;\n        else if(original_fault)fault_ack<=1;\n    end')
 s=s.replace('control_candidate candidate (','control_candidate candidate (\n        .fault_ack_i(fault_ack),.fault_pending_o(candidate_fault_pending),',1)
 s=s.replace('    assign mismatch=', '    assign mismatch=(candidate_fault_pending !== (original_fault&&!fault_ack)) ||',1)
 (verification/'control_probe.sv').write_text(s)
 s=(previous/'tb_control.cpp').read_text().replace('        d.eval();++checks;', '        d.verify_abort_packet=d.cancel&&((clocks&1U)!=0);\n        d.eval();++checks;',1)
 (verification/'tb_control.cpp').write_text(s)
 write(AREA/'preparation.json',dict(status='PASS_PREPARATION_NOT_RTL',recipe_sha256=sha(OUT/'edit-recipe.json'),production={n:e['candidate_sha256'] for n,e in prod.items()},public_added_cycles=0,assertions_disabled_or_downgraded=False))
 print('V110_FAULT_PREPARED_NOT_RUN')
if __name__=='__main__':main()
