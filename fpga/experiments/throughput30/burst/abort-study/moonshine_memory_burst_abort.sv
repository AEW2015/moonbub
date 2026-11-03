`timescale 1ns/1ps
`default_nettype none
// EXPERIMENTAL test-only arbiter: collects aligned 8-word tile runs, grants
// LCD line reads priority over starting a write burst, then emits BL8 writes.
// Test-only abort flushes unissued staging; requires explicit drain before reuse.
module moonshine_memory_burst_abort(
 input wire clk,read_clk,reset,abort,
 input wire pixel_valid,output wire pixel_ready,input wire[23:0]pixel_address,input wire[15:0]pixel_rgb565,
 input wire line_req_valid,output wire line_req_ready,input wire[23:0]line_req_address,
 output wire line_data_valid,output wire[15:0]line_data,
 output wire idle,output reg protocol_fault,
 output wire[12:0]sdram_a,output wire[1:0]sdram_bs,inout wire[15:0]sdram_dq,
 output wire sdram_clk,output wire[1:0]sdram_cke,sdram_cs_n,
 output wire sdram_ras_n,sdram_cas_n,sdram_we_n,sdram_ldqm,sdram_udqm
);
 reg line_busy,burst_pending;reg[23:0]read_address;reg[8:0]received;reg[2:0]beat;
 reg[127:0]write_data;reg[23:0]write_address;reg[2:0]write_index;reg write_full;
 wire req_ready,mem_idle,rsp_valid;wire[15:0]rsp_data;
 wire request_read=line_busy&&!burst_pending;
 wire request_write=!line_busy&&!line_req_valid&&write_full&&!protocol_fault&&!abort;
 wire request_valid=request_read||request_write;
 assign line_req_ready=!line_busy;
 assign pixel_ready=!write_full&&!protocol_fault&&!abort;
 assign idle=mem_idle&&!line_busy&&!write_full&&(write_index==0)&&!protocol_fault;
 assign line_data_valid=rsp_valid&&line_busy;
 assign line_data=rsp_data;
 always @(posedge clk)begin
  if(reset)begin
   line_busy<=0;burst_pending<=0;read_address<=0;received<=0;beat<=0;
   write_data<=0;write_address<=0;write_index<=0;write_full<=0;protocol_fault<=0;
  end else begin
   if(line_req_valid&&line_req_ready)begin line_busy<=1;read_address<=line_req_address;received<=0;burst_pending<=0;end
   if(request_read&&req_ready)begin burst_pending<=1;beat<=0;end
   if(rsp_valid&&line_busy)begin
    received<=received+1'b1;beat<=beat+1'b1;
    if(beat==7)begin burst_pending<=0;read_address<=read_address+8;end
    if(received==479)line_busy<=0;
   end
   if(request_write&&req_ready)write_full<=0;
   // Candidate: discard only unissued staged words on abort. Already issued
   // SDRAM bursts and active LCD reads continue; idle stays low until drained.
   if(abort)begin write_index<=0;write_full<=0;protocol_fault<=0;end
   else if(pixel_valid&&pixel_ready)begin
    if((write_index==0&&pixel_address[2:0]!=0)||
       (write_index!=0&&pixel_address!=write_address+{21'b0,write_index}))protocol_fault<=1;
    else begin
     if(write_index==0)write_address<=pixel_address;
     write_data[write_index*16+:16]<=pixel_rgb565;
     if(write_index==7)begin write_index<=0;write_full<=1;end
     else write_index<=write_index+1'b1;
    end
   end
  end
 end
 moonshine_sdram_burst controller(.clk(clk),.read_clk(read_clk),.reset(reset),.request_valid(request_valid),.request_ready(req_ready),
 .request_write(!request_read),.request_address(request_read ? read_address:write_address),.request_burst_data(write_data),
 .response_valid(rsp_valid),.response_data(rsp_data),.idle(mem_idle),
 .sdram_a(sdram_a),.sdram_bs(sdram_bs),.sdram_dq(sdram_dq),.sdram_clk(sdram_clk),
 .sdram_cke(sdram_cke),.sdram_cs_n(sdram_cs_n),.sdram_ras_n(sdram_ras_n),.sdram_cas_n(sdram_cas_n),
 .sdram_we_n(sdram_we_n),.sdram_ldqm(sdram_ldqm),.sdram_udqm(sdram_udqm));
endmodule
`default_nettype wire
