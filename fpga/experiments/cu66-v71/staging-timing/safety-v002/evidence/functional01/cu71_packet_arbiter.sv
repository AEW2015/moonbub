// One accepted synchronous packet read at a time, with retained response owner.
`timescale 1ns/1ps
`default_nettype none
module cu71_packet_arbiter(
 input wire clk,rst,
 input wire p0_valid,output wire p0_ready,input wire [15:0] p0_address,
 input wire [63:0] p0_generation,input wire [31:0] p0_sequence,
 output wire p0_rsp_valid,input wire p0_rsp_ready,output wire [15:0] p0_rsp_address,
 output wire [63:0] p0_rsp_generation,output wire [31:0] p0_rsp_sequence,output wire [7:0] p0_rsp_data,
 input wire p1_valid,output wire p1_ready,input wire [15:0] p1_address,
 input wire [63:0] p1_generation,input wire [31:0] p1_sequence,
 output wire p1_rsp_valid,input wire p1_rsp_ready,output wire [15:0] p1_rsp_address,
 output wire [63:0] p1_rsp_generation,output wire [31:0] p1_rsp_sequence,output wire [7:0] p1_rsp_data,
 output wire req_valid,input wire req_ready,output wire [15:0] req_address,
 output wire [63:0] req_generation,output wire [31:0] req_sequence,
 input wire rsp_valid,output wire rsp_ready,input wire [15:0] rsp_address,
 input wire [63:0] rsp_generation,input wire [31:0] rsp_sequence,input wire [7:0] rsp_data,
 output wire busy,output reg identity_fault
);
 reg outstanding=0,owner=0,next_owner=0,selection_locked=0,locked_choice=0;
 reg [15:0] expected_address;reg [63:0] expected_generation;reg [31:0] expected_sequence;
 wire choice=selection_locked ? locked_choice : p1_valid&&(!p0_valid||next_owner);
 assign req_valid=!rst&&!outstanding&&(p0_valid||p1_valid);
 assign req_address=choice?p1_address:p0_address;
 assign req_generation=choice?p1_generation:p0_generation;
 assign req_sequence=choice?p1_sequence:p0_sequence;
 assign p0_ready=!rst&&!outstanding&&!choice&&req_ready;
 assign p1_ready=!rst&&!outstanding&&choice&&req_ready;
 assign p0_rsp_valid=!rst&&outstanding&&!owner&&rsp_valid;
 assign p1_rsp_valid=!rst&&outstanding&&owner&&rsp_valid;
 assign p0_rsp_address=rsp_address;assign p1_rsp_address=rsp_address;
 assign p0_rsp_generation=rsp_generation;assign p1_rsp_generation=rsp_generation;
 assign p0_rsp_sequence=rsp_sequence;assign p1_rsp_sequence=rsp_sequence;
 assign p0_rsp_data=rsp_data;assign p1_rsp_data=rsp_data;
 assign rsp_ready=outstanding&&(owner?p1_rsp_ready:p0_rsp_ready)&&!rst;
 assign busy=outstanding;
 always @(posedge clk)begin
  if(rst)begin outstanding<=0;owner<=0;next_owner<=0;selection_locked<=0;locked_choice<=0;identity_fault<=0;expected_address<=0;expected_generation<=0;expected_sequence<=0;end
  else begin
   if(req_valid&&req_ready)begin
    outstanding<=1;owner<=choice;next_owner<=!choice;selection_locked<=0;
    expected_address<=req_address;expected_generation<=req_generation;expected_sequence<=req_sequence;
   end
   if(req_valid&&!req_ready&&!selection_locked)begin selection_locked<=1;locked_choice<=choice;end
   if(rsp_valid&&outstanding)begin
    if(rsp_address!=expected_address||rsp_generation!=expected_generation||rsp_sequence!=expected_sequence)identity_fault<=1;
    if(rsp_ready)outstanding<=0;
   end
   if(rsp_valid&&!outstanding)identity_fault<=1;
  end
 end
endmodule
`default_nettype wire
