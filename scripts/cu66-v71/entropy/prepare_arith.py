"""Append arithmetic-decision pipeline states without changing AB38 rounding."""
from pathlib import Path
import hashlib,json,re
r=Path(__file__).resolve().parents[3];p=r/'fpga/experiments/cu66-v71/entropy';parent=p/'cu71_ab38_decoder_cfgpipe.sv';out=p/'cu71_ab38_decoder_arithpipe.sv';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
s=parent.read_text().replace('module cu71_ab38_decoder_cfgpipe #(', 'module cu71_ab38_decoder_arithpipe #(')
s=s.replace('FINISH_BEGIN, FINISH_FIRST, FINISH_SECOND, CFG_MODULO', 'FINISH_BEGIN, FINISH_FIRST, FINISH_SECOND, CFG_MODULO,\n        ARITH_PRODUCT, ARITH_CLAMP, ARITH_BOUNDARY, ARITH_APPLY')
start=s.index('    logic [16:0] interval_span, interval_partition;');end=s.index('    always_comb begin\n        debug_state=',start)
s=s[:start]+'''    // Snapshot one valid decision. No interval/context can mutate until APPLY.
    logic [1:0] arith_stream;
    logic [8:0] arith_address;
    logic [7:0] arith_probability;
    logic [16:0] arith_span,arith_product;
    logic [15:0] arith_low,arith_code,arith_partition,arith_boundary;
    logic [8:0] arith_delta,arith_probability_next;
    wire [8:0] probability_address=({7'd0,stream}*9'd88)+{2'd0,arithmetic_context};
    wire [16:0] interval_span={1'b0,high[stream]}-{1'b0,low[stream]}+17'd1;
    always_comb begin
        if(arith_code>arith_boundary)begin
            arith_delta={1'b0,arith_probability}>>5;
            if(arith_delta==0)arith_delta=1;
            arith_probability_next=({1'b0,arith_probability}>arith_delta)?({1'b0,arith_probability}-arith_delta):9'd1;
        end else begin
            arith_delta=(9'd256-{1'b0,arith_probability})>>5;
            if(arith_delta==0)arith_delta=1;
            arith_probability_next={1'b0,arith_probability}+arith_delta;
            if(arith_probability_next>255)arith_probability_next=255;
        end
    end
'''+s[end:]
s=s.replace('            cfg_mod_dividend<=0;cfg_mod_remainder<=0;cfg_mod_bit<=0;', '''            cfg_mod_dividend<=0;cfg_mod_remainder<=0;cfg_mod_bit<=0;
            arith_stream<=0;arith_address<=0;arith_probability<=0;arith_span<=0;arith_product<=0;
            arith_low<=0;arith_code<=0;arith_partition<=0;arith_boundary<=0;''')
start=s.index('                ARITH_DECIDE:begin');end=s.index('                ARITH_RENORM:begin',start)
s=s[:start]+'''                ARITH_DECIDE:begin
                    if(arithmetic_context>=88||low[stream]>=high[stream]||code[stream]<low[stream]||code[stream]>high[stream])fail(8'h21);
                    else begin
                        arith_stream<=stream;arith_address<=probability_address;
                        arith_probability<=probabilities[probability_address];
                        arith_span<=interval_span;arith_low<=low[stream];arith_code<=code[stream];
                        state<=ARITH_PRODUCT;
                    end
                end
                ARITH_PRODUCT:begin
                    // Exact original25-bit product, floor divide by256.
                    arith_product<=17'((25'(arith_span)*25'(arith_probability))>>8);
                    state<=ARITH_CLAMP;
                end
                ARITH_CLAMP:begin
                    // Valid captured interval has2<=span<=65536. The clamped
                    // partition is therefore1..65535 and fits16bits exactly.
                    if(arith_product==0)arith_partition<=16'd1;
                    else if(arith_product>=arith_span)arith_partition<=arith_span[15:0]-16'd1;
                    else arith_partition<=arith_product[15:0];
                    state<=ARITH_BOUNDARY;
                end
                ARITH_BOUNDARY:begin
                    arith_boundary<=arith_low+arith_partition-16'd1;
                    state<=ARITH_APPLY;
                end
                ARITH_APPLY:begin
                    decoded_decisions<=decoded_decisions+1;
                    arithmetic_bit<=(arith_code>arith_boundary);
                    probabilities[arith_address]<=arith_probability_next[7:0];
                    if(arith_code>arith_boundary)low[arith_stream]<=arith_boundary+16'd1;
                    else high[arith_stream]<=arith_boundary;
                    state<=ARITH_RENORM;
                end
'''+s[end:]
out.write_text(s,newline='\n')
tokens=[x.strip()for x in re.search(r'typedef enum logic \[7:0\] \{(.*?)\}',s,re.S)[1].split(',')]
(p/'arith-derivation.json').write_text(json.dumps({'parent':parent.relative_to(r).as_posix(),'parent_sha256':sha(parent),'candidate':out.relative_to(r).as_posix(),'candidate_sha256':sha(out),'new_states':{n:tokens.index(n)for n in ['ARITH_PRODUCT','ARITH_CLAMP','ARITH_BOUNDARY','ARITH_APPLY']},'scope':'Fourextraarithmeticdecisioncycles; identicalfloor/clamp/boundary/probadaptation. Capturedstream/address/operands; outerabortdominatesallprobabilitywrites. OlddebugstateIDsunchanged.','hardware':False},indent=2)+'\n')
print('PREPARED_ARITHMETIC_DECISION_MICROPIPE',sha(out))
