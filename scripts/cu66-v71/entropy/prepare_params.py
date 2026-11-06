"""Snapshot and pipeline exact 32-bit parameter length arithmetic."""
from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[3];p=r/'fpga/experiments/cu66-v71/entropy';parent=p/'cu71_ab38_decoder_arithpipe_v3.sv';out=p/'cu71_ab38_decoder_arithpipe_v4.sv';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
s=parent.read_text().replace('module cu71_ab38_decoder_arithpipe_v3 #(', 'module cu71_ab38_decoder_arithpipe_v4 #(')
s=s.replace('BAND_LIMIT, BAND_TEST, BAND_POSITION, BAND_STORE\n','BAND_LIMIT, BAND_TEST, BAND_POSITION, BAND_STORE,\n        PARAM_BOUNDS, PARAM_SIZE, PARAM_VALIDATE\n')
s=s.replace('    logic [2:0] parameter_byte;', '''    logic [2:0] parameter_byte;
    logic [1:0] param_stream;
    logic [31:0] param_bits,param_length,param_chunk,param_count,param_capacity,param_rounded,param_encoded;
    logic [22:0] param_limit;
    logic [7:0] param_k0,param_k1;''')
start=s.index('                PARAM_CHECK:begin');end=s.index('                PAD_READ:',start)
s=s[:start]+'''                PARAM_CHECK:begin
                    param_stream<=stream;param_bits<=stream_bits[stream];param_length<=lengths[stream];
                    param_chunk<=stream_chunk[stream];param_k0<=stream_k0[stream];param_k1<=stream_k1[stream];
                    param_count<=event_counts[2'(stream-2'd1)];param_limit<=event_limits[2'(stream-2'd1)];
                    state<=PARAM_BOUNDS;
                end
                PARAM_BOUNDS:begin
                    // Preserve original32-bit wrap before shifting/dividing.
                    param_capacity<=32'd8*(param_length-32'd6);
                    param_rounded<=param_bits+32'd7;state<=PARAM_SIZE;
                end
                PARAM_SIZE:begin
                    param_encoded<=32'd6+(param_rounded>>3);state<=PARAM_VALIDATE;
                end
                PARAM_VALIDATE:begin
                    if(param_bits<18 || param_bits>param_capacity || param_encoded!=param_length)fail(8'h08);
                    else if(param_stream==0 && (param_k0>13||param_k1!=255))fail(8'h09);
                    else if(param_stream!=0 && (param_k0>19||param_k1>11||param_count>{9'd0,param_limit}))fail(8'h0a);
                    else begin stream_base[param_stream]<=param_chunk+6;state<=PAD_READ;end
                end
'''+s[end:]
out.write_text(s,newline='\n');m=json.loads((p/'arith-v3-derivation.json').read_text());m['new_states'].update(PARAM_BOUNDS=51,PARAM_SIZE=52,PARAM_VALIDATE=53)
(p/'arith-v4-derivation.json').write_text(json.dumps({'parent':parent.relative_to(r).as_posix(),'parent_sha256':sha(parent),'candidate':out.relative_to(r).as_posix(),'candidate_sha256':sha(out),'new_states':m['new_states'],'scope':'Exact32bitwrappedparameterboundsandceilbytecount split acrosssnapshot,rounded,size,validation;errorpriorityretained.','hardware':False},indent=2)+'\n');print('PREPARED_PARAMETER_PIPELINE',sha(out))
