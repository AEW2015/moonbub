`timescale 1ns/1ps
// Two bounded reference slots filled by authenticated, held 128-bit blocks.
module cu81_reference_prefetch (
 input logic clk,rst,abort_i,
 input logic epoch_valid,output logic epoch_ready,input logic [63:0] epoch_generation,
 input logic [1:0] epoch_reference_bank,input logic lease_held,
 output logic lease_busy,epoch_active,draining,epoch_done,epoch_aborted,epoch_fault,
 output logic [3:0] fault_code,
 input logic lookup_valid,output logic lookup_ready,input logic [63:0] lookup_generation,
 input logic [1:0] lookup_reference_bank,lookup_plane,input logic [16:0] lookup_tile,
 output logic ref_valid,input logic ref_ready,output logic [63:0] ref_generation,
 output logic [1:0] ref_reference_bank,ref_plane,output logic [16:0] ref_tile,
 output logic [511:0] ref_pixels,
 // Caller authenticates successful candidate completion and translates its bank to reference_bank.
 input logic retire_valid,output logic retire_ready,input logic [63:0] retire_generation,
 input logic [1:0] retire_reference_bank,retire_plane,input logic [16:0] retire_tile,input logic retire_unused,
 output logic mem_req_valid,input logic mem_req_ready,output logic [23:0] mem_req_address,
 output logic [63:0] mem_req_generation,output logic [1:0] mem_req_bank,mem_req_plane,mem_req_block,output logic [16:0] mem_req_index,
 input logic mem_rsp_valid,output logic mem_rsp_ready,input logic [127:0] mem_rsp_data,
 input logic [63:0] mem_rsp_generation,input logic [1:0] mem_rsp_bank,mem_rsp_plane,mem_rsp_block,input logic [16:0] mem_rsp_index,input logic mem_rsp_error,
 output logic block_commit,output logic [23:0] block_commit_address,
 output logic mem_outstanding,output logic [1:0] slot_occupied,slot_full,
 output logic [31:0] read_commands,read_beats,tiles_filled,lookups,tiles_retired,unused_retired
);
 `include "cu70_memory_map.svh"
 localparam logic [1:0] EMPTY=0,FILL=1,FULL=2;
 logic active,aborting,pending,response_pending,response_slot;
 logic [63:0] generation,latest_generation,slot_generation[2];
 logic [1:0] bank,slot_bank[2],slot_plane[2],slot_state[2];
 logic [16:0] slot_tile[2],walk_tile;
 logic [1:0] walk_plane;
 logic [13:0] allocated;
 logic [511:0] slot_pixels[2];
 logic claimed[2],served[2];
 logic [2:0] blocks[2];
 logic read_slot;
 logic [1:0] read_block;logic [23:0] read_address;
 logic empty_found,empty_slot,fill_found,fill_slot,lookup_found,lookup_slot,retire_found,retire_slot;
 logic fault_now;
 logic [3:0] fault_now_code;
 always_comb begin
  fault_now=0;fault_now_code=0;
  if(active&&!aborting)begin
   if(!lease_held)begin fault_now=1;fault_now_code=2;end
   else if(mem_rsp_valid&&!pending)begin fault_now=1;fault_now_code=3;end
   else if(mem_rsp_valid&&pending&&!rst)begin
    if(mem_rsp_error)begin fault_now=1;fault_now_code=4;end
    else if(mem_rsp_generation!=slot_generation[read_slot]||mem_rsp_bank!=slot_bank[read_slot]||mem_rsp_plane!=slot_plane[read_slot]||mem_rsp_index!=slot_tile[read_slot])begin fault_now=1;fault_now_code=5;end
    else if(mem_rsp_block!=read_block)begin fault_now=1;fault_now_code=6;end
   end
  end
  empty_found=0;empty_slot=0;fill_found=0;fill_slot=0;
  lookup_found=0;lookup_slot=0;retire_found=0;retire_slot=0;
  for(integer i=1;i>=0;i=i-1)begin
   slot_occupied[i]=slot_state[i]!=EMPTY;slot_full[i]=slot_state[i]==FULL;
   if(slot_state[i]==EMPTY)begin empty_found=1;empty_slot=1'(i);end
   if(slot_state[i]==FILL)begin fill_found=1;fill_slot=1'(i);end
   if(slot_state[i]==FULL&&slot_generation[i]==lookup_generation&&slot_bank[i]==lookup_reference_bank&&slot_plane[i]==lookup_plane&&slot_tile[i]==lookup_tile&&!claimed[i])begin lookup_found=1;lookup_slot=1'(i);end
   if(slot_state[i]==FULL&&slot_generation[i]==retire_generation&&slot_bank[i]==retire_reference_bank&&slot_plane[i]==retire_plane&&slot_tile[i]==retire_tile&&!(response_pending&&response_slot==1'(i))&&((retire_unused&&!claimed[i])||(!retire_unused&&claimed[i]&&served[i])))begin retire_found=1;retire_slot=1'(i);end
  end
  epoch_ready=!rst&&!abort_i&&!active&&!pending;
  lease_busy=active||pending;epoch_active=active;draining=aborting&&pending;mem_outstanding=pending;
  lookup_ready=active&&!rst&&!abort_i&&!aborting&&!fault_now&&lease_held&&!response_pending&&lookup_found;
  retire_ready=active&&!rst&&!abort_i&&!aborting&&!fault_now&&lease_held&&retire_found&&!(lookup_valid&&lookup_ready&&lookup_slot==retire_slot);
  ref_valid=response_pending&&active&&!rst&&!abort_i&&!aborting&&!fault_now&&lease_held;
  ref_generation=slot_generation[response_slot];ref_reference_bank=slot_bank[response_slot];
  ref_plane=slot_plane[response_slot];ref_tile=slot_tile[response_slot];ref_pixels=slot_pixels[response_slot];
  mem_req_valid=active&&!rst&&!abort_i&&!aborting&&!fault_now&&lease_held&&!pending&&fill_found;
  mem_req_address=canonical_base(slot_bank[fill_slot])+(slot_plane[fill_slot]==0?24'd0:slot_plane[fill_slot]==1?24'd172800:24'd216000)+24'(slot_tile[fill_slot])*24'd32+24'(blocks[fill_slot])*24'd8;
  mem_req_generation=slot_generation[fill_slot];mem_req_bank=slot_bank[fill_slot];mem_req_plane=slot_plane[fill_slot];mem_req_index=slot_tile[fill_slot];mem_req_block=2'(blocks[fill_slot]);
  mem_rsp_ready=pending&&!rst;
  block_commit=mem_rsp_valid&&mem_rsp_ready&&active&&!aborting&&!abort_i&&!fault_now&&lease_held;block_commit_address=read_address;

 end
 always_ff @(posedge clk)begin
  if(rst)begin
   active<=0;aborting<=0;pending<=0;response_pending<=0;response_slot<=0;
   generation<=0;latest_generation<=0;bank<=0;walk_tile<=0;walk_plane<=0;allocated<=0;read_slot<=0;read_block<=0;read_address<=0;
   epoch_done<=0;epoch_aborted<=0;epoch_fault<=0;fault_code<=0;
   read_commands<=0;read_beats<=0;tiles_filled<=0;lookups<=0;tiles_retired<=0;unused_retired<=0;
   for(integer i=0;i<2;i=i+1)begin slot_state[i]<=EMPTY;slot_generation[i]<=0;slot_bank[i]<=0;slot_plane[i]<=0;slot_tile[i]<=0;slot_pixels[i]<=0;claimed[i]<=0;served[i]<=0;blocks[i]<=0;end
  end else begin
   epoch_done<=0;epoch_aborted<=0;
   if(epoch_valid&&epoch_ready)begin
    epoch_fault<=0;fault_code<=0;generation<=epoch_generation;bank<=epoch_reference_bank;
    walk_tile<=0;walk_plane<=0;allocated<=0;aborting<=0;response_pending<=0;
    read_commands<=0;read_beats<=0;tiles_filled<=0;lookups<=0;tiles_retired<=0;unused_retired<=0;
    if(epoch_generation==0||epoch_generation<=latest_generation||epoch_reference_bank>2||!lease_held)begin epoch_fault<=1;fault_code<=1;epoch_done<=1;epoch_aborted<=1;end
    else begin active<=1;latest_generation<=epoch_generation;end
   end
   if(active&&!aborting&&!abort_i&&!fault_now&&lease_held)begin
    if(empty_found&&!fill_found&&allocated<8100)begin
     slot_state[empty_slot]<=FILL;slot_generation[empty_slot]<=generation;slot_bank[empty_slot]<=bank;
     slot_plane[empty_slot]<=walk_plane;slot_tile[empty_slot]<=walk_tile;slot_pixels[empty_slot]<=0;
     claimed[empty_slot]<=0;served[empty_slot]<=0;blocks[empty_slot]<=0;allocated<=allocated+1'b1;
     if(walk_tile==(walk_plane==0?17'd5399:17'd1349))begin walk_tile<=0;walk_plane<=walk_plane+1'b1;end
     else walk_tile<=walk_tile+1'b1;
    end
    if(lookup_valid&&lookup_ready)begin response_pending<=1;response_slot<=lookup_slot;claimed[lookup_slot]<=1;lookups<=lookups+1'b1;end
    if(ref_valid&&ref_ready)begin response_pending<=0;served[response_slot]<=1;end
    if(retire_valid&&retire_ready)begin slot_state[retire_slot]<=EMPTY;tiles_retired<=tiles_retired+1'b1;if(retire_unused)unused_retired<=unused_retired+1'b1;end
    if(mem_req_valid&&mem_req_ready)begin pending<=1;read_slot<=fill_slot;read_block<=2'(blocks[fill_slot]);read_address<=mem_req_address;read_commands<=read_commands+1'b1;end
    if(allocated==8100&&!slot_occupied[0]&&!slot_occupied[1]&&!pending)begin active<=0;epoch_done<=1;end
   end
   if(mem_rsp_valid&&mem_rsp_ready)begin
    // The physical BL8 is represented by one authenticated 128-bit transfer.
    read_beats<=read_beats+32'd8;pending<=0;
    if(!aborting&&!abort_i&&!fault_now)begin
     slot_pixels[read_slot][int'(read_block)*128+:128]<=mem_rsp_data;
     blocks[read_slot]<=blocks[read_slot]+1'b1;
     if(read_block==3)begin slot_state[read_slot]<=FULL;tiles_filled<=tiles_filled+1'b1;end
    end
   end
   if(active&&(abort_i||fault_now))begin
    aborting<=1;response_pending<=0;
    for(integer i=0;i<2;i=i+1)slot_state[i]<=EMPTY;
    if(fault_now)begin epoch_fault<=1;fault_code<=fault_now_code;end
   end
   if(active&&aborting&&!pending)begin active<=0;aborting<=0;epoch_done<=1;epoch_aborted<=1;end
  end
 end
endmodule
