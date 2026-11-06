from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[3];s=r/'fpga/experiments/cu66-v71/packet-prefix-v002/cu71_packet_presum.sv';d=r/'fpga/experiments/cu66-v71/packet-prefix-v003';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(s)=='9ab9f4abd82d130cd627a952f78efe841a0fc3505a832e40348f64d82d3ad7e2'
t=s.read_text().replace('module cu71_packet_presum (','module cu71_packet_hudsum (')
t=t.replace('INNER_SUM_MERGE, INNER_SUM_TOTAL','INNER_SUM_MERGE, INNER_SUM_TOTAL, HUD_SUM_PAIRS, HUD_SUM_MERGE, HUD_SUM_TOTAL')
t=t.replace('logic [31:0] inner_sum0,inner_sum1,inner_sum2,inner_sum01,inner_length_total;','logic [31:0] inner_sum0,inner_sum1,inner_sum2,inner_sum01,inner_length_total;\n    logic [31:0] hud_sum0,hud_sum1,hud_sum01,hud_length_total;')
t=t.replace('inner_sum01<=0;inner_length_total<=0;','inner_sum01<=0;inner_length_total<=0;\n            hud_sum0<=0;hud_sum1<=0;hud_sum01<=0;hud_length_total<=0;')
old="hud32(54)+hud32(58)+hud32(62)+hud32(66)+32'd110!=32'(metadata_hud_bytes)";assert t.count(old)==1;t=t.replace(old,"hud_length_total!=32'(metadata_hud_bytes)")
old="else if(outer_validated&&(scan_addr==metadata_hud_addr+16'd105)) state<=CHECK_HUD;";assert t.count(old)==1;t=t.replace(old,"else if(outer_validated&&(scan_addr==metadata_hud_addr+16'd105)) state<=HUD_SUM_PAIRS;")
t=t.replace('                CHECK_HUD: begin','''                // Last HUD header byte is captured before the first pair stage.
                // Unchecked sums are private; CHECK_HUD retains code11-before12.
                HUD_SUM_PAIRS: begin
                    hud_sum0<=hud32(54)+hud32(58);
                    hud_sum1<=hud32(62)+hud32(66);
                    state<=HUD_SUM_MERGE;
                end
                HUD_SUM_MERGE: begin
                    hud_sum01<=hud_sum0+hud_sum1;
                    state<=HUD_SUM_TOTAL;
                end
                HUD_SUM_TOTAL: begin
                    hud_length_total<=hud_sum01+32'd110;
                    state<=CHECK_HUD;
                end
                CHECK_HUD: begin''')
p=d/'cu71_packet_hudsum.sv';p.write_text(t,newline='\n');(d/'derivation.json').write_text(json.dumps(dict(parent=str(s.relative_to(r)),parent_sha256=sha(s),output_sha256=sha(p),change='Three HUD length sum stages; unsigned modulo32, code11-before12, bounds/types/rectangles unchanged; +8 successful clocks versusv69'),indent=2)+'\n');print(p)
