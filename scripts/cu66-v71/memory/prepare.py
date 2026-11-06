"""Freeze the qualified controller and explicit v70-to-v71 wrapper derivation."""
from pathlib import Path
import hashlib,json,sys,shutil
root=Path(__file__).resolve().parents[3]
out=root/'fpga/experiments/cu66-v71/memory'
baseline=root/'fpga/experiments/cu66-v70/memory'
historical_root=Path('C:/Users/lavat/codex/moonbub')
qualified=historical_root/'fpga/diagnostics/sdr2-20261105/source-v004/controller.sv'
if not qualified.exists():qualified=out/'moonshine_sdram_burst.sv'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(qualified)=='05a9a9471f9c9eb61209c55579b82f9d228cc01328044589eec989b200d6f65a'
(out/'moonshine_sdram_burst.sv').write_bytes(qualified.read_bytes())
text=(baseline/'cu70_memory_system.sv').read_text().replace('module cu70_memory_system','module cu71_memory_system')
text=text.replace(' output logic idle\n', ''' input logic lcd_req_valid,output logic lcd_req_ready,input logic[23:0]lcd_req_addr,
 output logic lcd_rsp_valid,input logic lcd_rsp_ready,output logic[127:0]lcd_rsp_data,output logic lcd_rsp_error,
 input logic lcd_abort_i,output logic lcd_busy,lcd_aborted,
 output logic[31:0]lcd_completed_reads,lcd_max_wait,
 output logic idle
''')
text=text.replace(' logic [23:0] mem_req_addr;logic [15:0] mem_req_data,mem_rsp_data;', ''' logic [23:0] mem_req_addr;logic[127:0]mem_req_burst_data;logic[15:0]mem_req_burst_mask,mem_rsp_data;
 logic l_valid,l_ready,l_rsp_valid,l_rsp_ready,l_rsp_error,l_active,l_issued,l_aborting;
 logic[23:0]l_addr;logic[127:0]l_rsp_data;
 assign lcd_req_ready=!l_active&&!rst&&!lcd_abort_i;
 assign l_valid=l_active&&!l_issued&&!l_aborting&&!lcd_abort_i;
 assign lcd_rsp_valid=l_active&&l_issued&&l_rsp_valid&&!l_aborting&&!lcd_abort_i&&!rst;
 assign lcd_rsp_data=l_rsp_data;assign lcd_rsp_error=l_rsp_error;
 assign l_rsp_ready=l_active&&l_issued&&(l_aborting||lcd_abort_i||lcd_rsp_ready);
 assign lcd_busy=l_active;
 always_ff @(posedge clk)begin
  if(rst)begin l_active<=0;l_issued<=0;l_aborting<=0;lcd_aborted<=0;l_addr<=0;end
  else begin
   lcd_aborted<=0;
   if(lcd_req_valid&&lcd_req_ready)begin l_active<=1;l_issued<=0;l_aborting<=0;l_addr<=lcd_req_addr;end
   if(l_valid&&l_ready)l_issued<=1;
   if(l_active&&(lcd_abort_i||l_aborting))begin
    l_aborting<=1;
    if(!l_issued||(l_rsp_valid&&l_rsp_ready))begin l_active<=0;l_issued<=0;l_aborting<=0;lcd_aborted<=1;end
   end else if(l_rsp_valid&&l_rsp_ready)begin l_active<=0;l_issued<=0;end
  end
 end''')
