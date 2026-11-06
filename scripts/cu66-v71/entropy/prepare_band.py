"""Preserve arithmetic v1; pipeline measured BAND_CHECK multiply/compare cone."""
from pathlib import Path
import hashlib,json,re
r=Path(__file__).resolve().parents[3];p=r/'fpga/experiments/cu66-v71/entropy';parent=p/'cu71_ab38_decoder_arithpipe.sv';out=p/'cu71_ab38_decoder_arithpipe_v2.sv';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
s=parent.read_text().replace('module cu71_ab38_decoder_arithpipe #(', 'module cu71_ab38_decoder_arithpipe_v2 #(')
s=s.replace('ARITH_PRODUCT, ARITH_CLAMP, ARITH_BOUNDARY, ARITH_APPLY', 'ARITH_PRODUCT, ARITH_CLAMP, ARITH_BOUNDARY, ARITH_APPLY,\n        BAND_LIMIT, BAND_TEST, BAND_POSITION, BAND_STORE')
s=s.replace('    logic [1:0] band;', '''    logic [1:0] band;
    logic [1:0] band_snapshot;
    logic [5:0] band_width_snapshot,band_coefficient;
    logic [22:0] band_base,band_limit;''')
s=s.replace('            band<=0;raw_coefficient<=0;', '            band_snapshot<=0;band_width_snapshot<=0;band_coefficient<=0;band_base<=0;band_limit<=0;\n            band<=0;raw_coefficient<=0;')
start=s.index('                BAND_CHECK:begin');end=s.index('                RAW_COEF_LOW:',start)
s=s[:start]+'''                BAND_CHECK:begin
                    band_snapshot<=band;band_width_snapshot<=band_width(band);
                    // Full17x6product fits23bits; avoids(block+1)->DSP->compare.
                    band_base<=23'(23'(block_number)*23'(band_width(band)));
                    state<=BAND_LIMIT;
                end
                BAND_LIMIT:begin
                    band_limit<=band_base+{17'd0,band_width_snapshot};state<=BAND_TEST;
                end
                BAND_TEST:begin
                    if(pending_index[band_snapshot]<$signed({9'd0,band_limit}))begin
                        if(pending_index[band_snapshot]<$signed({9'd0,band_base}))fail(8'h13);
                        else state<=BAND_POSITION;
                    end else if(band_snapshot==2)begin
                        if(block_number+1==nblocks && (pending_left[0]!=0||pending_left[1]!=0||pending_left[2]!=0||stream_finished!=4'b1111))fail(8'h14);
                        else state<=OUTPUT_TILE;
                    end else begin band<=band_snapshot+1'b1;state<=BAND_CHECK;end
                end
                BAND_POSITION:begin
                    // Proven by BAND_TEST:0<=index-base<width<=43. Low6bit
                    // subtraction therefore preserves the exact coefficient.
                    band_coefficient<=band_low(band_snapshot)+(pending_index[band_snapshot][5:0]-band_base[5:0]);
                    state<=BAND_STORE;
                end
                BAND_STORE:begin
                    tile[zig_address(band_coefficient)]<=pending_value[band_snapshot];
                    stream<=band_snapshot+1;state<=EVENT_START;
                end
'''+s[end:]
out.write_text(s,newline='\n');tokens=[x.strip()for x in re.search(r'typedef enum logic \[7:0\] \{(.*?)\}',s,re.S)[1].split(',')]
names=['ARITH_PRODUCT','ARITH_CLAMP','ARITH_BOUNDARY','ARITH_APPLY','BAND_LIMIT','BAND_TEST','BAND_POSITION','BAND_STORE']
(p/'arith-v2-derivation.json').write_text(json.dumps({'parent':parent.relative_to(r).as_posix(),'parent_sha256':sha(parent),'candidate':out.relative_to(r).as_posix(),'candidate_sha256':sha(out),'new_states':{n:tokens.index(n)for n in names},'scope':'Arithmeticpipelineplusregisteredbandbase/limit/position. Full17x6product23bits, exactsigned32comparison, guardedoffset0..42. ExistingdebugIDsretained; abortdominatescoefficient/probabilitystores.','hardware':False},indent=2)+'\n');print('PREPARED_BAND_RANGE_PIPELINE',sha(out))
