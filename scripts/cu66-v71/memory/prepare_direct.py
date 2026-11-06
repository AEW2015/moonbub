"""Canonical tile-major physical storage, unchanged logical tile/identity API."""
from pathlib import Path
import hashlib,json,re
r=Path(__file__).resolve().parents[3];p=r/'fpga/experiments/cu66-v71/memory';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
tile=(p/'cu71_tile_memory.sv').read_text().replace('module cu71_tile_memory (','module cu71_tile_memory_direct (')
tile=tile.replace('input logic [15:0] word_rsp_data,input logic word_rsp_error','input logic [15:0] word_rsp_data,input logic[127:0]word_rsp_burst_data,input logic word_rsp_error')
tile=tile.replace("word_req_addr=tile_base+24'(int'(word_index[4:2])*int'(pitch))+24'(word_index[1:0]);", "word_req_addr=tile_base+24'(word_index);")
tile=tile.replace("word_req_burst_data=128'(pixels[int'(word_index[4:2])*64+:64])<<(word_req_addr[2:0]*16);", "word_req_burst_data=pixels[int'(word_index)*16+:128];")
tile=tile.replace("word_req_burst_mask=16'hffff^(16'h00ff<<(word_req_addr[2:0]*2));", "word_req_burst_mask=16'h0000;")
start=tile.index('     if(chosen_plane==0)begin');end=tile.index('     state<=bad_metadata?RESULT:ISSUE;',start)
tile=tile[:start]+'''     // Tile-major physical storage: each512-bit tile is32alignedwords.
     tile_base<=canonical_base(chosen_bank)+(chosen_plane==0?24'd0:chosen_plane==1?24'd172800:24'd216000)+(24'(chosen_index)<<5);
'''+tile[end:]
tile=tile.replace("if(!writing)pixels[int'(word_index)*16+:16]<=word_rsp_data;", "if(!writing)pixels[int'(word_index)*16+:128]<=word_rsp_burst_data;")
tile=tile.replace('if(word_index==(writing?28:31))', 'if(word_index==24)').replace("word_index<=word_index+(writing?5'd4:5'd1);", "word_index<=word_index+5'd8;")
assert 'word_index[4:2]'not in tile and 'word_rsp_burst_data;'in tile
(p/'cu71_tile_memory_direct.sv').write_text(tile,newline='\n')

s=(p/'cu71_word_bridge_burst.sv').read_text().replace('module cu71_word_bridge_burst #(', 'module cu71_word_bridge_direct #(')
s=s.replace('output logic[15:0]p0_rsp_data,output logic p0_rsp_error,', 'output logic[15:0]p0_rsp_data,output logic[127:0]p0_rsp_burst_data,output logic p0_rsp_error,')
s=s.replace('  p0_rsp_data=response_data[0][15:0];', '  p0_rsp_burst_data=response_data[0];p0_rsp_data=response_data[0][15:0];')
s=s.replace('selected<2&&!writing[selected]', 'selected==1&&!writing[selected]')
s=s.replace('if(owner<2)cache_data[owner*8+beat]<=mem_rsp_data;', 'if(owner==1)cache_data[owner*8+beat]<=mem_rsp_data;')
s=s.replace('      if(owner<2)begin', '''      if(owner==0)begin
       response_data[0]<={mem_rsp_data,read_payload[111:0]};
      end else if(owner==1)begin''')
assert 'p0_rsp_burst_data='in s
(p/'cu71_word_bridge_direct.sv').write_text(s,newline='\n')

t=(p/'cu71_memory_system_burst.sv').read_text().replace('module cu71_memory_system_burst #(', 'module cu71_memory_system_direct #(')
t=t.replace(' logic t_valid,', ' logic[127:0]t_rsp_burst_data;logic t_valid,',1)
t=t.replace(' cu71_tile_memory tiles(', ' cu71_tile_memory_direct tiles(').replace(' cu71_word_bridge_burst bridge(', ' cu71_word_bridge_direct bridge(')
t=t.replace('.word_rsp_data(t_rsp_data),', '.word_rsp_data(t_rsp_data),.word_rsp_burst_data(t_rsp_burst_data),')
t=t.replace('.p0_rsp_data(t_rsp_data),', '.p0_rsp_data(t_rsp_data),.p0_rsp_burst_data(t_rsp_burst_data),')
(p/'cu71_memory_system_direct.sv').write_text(t,newline='\n')
(p/'direct-derivation.json').write_text(json.dumps({'status':'SOURCE_ONLY_PENDING_SIMULATION','parents':{n:sha(p/n)for n in ['cu71_tile_memory.sv','cu71_word_bridge_burst.sv','cu71_memory_system_burst.sv']},'candidates':{n:sha(p/n)for n in ['cu71_tile_memory_direct.sv','cu71_word_bridge_direct.sv','cu71_memory_system_direct.sv']},'layout':'planeBase+tileIndex*32+floor((localY*8+localX)/2), evenbyteislow; Y90x60tiles,UV45x30','logical_API':'unchanged512pixels+generation/bank/plane/index','controller':'unchangedselectedSDR2','hardware':False},indent=2)+'\n')
print('PREPARED_TILE_MAJOR_DIRECT_MEMORY_SOURCE')
