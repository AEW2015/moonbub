// One registered accepted packet request at a time, with retained owner and identity.
`timescale 1ns/1ps
`default_nettype none
module cu71_packet_arbiter_cut_v001(
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
 // Exactly one accepted request: queued before backend issue, then awaiting response.
 reg pending=0,outstanding=0,owner=0,next_owner=0;
 reg [15:0] expected_address;reg [63:0] expected_generation;reg [31:0] expected_sequence;
 wire choice=p1_valid&&(!p0_valid||next_owner);
 wire empty=!pending&&!outstanding;
 assign req_valid=!rst&&pending;
 assign req_address=expected_address;
 assign req_generation=expected_generation;
 assign req_sequence=expected_sequence;
 assign p0_ready=!rst&&empty&&!choice;
 assign p1_ready=!rst&&empty&&choice;
 assign p0_rsp_valid=!rst&&outstanding&&!owner&&rsp_valid;
 assign p1_rsp_valid=!rst&&outstanding&&owner&&rsp_valid;
 assign p0_rsp_address=rsp_address;assign p1_rsp_address=rsp_address;
 assign p0_rsp_generation=rsp_generation;assign p1_rsp_generation=rsp_generation;
 assign p0_rsp_sequence=rsp_sequence;assign p1_rsp_sequence=rsp_sequence;
 assign p0_rsp_data=rsp_data;assign p1_rsp_data=rsp_data;
 assign rsp_ready=outstanding&&(owner?p1_rsp_ready:p0_rsp_ready)&&!rst;
 // Fence root release on the SAME edge as a new upstream acceptance.
 assign busy=pending||outstanding||(!rst&&empty&&(p0_valid||p1_valid));
 always @(posedge clk)begin
  if(rst)begin pending<=0;outstanding<=0;owner<=0;next_owner<=0;identity_fault<=0;expected_address<=0;expected_generation<=0;expected_sequence<=0;end
  else begin
   if((p0_valid&&p0_ready)||(p1_valid&&p1_ready))begin
    pending<=1;owner<=choice;next_owner<=!choice;
    expected_address<=choice?p1_address:p0_address;
    expected_generation<=choice?p1_generation:p0_generation;
    expected_sequence<=choice?p1_sequence:p0_sequence;
   end
   if(req_valid&&req_ready)begin pending<=0;outstanding<=1;end
   // Match the original: even an identity-bad outstanding response is forwarded
   // to its owner and faults; unsolicited/preissue responses fault but never route.
   if(rsp_valid&&outstanding)begin
    if(rsp_address!=expected_address||rsp_generation!=expected_generation||rsp_sequence!=expected_sequence)identity_fault<=1;
    if(rsp_ready)outstanding<=0;
   end
   if(rsp_valid&&!outstanding)identity_fault<=1;
  end
 end

endmodule
`default_nettype wire
