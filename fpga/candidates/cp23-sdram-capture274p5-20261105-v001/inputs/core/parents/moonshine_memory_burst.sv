`timescale 1ns/1ps
`default_nettype none
// Experimental scanout-priority adapter. Full-pixel writes are gathered into
// aligned masked BL8 bursts; scanout reads take priority between bursts.
module moonshine_memory_burst(
 input wire clk,read_clk,reset,
 input wire pixel_valid,output wire pixel_ready,input wire[23:0]pixel_address,input wire[15:0]pixel_rgb565,
 input wire force_flush,input wire discard,
 input wire line_req_valid,output wire line_req_ready,input wire[23:0]line_req_address,
 output wire line_data_valid,output wire[15:0]line_data,
 output wire idle,
 output wire[12:0]sdram_a,output wire[1:0]sdram_bs,inout wire[15:0]sdram_dq,
 output wire sdram_clk,output wire[1:0]sdram_cke,sdram_cs_n,
 output wire sdram_ras_n,sdram_cas_n,sdram_we_n,sdram_ldqm,sdram_udqm
);
 reg line_busy,burst_pending;reg[23:0]read_address;reg[8:0]received;reg[2:0]beat;
 wire req_ready,mem_idle,rsp_valid;wire[15:0]rsp_data;
 wire packed_valid,packed_ready,packed_empty;wire[23:0]packed_address;
 wire[127:0]packed_data;wire[15:0]packed_mask;
 wire request_read=line_busy&&!burst_pending;
 wire request_write=!line_busy && !line_req_valid && packed_valid;
 wire request_valid=request_read || request_write;
 assign line_req_ready=!line_busy;
 assign packed_ready=request_write && req_ready;
 assign idle=mem_idle && !line_busy && !line_req_valid && packed_empty;
 assign line_data_valid=rsp_valid && line_busy;assign line_data=rsp_data;
 moonshine_burst_packer packer(.clk(clk),.reset(reset),.pixel_valid(pixel_valid),.pixel_ready(pixel_ready),
  .pixel_address(pixel_address),.pixel_data(pixel_rgb565),.force_flush(force_flush),.discard(discard),.empty(packed_empty),
  .burst_valid(packed_valid),.burst_ready(packed_ready),.burst_address(packed_address),.burst_data(packed_data),.burst_mask(packed_mask));
 always @(posedge clk)begin
  if(reset)begin line_busy<=0;burst_pending<=0;read_address<=0;received<=0;beat<=0;end
  else begin
   if(line_req_valid&&line_req_ready)begin line_busy<=1;read_address<=line_req_address;received<=0;burst_pending<=0;end
   if(request_read&&req_ready)begin burst_pending<=1;beat<=0;end
   if(rsp_valid&&line_busy)begin
    received<=received+1'b1;beat<=beat+1'b1;
    if(beat==7)begin burst_pending<=0;read_address<=read_address+8;end
    if(received==479)line_busy<=0;
   end
  end
 end
 moonshine_sdram_burst controller(.clk(clk),.read_clk(read_clk),.reset(reset),.request_valid(request_valid),.request_ready(req_ready),
  .request_write(!request_read),.request_address(request_read ? read_address:packed_address),
  .request_burst_data(packed_data),.request_burst_mask(packed_mask),
  .response_valid(rsp_valid),.response_data(rsp_data),.idle(mem_idle),
  .sdram_a(sdram_a),.sdram_bs(sdram_bs),.sdram_dq(sdram_dq),.sdram_clk(sdram_clk),.sdram_cke(sdram_cke),.sdram_cs_n(sdram_cs_n),
  .sdram_ras_n(sdram_ras_n),.sdram_cas_n(sdram_cas_n),.sdram_we_n(sdram_we_n),.sdram_ldqm(sdram_ldqm),.sdram_udqm(sdram_udqm));
endmodule
`default_nettype wire
