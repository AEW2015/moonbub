"""Isolated dequant classification stage for measured input-to-payload cone."""
from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[2]
src=r/'fpga/experiments/cu66-v71/inverse-reset/cu71_dequant_resetlight.sv'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(src)=='e2abdd9ecfe74612ed1f4f495be5d760454aa7431d9c23e19fe919d02d8a891a'
out=r/'fpga/experiments/cu66-v71/dequant-validpipe';out.mkdir(exist_ok=False)
t=src.read_text().replace('module cu71_dequant_resetlight (','module cu71_dequant_validpipe (')
t=t.replace('{IDLE, RUN, HOLD_TILE} state_t;','{IDLE, RUN, HOLD_TILE, VALIDATE_INPUT} state_t;')
old='''        input_bad=(in_scale_code==3);
        for(integer i=0;i<64;i=i+1)
            if($signed(in_coefficients[i*16 +:16]) < -16'sd2048 ||
               $signed(in_coefficients[i*16 +:16]) > 16'sd2048)input_bad=1;
'''
assert t.count(old)==1;t=t.replace(old,'        input_bad=(scale_code==3)||(|bad_group);\n')
t=t.replace('assign fast_result=input_bad || in_coefficients==0;','assign fast_result=input_bad || (&zero_group);')
anchor='    logic input_bad, fast_result;'
assert t.count(anchor)==1
t=t.replace(anchor,anchor+'''
    // Captured only with accepted metadata, used only in VALIDATE_INPUT.
    // These private classification payload bits need no bulk reset.
    logic [7:0] bad_group,zero_group;
    function automatic logic bad_eight(input logic [127:0] tile);
        begin
            bad_eight=0;
            for(integer c=0;c<8;c=c+1)
                if($signed(tile[c*16 +:16])< -16'sd2048 ||
                   $signed(tile[c*16 +:16])>16'sd2048)bad_eight=1;
        end
    endfunction
    for(genvar g=0;g<8;g=g+1)begin:g_classify
        always_ff @(posedge clk)if(in_valid && in_ready)begin
            bad_group[g]<=bad_eight(in_coefficients[g*128 +:128]);
            zero_group[g]<=in_coefficients[g*128 +:128]==0;
        end
    end''')
t=t.replace('out_id<=in_id;out_error<=input_bad;issue_group<=0;issued_all<=0;',
            "out_id<=in_id;out_error<=0;issue_group<=0;issued_all<=0;")
old='''                    if(fast_result)state<=HOLD_TILE;else state<=RUN;
                end
            end
            RUN:begin'''
new='''                    state<=VALIDATE_INPUT;
                end
            end
            VALIDATE_INPUT:begin
                out_error<=input_bad;
                if(fast_result)state<=HOLD_TILE;else state<=RUN;
            end
            RUN:begin'''
assert t.count(old)==1;t=t.replace(old,new)
old='state==IDLE && in_valid && in_ready && fast_result'
assert t.count(old)==1;t=t.replace(old,'state==VALIDATE_INPUT && fast_result')
t=t.replace('// Same one-outstanding ready/valid contract; nonzero valid tiles take 10\n// work clocks instead of 8. Invalid and zero tiles retain the fast path.',
'''// Same one-outstanding contract with one extra input-classification work clock.
// Only valid output payload/ID/error is a result; invalid-time error may differ.''')
p=out/'cu71_dequant_validpipe.sv';p.write_text(t,newline='\n')
(out/'derivation.json').write_text(json.dumps(dict(parent=src.relative_to(r).as_posix(),
 parent_sha256=sha(src),source_sha256=sha(p),added_work_cycles=1,
 new_payload_reset_bits=0,classification_bits=16,
 status='ISOLATED_UNQUALIFIED_INPUT_VALIDATION_PIPELINE',hardware=False),indent=2)+'\n')
print(sha(p))
