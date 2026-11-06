`timescale 1ns/1ps
`default_nettype none
// Composition boundary for the preserved private sink. Completion must come
// from the exact tagged KEY engine; tag validation occurs there. Check full
// owner/epoch/frame before its boolean can cross into the private storage FSM.
module ar03_yuv_store_owned #(
 parameter integer TOTAL_BYTES=518400,
 parameter [23:0] APERTURE_BASE=24'h100000,
 parameter integer APERTURE_WORDS=262144
)(
 input wire clk,reset,
 input wire start_valid,output wire start_ready,
 input wire [63:0] start_owner,input wire [31:0] start_epoch,start_frame,
 input wire [23:0] start_base,
 input wire in_valid,output wire in_ready,input wire [7:0] in_byte,
 input wire [63:0] in_owner,input wire [31:0] in_epoch,in_frame,input wire in_last,
 input wire abort,input wire fault,
 input wire completion_valid,input wire [63:0] completion_owner,
 input wire [31:0] completion_epoch,completion_frame,
 input wire release_valid,input wire [63:0] release_owner,
 input wire [31:0] release_epoch,release_frame,
 output wire completion_rejected,output wire release_rejected,
 output wire pixel_valid,input wire pixel_ready,
 output wire [23:0] pixel_address,output wire [15:0] pixel_data,
 output wire force_flush,output wire discard,input wire memory_idle,
 output wire busy,output wire done,output wire failed,output wire aborted,
 output wire [63:0] owner,output wire [31:0] accepted_bytes,
 output wire [31:0] accepted_words,output wire [3:0] error_code,state
);
 reg [31:0] held_epoch,held_frame;
 wire occupied=owner!=0;
 wire complete_match=occupied&&completion_owner==owner&&
  completion_epoch==held_epoch&&completion_frame==held_frame;
 wire release_match=occupied&&release_owner==owner&&
  release_epoch==held_epoch&&release_frame==held_frame;
 assign completion_rejected=completion_valid&&!complete_match;
 assign release_rejected=release_valid&&!release_match;
 always @(posedge clk)begin
  if(reset)begin held_epoch<=0;held_frame<=0;end
  else if(start_valid&&start_ready)begin held_epoch<=start_epoch;held_frame<=start_frame;end
 end
 ar03_yuv_store #(.TOTAL_BYTES(TOTAL_BYTES),.APERTURE_BASE(APERTURE_BASE),.APERTURE_WORDS(APERTURE_WORDS)) core(
  .clk(clk),.reset(reset),.start_valid(start_valid),.start_ready(start_ready),
  .start_owner(start_owner),.start_epoch(start_epoch),.start_frame(start_frame),.start_base(start_base),
  .in_valid(in_valid),.in_ready(in_ready),.in_byte(in_byte),.in_owner(in_owner),.in_epoch(in_epoch),.in_frame(in_frame),.in_last(in_last),
  .abort(abort),.fault(fault),.integrity_valid(completion_valid&&complete_match),.release_result(release_valid&&release_match),
  .pixel_valid(pixel_valid),.pixel_ready(pixel_ready),.pixel_address(pixel_address),.pixel_data(pixel_data),
  .force_flush(force_flush),.discard(discard),.memory_idle(memory_idle),
  .busy(busy),.done(done),.failed(failed),.aborted(aborted),.owner(owner),.accepted_bytes(accepted_bytes),
  .accepted_words(accepted_words),.error_code(error_code),.state(state));
endmodule
`default_nettype wire
