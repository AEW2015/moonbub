#!/usr/bin/env python3
"""Prepare reversible same-edge owned fault bits, exact-module proof adapters; no RTL run."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'fpga/experiments/cu66-v109-fault'
AREA=ROOT/'experiments/python-gamebub-v109/fault'
BASE=ROOT/'experiments/python-gamebub-v108/outtile-native/20261108T101802940240Z/receipt.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,j):p.write_text(json.dumps(j,indent=2,sort_keys=True)+'\n')
def main():
 card=json.loads(BASE.read_text());prod={};sub={};verification=OUT/'verification';verification.mkdir(parents=True,exist_ok=True)
 targets=['cu66_inverse_stream_v91j.sv','cu66_reconstruct_stream_v91k.sv','cs88_coefficients_v91k.sv','cs88_pipeline_v91k.sv']
 for name in targets:
  alias,meta=next((a,m) for a,m in card['source_origins'].items() if Path(a).name==name)
  p=ROOT/meta['path'];assert sha(p)==meta['sha256'];s=p.read_text();edits=[]
  def edit(before,after):
   nonlocal s
   assert s.count(before)==1,(name,before,s.count(before));s=s.replace(before,after,1);edits.append(dict(before=before,after=after,expected_occurrences=1))
  if name!='cs88_pipeline_v91k.sv':
   edit('    output logic [7:0] error,','    output logic [7:0] error,\n    // Same-edge next-status predicate, never a delayed sample of error.\n    output logic fault_o,')
   # Every assignment shares its existing statement block and procedural priority.
   assignments=list(re.finditer(r'(?<![\w])error\s*<=\s*([^;]+);',s))
   for m in reversed(assignments):
    before=m[0];after=before+'fault_o<=('+m[1]+')!=0;'
    # Repeated clears are replaced together with their unique surrounding line.
    line_start=s.rfind('\n',0,m.start())+1;line_end=s.find('\n',m.end())
    line=s[line_start:line_end];assert line.count(before)==1
    edit(line,line.replace(before,after,1))
   if name!='cs88_coefficients_v91k.sv':
    for before,after in [('error!=0','fault_o'),('error==0','!fault_o')]:
     for line in list(dict.fromkeys(x for x in s.splitlines() if before in x)):
      edit(line,line.replace(before,after))
   assertion='''`ifndef SYNTHESIS
    // Checked in all cycles, including sticky failure and retry/abort edges.
    always_ff @(posedge clk)begin
        assert(fault_o==(error!=0)) else $fatal(1,"same-edge fault/status mismatch");
    end
`endif
'''
   edit('endmodule',assertion+'endmodule')
  else:
   edit('    logic reconstruction_cancel;','    logic reconstruction_cancel;\n    logic inverse_fault, reconstruction_fault, coefficient_fault;')
   for before,after in [('inverse_error!=0','inverse_fault'),('reconstruct_error!=0','reconstruction_fault'),('coefficient_error!=0','coefficient_fault')]:
    for line in list(dict.fromkeys(x for x in s.splitlines() if before in x)):edit(line,line.replace(before,after))
   edit('    assign done=coefficient_done&&inverse_done&&reconstruct_done&&error==0;','    assign done=coefficient_done&&inverse_done&&reconstruct_done&&!(coefficient_fault||inverse_fault||reconstruction_fault);')
   for err,fault in [('inverse_error','inverse_fault'),('reconstruct_error','reconstruction_fault'),('coefficient_error','coefficient_fault')]:
    edit('.error('+err+')','.error('+err+'),.fault_o('+fault+')')
   check='''`ifndef SYNTHESIS
    always_ff @(posedge clk)begin
        assert(inverse_fault==(inverse_error!=0)) else $fatal(1,"top inverse fault/status mismatch");
        assert(reconstruction_fault==(reconstruct_error!=0)) else $fatal(1,"top reconstruction fault/status mismatch");
        assert(coefficient_fault==(coefficient_error!=0)) else $fatal(1,"top coefficient fault/status mismatch");
    end
`endif
'''
   edit('endmodule',check+'endmodule')
  target=OUT/name;target.write_text(s);reverse=s
  for e in reversed(edits):assert reverse.count(e['after'])==1;reverse=reverse.replace(e['after'],e['before'],1)
  assert reverse==p.read_text()
  prod[name]=dict(alias=alias,original=meta['path'],original_sha256=sha(p),candidate=str(target.relative_to(ROOT)),candidate_sha256=sha(target),edits=edits)
  sub[alias]=dict(path=str(target.relative_to(ROOT)),sha256=sha(target))
 recipe=dict(schema='v109-same-edge-owned-fault-recipe-v1',status='PREPARED_NOT_RTL_QUALIFIED',baseline_receipt=str(BASE.relative_to(ROOT)),baseline_receipt_sha256=sha(BASE),production=prod,source_origins={a:sub.get(a,m) for a,m in card['source_origins'].items()},added_public_cycles=0,error_assignment_policy='fault_o NBA is adjacent to each original error NBA in its original branch/task; original last-assignment priority and implicit hold are unchanged; no sampling registered error')
 write(OUT/'edit-recipe.json',recipe)
 # Complete inverse pair uses actual selected V108 children; all existing oracle checks retained.
 for suffix,key in [('original','original'),('candidate','candidate')]:
  p=ROOT/prod['cu66_inverse_stream_v91j.sv'][key];s=p.read_text().replace('module cu66_inverse_stream_v91j (','module locality_'+suffix+' (',1)
  if suffix=='original':s=s.replace('    output logic [7:0] error,','    output logic [7:0] error,\n    output logic fault_o,',1).replace('endmodule','    assign fault_o=(error!=0);\nendmodule',1)
  (verification/('locality_'+suffix+'.sv')).write_text(s)
 prev=ROOT/'fpga/experiments/cu66-v107-meta-flags/verification'
 probe=(prev/'locality_probe.sv').read_text()
 probe=probe.replace('output logic [7:0] probe_fault);','output logic [7:0] probe_fault, output logic probe_fault_equal);',1)
 probe=probe.replace('locality_original old_dut(', 'logic old_fault,new_fault;\nassign probe_fault_equal=(old_fault==new_fault);\nlocality_original old_dut(.in_metadata_bad(verify_metadata_bad),.in_domain_bad(verify_domain_bad),.fault_o(old_fault),',1)
 probe=probe.replace('locality_candidate new_dut(','locality_candidate new_dut(.fault_o(new_fault),',1)
 (verification/'locality_probe.sv').write_text(probe)
 for name in ('tb_inverse.cpp','historical_inverse.cpp'):
  s=(prev/name).read_text()
  if name=='tb_inverse.cpp':
   s=s.replace('BOTH(error,0U);','BOTH(error,0U);NEW(fault_o)=0;',100)
   s=s.replace('need(d.probe_outputs_equal&&d.probe_stores_equal,','need(d.probe_fault_equal,"co-registered fault exact same-cycle status");\n need(d.probe_outputs_equal&&d.probe_stores_equal,')
  (verification/name).write_text(s)
 # Reconstruct transparent adapters preserve exact independently checked coordinate views.
 previous=ROOT/'fpga/experiments/cu66-v104-control';adapter=json.loads((previous/'adapter.json').read_text())
 for suffix,key in [('original','original'),('candidate','candidate')]:
  p=ROOT/prod['cu66_reconstruct_stream_v91k.sv'][key];s=p.read_text().replace('module cu66_reconstruct_stream_v91k (','module control_'+suffix+' (',1)
  s=s.replace('\n);',adapter['extra_ports'],1)
  if suffix=='original':s=s.replace('    output logic [7:0] error,','    output logic [7:0] error,\n    output logic fault_o,',1).replace('endmodule','    assign fault_o=(error!=0);\nendmodule',1)
  s=s.replace('endmodule',adapter['assignments']['candidate']+'endmodule',1)
  (verification/('control_'+suffix+'.sv')).write_text(s)
 s=(previous/'control_probe.sv').read_text()
 s=s.replace('    logic  candidate_lookup_req;','    logic original_fault,candidate_fault;\n    logic  candidate_lookup_req;',1)
 s=s.replace('control_original original (','control_original original (\n        .fault_o(original_fault),',1).replace('control_candidate candidate (','control_candidate candidate (\n        .fault_o(candidate_fault),',1)
 s=s.replace('    assign mismatch=','    assign mismatch=(original_fault !== candidate_fault) ||',1)
 (verification/'control_probe.sv').write_text(s)
 (verification/'tb_control.cpp').write_text((previous/'tb_control.cpp').read_text())
 write(AREA/'preparation.json',dict(status='PASS_PREPARATION_NOT_RTL',recipe_sha256=sha(OUT/'edit-recipe.json'),production={n:e['candidate_sha256'] for n,e in prod.items()},public_added_cycles=0,assertions_disabled_or_downgraded=False))
 print('FAULT_PREPARED_NOT_RUN',json.dumps(sub,sort_keys=True))
if __name__=='__main__':main()
