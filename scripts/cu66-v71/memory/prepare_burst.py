"""Derive a fourth-client RGB BL8 variant; preserve the qualified baseline."""
from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[3];p=r/'fpga/experiments/cu66-v71/memory';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
base=p/'cu71_word_bridge.sv';s=base.read_text().replace('module cu71_word_bridge #(', 'module cu71_word_bridge_burst #(')
s=s.replace(' output logic mem_req_valid,', ''' input logic p3_valid,output logic p3_ready,input logic[23:0]p3_addr,input logic[127:0]p3_data,input logic[15:0]p3_mask,
 output logic p3_rsp_valid,input logic p3_rsp_ready,output logic p3_rsp_error,
 output logic mem_req_valid,''')
s=s.replace(' output logic[31:0]lcd_completed_reads,lcd_max_wait', ' output logic[31:0]lcd_completed_reads,lcd_max_wait,rgb_completed_writes,rgb_max_wait')
s=s.replace('logic[2:0]pending,response_valid,response_error,writing;', 'logic[3:0]pending,response_valid,response_error,writing;')
s=s.replace('[0:2]', '[0:3]').replace('i<3;i=i+1','i<4;i=i+1')
s=s.replace(' logic prefer_one;', ' logic[1:0]background_phase,background_selected;')
s=s.replace(' logic[127:0]canonical_burst_data;logic[15:0]canonical_burst_mask;', ' logic[127:0]canonical_burst_data,rgb_burst_data;logic[15:0]canonical_burst_mask,rgb_burst_mask;')
s=s.replace(' wire any_pending=|pending;', ''' function automatic logic rgb_block_allowed(input logic[23:0]addr);
  rgb_block_allowed=(addr>=RGB0_BASE&&{1'b0,addr}+25'd7<{1'b0,RGB0_BASE}+RGB0_WORDS)||
                    (addr>=RGB1_BASE&&{1'b0,addr}+25'd7<{1'b0,RGB1_BASE}+RGB1_WORDS);
 endfunction
 wire any_pending=|pending;''')
s=s.replace('background_pending=pending[0]||pending[1];', '''background_pending=pending[0]||pending[1]||pending[3];
  case(background_phase)
   0:background_selected=pending[0]?0:pending[1]?1:3;
   1:background_selected=pending[1]?1:pending[3]?3:0;
   default:background_selected=pending[3]?3:pending[0]?0:1;
  endcase''')
s=s.replace('pending[1]&&(!pending[0]||prefer_one)?1:0;', 'background_selected;')
s=s.replace('  p0_rsp_valid=', '''  p3_ready=!rst&&!pending[3]&&!response_valid[3]&&!(state!=IDLE&&owner==3);
  p3_rsp_valid=response_valid[3]&&!rst;p3_rsp_error=response_error[3];
  p0_rsp_valid=''',1)
s=s.replace('owner==0?canonical_burst_data:', 'owner==0?canonical_burst_data:owner==3?rgb_burst_data:')
s=s.replace('owner==0?canonical_burst_mask:', 'owner==0?canonical_burst_mask:owner==3?rgb_burst_mask:')
s=s.replace('prefer_one<=0;', 'background_phase<=0;')
s=s.replace('lcd_completed_reads<=0;lcd_max_wait<=0;', 'lcd_completed_reads<=0;lcd_max_wait<=0;rgb_completed_writes<=0;rgb_max_wait<=0;rgb_burst_data<=0;rgb_burst_mask<=16\'hffff;')
s=s.replace('   if(p0_rsp_valid&&p0_rsp_ready)', '   if(p3_rsp_valid&&p3_rsp_ready)response_valid[3]<=0;\n   if(p0_rsp_valid&&p0_rsp_ready)',1)
s=s.replace('   case(state)', '''   if(p3_valid&&p3_ready)begin pending[3]<=1;address[3]<=p3_addr;wdata[3]<=0;writing[3]<=1;wait_cycles[3]<=0;rgb_burst_data<=p3_data;rgb_burst_mask<=p3_mask;end
   case(state)''',1)
s=s.replace('prefer_one<=selected==0;', 'background_phase<=selected==0?1:selected==1?2:0;')
s=s.replace('(selected==2&&address[selected][2:0]!=0)', '((selected==2||selected==3)&&address[selected][2:0]!=0)||(selected==3&&!rgb_block_allowed(address[selected]))')
s=s.replace('     response_data[owner]<=0;response_valid[owner]<=1;completed_writes<=completed_writes+1;state<=IDLE;', '''     response_data[owner]<=0;response_valid[owner]<=1;completed_writes<=completed_writes+1;state<=IDLE;
     if(owner==3)begin rgb_completed_writes<=rgb_completed_writes+1;if(wait_cycles[3]>rgb_max_wait)rgb_max_wait<=wait_cycles[3];end''')
