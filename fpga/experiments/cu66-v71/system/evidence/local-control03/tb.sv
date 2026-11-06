`timescale 1ns/1ps
module tb;
reg  clk=0;
reg  rst=0;
reg  bus_write=0;
reg [11:0] bus_address=0;
reg [31:0] bus_wdata=0;
wire [31:0] bus_rdata;
reg  transport_fault=0;
wire  start_valid;
reg  start_ready=0;
wire [63:0] start_generation;
wire [31:0] start_packet_bytes;
wire  abort_i;
wire  clear_fault;
reg  busy=0;
reg  done=0;
reg  error=0;
reg [7:0] stage=0;
reg [7:0] error_code=0;
reg  memory_tile_busy=0;
reg  memory_aux_busy=0;
reg [31:0] accepted_count=0;
reg [31:0] presented_count=0;
reg [31:0] rejected_count=0;
reg [31:0] lcd_underruns=0;
reg  packet_req_valid=0;
wire  packet_req_ready;
reg [15:0] packet_req_address=0;
reg [63:0] packet_req_generation=0;
reg [31:0] packet_req_sequence=0;
wire  packet_rsp_valid;
reg  packet_rsp_ready=0;
wire [15:0] packet_rsp_address;
wire [63:0] packet_rsp_generation;
wire [31:0] packet_rsp_sequence;
wire [7:0] packet_rsp_data;
reg  hud_prepare_valid=0;
wire  hud_prepare_ready;
reg [63:0] active_generation=0;
reg [31:0] active_frame_id=0;
reg [31:0] active_reference_id=0;
reg  active_key=0;
reg [15:0] hud_address=0;
reg [15:0] hud_bytes=0;
reg [127:0] expected_hud_tag=0;
reg [1:0] candidate_bank=0;
wire  hud_result_valid;
reg  hud_result_ready=0;
wire [63:0] hud_result_generation;
wire [31:0] hud_result_frame_id;
wire [31:0] hud_result_reference_id;
wire [127:0] hud_result_tag;
wire [15:0] hud_result_words;
wire  hud_result_success;
wire  hud_drain_valid;
reg  hud_drain_ready=0;
wire [63:0] hud_drain_generation;
wire [31:0] hud_drain_frame_id;
wire [1:0] hud_drain_bank;
wire [127:0] hud_drain_tag;
wire [15:0] hud_drain_words;
wire  hud_drain_success;
reg  software_command_valid=0;
wire  software_command_ready;
reg [2:0] software_command_opcode=0;
wire  software_ack_valid;
reg  software_ack_ready=0;
wire [2:0] software_ack_opcode;
wire [63:0] software_ack_generation;
wire [31:0] software_ack_frame_id;
wire  software_ack_success;
wire  hud_aux_req_valid;
reg  hud_aux_req_ready=0;
wire [63:0] hud_aux_generation;
wire [31:0] hud_aux_frame_id;
wire  hud_aux_req_write;
wire [23:0] hud_aux_req_addr;
wire [15:0] hud_aux_req_data;
reg  hud_aux_rsp_valid=0;
wire  hud_aux_rsp_ready;
reg [15:0] hud_aux_rsp_data=0;
reg  hud_aux_rsp_error=0;
wire [9:0] diag_address;
reg [31:0] diag_data=0;
wire  quarantine;
always #5 clk=~clk;
cu71_local_control d(.*);
integer checks=0,start_count=0,result_count=0,drain_count=0,ack_count=0,abort_count=0,aux_count=0;
reg aux_pending=0;reg[15:0] memory_word=0;
always @(posedge clk)if(!rst)begin
 if(start_valid&&start_ready)start_count<=start_count+1;
 if(hud_result_valid&&hud_result_ready)result_count<=result_count+1;
 if(hud_drain_valid&&hud_drain_ready)drain_count<=drain_count+1;
 if(software_ack_valid&&software_ack_ready)ack_count<=ack_count+1;
 if(abort_i)abort_count<=abort_count+1;
 if(hud_aux_req_valid&&hud_aux_req_ready)begin
  aux_pending<=1;aux_count<=aux_count+1;
  if(hud_aux_req_write)memory_word<=hud_aux_req_data;
 end
 if(aux_pending)begin hud_aux_rsp_valid<=1;hud_aux_rsp_data<=memory_word;aux_pending<=0;end
 if(hud_aux_rsp_valid&&hud_aux_rsp_ready)hud_aux_rsp_valid<=0;
end
task tick;begin @(posedge clk);#1;end endtask
task require(input ok,input[767:0]message);begin checks=checks+1;if(ok!==1'b1)$fatal(1,"%0s",message);end endtask
task wr(input[11:0]a,input[31:0]v);begin @(negedge clk);bus_address=a;bus_wdata=v;bus_write=1;tick();@(negedge clk);bus_write=0;end endtask
task set_context(input[63:0]g,input[31:0]f,input[31:0]refid);begin wr('h040,g[31:0]);wr('h044,g[63:32]);wr('h048,f);wr('h04c,refid);end endtask
task cmd(input[31:0]seq,input[7:0]op,input[31:0]expected_status);
integer timeout;begin
 wr('h020,seq);wr('h024,{24'd0,op});bus_address='h028;#1;timeout=0;
 while(bus_rdata!=seq&&timeout<1000)begin tick();timeout=timeout+1;end
 require(timeout<1000,"bounded command completion");bus_address='h02c;#1;
 if(bus_rdata!==expected_status)$display("command seq=%0d op=%0d status=%h expected=%h",seq,op,bus_rdata,expected_status);
 require(bus_rdata===expected_status,"command status");
end endtask
initial begin
 rst=1;repeat(3)tick();@(negedge clk);rst=0;
 start_ready=1;hud_result_ready=1;hud_drain_ready=1;software_ack_ready=1;hud_aux_req_ready=1;packet_rsp_ready=1;
 bus_address=0;#1;require(bus_rdata==32'h43553731,"distinct CU71 identity");
 set_context(0,0,0);wr('h050,8);wr('h054,32'h88aa689f);cmd(1,1,32'h80000002);
 require(d.staging_begin_ready&&d.staged_generation==0,"invalid begin cannot mutate staging");
 set_context(1,10,0);cmd(2,1,0);require(d.upload_ready,"loader ready");
 wr('h100,32'h03020100);repeat(5)tick();wr('h100,32'h07060504);repeat(5)tick();
 bus_address='h104;#1;require(bus_rdata==8,"actual bytes stored");
 set_context(99,10,0);cmd(3,2,32'h80000003);require(!d.sealed_valid,"stale seal cannot mutate");
 set_context(1,10,0);cmd(4,2,0);require(d.sealed_valid,"sealed immutable packet");
 set_context(99,10,0);cmd(5,3,32'h80000004);require(start_count==0&&!d.staging_active,"stale start cannot activate");
 cmd(6,4,32'h80000005);require(d.sealed_valid,"stale discard cannot free");
 set_context(1,10,0);cmd(7,3,0);busy=1;repeat(3)tick();require(start_count==1&&d.staging_active,"one valid owner admission");
 wr('h050,0);cmd(8,21,0);bus_address='h030;#1;require(bus_rdata==32'h03020100,"actual staged word read");
 wr('h050,4);cmd(9,21,0);bus_address='h030;#1;require(bus_rdata==32'h07060504,"second staged word read");
 set_context(99,10,0);cmd(10,21,32'h8000000b);require(!quarantine&&d.staging_faults==0,"stale CPU read rejected before packet arbiter");
 set_context(1,10,0);active_generation=1;active_frame_id=10;active_reference_id=0;candidate_bank=0;hud_bytes=100;hud_address=12;
 expected_hud_tag=128'h00112233445566778899aabbccddeeff;hud_prepare_valid=1;tick();@(negedge clk);hud_prepare_valid=0;
 require(d.hud_pending&&d.hud_fid==10,"HUD request snapshot");
 wr('h050,1);wr('h054,21120);wr('h060,32'h00112233);wr('h064,32'h44556677);wr('h068,32'h8899aabb);wr('h06c,32'hccddeeff);
 set_context(99,10,0);cmd(11,16,32'h80000007);require(result_count==0,"stale HUD result cannot pulse");
 set_context(1,10,0);cmd(12,16,0);require(result_count==1,"matching HUD result completes");
 wr('h050,21120);cmd(13,17,32'h80000008);require(aux_count==0,"out of bounds AUX cannot become orphaned request");
 wr('h050,0);wr('h054,16'hbeef);cmd(14,17,0);require(aux_count==1&&memory_word==16'hbeef,"actual AUX completion");
 cmd(15,18,0);bus_address='h030;#1;require(bus_rdata==16'hbeef,"readback response not expected data injection");
 wr('h050,1);wr('h054,21120);wr('h058,0);cmd(16,19,0);require(drain_count==1,"matching drain forwarded after actual AUX responses");
 software_command_opcode=5;software_command_valid=1;tick();@(negedge clk);software_command_valid=0;
 require(d.soft_pending,"software command snapshot");
 wr('h050,5);wr('h054,1);set_context(1,10,99);cmd(17,20,32'h8000000a);require(ack_count==0,"stale reference cannot ACK COMMIT");
 set_context(1,10,0);cmd(18,20,0);require(ack_count==1&&!d.soft_pending,"matching COMMIT ACK");
 stage=10;cmd(19,5,32'h80000006);require(abort_count==0,"postcommit abort blocked");
 stage=5;cmd(20,5,0);require(abort_count==1,"precommit abort requested once");
 cmd(20,5,0);require(abort_count==1,"same sequence retry idempotent");
 busy=0;repeat(8)tick();require(d.staging_begin_ready&&!d.frame_active,"packet released only after observed owner completion");
 wr('h050,8);wr('h054,32'h88aa689f);cmd(21,1,32'h80000002);require(d.staging_begin_ready,"old generation rejected without allocation");
 set_context(2,11,10);transport_fault=1;cmd(22,1,32'h80000002);require(quarantine&&d.staging_begin_ready,"transport quarantine blocks new publication");
 $display("CU71_LOCAL_CONTROL_PASS checks=%0d starts=%0d aux=%0d results=%0d drains=%0d softacks=%0d",checks,start_count,aux_count,result_count,drain_count,ack_count);$finish;
end
initial begin #20000000;$fatal(1,"test watchdog");end
endmodule
