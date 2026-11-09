#!/usr/bin/env python3
"""Emit or verify the reversible V116 Rice payload/view cut and faithful adapters."""
import argparse
import hashlib
import json
import re
from pathlib import Path
R=Path(__file__).resolve().parents[3]
S=R/'fpga/experiments/cu66-v116-rice'
V=S/'verification'
OLD=R/'fpga/experiments/cu66-v115-ingress'
PIN='37c8f5bb79621117c0e9e05096b6edead446540b026b7240819bac39838660a3'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return str(p.relative_to(R))
def save(p,q):p.write_text(json.dumps(q,indent=2,sort_keys=True)+'\n')
ASSERTIONS='''`ifndef SYNTHESIS
    // Independent old-value/view and owner model. This checker has no effect on
    // synthesized hardware. Prepared-state fixtures explicitly initialize it.
    logic v116_check_seen=0;
    logic v116_expected_zero, v116_owned;
    logic [23:0] v116_expected_value, v116_expected_payload, v116_previous_payload;
    logic v116_previous_success;
    logic v116_success_event, v116_error_event;
    logic [23:0] v116_reference_suffix, v116_reference_value;
    always_comb begin
        v116_success_event=0;
        v116_error_event=0;
        v116_reference_suffix=serial ? ((suffix_acc<<1) | 24'(extracted)) : 24'(extracted);
        v116_reference_value=quotient==15 ? v116_reference_suffix :
            ((24'(quotient)<<k) | v116_reference_suffix);
        // Reconstruct all old write-site priorities independently of the view.
        if (!reset && !stream_start && active) begin
            if (req_valid && req_ready)
                v116_error_event=failed!=0 || req_k>19 || req_escape>24;
            else if (in_valid && in_ready)
                v116_error_event=word_bad && state!=IDLE;
            else if (state==PREFIX && !out_valid)
                v116_error_event=failed!=0 || prefix_empty ||
                    (can_step && !serial && !found_one && window<15);
            else if (state==SUFFIX && !out_valid) begin
                v116_error_event=remaining<32'(suffix_left);
                v116_success_event=!v116_error_event && can_step && (!serial || suffix_left<=1);
            end
        end
    end
    always_ff @(posedge clk) begin
        if (v116_check_seen) begin
            assert(out_value==v116_expected_value && output_zero==v116_expected_zero)
                else $fatal(1,"V116 exact old-value/zero-view mismatch");
            assert(output_zero || v116_owned)
                else $fatal(1,"V116 previous owner payload exposed");
            if (v116_previous_success)
                assert(successful_payload==v116_expected_payload)
                    else $fatal(1,"V116 successful payload mismatch");
            else
                assert(successful_payload==v116_previous_payload)
                    else $fatal(1,"V116 payload changed without successful suffix completion");
            if (output_zero)
                assert(out_value==0)else $fatal(1,"V116 zero view leaks private payload");
            if (out_valid && out_error!=OK)
                assert(output_zero)else $fatal(1,"V116 error lacks zero view");
        end
        v116_check_seen<=1;
        v116_previous_payload<=successful_payload;
        v116_previous_success<=v116_success_event;
        if (reset || stream_start) begin
            v116_expected_zero<=1;
            v116_expected_value<=0;
            v116_owned<=0;
        end else if (v116_error_event) begin
            v116_expected_zero<=1;
            v116_expected_value<=0;
        end else if (v116_success_event) begin
            v116_expected_zero<=0;
            v116_expected_value<=v116_reference_value;
            v116_expected_payload<=v116_reference_value;
            v116_owned<=1;
        end
    end
`endif
'''
EDITS=[
 ('    logic [23:0] suffix_acc;','''    logic [23:0] suffix_acc;
    // Private payload is written only by an original successful suffix edge.
    // Reset/start/error change the logical view, never this 24-bit bank.
    logic [23:0] successful_payload;
    logic output_zero;
    assign out_value=output_zero ? 24'd0 : successful_payload;''',1),
 ('out_value<=0;', 'output_zero<=1;',3),
 ('out_value<=decoded_value;', 'output_zero<=0; successful_payload<=decoded_value;',1),
 ('endmodule', ASSERTIONS+'endmodule',1),
]
def transform(text,edits):
 for before,after,n in edits:
  assert text.count(before)==n,(before,text.count(before),n)
  text=text.replace(before,after,n)
 return text

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--write',action='store_true');args=ap.parse_args()
 original=OLD/'br88_rice_elastic.sv';assert sha(original)==PIN
 candidate=S/'br88_rice_elastic.sv';text=transform(original.read_text(),EDITS)
 if args.write:
  candidate.write_text(text)
  save(S/'edit-recipe.json',dict(schema='v116-rice-unreset-payload-zero-view-v1',original=rel(original),original_sha256=PIN,candidate=rel(candidate),candidate_sha256=sha(candidate),declared_public_cycle_delta=0,edits=[dict(before=b,after=a,occurrences=n)for b,a,n in EDITS]))
 assert candidate.read_text()==text
 recipe=json.loads((S/'edit-recipe.json').read_text());assert recipe['candidate_sha256']==sha(candidate)
 for b,a,n in reversed(EDITS):
  assert text.count(a)==n
  text=text.replace(a,b,n)
 assert text==original.read_text()
 for block in re.findall(r'`ifndef SYNTHESIS(.*?)`endif',original.read_text(),re.S):assert block in candidate.read_text()
 adapters=[]
 def adapt(source,path,edits):
  t=transform(source.read_text(),edits)
  if args.write:path.write_text(t)
  assert path.read_text()==t
  for b,a,n in reversed(edits):assert t.count(a)==n;t=t.replace(a,b,n)
  assert t==source.read_text()
  adapters.append(dict(source=rel(source),source_sha256=sha(source),path=rel(path),sha256=sha(path),edits=[dict(before=b,after=a,occurrences=n)for b,a,n in edits]))
 adapt(original,V/'rice_original.sv',[('module br88_rice_elastic (','module rice_original (',1)])
 adapt(candidate,V/'rice_candidate.sv',[('module br88_rice_elastic (','module rice_candidate (',1)])
 # The original paired equality expressions remain exact and unedited.
 adapt(OLD/'verification/rice_probe.sv',V/'rice_probe.sv',[
  ('probe_suffix_left);','probe_suffix_left, output logic probe_output_zero, output logic [23:0] probe_payload);',1),
  ('endmodule','assign probe_output_zero=new_dut.output_zero;\nassign probe_payload=new_dut.successful_payload;\nendmodule',1)])
 adapt(OLD/'verification/historical_rice.cpp',V/'historical_rice.cpp',[])
 bench_edits=[
  ('#include "historical_rice.cpp"','#include "historical_rice.cpp"\n#include "view_directed.cpp"',1),
  ('BOTH(out_value,0U);','OLD(out_value)=0U;NEW(output_zero)=1U;NEW(successful_payload)=0U;NEW(v116_check_seen)=0U;NEW(v116_owned)=0U;NEW(v116_expected_zero)=1U;NEW(v116_expected_value)=0U;',1),
  (' const auto parameter_clocks=oracle.clocks;',' const auto parameter_clocks=oracle.clocks;\n oracle=Oracle{};oracle.trace=&trace;oracle.phase="view-directed";\n const unsigned view_checks=view_directed(seed);',1),
 ]
 bench_edits.append(('NEW(prefix_window)=std::min(uint32_t(size-consumed),uint32_t(15));\n  NEW(remaining_nonzero)=uint32_t(size-consumed)!=0;NEW(load_nonzero)=loaded<size;',
 'BOTH(prefix_window,std::min(uint32_t(size-consumed),uint32_t(15)));\n  BOTH(remaining_nonzero,uint32_t(size-consumed)!=0);BOTH(load_nonzero,loaded<size);',1))
 bench_edits.append(('<<parameter_clocks<<",\\\"prepared_clocks', '<<parameter_clocks<<",\\\"view_directed_checks\\\":"<<view_checks<<",\\\"prepared_clocks',1))
 adapt(OLD/'verification/tb_rice.cpp',V/'tb_rice.cpp',bench_edits)
 # Keep all frozen ingress test/checker bodies; reference context routes to old Rice.
 ing=R/'fpga/experiments/cu66-v115-final-ingress'
 adapt(ing/'verification/ingress_probe.sv',V/'ingress_probe.sv',[
  ('endmodule','''    // Additional exact raw Rice visibility through the real context pair.
    always_ff @(posedge clk) begin
        assert(dut.context_decoder.parser.out_value===reference_dut.context_decoder.parser.out_value)
            else $fatal(1,"V116 real-context raw Rice value mismatch");
        assert(dut.context_decoder.parser.out_valid===reference_dut.context_decoder.parser.out_valid)
            else $fatal(1,"V116 real-context Rice valid mismatch");
        assert(dut.context_decoder.parser.out_error===reference_dut.context_decoder.parser.out_error)
            else $fatal(1,"V116 real-context Rice error mismatch");
    end
endmodule''',1)])
 adapt(ing/'verification/tb_ingress.cpp',V/'tb_ingress.cpp',[])
 adapt(ing/'br88_packet_ingress_sync_v91h.sv',V/'br88_packet_ingress_sync_v91h_reference.sv',[
  ('module br88_packet_ingress_sync_v91h #(','module br88_packet_ingress_sync_v91h_reference #(',1),
  ('    br88_context #(','    br88_context_reference #(',1)])
 ctx=R/'fpga/experiments/cu66-v113-geometry/br88_context.sv'
 adapt(ctx,V/'br88_context_reference.sv',[
  ('module br88_context #(','module br88_context_reference #(',1),
  ('    br88_rice_elastic parser (','    rice_original parser (',1)])
 if args.write:save(V/'adapters.json',dict(schema='v116-rice-faithful-adapters-v1',adapters=adapters,old_exact_public_checker_modified=False,old_historical_body_modified=False,prepared_fixture_only_private_tuple_extension=True))
 else:assert json.loads((V/'adapters.json').read_text())['adapters']==adapters
 print('V116_RICE_PREPARED_NOT_RUN',sha(candidate))
if __name__=='__main__':main()
