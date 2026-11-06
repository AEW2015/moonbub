"""Replace the measured 17-bit variable modulo chain with bounded microsteps."""
from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[2];p=r/'fpga/experiments/cu66-v69/entropy/cu66_ab38_decoder.sv'
d=r/'fpga/experiments/cu66-v71/entropy';d.mkdir(parents=True,exist_ok=True);f=d/'cu71_ab38_decoder_cfgpipe.sv';assert not f.exists()
s=p.read_text().replace('module cu66_ab38_decoder #(', 'module cu71_ab38_decoder_cfgpipe #(',1)
s=s.replace('        FINISH_BEGIN, FINISH_FIRST, FINISH_SECOND\n', '        FINISH_BEGIN, FINISH_FIRST, FINISH_SECOND, CFG_MODULO\n',1)
anchor='    logic [15:0] packet_bytes;';assert s.count(anchor)==1
s=s.replace(anchor,'''    // Accepted metadata is immutable throughout17 restoring-remainder steps.
    logic [16:0] cfg_mod_dividend;
    logic [7:0] cfg_mod_remainder;
    logic [4:0] cfg_mod_bit;
    wire [8:0] cfg_mod_shift={cfg_mod_remainder,cfg_mod_dividend[16]};
    wire [8:0] cfg_mod_next=cfg_mod_shift>=blocks_w ? cfg_mod_shift-blocks_w : cfg_mod_shift;
'''+anchor)
old='                       (cfg_blocks_w!=0 && cfg_blocks%{8\'d0,cfg_blocks_w}!=0)||\n';assert s.count(old)==1;s=s.replace(old,'')
old='            packet_bytes<=0;nblocks<=0;blocks_w<=0;block_number<=0;dc_column<=0;';assert s.count(old)==1
s=s.replace(old,old+'\n            cfg_mod_dividend<=0;cfg_mod_remainder<=0;cfg_mod_bit<=0;')
old='                        block_number<=0;dc_column<=0;previous_dc<=0;byte_cache_valid<=0;stream_finished<=0;initial_events<=1;state<=CRC_READ;';assert s.count(old)==1
s=s.replace(old,'''                        block_number<=0;dc_column<=0;previous_dc<=0;byte_cache_valid<=0;stream_finished<=0;initial_events<=1;
                        cfg_mod_dividend<=cfg_blocks;cfg_mod_remainder<=0;cfg_mod_bit<=16;state<=CFG_MODULO;''')
anchor='                READ_REQUEST:if(rd_req_ready)begin rd_req_valid<=0;state<=READ_RESPONSE;end';assert s.count(anchor)==1
s=s.replace(anchor,'''                CFG_MODULO:begin
                    cfg_mod_remainder<=cfg_mod_next[7:0];cfg_mod_dividend<=cfg_mod_dividend<<1;
                    if(cfg_mod_bit==0)begin
                        if(cfg_mod_next!=0)fail(8'h01);else state<=CRC_READ;
                    end else cfg_mod_bit<=cfg_mod_bit-1'b1;
                end
'''+anchor)
assert '%' not in s,'Only expected modulo operation should have existed'
f.write_text(s,newline='\n');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(d/'derivation.json').write_text(json.dumps(dict(parent=str(p.relative_to(r)),parent_sha256=sha(p),candidate_sha256=sha(f),
 change='Cfg-only geometry modulo uses17 bounded microcycles; no accepted packet read before successful check. Other state codes unchanged; CFG_MODULO appended.',
 evidence_reason='Exact-target path dispatch->entropy/DSPenable had70logic levels including48CARRY4 and-23.499ns synthesis slack; no clock/constraint relaxation.',
 status='FUNCTIONAL_AND_TARGET_TIMING_PENDING'),indent=2)+'\n');print(f)