text=text.replace('assign idle=!tile_busy&&!aux_busy&&!bridge_busy&&mem_idle;', 'assign idle=!tile_busy&&!aux_busy&&!lcd_busy&&!bridge_busy&&mem_idle;')
text=text.replace('cu70_word_bridge bridge(', 'cu71_word_bridge bridge(')
text=text.replace(' logic t_valid,t_ready,t_write,t_rsp_valid,t_rsp_ready,t_rsp_error;', ' logic t_valid,t_ready,t_write,t_rsp_valid,t_rsp_ready,t_rsp_error;logic[127:0]t_burst_data;logic[15:0]t_burst_mask;')
text=text.replace(' cu70_tile_memory tiles(', ' cu71_tile_memory tiles(')
text=text.replace('.word_req_data(t_data),', '.word_req_data(t_data),.word_req_burst_data(t_burst_data),.word_req_burst_mask(t_burst_mask),')
text=text.replace('.p0_data(t_data),', '.p0_data(t_data),.p0_burst_data(t_burst_data),.p0_burst_mask(t_burst_mask),')
text=text.replace('  .mem_req_valid,.mem_req_ready,.mem_req_write,.mem_req_addr,.mem_req_data,.mem_rsp_valid,.mem_rsp_data,.mem_idle,', '''  .p2_valid(l_valid),.p2_ready(l_ready),.p2_addr(l_addr),.p2_rsp_valid(l_rsp_valid),.p2_rsp_ready(l_rsp_ready),.p2_rsp_data(l_rsp_data),.p2_rsp_error(l_rsp_error),
  .mem_req_valid,.mem_req_ready,.mem_req_write,.mem_req_addr,.mem_req_burst_data,.mem_req_burst_mask,.mem_rsp_valid,.mem_rsp_data,.mem_idle,
  .lcd_completed_reads,.lcd_max_wait,''')
text=text.replace('cu70_sdram_controller #(', 'moonshine_sdram_burst #(')
text=text.replace('.request_write(mem_req_write),.request_address(mem_req_addr),.request_data(mem_req_data),', '.request_write(mem_req_write),.request_read_wait(4\'d4),.request_address(mem_req_addr),.request_burst_data(mem_req_burst_data),.request_burst_mask(mem_req_burst_mask),')
assert 'mem_req_data' not in text
(out/'cu71_memory_system.sv').write_text(text,newline='\n')
tile=(baseline/'cu70_tile_memory.sv').read_text().replace('module cu70_tile_memory','module cu71_tile_memory')
tile=tile.replace('output logic [15:0] word_req_data,', 'output logic [15:0] word_req_data,output logic[127:0]word_req_burst_data,output logic[15:0]word_req_burst_mask,')
tile=tile.replace('  word_req_data=pixels[int\'(word_index)*16+:16];', '''  word_req_data=pixels[int'(word_index)*16+:16];
  word_req_burst_data=128'(pixels[int'(word_index[4:2])*64+:64])<<(word_req_addr[2:0]*16);
  word_req_burst_mask=16'hffff^(16'h00ff<<(word_req_addr[2:0]*2));''')
tile=tile.replace('if(word_index==31)state<=RESULT;', 'if(word_index==(writing?28:31))state<=RESULT;')
tile=tile.replace('word_index<=word_index+1;', "word_index<=word_index+(writing?5'd4:5'd1);")
assert 'word_req_burst_data=' in tile
(out/'cu71_tile_memory.sv').write_text(tile,newline='\n')
(out/'controller-origin.json').write_text(json.dumps({'source':str(qualified),'sha256':sha(qualified),'byte_identical':True,'frequency_hz':100000000,'read_phase_degrees':274.5,'read_wait':4,'retime':'posedge','MRS':'0x033','scope':'Standalone controller selected profile qualification reused; system timing/throughput not established'},indent=2)+'\n')
verification=out/'verification';verification.mkdir(exist_ok=True)
frozen=historical_root/'fpga/exports/cpl1-timing-fsmcopy-source-20261105-v002/sim-inputs'
origins={}
for src,target in [(frozen/'core/parents/sdram_model_bounded.sv',verification/'model_base.sv'),(frozen/'sim/support-primitives.sv',verification/'primitives.sv')]:
 if src.exists():shutil.copy2(src,target)
 assert target.exists()
 origins[target.relative_to(out).as_posix()]={'historical_source':str(src),'sha256':sha(target)}
for name in ['cpl1_sdram_models.py','sdr2_model_checked.py','sdr2_model_spec_v2.py']:
 src=historical_root/'scripts'/name;target=Path(__file__).parent/name
 if src.exists():shutil.copy2(src,target)
 assert target.exists()
 origins['scripts/'+name]={'historical_source':str(src),'sha256':sha(target)}
(out/'verification-origin.json').write_text(json.dumps(origins,indent=2)+'\n')
print('PREPARED_CU71_QUALIFIED_BACKEND',out)
