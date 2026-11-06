"""Isolate AB38 header sums; preserve modular widths and rejection priority."""
from pathlib import Path
import hashlib,json,re
r=Path(__file__).resolve().parents[3]
src=r/'fpga/experiments/cu66-v71/entropy/cu71_ab38_decoder_arithpipe_v4.sv'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(src)=='93b79e7d074aa606b4461d7fcd73069e323739012d66963fa1a0d5fa6633763b'
out=r/'fpga/experiments/cu66-v71/entropy-headerpipe';out.mkdir(exist_ok=False)
t=src.read_text().replace('module cu71_ab38_decoder_arithpipe_v4 #(','module cu71_ab38_decoder_headerpipe_v5 #(')
anchor='        PARAM_BOUNDS, PARAM_SIZE, PARAM_VALIDATE'
assert t.count(anchor)==1;t=t.replace(anchor,anchor+', HEADER_SUM, HEADER_INSTALL')
anchor='    logic [31:0] lengths [0:3];'
t=t.replace(anchor,anchor+'''
    // Private payload registers: all assigned before HEADER_INSTALL, no reset.
    logic [31:0] header_pair01,header_pair23,header_total;
    logic [31:0] header_prefix1,header_prefix2,header_prefix3;''')
old='''                    else if(32'd46+h32(14)+h32(18)+h32(22)+h32(26)!={16'd0,packet_bytes})fail(8'h04);
                    else begin'''
new='''                    else begin
                        header_pair01<=h32(14)+h32(18);
                        header_pair23<=h32(22)+h32(26);'''
assert t.count(old)==1;t=t.replace(old,new)
old='''                        stream_chunk[0]<=42;stream_chunk[1]<=42+h32(14);stream_chunk[2]<=42+h32(14)+h32(18);stream_chunk[3]<=42+h32(14)+h32(18)+h32(22);
                        raw_mode<=header[5][0];stream<=0;state<=STREAM_BEGIN;
                    end
                end
                STREAM_BEGIN:begin'''
new='''                        state<=HEADER_SUM;
                    end
                end
                HEADER_SUM:begin
                    // All assignments retain the original unsigned32-bit wrap.
                    header_total<=32'd46+header_pair01+header_pair23;
                    header_prefix1<=32'd42+lengths[0];
                    header_prefix2<=32'd42+header_pair01;
                    header_prefix3<=32'd42+header_pair01+lengths[2];
                    state<=HEADER_INSTALL;
                end
                HEADER_INSTALL:begin
                    if(header_total!={16'd0,packet_bytes})fail(8'h04);
                    else begin
                        stream_chunk[0]<=42;stream_chunk[1]<=header_prefix1;
                        stream_chunk[2]<=header_prefix2;stream_chunk[3]<=header_prefix3;
                        raw_mode<=header[5][0];stream<=0;state<=STREAM_BEGIN;
                    end
                end
                STREAM_BEGIN:begin'''
assert t.count(old)==1;t=t.replace(old,new)
p=out/'cu71_ab38_decoder_headerpipe_v5.sv';p.write_text(t,newline='\n')
enum=t.split('typedef enum logic [7:0] {',1)[1].split('} state_t;',1)[0]
names=[v.strip()for v in enum.split(',')]
states={n:names.index(n)for n in ['HEADER_SUM','HEADER_INSTALL']}
(out/'derivation.json').write_text(json.dumps(dict(status='ISOLATED_HEADER_SUM_PRIVATE_STAGES_NOT_SELECTED',
 parent=src.relative_to(r).as_posix(),parent_sha256=sha(src),source_sha256=sha(p),new_states=states,
 added_header_work_cycles=2,preserved_width='Unsigned32-bit modulo length/prefix sums; packet bytes zero-extended16bit',
 error_priority='CRC02 before fixed header03 before length04; arithmetic/stream checks unchanged',
 private_early_writes='lengths/events/limits captured before length04 rejection; no coefficient/probability operation before validation',
 new_payload_reset_bits=0,hardware=False),indent=2)+'\n')
print(json.dumps(dict(source_sha256=sha(p),new_states=states)))
