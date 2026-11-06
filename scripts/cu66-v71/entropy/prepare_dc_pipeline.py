"""Register the measured signed DC sum before range/control fanout."""
from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[3]
src=r/'fpga/experiments/cu66-v71/entropy-headerpipe/cu71_ab38_decoder_headerpipe_v5.sv'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(src)=='8715c9f29c481d8a02bfa3e86eccb57efdea21b3fb1d4cc36110724a85d02893'
out=r/'fpga/experiments/cu66-v71/entropy-dcpipe';out.mkdir(exist_ok=False)
t=src.read_text().replace('module cu71_ab38_decoder_headerpipe_v5 #(','module cu71_ab38_decoder_dcpipe_v6 #(')
anchor='PARAM_VALIDATE, HEADER_SUM, HEADER_INSTALL'
assert t.count(anchor)==1;t=t.replace(anchor,anchor+', DC_CHECK')
anchor='    logic [31:0] lengths [0:3];'
t=t.replace(anchor,anchor+'\n    // Private signed32-bit payload; DC_VALUE always writes before DC_CHECK.\n    logic signed [31:0] dc_prediction;')
old='''                DC_VALUE:begin
                    if((dc_column==0?32'sd0:previous_dc)+unzigzag(rice_value)<-2048 || (dc_column==0?32'sd0:previous_dc)+unzigzag(rice_value)>2048)fail(8'h12);
                    else begin previous_dc<=(dc_column==0?32'sd0:previous_dc)+unzigzag(rice_value);tile[0]<=16'((dc_column==0?32'sd0:previous_dc)+unzigzag(rice_value));state<=DC_COMMIT;end
                end'''
new='''                DC_VALUE:begin
                    dc_prediction<=(dc_column==0?32'sd0:previous_dc)+unzigzag(rice_value);
                    state<=DC_CHECK;
                end
                DC_CHECK:begin
                    if(dc_prediction<-2048 || dc_prediction>2048)fail(8'h12);
                    else begin previous_dc<=dc_prediction;tile[0]<=16'(dc_prediction);state<=DC_COMMIT;end
                end'''
assert t.count(old)==1;t=t.replace(old,new)
p=out/'cu71_ab38_decoder_dcpipe_v6.sv';p.write_text(t,newline='\n')
names=[x.strip()for x in t.split('typedef enum logic [7:0] {',1)[1].split('} state_t;',1)[0].split(',')]
(out/'derivation.json').write_text(json.dumps(dict(status='ISOLATED_DC_SUM_STAGE_NOT_SELECTED',
 parent=src.relative_to(r).as_posix(),parent_sha256=sha(src),source_sha256=sha(p),
 new_states={'DC_CHECK':names.index('DC_CHECK')},added_work_cycles='One per nonraw block, zero for raw mode',
 preserved_math='Same signed32-bit wrapped predecessor + unzigzag sum; same signed bounds [-2048,2048], error12,16bitstore',
 new_payload_reset_bits=0,hardware=False),indent=2)+'\n')
print(sha(p))
