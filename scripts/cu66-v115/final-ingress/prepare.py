#!/usr/bin/env python3
"""Preserve existing REQ/WAIT edges while splitting full32 address and bounds."""
import hashlib,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[3];S=R/'fpga/experiments/cu66-v115-final-ingress';V=S/'verification';REF=R/'fpga/experiments/cu66-v115-refined-ingress'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return str(p.relative_to(R))
def write(p,q):p.write_text(json.dumps(q,indent=2,sort_keys=True)+'\n')
def main():
 source=REF/'br88_packet_ingress_sync_v91h.sv';assert sha(source)=='93b965d5d02d89e9f8b88b64340af7bd8f7c08568694e1dc0aaeb41c19bfcaf2';text=source.read_text();edits=[]
 def edit(a,b):
  nonlocal text
  assert text.count(a)==1;text=text.replace(a,b,1);edits.append(dict(before=a,after=b,occurrences=1))
 a='    always_ff @(posedge clk)if(state==FETCH_REQ)expected_fetch_addr<=prepared_request_addr;'
 b=a+'''
    // FINAL_REQUEST_BOUNDS_BEGIN: private future-address ownership crosses the
    // already existing real request edge. All32 address bits and the original
    // six-bit next-index expression above are preserved. Payload is unreset.
    logic [31:0] next_address_at_request;
    always_ff @(posedge clk)if(stage_read_req)next_address_at_request<=next_request_addr;
`ifndef SYNTHESIS
    logic next_address_warm;
    always_ff @(posedge clk)begin
        if(cancelled||context_failure||(context_active&&ctx_done)||
           (state==FETCH_WAIT&&stage_read_rsp))next_address_warm<=0;
        else if(stage_read_req)next_address_warm<=1;
        if(state==FETCH_WAIT&&!cancelled&&!context_failure&&!(context_active&&ctx_done))begin
            assert(next_address_warm)else $fatal(1,"WAIT lacks its actual preceding request owner");
            assert(next_address_at_request==next_request_addr)
                else $fatal(1,"owned next address differs from unchanged full32 formula");
        end
    end
`endif
    // FINAL_REQUEST_BOUNDS_END
'''
 edit(a,b)
 a="            prepared_request_addr<=next_request_addr;\n            prepared_request_in_bounds<=next_request_addr<size_bytes && next_request_addr<32'(MAX_PACKET_BYTES);"
 b="            prepared_request_addr<=next_address_at_request;\n            prepared_request_in_bounds<=next_address_at_request<size_bytes && next_address_at_request<32'(MAX_PACKET_BYTES);"
 edit(a,b);candidate=S/source.name;candidate.write_text(text)
 back=text
 for e in reversed(edits):assert back.count(e['after'])==1;back=back.replace(e['after'],e['before'],1)
 assert back==source.read_text()
 for block in re.findall(r'`ifndef SYNTHESIS(.*?)`endif',source.read_text(),re.S):assert block in text
 write(S/'edit-recipe.json',dict(schema='v115-final-existing-request-WAIT-address-bounds-cut-v1',original=rel(source),original_sha256=sha(source),candidate=rel(candidate),candidate_sha256=sha(candidate),edits=edits,public_cycle_delta=0,new_private_stage='Full32 next address captured at actual stage_read_req edge; existing WAIT prepares address/bounds from it.',index_width_unchanged=6,address_width_unchanged=32,original_next_address_formula_unchanged=True,initial_begin_fetch_unchanged=True,original_current_request_owner_unchanged=True,payload_reset=False,validity_register_synthesis=False))
 # Exact original/refined public pair, now using frozen93 as the reference.
 refcopy=V/'br88_packet_ingress_sync_v91h_reference.sv';refcopy.write_text(source.read_text().replace('module br88_packet_ingress_sync_v91h #(','module br88_packet_ingress_sync_v91h_reference #(',1))
 adapters=dict(schema='v115-final-additive-request-boundary-original-public-pair-v1',reference_module=dict(original=rel(source),original_sha256=sha(source),copy=rel(refcopy),copy_sha256=sha(refcopy),module_rename_only=True),parser_unchanged=True,initial_coverage_gate_retained=True,refined_additive_tests_retained=True)
 for key,name in [('wrapper','ingress_probe.sv'),('bench','tb_ingress.cpp')]:
  p=REF/'verification'/name;q=V/name;q.write_bytes(p.read_bytes());adapters[key]=dict(original=rel(p),original_sha256=sha(p),candidate=rel(q),candidate_sha256=sha(q),edits=[])
 write(V/'adapters.json',adapters);print('FINAL_INGRESS_PREPARED_NOT_RUN',sha(candidate))
if __name__=='__main__':main()
