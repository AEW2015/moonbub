#!/usr/bin/env python3
"""Exact source-only recipe for precomputed token-owned tuple predicates."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'fpga/experiments/cu66-v107-meta-flags'
def sha(s):return hashlib.sha256(s.encode()).hexdigest()
def main():
 bases={'cu66_coefficient_elastic.sv':('fpga/experiments/cu66-v107-elastic/cu66_coefficient_elastic.sv','28de630dc9266ff23302ecf96155e7b4135ee26b6140682483c219791b9b61e9'),'cu66_inverse_stream_v91j.sv':('fpga/experiments/cu66-v107-value-check/cu66_inverse_stream_v91j.sv','c93bec92283985070c0ef343be3377d44ffa04c513e37232d8962344fb6180c9'),'cs88_pipeline_v91k.sv':('fpga/experiments/cu66-v107-elastic/cs88_pipeline_v91k.sv','d9441f5a4600daf48cbb201cf731c42d724bf9f0c5609bf8b9249d683cf5e57d')}
 original={n:(ROOT/p).read_text() for n,(p,h) in bases.items()}
 for n,(p,h) in bases.items():assert sha(original[n])==h,n
 inverse=original['cu66_inverse_stream_v91j.sv'];i=inverse.index('    function automatic logic [10:0] quant_cell');helper=inverse[i:inverse.index('    endfunction',i)+len('    endfunction')]
 def meta(pre):return f"{pre}plane>2||{pre}tile>=({pre}plane==0?13'd5400:13'd1350)||{pre}qcell!=quant_cell({pre}plane,{pre}tile)"
 def domain(pre):return f"{pre}qscale==3||!({pre}value[15:11]==5'd0||{pre}value[15:11]==5'b11111||{pre}value==16'h0800)"
 edits={n:[] for n in bases}
 def add(n,a,b):edits[n].append(dict(before=a,after=b,expected_occurrences=1))
 stage='cu66_coefficient_elastic.sv'
 add(stage,'    output logic output_done, occupied\n','    output logic output_done, occupied,\n    output logic out_metadata_bad, out_domain_bad\n')
 add(stage,'    logic [129:0] payload;','    logic [129:0] payload;\n    // Private token-owned data; full/fence ownership masks unreset contents.\n    logic [1:0] tuple_checks;\n'+helper)
 add(stage,'    assign kill=reset||start||cancel;','    assign out_metadata_bad=tuple_checks[1];\n    assign out_domain_bad=tuple_checks[0];\n    assign kill=reset||start||cancel;')
 add(stage,'                full<=1;','                tuple_checks<={('+meta('in_')+'),('+domain('in_')+')};\n                full<=1;')
 add(stage,'`ifndef SYNTHESIS\n','''`ifndef SYNTHESIS
    // Compare only owned, consumed token data; unowned flag contents may differ.
    always_ff @(posedge clk)if(!kill&&out_valid&&out_ready)begin
        assert(out_metadata_bad==('''+meta('out_')+'''))
            else $fatal(1,"coefficient static metadata flag mismatch");
        assert(out_domain_bad==('''+domain('out_')+'''))
            else $fatal(1,"coefficient static domain flag mismatch");
    end
    assert property (@(posedge clk) disable iff(kill)
        out_valid&&!out_ready |=> kill || (out_valid&&$stable(tuple_checks)))
        else $fatal(1,"coefficient held checks changed");
''')
 inv='cu66_inverse_stream_v91j.sv'
 add(inv,'    input logic signed [15:0] in_value,','    input logic signed [15:0] in_value,\n    input logic in_metadata_bad, in_domain_bad,')
 prefix="    assign input_metadata_bad=in_plane>2||in_tile>=(in_plane==0?13'd5400:13'd1350)||\n        in_qcell!=quant_cell(in_plane,in_tile)||"
 add(inv,prefix,'    assign input_metadata_bad=in_metadata_bad||')
 add(inv,"else if(in_qscale==3||!(in_value[15:11]==5'd0||in_value[15:11]==5'b11111||in_value==16'h0800))input_fault=3;",'else if(in_domain_bad)input_fault=3;')
 add(inv,'`ifndef SYNTHESIS\n','''`ifndef SYNTHESIS
    // Sidebands are valid only for the same owned token as the input tuple.
    always_ff @(posedge clk)if(!kill&&running&&in_valid&&in_ready)begin
        assert(in_metadata_bad==('''+meta('in_')+'''))
            else $fatal(1,"inverse static metadata flag mismatch");
        assert(in_domain_bad==('''+domain('in_')+'''))
            else $fatal(1,"inverse static domain flag mismatch");
    end
''')
 top='cs88_pipeline_v91k.sv'
 add(top,'    logic staged_valid, staged_ready, staged_done;','    logic staged_valid, staged_ready, staged_done;\n    logic staged_metadata_bad, staged_domain_bad;')
 add(top,'        .out_value(staged_value));','        .out_value(staged_value),.out_metadata_bad(staged_metadata_bad),.out_domain_bad(staged_domain_bad));')
 add(top,'        .in_index(staged_index),.in_value(staged_value),','        .in_index(staged_index),.in_value(staged_value),\n        .in_metadata_bad(staged_metadata_bad),.in_domain_bad(staged_domain_bad),')
 recipe=dict(schema='v107-meta-flags-exact-source-recipe-v1',status='PREPARED_NOT_QUALIFIED',public_extra_cycles=0,token_data_bits=132,helper_sha256=sha(helper),production={})
 OUT.mkdir(parents=True,exist_ok=True)
 for n,(p,h) in bases.items():
  s=original[n]
  for e in edits[n]:assert s.count(e['before'])==1,(n,e['before']);s=s.replace(e['before'],e['after'],1)
  (OUT/n).write_text(s);recipe['production'][n]=dict(original=p,original_sha256=h,candidate_sha256=sha(s),edits=edits[n])
 (OUT/'edit-recipe.json').write_text(json.dumps(recipe,indent=2,sort_keys=True)+'\n');print(json.dumps({n:v['candidate_sha256'] for n,v in recipe['production'].items()},indent=2))
if __name__=='__main__':main()
