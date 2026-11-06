"""Isolate the measured wide input-classification path with one valid stage."""
from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[2]
src=r/'fpga/experiments/cu66-v71/inverse-index/cu71_idct_indexed.sv'
out=r/'fpga/experiments/cu66-v71/inverse-validpipe'
out.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(src)=='fe1d7f3684ac7e8c15bc80e5a9b4734863103510faa2087d75b00a6b94d2d41d'
t=src.read_text().replace('module cu71_idct_indexed (','module cu71_idct_validpipe (')
t=t.replace('DC_SECOND_ACC, OUTPUT_TILE} state_t;','DC_SECOND_ACC, OUTPUT_TILE, VALIDATE_INPUT} state_t;')
t=t.replace('    logic input_bad;', '''    // Classification payload is overwritten on every accepted input before
    // VALIDATE_INPUT uses it. No bulk or startup payload reset is required.
    logic [7:0] bad_group, zero_group, ac_zero_group;
    function automatic logic bad_eight(input logic [159:0] tile);
        begin
            bad_eight=1'b0;
            for(integer c=0;c<8;c=c+1)
                if($signed(tile[c*20 +:20])>20'sd522240 ||
                   $signed(tile[c*20 +:20])< -20'sd522240)bad_eight=1'b1;
        end
    endfunction
    for(genvar g=0;g<8;g=g+1)begin:g_classify
        always_ff @(posedge clk)if(in_valid && in_ready)begin
            bad_group[g]<=bad_eight(in_tile[g*160 +:160]);
            zero_group[g]<=in_tile[g*160 +:160]==0;
            if(g==0)ac_zero_group[g]<=in_tile[159:20]==0;
            else ac_zero_group[g]<=in_tile[g*160 +:160]==0;
        end
    end''')
old='''        input_bad=1'b0;
        for (integer n=0; n<64; n=n+1)
            if ($signed(in_tile[n*20 +:20]) > 20'sd522240 ||
                $signed(in_tile[n*20 +:20]) < -20'sd522240)
                input_bad=1'b1;
'''
assert t.count(old)==1
t=t.replace(old,'')
t=t.replace('                    out_error<=input_bad;','                    out_error<=1\'b0;')
old='''                    if (input_bad || in_tile==0) begin
                        for(index=0;index<64;index=index+1)result_word[index]<=0;
                        state<=OUTPUT_TILE;
                    end else if (in_tile[1279:20]==0) state<=DC_FIRST_MUL;
                    else state<=FIRST_MUL;
                end'''
new='''                    state<=VALIDATE_INPUT;
                end
                VALIDATE_INPUT: begin
                    out_error<=|bad_group;
                    if ((|bad_group) || (&zero_group)) begin
                        for(index=0;index<64;index=index+1)result_word[index]<=0;
                        state<=OUTPUT_TILE;
                    end else if (&ac_zero_group) state<=DC_FIRST_MUL;
                    else state<=FIRST_MUL;
                end'''
assert t.count(old)==1
t=t.replace(old,new)
p=out/'cu71_idct_validpipe.sv';p.write_text(t,newline='\n')
(out/'derivation.json').write_text(json.dumps(dict(parent=str(src.relative_to(r)),parent_sha256=sha(src),
 source_sha256=sha(p),status='UNQUALIFIED_ISOLATED_INPUT_CLASSIFICATION_PIPELINE',
 added_work_cycles_per_accepted_tile=1,valid_outputs='Must match parent with one-clock delayed accepted input',
 invalid_out_error='May change outside out_valid; qualified output semantics retained',
 classification_bits=24,new_payload_reset_bits=0,hardware=False),indent=2)+'\n')
print(sha(p))