assert 'prefer_one'not in s and 'p3_valid&&p3_ready'in s
(p/'cu71_word_bridge_burst.sv').write_text(s,newline='\n')
base_top=p/'cu71_memory_system.sv';t=base_top.read_text().replace('module cu71_memory_system #(', 'module cu71_memory_system_burst #(')
t=t.replace(' output logic idle\n', ''' input logic rgb_req_valid,output logic rgb_req_ready,input logic[23:0]rgb_req_addr,input logic[127:0]rgb_req_data,input logic[15:0]rgb_req_mask,
 output logic rgb_rsp_valid,input logic rgb_rsp_ready,output logic rgb_rsp_error,
 input logic rgb_abort_i,output logic rgb_busy,rgb_aborted,
 output logic[31:0]rgb_completed_writes,rgb_max_wait,
 output logic idle
''')
t=t.replace(' logic t_valid,', ''' logic b_valid,b_ready,b_rsp_valid,b_rsp_ready,b_rsp_error,b_active,b_issued,b_aborting;
 logic[23:0]b_addr;logic[127:0]b_data;logic[15:0]b_mask;
 assign rgb_req_ready=!b_active&&!rst&&!rgb_abort_i;
 assign b_valid=b_active&&!b_issued&&!b_aborting&&!rgb_abort_i;
 assign rgb_rsp_valid=b_active&&b_issued&&b_rsp_valid&&!b_aborting&&!rgb_abort_i&&!rst;
 assign rgb_rsp_error=b_rsp_error;
 assign b_rsp_ready=b_active&&b_issued&&(b_aborting||rgb_abort_i||rgb_rsp_ready);
 assign rgb_busy=b_active;
 always_ff @(posedge clk)begin
  if(rst)begin b_active<=0;b_issued<=0;b_aborting<=0;rgb_aborted<=0;b_addr<=0;b_data<=0;b_mask<=16'hffff;end
  else begin
   rgb_aborted<=0;
   if(rgb_req_valid&&rgb_req_ready)begin b_active<=1;b_issued<=0;b_aborting<=0;b_addr<=rgb_req_addr;b_data<=rgb_req_data;b_mask<=rgb_req_mask;end
   if(b_valid&&b_ready)b_issued<=1;
   if(b_active&&(rgb_abort_i||b_aborting))begin
    b_aborting<=1;
    if(!b_issued||(b_rsp_valid&&b_rsp_ready))begin b_active<=0;b_issued<=0;b_aborting<=0;rgb_aborted<=1;end
   end else if(b_rsp_valid&&b_rsp_ready)begin b_active<=0;b_issued<=0;end
  end
 end
 logic t_valid,''',1)
t=t.replace('!lcd_busy&&!bridge_busy', '!lcd_busy&&!rgb_busy&&!bridge_busy')
t=t.replace(' cu71_word_bridge bridge(', ' cu71_word_bridge_burst bridge(')
t=t.replace('  .mem_req_valid,.mem_req_ready,', '''  .p3_valid(b_valid),.p3_ready(b_ready),.p3_addr(b_addr),.p3_data(b_data),.p3_mask(b_mask),
  .p3_rsp_valid(b_rsp_valid),.p3_rsp_ready(b_rsp_ready),.p3_rsp_error(b_rsp_error),.rgb_completed_writes,.rgb_max_wait,
  .mem_req_valid,.mem_req_ready,''',1)
assert 'cu71_word_bridge_burst bridge'in t
(p/'cu71_memory_system_burst.sv').write_text(t,newline='\n')
(p/'burst-derivation.json').write_text(json.dumps({'parents':{n:sha(p/n)for n in ['cu71_memory_system.sv','cu71_word_bridge.sv']},'candidates':{n:sha(p/n)for n in ['cu71_memory_system_burst.sv','cu71_word_bridge_burst.sv']},'contract':'RGBonlyaligned8x16write,data128,activehighdisabledbyteMask16,actualcontrollerrecoverycompletion,oneoutstanding,abortdrain;LCD2:1quota+4cyclelookahead;3waybackgroundRR','hardware':False},indent=2)+'\n')
print('PREPARED_EXPLICIT_RGB_BL8_VARIANT')
