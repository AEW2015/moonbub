#!/usr/bin/env python3
"""Prepare an isolated exact-visible-output IDCT payload reset cut. No RTL run."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'fpga/experiments/cu66-v107-idct-reset/cu66_idct8x8.sv'
OUT=ROOT/'fpga/experiments/cu66-v108-outtile'
HASH='2495e1d5461771cd2d09ce8770ea7818f4f38703bf035bbed4049cdd4226d44f'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert sha(BASE)==HASH
    OUT.mkdir(parents=True,exist_ok=True);text=BASE.read_text();edits=[]
    def edit(before,after):
        nonlocal text
        assert text.count(before)==1,before
        text=text.replace(before,after,1);edits.append(dict(before=before,after=after,expected_occurrences=1))
    edit('    integer lane;\n    integer index;\n','    integer lane;\n')
    marker='    always_ff @(posedge clk) begin\n        if (rst || abort_frame) begin'
    block='''    // OUTTILE_PRIVATE_WORDS_BEGIN: public zero/partial-word visibility is exact.
    logic [63:0] out_written;
    for(genvar out_word=0;out_word<64;out_word=out_word+1)begin: output_words
        localparam integer ROW=out_word/8, COL=out_word%8;
        localparam integer RESULT_LANE=(ROW<4?ROW:7-ROW)+4*(COL%2);
        logic [23:0] payload;
        // This storage has local math-state enables only. A simultaneous kill
        // clears visibility below; a future visible word is replaced completely.
        always_ff @(posedge clk)begin
            if(state==DC_SECOND_ACC)
                payload<=rounded({{2{products[0][37]}},products[0]});
            else if(state==SECOND_ACC && k==7 && group_index==2'(COL/2))begin
                if(ROW<4)payload<=rounded(next_even[RESULT_LANE]+next_odd[RESULT_LANE]);
                else payload<=rounded(next_even[RESULT_LANE]-next_odd[RESULT_LANE]);
            end
        end
        assign out_tile[out_word*24+:24]=out_written[out_word]?payload:24'd0;
`ifndef SYNTHESIS
        assert property (@(posedge clk)disable iff(rst||abort_frame)
            $rose(out_written[out_word]) |-> $past(state==DC_SECOND_ACC ||
                (state==SECOND_ACC&&k==7&&group_index==2'(COL/2))))
            else $fatal(1,"output word exposed without complete replacement");
`endif
    end
    // OUTTILE_PRIVATE_WORDS_END

'''
    edit(marker,block+marker)
    edit("            out_tile<='0;","            out_written<='0;")
    edit('                        out_tile<=0;','                        out_written<=0;')
    edit('''                    for (index=0; index<64; index=index+1)
                        out_tile[index*24 +:24]<=rounded({{2{products[0][37]}},products[0]});''',"                    out_written<='1;")
    edit('''                                out_tile[((lane%4)*8+int'(group_index)*2+lane/4)*24 +:24]
                                    <=rounded(next_even[lane]+next_odd[lane]);
                                out_tile[((7-lane%4)*8+int'(group_index)*2+lane/4)*24 +:24]
                                    <=rounded(next_even[lane]-next_odd[lane]);''','''                                out_written[(lane%4)*8+int'(group_index)*2+lane/4]<=1;
                                out_written[(7-lane%4)*8+int'(group_index)*2+lane/4]<=1;''')
    path=OUT/'cu66_idct8x8.sv';path.write_text(text)
    recipe=dict(schema='v108-idct-output-payload-exact-recipe-v1',status='PREPARED_NOT_RTL_QUALIFIED',original_path=str(BASE.relative_to(ROOT)),original_sha256=HASH,candidate_path=str(path.relative_to(ROOT)),candidate_sha256=sha(path),edits=edits,public_added_cycles=0,public_output_mask='Each of64 public24-bit words is zero unless its written bit is owned; every visible nonzero word has a same-edge complete payload write before first exposure.',private_payload_reset=False,mask_reset_bits=64,old_out_tile_reset_bits=1536)
    reverse=text
    for e in reversed(edits):
        assert reverse.count(e['after'])==1
        reverse=reverse.replace(e['after'],e['before'],1)
    assert reverse==BASE.read_text()
    (OUT/'edit-recipe.json').write_text(json.dumps(recipe,indent=2,sort_keys=True)+'\n')
    print('OUTTILE_PREPARED',sha(path))
if __name__=='__main__':main()
