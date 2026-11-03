`timescale 1ns/1ps
`default_nettype none
// Experiment only. Existing line-fetch and 8-pixel burst packing plus a
// separate staging arbiter; no output backpressure for compressed reads.
module moonshine_memory_staging(
 input wire clk,read_clk,reset,
 input wire pixel_valid,output wire pixel_ready,input wire[23:0]pixel_address,input wire[15:0]pixel_rgb565,
 input wire line_req_valid,output wire line_req_ready,input wire[23:0]line_req_address,
 output wire line_data_valid,output wire[15:0]line_data,
 input wire jwrite_valid,output wire jwrite_ready,input wire[23:0]jwrite_addr,input wire[127:0]jwrite_data,
 input wire jread_valid,output wire jread_ready,input wire[23:0]jread_addr,output wire jread_data_valid,output wire[15:0]jread_data,
 output wire idle,output wire protocol_fault,
 output wire[12:0]sdram_a,output wire[1:0]sdram_bs,inout wire[15:0]sdram_dq,
 output wire sdram_clk,output wire[1:0]sdram_cke,sdram_cs_n,
 output wire sdram_ras_n,sdram_cas_n,sdram_we_n,sdram_ldqm,sdram_udqm
);
 reg line_busy,burst_pending;reg[23:0]read_address;reg[8:0]received;reg[2:0]beat;
 reg[127:0]write_data;reg[23:0]write_address;reg[2:0]write_index;reg write_full,pixel_fault;
 wire ctrl_ready,ctrl_idle,ctrl_rsp_valid;wire[15:0]ctrl_rsp_data;
 wire req_valid,req_write,arb_read_busy,arb_fault,display_ready,pixel_burst_ready;
 wire[23:0]req_address;wire[127:0]req_data;
 wire display_valid=line_busy&&!burst_pending;
 assign line_req_ready=!line_busy;
 assign pixel_ready=!write_full&&!protocol_fault;
 assign protocol_fault=pixel_fault||arb_fault;
 assign idle=ctrl_idle&&!line_busy&&!write_full&&(write_index==0)&&!protocol_fault&&
             !arb_read_busy&&!jwrite_valid&&!jread_valid;
 always @(posedge clk)begin
  if(reset)begin
   line_busy<=0;burst_pending<=0;read_address<=0;received<=0;beat<=0;
   write_data<=0;write_address<=0;write_index<=0;write_full<=0;pixel_fault<=0;
  end else begin
   if(line_req_valid&&line_req_ready)begin line_busy<=1;read_address<=line_req_address;received<=0;burst_pending<=0;end
   if(display_valid&&display_ready)begin burst_pending<=1;beat<=0;end
   if(line_data_valid&&line_busy)begin
    received<=received+1'b1;beat<=beat+1'b1;
    if(beat==7)begin burst_pending<=0;read_address<=read_address+8;end
    if(received==479)line_busy<=0;
   end
   if(pixel_burst_ready)write_full<=0;
   if(pixel_valid&&pixel_ready)begin
    if((write_index==0&&pixel_address[2:0]!=0)||
       (write_index!=0&&pixel_address!=write_address+{21'b0,write_index}))pixel_fault<=1;
    else begin
     if(write_index==0)write_address<=pixel_address;
     write_data[write_index*16+:16]<=pixel_rgb565;
     if(write_index==7)begin write_index<=0;write_full<=1;end
     else write_index<=write_index+1'b1;
    end
   end
  end
 end
 staging_arbiter arb(.clk(clk),.reset(reset),
  .display_valid(display_valid),.display_ready(display_ready),.display_addr(read_address),
  .display_data_valid(line_data_valid),.display_data(line_data),
  .pixel_valid(write_full),.pixel_ready(pixel_burst_ready),.pixel_addr(write_address),.pixel_data(write_data),
  .jwrite_valid(jwrite_valid),.jwrite_ready(jwrite_ready),.jwrite_addr(jwrite_addr),.jwrite_data(jwrite_data),
  .jread_valid(jread_valid),.jread_ready(jread_ready),.jread_addr(jread_addr),.jread_data_valid(jread_data_valid),.jread_data(jread_data),
  .request_valid(req_valid),.request_ready(ctrl_ready),.request_write(req_write),.request_addr(req_address),.request_data(req_data),
  .response_valid(ctrl_rsp_valid),.response_data(ctrl_rsp_data),.read_busy(arb_read_busy),.protocol_fault(arb_fault));
 moonshine_sdram_burst controller(.clk(clk),.read_clk(read_clk),.reset(reset),.request_valid(req_valid),.request_ready(ctrl_ready),
  .request_write(req_write),.request_address(req_address),.request_burst_data(req_data),
  .response_valid(ctrl_rsp_valid),.response_data(ctrl_rsp_data),.idle(ctrl_idle),
  .sdram_a(sdram_a),.sdram_bs(sdram_bs),.sdram_dq(sdram_dq),.sdram_clk(sdram_clk),
  .sdram_cke(sdram_cke),.sdram_cs_n(sdram_cs_n),.sdram_ras_n(sdram_ras_n),.sdram_cas_n(sdram_cas_n),
  .sdram_we_n(sdram_we_n),.sdram_ldqm(sdram_ldqm),.sdram_udqm(sdram_udqm));
endmodule
`default_nettype wire
