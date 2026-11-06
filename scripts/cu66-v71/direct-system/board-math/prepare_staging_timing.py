"""Isolated registered-upload-capacity staging/control candidate; no builds."""
from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[4];d=r/'fpga/experiments/cu66-v71/staging-timing';assert not d.exists();d.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=r/'fpga/experiments/cu66-v71/system/cu71_packet_staging.sv';old=p.read_text();new=old.replace('module cu71_packet_staging #(','module cu71_packet_staging_credit #(')
new=new.replace('output reg [31:0] packet_bytes,written_bytes,output wire [31:0] actual_crc,','output reg [31:0] packet_bytes,written_bytes,output wire [31:0] actual_crc,\n output reg [2:0] upload_capacity,')
new=new.replace('reg [2:0] held_count;','reg [2:0] held_count;\n reg [31:0] remaining_bytes;\n reg within_packet;')
new=new.replace('expected_crc<=0;held_word<=0;held_count<=0;','expected_crc<=0;held_word<=0;held_count<=0;remaining_bytes<=0;upload_capacity<=0;within_packet<=1;')
new=new.replace("written_bytes<=0;crc<=32'hffffffff;\n    end else", "written_bytes<=0;crc<=32'hffffffff;remaining_bytes<=begin_bytes;within_packet<=1;\n     upload_capacity<=begin_bytes>=4 ? 3'd4 : begin_bytes[2:0];\n    end else")
assert "remaining_bytes<=begin_bytes" in new
new=new.replace("{1'b0,written_bytes}+upload_count<={1'b0,packet_bytes}",'within_packet&&upload_count<=upload_capacity')
new=new.replace("held_count<=held_count-1'b1;written_bytes<=written_bytes+1'b1;","held_count<=held_count-1'b1;written_bytes<=written_bytes+1'b1;\n    remaining_bytes<=remaining_bytes-1'b1;\n    within_packet<=written_bytes==32'hffffffff || (within_packet&&remaining_bytes!=0);\n    upload_capacity<=remaining_bytes>4 || remaining_bytes==0 ? 3'd4 : remaining_bytes[2:0]-3'd1;")
(d/'cu71_packet_staging_credit.sv').write_text(new,newline='\n')
parents={str(p.relative_to(r)):sha(p)}
for profile in ['cu71','dy71']:
 p=r/f'fpga/experiments/cu66-v71/bus-split/{profile}_local_control_split.sv';s=p.read_text();parents[str(p.relative_to(r))]=sha(p)
 s=s.replace(f'module {profile}_local_control_split(',f'module {profile}_local_control_credit(')
 s=s.replace(" wire [31:0] remaining=packet_bytes-written_bytes;\n wire [2:0] upload_bytes=remaining>=4?3'd4:remaining[2:0];",' wire [2:0] upload_bytes;')
 assert 'remaining=packet_bytes-written_bytes'not in s
 s=s.replace('cu71_packet_staging staging(','cu71_packet_staging_credit staging(').replace('.upload_count(upload_bytes),','.upload_count(upload_bytes),.upload_capacity(upload_bytes),')
 (d/f'{profile}_local_control_credit.sv').write_text(s,newline='\n')
files={f.relative_to(r).as_posix():sha(f)for f in d.glob('*.sv')}
(d/'derivation.json').write_text(json.dumps({'parents':parents,'candidate_sources':files,'interface_change':'Versioned stager adds upload_capacity[2:0]; versioned split CSRs retain exact external port signature','invariant':'remaining_bytes == packet_bytes-written_bytes; upload_capacity == min(remaining_bytes,4)','counter_priority':'reset > accepted BEGIN; actual byte drain assignment has original later priority; mutually exclusive legal state guards retained','stale_capacity':'Held across discard/release/seal/activate exactly like packet_bytes/written_bytes; only gated by original upload_ready','MAX_BYTES':'Original parameter and full32-bit begin validation preserved, no narrowed capacity bound assumption','Vivado_started':False},indent=2)+'\n')
print(d)
