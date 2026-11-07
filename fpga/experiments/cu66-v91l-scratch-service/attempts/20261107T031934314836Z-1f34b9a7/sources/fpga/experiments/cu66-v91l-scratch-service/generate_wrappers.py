#!/usr/bin/env python3
"""Deterministic wrapper composition; preserve all frozen source bytes."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
AREA=Path(__file__).resolve().parent
PORTS='''
 input logic scratch_reset,scratch_cancel,scratch_req_valid,output logic scratch_req_ready,
 input logic scratch_req_write,input logic [17:0] scratch_req_addr,
 input logic [127:0] scratch_req_data,input logic [31:0] scratch_req_epoch,
 output logic scratch_rsp_valid,input logic scratch_rsp_ready,
 output logic [127:0] scratch_rsp_data,output logic [31:0] scratch_rsp_epoch,output logic scratch_rsp_error,
 output logic scratch_busy,scratch_pending,output logic [2:0] scratch_state,
 output logic [3:0] scratch_beats,scratch_words,output logic [1:0] memory_owner,
 output logic [31:0] scratch_requests,scratch_commands,scratch_responses,scratch_cancels,scratch_invalid,
 output logic [31:0] scratch_write_requests,scratch_read_requests,scratch_write_words,scratch_read_words'''
NAMES='scratch_reset scratch_cancel scratch_req_valid scratch_req_ready scratch_req_write scratch_req_addr scratch_req_data scratch_req_epoch scratch_rsp_valid scratch_rsp_ready scratch_rsp_data scratch_rsp_epoch scratch_rsp_error scratch_busy scratch_pending scratch_state scratch_beats scratch_words memory_owner scratch_requests scratch_commands scratch_responses scratch_cancels scratch_invalid scratch_write_requests scratch_read_requests scratch_write_words scratch_read_words'.split()
CONNECT=',\n'.join('.'+n+'('+n+')' for n in NAMES)
new=(ROOT/'fpga/experiments/cu66-v91l-reference-reader/reference_shared_timed.sv').read_text()
new=new.replace('module reference_shared_timed','module scratch_shared_timed',1)
new=new.replace('output logic [127:0] ref_line_rsp_data);','output logic [127:0] ref_line_rsp_data,'+PORTS+');',1)
new=new.replace('shared_sdram_timed #','scratch_sdram_timed #',1)
new=new.replace('.precharges(precharges));','.precharges(precharges),\n'+CONNECT+');',1)
(AREA/'scratch_shared_timed.sv').write_text(new)
new=(ROOT/'fpga/experiments/cu66-v91l-shared-service/shared_sdram_timed.sv').read_text()
new=new.replace('module shared_sdram_timed','module scratch_sdram_timed',1)
new=new.replace('output integer precharges);','output integer precharges,'+PORTS+');',1)
# Interpose only at the existing raw controller port, never alter frozen video service.
start=new.index(' shared_sdram_service service(');end=new.index(' moonshine_sdram #',start)
service=new[start:end]
service=service.replace('.wr_req_valid(wr_req_valid)', '.wr_req_valid(wr_req_valid&&memory_owner==1&&!memory_accepted)')
service=service.replace('.rd_req_valid(rd_req_valid)', '.rd_req_valid(rd_req_valid&&memory_owner==1&&!memory_accepted)')
service=service.replace('.wr_req_ready(wr_req_ready)', '.wr_req_ready(video_wr_ready)')
service=service.replace('.rd_req_ready(rd_req_ready)', '.rd_req_ready(video_rd_ready)')
for n in ['controller_valid','controller_write','controller_addr','controller_data']:
 service=service.replace('.'+n+'('+n+')','.'+n+'(video_'+n+')')
service=service.replace('.controller_ready(controller_ready)', '.controller_ready(controller_ready&&memory_owner==1)')
service=service.replace('.controller_read_valid(controller_read_valid)', '.controller_read_valid(controller_read_valid&&memory_owner==1)')
arb='''
 wire video_wr_ready,video_rd_ready,video_controller_valid,video_controller_write;
 wire [23:0] video_controller_addr;wire [15:0] video_controller_data;
 wire scratch_ctrl_valid,scratch_ctrl_write,scratch_bridge_req_ready;
 wire [23:0] scratch_ctrl_addr;wire [15:0] scratch_ctrl_data;
 logic memory_accepted=0,last_scratch=1;
 wire video_offer=(wr_req_valid&&!wr_reset&&!wr_cancel)||(rd_req_valid&&!rd_reset&&!rd_cancel);
 wire scratch_offer=scratch_req_valid&&!scratch_reset&&!scratch_cancel;
 assign wr_req_ready=video_wr_ready&&memory_owner==1&&!memory_accepted;
 assign rd_req_ready=video_rd_ready&&memory_owner==1&&!memory_accepted;
 assign scratch_req_ready=scratch_bridge_req_ready&&memory_owner==2&&!memory_accepted;
 assign controller_valid=(memory_owner==1&&video_controller_valid)||(memory_owner==2&&scratch_ctrl_valid);
 assign controller_write=memory_owner==1?video_controller_write:scratch_ctrl_write;
 assign controller_addr=memory_owner==1?video_controller_addr:scratch_ctrl_addr;
 assign controller_data=memory_owner==1?video_controller_data:scratch_ctrl_data;
 always_ff @(posedge clk)begin
  if(power_on_reset)begin memory_owner<=0;memory_accepted<=0;last_scratch<=1;end
  else case(memory_owner)
   0:begin
    memory_accepted<=0;
    if(video_offer&&(!scratch_offer||last_scratch))begin memory_owner<=1;last_scratch<=0;end
    else if(scratch_offer)begin memory_owner<=2;last_scratch<=1;end
   end
   1:begin
    if((wr_req_valid&&wr_req_ready)||(rd_req_valid&&rd_req_ready))memory_accepted<=1;
    if((memory_accepted&&source_owner==0)||(!memory_accepted&&!video_offer&&source_owner==0))begin memory_owner<=0;memory_accepted<=0;end
   end
   2:begin
    if(scratch_req_valid&&scratch_req_ready)memory_accepted<=1;
    if((memory_accepted&&!scratch_busy)||(!memory_accepted&&!scratch_offer))begin memory_owner<=0;memory_accepted<=0;end
   end
   default:memory_owner<=0;
  endcase
 end
 scratch_line_bridge scratch(
 .clk(clk),.power_on_reset(power_on_reset),.reset(scratch_reset),.cancel(scratch_cancel),
 .req_valid(scratch_req_valid&&memory_owner==2&&!memory_accepted),.req_ready(scratch_bridge_req_ready),
 .req_write(scratch_req_write),.req_addr(scratch_req_addr),.req_data(scratch_req_data),.req_epoch(scratch_req_epoch),
 .rsp_valid(scratch_rsp_valid),.rsp_ready(scratch_rsp_ready),.rsp_data(scratch_rsp_data),.rsp_epoch(scratch_rsp_epoch),.rsp_error(scratch_rsp_error),
 .ctrl_valid(scratch_ctrl_valid),.ctrl_ready(controller_ready&&memory_owner==2),.ctrl_idle(controller_idle),
 .ctrl_write(scratch_ctrl_write),.ctrl_addr(scratch_ctrl_addr),.ctrl_data(scratch_ctrl_data),
 .ctrl_read_valid(controller_read_valid&&memory_owner==2),.ctrl_read_data(controller_read_data),
 .busy(scratch_busy),.pending(scratch_pending),.state(scratch_state),.beats(scratch_beats),.words(scratch_words),
 .count_requests(scratch_requests),.count_commands(scratch_commands),.count_responses(scratch_responses),.count_cancels(scratch_cancels),.count_invalid(scratch_invalid),
 .count_write_requests(scratch_write_requests),.count_read_requests(scratch_read_requests),.count_write_words(scratch_write_words),.count_read_words(scratch_read_words));
 always_ff @(posedge clk)if(!power_on_reset)begin
  assert(memory_owner<=2);
  if(source_owner!=0)assert(memory_owner==1);
  if(scratch_busy)assert(memory_owner==2);
  if(controller_read_valid)assert((memory_owner==1&&source_owner==2)||(memory_owner==2&&scratch_pending));
 end
'''
new=new[:start]+arb+service+new[end:]
# Keep all old receipt names: physical command owner3 denotes the new scratchclient.
new=new.replace('source_owner,controller_write,controller_addr,controller_data);','memory_owner==2?3:32\'(source_owner),controller_write,controller_addr,controller_data);')
new=new.replace('source_owner,controller_read_data);','memory_owner==2?3:32\'(source_owner),controller_read_data);')
insert='''
 logic [1:0] last_memory_owner=0;
 logic scratch_offered=0;
 logic [2:0] previous_scratch_state=0;
 logic previous_scratch_idle=0;
 always @(posedge clk)begin
  if(!power_on_reset)begin
   if(memory_owner!=last_memory_owner)$display("{\\"type\\":\\"scratch_owner\\",\\"cycle\\":%0d,\\"time_ps\\":%0d,\\"old_owner\\":%0d,\\"owner\\":%0d}",receipt_cycle+1,longint'($realtime*1000.0),last_memory_owner,memory_owner);
   if(memory_owner==0&&(video_offer||scratch_offer))$display("{\\"type\\":\\"scratch_arbitrate\\",\\"cycle\\":%0d,\\"time_ps\\":%0d,\\"video_offer\\":%0d,\\"scratch_offer\\":%0d,\\"last_scratch\\":%0d}",receipt_cycle+1,longint'($realtime*1000.0),video_offer,scratch_offer,last_scratch);
   if(scratch_reset||scratch_cancel)$display("{\\"type\\":\\"scratch_kill\\",\\"cycle\\":%0d,\\"time_ps\\":%0d,\\"reset\\":%0d,\\"cancel\\":%0d}",receipt_cycle+1,longint'($realtime*1000.0),scratch_reset,scratch_cancel);
   if(scratch_req_valid&&scratch_req_ready)$display("{\\"type\\":\\"scratch_req\\",\\"cycle\\":%0d,\\"time_ps\\":%0d,\\"write\\":%0d,\\"address\\":%0d,\\"epoch\\":%0d,\\"data\\":\\"%032h\\"}",receipt_cycle+1,longint'($realtime*1000.0),scratch_req_write,scratch_req_addr,scratch_req_epoch,scratch_req_data);
   if(scratch_rsp_valid&&!scratch_offered)$display("{\\"type\\":\\"scratch_rsp_offer\\",\\"cycle\\":%0d,\\"time_ps\\":%0d,\\"epoch\\":%0d,\\"error\\":%0d,\\"data\\":\\"%032h\\"}",receipt_cycle+1,longint'($realtime*1000.0),scratch_rsp_epoch,scratch_rsp_error,scratch_rsp_data);
   if(scratch_rsp_valid&&scratch_rsp_ready)$display("{\\"type\\":\\"scratch_rsp\\",\\"cycle\\":%0d,\\"time_ps\\":%0d,\\"epoch\\":%0d,\\"error\\":%0d,\\"data\\":\\"%032h\\"}",receipt_cycle+1,longint'($realtime*1000.0),scratch_rsp_epoch,scratch_rsp_error,scratch_rsp_data);
   if(scratch_busy&&(scratch_state!=previous_scratch_state||controller_idle!=previous_scratch_idle||scratch_pending))$display("{\\"type\\":\\"scratch_fence\\",\\"cycle\\":%0d,\\"time_ps\\":%0d,\\"state\\":%0d,\\"pending\\":%0d,\\"beats\\":%0d,\\"words\\":%0d,\\"controller_idle\\":%0d}",receipt_cycle+1,longint'($realtime*1000.0),scratch_state,scratch_pending,scratch_beats,scratch_words,controller_idle);
  end
  last_memory_owner<=memory_owner;scratch_offered<=scratch_rsp_valid&&!scratch_rsp_ready;previous_scratch_state<=scratch_state;previous_scratch_idle<=controller_idle;
 end
'''
new=new.replace('endmodule',insert+'endmodule')
(AREA/'scratch_sdram_timed.sv').write_text(new)
