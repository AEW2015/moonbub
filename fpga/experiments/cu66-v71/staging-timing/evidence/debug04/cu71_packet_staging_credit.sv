// Bounded local loader: byte-exact immutable CU66 staging, no codec substitution.
`timescale 1ns/1ps
`default_nettype none
module cu71_packet_staging_credit #(
 parameter integer MAX_BYTES=49152
)(
 input wire clk,rst,
 input wire begin_valid,output wire begin_ready,
 input wire [63:0] begin_generation,input wire [31:0] begin_bytes,begin_crc,
 input wire upload_valid,output wire upload_ready,
 input wire [31:0] upload_word,input wire [2:0] upload_count,
 input wire seal_valid,activate_valid,release_valid,discard_valid,
 output wire sealed_valid,active,output reg [63:0] generation,
 output reg [31:0] packet_bytes,written_bytes,output wire [31:0] actual_crc,
 output reg [2:0] upload_capacity,
 output reg [31:0] faults,
 input wire packet_req_valid,output wire packet_req_ready,
 input wire [15:0] packet_req_address,input wire [63:0] packet_req_generation,
 input wire [31:0] packet_req_sequence,
 output reg packet_rsp_valid,input wire packet_rsp_ready,
 output reg [15:0] packet_rsp_address,output reg [63:0] packet_rsp_generation,
 output reg [31:0] packet_rsp_sequence,output reg [7:0] packet_rsp_data
);
 localparam [1:0] EMPTY=0,LOADING=1,SEALED=2,ACTIVE=3;
 reg [1:0] state=EMPTY;
 (* ram_style="block" *) reg [7:0] bytes[0:MAX_BYTES-1];
 reg [31:0] crc=32'hffffffff,expected_crc,held_word;
 reg [2:0] held_count;
 reg [31:0] remaining_bytes;
 reg [7:0] memory_q;
 reg read_pending,read_bad;
 reg [15:0] held_address;
 reg [63:0] held_generation;
 reg [31:0] held_sequence;
 function automatic [31:0] crc_byte(input [31:0] previous,input [7:0] data);
 reg [31:0] value;integer i;
 begin
  value=previous^{24'd0,data};
  for(i=0;i<8;i=i+1)value=value[0] ? (value>>1)^32'hedb88320 : value>>1;
  crc_byte=value;
 end endfunction
 assign begin_ready=state==EMPTY&&!rst;
 assign upload_ready=state==LOADING&&held_count==0&&!rst;
 assign sealed_valid=state==SEALED&&!rst;
 assign active=state==ACTIVE&&!rst;
 assign actual_crc=~crc;
 assign packet_req_ready=active&&!read_pending&&!packet_rsp_valid;
 // One synchronous read and one byte write port; no bulk-data reset.
 always @(posedge clk)begin
  memory_q<=bytes[packet_req_address<MAX_BYTES ? packet_req_address : 16'd0];
  if(!rst&&state==LOADING&&held_count!=0)bytes[written_bytes[15:0]]<=held_word[7:0];
 end
 always @(posedge clk)begin
  if(rst)begin
   state<=EMPTY;generation<=0;packet_bytes<=0;written_bytes<=0;crc<=32'hffffffff;
   expected_crc<=0;held_word<=0;held_count<=0;remaining_bytes<=0;upload_capacity<=0;faults<=0;read_pending<=0;read_bad<=0;
   held_address<=0;held_generation<=0;held_sequence<=0;
   packet_rsp_valid<=0;packet_rsp_address<=0;packet_rsp_generation<=0;packet_rsp_sequence<=0;packet_rsp_data<=0;
  end else begin
   if(begin_valid)begin
    if(begin_ready&&begin_generation!=0&&begin_bytes!=0&&begin_bytes<=MAX_BYTES)begin
     state<=LOADING;generation<=begin_generation;packet_bytes<=begin_bytes;expected_crc<=begin_crc;
     written_bytes<=0;crc<=32'hffffffff;remaining_bytes<=begin_bytes;
     upload_capacity<=begin_bytes>=4 ? 3'd4 : begin_bytes[2:0];
    end else faults[0]<=1;
   end
   if(upload_valid)begin
    if(upload_ready&&upload_count>=1&&upload_count<=4&&
       upload_count<=upload_capacity)begin
     held_word<=upload_word;held_count<=upload_count;
    end else faults[1]<=1;
   end
   if(state==LOADING&&held_count!=0)begin
    crc<=crc_byte(crc,held_word[7:0]);held_word<=held_word>>8;
    held_count<=held_count-1'b1;written_bytes<=written_bytes+1'b1;
    remaining_bytes<=remaining_bytes-1'b1;
    upload_capacity<=remaining_bytes>4 ? 3'd4 : remaining_bytes[2:0]-3'd1;
   end
   if(seal_valid)begin
    if(state==LOADING&&held_count==0&&written_bytes==packet_bytes&&actual_crc==expected_crc)state<=SEALED;
    else faults[2]<=1;
   end
   if(activate_valid)begin
    if(sealed_valid)state<=ACTIVE;else faults[3]<=1;
   end
   if(packet_rsp_valid&&packet_rsp_ready)packet_rsp_valid<=0;
   if(packet_req_valid&&packet_req_ready)begin
    held_address<=packet_req_address;held_generation<=packet_req_generation;held_sequence<=packet_req_sequence;
    read_bad<=packet_req_address>=packet_bytes||packet_req_generation!=generation;
    if(packet_req_address>=packet_bytes||packet_req_generation!=generation)faults[4]<=1;
    read_pending<=1;
   end
   if(read_pending)begin
    packet_rsp_address<=held_address;packet_rsp_generation<=held_generation;packet_rsp_sequence<=held_sequence;
    packet_rsp_data<=read_bad ? 8'd0 : memory_q;packet_rsp_valid<=1;read_pending<=0;
   end
   // Only the root owner may request release after its accepted operations drain.
   if(release_valid)begin
    if(active&&!read_pending&&!packet_rsp_valid&&!(packet_req_valid&&packet_req_ready))state<=EMPTY;
    else faults[5]<=1;
   end
   if(discard_valid)begin
    if((state==LOADING||state==SEALED)&&held_count==0)state<=EMPTY;
    else faults[6]<=1;
   end
  end
 end
endmodule
`default_nettype wire
