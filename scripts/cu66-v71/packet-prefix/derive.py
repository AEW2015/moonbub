from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[3]
s=r/'fpga/experiments/cu66-v69/packet/cu66_packet_control.sv'
d=r/'fpga/experiments/cu66-v71/packet-prefix-v001'
assert hashlib.sha256(s.read_bytes()).hexdigest()=='20d761a514073e8e5212eb70861f843441bc8d8f32b81bf7f02925cd202ae5a2'
t=s.read_text().replace('module cu66_packet_control (','module cu71_packet_prefix (')
t=t.replace('WAIT_COMMIT, DRAIN\n','WAIT_COMMIT, DRAIN, PREFIX_STARTS, PREFIX_ADDRESSES\n')
t=t.replace('logic [15:0] vector_start, vector_end;','logic [15:0] vector_start, vector_end;\n    logic [15:0] prefix0, prefix_yu, prefix_y;')
t=t.replace('inner_bytes<=0;vector_start<=0;vector_end<=0;','inner_bytes<=0;vector_start<=0;vector_end<=0;\n            prefix0<=0;prefix_yu<=0;prefix_y<=0;')
start=t.index('                        metadata_block_size<=inner_header[22];vector_start')
end=t.index('                CHECK_HUD: begin',start)
t=t[:start]+'''                        metadata_block_size<=inner_header[22];
                        // Preserve the original 16-bit modular prefix domain.
                        // Only checked, immutable header fields reach these stages.
                        prefix0<=16'd474+16'(inner32(44));
                        prefix_yu<=16'(inner32(48))+16'(inner32(52));
                        prefix_y<=16'(inner32(48));
                        for(i=0;i<3;i=i+1) begin
                            metadata_plane_bytes[i]<=16'(inner32(48+4*i))-16'd1;
                        end
                        state<=PREFIX_STARTS;
                    end
                end
                PREFIX_STARTS: begin
                    vector_start<=16'd474;vector_end<=prefix0;
                    plane_start[0]<=prefix0;
                    plane_start[1]<=prefix0+prefix_y;
                    plane_start[2]<=prefix0+prefix_yu;
                    state<=PREFIX_ADDRESSES;
                end
                PREFIX_ADDRESSES: begin
                    for(i=0;i<3;i=i+1) metadata_plane_addr[i]<=plane_start[i]+16'd1;
                    inner_validated<=1;state<=READ_REQUEST;
                end
'''+t[end:]
assert t.count('PREFIX_STARTS')==3 and t.count('PREFIX_ADDRESSES')==3
p=d/'cu71_packet_prefix.sv';p.write_text(t,newline='\n')
(d/'derivation.json').write_text(json.dumps(dict(parent=str(s.relative_to(r)),parent_sha256=hashlib.sha256(s.read_bytes()).hexdigest(),output_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),change='Two checked-prefix stages; original validation, priorities, widths, reset/abort/IO preserved; +2 successful parse clocks'),indent=2)+'\n')
print(p)
