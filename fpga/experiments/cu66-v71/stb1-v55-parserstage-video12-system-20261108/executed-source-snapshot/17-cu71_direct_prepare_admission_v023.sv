// DY71 provisional cache ownership. No invented completion or RGB readiness.
`timescale 1ns/1ps
module cu71_direct_prepare_admission_v023(
 input wire clk,rst,kill,
 input wire start_valid,output wire start_ready,
 input wire[63:0]generation,input wire[31:0]frame_id,
 input wire[1:0]canonical_bank,hud_bank,input wire cache_slot,
 output wire result_valid,input wire result_ready,
 output wire[63:0]result_generation,output wire[31:0]result_frame_id,
 output wire result_slot,result_success,output wire[7:0]result_reason,
 output wire worker_drained,busy,output reg fault,
 input wire descriptor_accepted,input wire[63:0]descriptor_generation,
 input wire[31:0]descriptor_frame_id,input wire descriptor_slot,
 output wire owner_prepare_valid,input wire owner_prepare_ready,
 output wire[63:0]owner_prepare_generation,output wire[31:0]owner_prepare_frame_id,
 output wire[1:0]owner_prepare_canonical_bank,owner_prepare_hud_bank,
 output wire owner_prepare_slot,
 input wire owner_prepared_raw_valid,
 input wire owner_prepared_valid,output wire owner_prepared_ready,
 input wire[63:0]owner_prepared_generation,input wire[31:0]owner_prepared_frame_id,
 input wire owner_prepared_slot,owner_prepared_error,input wire[7:0]owner_prepared_reason,
 output wire owner_abort_valid,input wire owner_abort_ready,
 output wire[63:0]owner_abort_generation,output wire[31:0]owner_abort_frame_id,
 output wire owner_abort_slot,input wire owner_abort_done,owner_abort_error
);
 localparam[2:0]IDLE=0,ACTIVE=1,READY=2,CANCEL=3,FAULT=4;
 reg[2:0]state;reg[63:0]held_generation;reg[31:0]held_frame;reg held_slot;
 wire prepared_match=owner_prepared_generation==held_generation&&owner_prepared_frame_id==held_frame&&owner_prepared_slot==held_slot;
 wire descriptor_match=descriptor_generation==held_generation&&descriptor_frame_id==held_frame&&descriptor_slot==held_slot;
 assign owner_prepare_valid=start_valid&&state==IDLE&&!kill&&!rst;
 assign start_ready=owner_prepare_ready&&state==IDLE&&!kill&&!rst;
 assign owner_prepare_generation=generation;assign owner_prepare_frame_id=frame_id;
 assign owner_prepare_canonical_bank=canonical_bank;assign owner_prepare_hud_bank=hud_bank;assign owner_prepare_slot=cache_slot;
 assign result_valid=state==ACTIVE&&owner_prepared_raw_valid&&prepared_match&&!kill&&!rst;
 assign owner_prepared_ready=state==ACTIVE&&prepared_match&&result_ready&&!kill&&!rst;
 assign result_generation=owner_prepared_generation;assign result_frame_id=owner_prepared_frame_id;
 assign result_slot=owner_prepared_slot;assign result_success=!owner_prepared_error;assign result_reason=owner_prepared_reason;
 assign owner_abort_valid=kill&&(state==ACTIVE||state==READY)&&!rst;
 assign owner_abort_generation=held_generation;assign owner_abort_frame_id=held_frame;assign owner_abort_slot=held_slot;
 // READY is work-drained but its lease remains owned until descriptor handoff.
 // During kill it is never drained until a real matching cancellation completes.
 assign worker_drained=!rst&&(state==IDLE||(state==READY&&!kill));
 assign busy=state==ACTIVE||state==CANCEL||state==FAULT;
 always @(posedge clk)begin
  if(rst)begin state<=IDLE;held_generation<=0;held_frame<=0;held_slot<=0;fault<=0;end
  else begin
   if(owner_prepared_valid&&state==ACTIVE&&!prepared_match)fault<=1;
   if(descriptor_accepted)begin
    if(state==READY&&descriptor_match&&!kill)state<=IDLE;
    else begin state<=FAULT;fault<=1;end
   end else if(owner_abort_valid&&owner_abort_ready)state<=CANCEL;
   else if(state==CANCEL&&owner_abort_done)begin
    if(owner_abort_error)begin state<=FAULT;fault<=1;end else state<=IDLE;
   end else if(result_valid&&result_ready)begin
    if(owner_prepared_error)state<=IDLE;else state<=READY;
   end else if(owner_prepare_valid&&owner_prepare_ready)begin
    state<=ACTIVE;held_generation<=generation;held_frame<=frame_id;held_slot<=cache_slot;
   end
  end
 end
endmodule
