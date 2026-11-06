`timescale 1ns/1ps
// Decoder-facing adapter for V81 wide-block slots. Completions are authenticated
// against admitted writes before reference-bank translation and retirement.
module cu81_reference_path (
 input logic clk,rst,abort_i,clear_fault,
 input logic epoch_valid,output logic epoch_ready,input logic [63:0] epoch_generation,
 input logic [1:0] epoch_reference_bank,epoch_candidate_bank,input logic [31:0] epoch_reference_id,
 input logic lease_held,output logic busy,fault,output logic [3:0] fault_code,
 output logic epoch_done,epoch_aborted,output logic [31:0] captured_reference_id,
 output logic [63:0] epoch_generation_active,
 input logic read_valid,output logic read_ready,input logic [63:0] read_generation,
 input logic [1:0] read_bank,read_plane,input logic [16:0] read_index,
 output logic read_rsp_valid,input logic read_rsp_ready,output logic [63:0] read_rsp_generation,
 output logic [1:0] read_rsp_bank,read_rsp_plane,output logic [16:0] read_rsp_index,
 output logic [511:0] read_rsp_pixels,output logic read_rsp_error,
 input logic write_valid,output logic write_ready,input logic [63:0] write_generation,
 input logic [1:0] write_bank,write_plane,input logic [16:0] write_index,input logic [511:0] write_pixels,
 output logic write_done_valid,input logic write_done_ready,output logic [63:0] write_done_generation,
 output logic [1:0] write_done_bank,write_done_plane,output logic [16:0] write_done_index,output logic write_done_error,
 output logic mem_write_valid,input logic mem_write_ready,output logic [63:0] mem_write_generation,
 output logic [1:0] mem_write_bank,mem_write_plane,output logic [16:0] mem_write_index,output logic [511:0] mem_write_pixels,
 input logic mem_done_valid,output logic mem_done_ready,input logic [63:0] mem_done_generation,
 input logic [1:0] mem_done_bank,mem_done_plane,input logic [16:0] mem_done_index,input logic mem_done_error,mem_write_aborted,
 output logic prefetch_req_valid,input logic prefetch_req_ready,output logic [23:0] prefetch_req_address,
 output logic [63:0] prefetch_req_generation,output logic [1:0] prefetch_req_bank,prefetch_req_plane,prefetch_req_block,output logic [16:0] prefetch_req_index,
 input logic prefetch_rsp_valid,output logic prefetch_rsp_ready,input logic [127:0] prefetch_rsp_data,
 input logic [63:0] prefetch_rsp_generation,input logic [1:0] prefetch_rsp_bank,prefetch_rsp_plane,prefetch_rsp_block,input logic [16:0] prefetch_rsp_index,input logic prefetch_rsp_error,
 output logic [31:0] prefetch_read_commands,prefetch_read_beats,prefetch_tiles_filled,prefetch_lookups,prefetch_tiles_retired,prefetch_unused_retired
);
 logic core_busy,core_fault,core_active,unused_core_draining,unused_core_outstanding,core_epoch_ready,epoch_admissible;
 logic [1:0] unused_occupied,unused_full;
 logic [3:0] core_fault_code;
 logic [63:0] generation;logic [1:0] reference_bank,candidate_bank;
 logic local_fault,core_fault_cleared,kill,lookup_pending,cancel_pending;
 logic [63:0] lookup_generation;logic [1:0] lookup_bank,lookup_plane;logic [16:0] lookup_index;
 logic core_read_valid,core_read_ready,core_rsp_valid,core_rsp_ready;
 logic [63:0] core_rsp_generation;logic [1:0] core_rsp_bank,core_rsp_plane;logic [16:0] core_rsp_index;logic [511:0] core_rsp_pixels;
 logic [1:0] ledger_valid;logic [1:0] ledger_plane[2];logic [16:0] ledger_index[2];
 logic ledger_free,ledger_free_slot,served_match,served_slot;
 logic write_pending,completion_held,completion_error,completion_retired;
 logic [63:0] accepted_generation;logic [1:0] accepted_bank,accepted_plane;logic [16:0] accepted_index;
 logic completion_match,retire_valid,retire_ready,retire_unused,write_metadata_valid;
 function automatic logic hidden_tile(input logic [1:0] plane,input logic [16:0] tile);
  integer x,y;
  begin
   x=int'(tile)%(plane==0?90:45);y=int'(tile)/(plane==0?90:45);
   if(plane==0)hidden_tile=((x>=3&&x<22)&&((y>=7&&y<9)||(y>=11&&y<13)))||
     ((x>=21&&x<61)&&(y>=45&&y<48))||((x>=21&&x<51)&&(y>=49&&y<51));
   else hidden_tile=(x>=11&&x<30&&y==23);
  end
 endfunction
 assign epoch_admissible=!lookup_pending&&!cancel_pending&&!write_pending&&!completion_held;
 assign epoch_ready=core_epoch_ready&&epoch_admissible;
 assign fault=local_fault||(core_fault&&!core_fault_cleared);
 assign fault_code=local_fault?4'd8:core_fault_code;
 assign kill=abort_i||fault;
 assign epoch_generation_active=generation;
 assign busy=core_busy||lookup_pending||cancel_pending||write_pending||completion_held;
 always_comb begin
  ledger_free=0;ledger_free_slot=0;served_match=0;served_slot=0;
  for(integer i=1;i>=0;i=i-1)begin
   if(!ledger_valid[i])begin ledger_free=1;ledger_free_slot=1'(i);end
   if(ledger_valid[i]&&ledger_plane[i]==accepted_plane&&ledger_index[i]==accepted_index)begin served_match=1;served_slot=1'(i);end
  end
 end
 assign core_read_valid=read_valid&&!lookup_pending&&!cancel_pending&&ledger_free&&!kill;

 assign read_ready=core_read_ready&&!lookup_pending&&!cancel_pending&&ledger_free&&!kill;

 assign read_rsp_valid=cancel_pending||(core_rsp_valid&&lookup_pending&&!kill);

 assign read_rsp_generation=lookup_generation;
 assign read_rsp_bank=lookup_bank;
 assign read_rsp_plane=lookup_plane;
 assign read_rsp_index=lookup_index;

 assign read_rsp_pixels=cancel_pending?512'd0:core_rsp_pixels;
 assign read_rsp_error=cancel_pending;

 assign core_rsp_ready=read_rsp_ready&&lookup_pending&&!cancel_pending&&!kill;

 assign write_metadata_valid=!core_active||(write_generation==generation&&write_bank==candidate_bank&&write_plane<=2&&write_index<(write_plane==0?17'd5400:17'd1350));
 assign mem_write_valid=write_valid&&!write_pending&&!completion_held&&!kill&&write_metadata_valid;

 assign write_ready=(write_metadata_valid?mem_write_ready:1'b1)&&!write_pending&&!completion_held&&!kill;

 assign mem_write_generation=write_generation;
 assign mem_write_bank=write_bank;
 assign mem_write_plane=write_plane;
 assign mem_write_index=write_index;
 assign mem_write_pixels=write_pixels;

 assign completion_match=write_pending&&mem_done_generation==accepted_generation&&mem_done_bank==accepted_bank&&mem_done_plane==accepted_plane&&mem_done_index==accepted_index;

 assign mem_done_ready=!completion_held&&!rst;

 assign retire_unused=hidden_tile(accepted_plane,accepted_index);

 assign retire_valid=completion_held&&!completion_retired&&!completion_error&&!kill&&
        accepted_generation==generation&&accepted_bank==candidate_bank&&(retire_unused||served_match);

 assign write_done_valid=completion_held&&(completion_retired||completion_error||kill)&&!rst;

 assign write_done_generation=accepted_generation;
 assign write_done_bank=accepted_bank;
 assign write_done_plane=accepted_plane;
 assign write_done_index=accepted_index;

 assign write_done_error=completion_error||kill;


 always_ff @(posedge clk)begin
  if(rst)begin
   generation<=0;reference_bank<=0;candidate_bank<=0;captured_reference_id<=0;local_fault<=0;core_fault_cleared<=0;
   lookup_pending<=0;cancel_pending<=0;lookup_generation<=0;lookup_bank<=0;lookup_plane<=0;lookup_index<=0;
   ledger_valid<=0;for(integer i=0;i<2;i=i+1)begin ledger_plane[i]<=0;ledger_index[i]<=0;end
   write_pending<=0;completion_held<=0;completion_error<=0;completion_retired<=0;
   accepted_generation<=0;accepted_bank<=0;accepted_plane<=0;accepted_index<=0;
  end else begin
   if(clear_fault&&!core_busy&&!lookup_pending&&!write_pending&&!completion_held)begin local_fault<=0;core_fault_cleared<=1;end
   if(epoch_valid&&epoch_ready)begin
    generation<=epoch_generation;reference_bank<=epoch_reference_bank;candidate_bank<=epoch_candidate_bank;captured_reference_id<=epoch_reference_id;
    ledger_valid<=0;core_fault_cleared<=0;local_fault<=epoch_candidate_bank>2||epoch_candidate_bank==epoch_reference_bank;
   end
   if(read_valid&&read_ready)begin lookup_pending<=1;lookup_generation<=read_generation;lookup_bank<=read_bank;lookup_plane<=read_plane;lookup_index<=read_index;end
   if(core_rsp_valid&&core_rsp_ready)begin
    lookup_pending<=0;ledger_valid[ledger_free_slot]<=1;ledger_plane[ledger_free_slot]<=lookup_plane;ledger_index[ledger_free_slot]<=lookup_index;
    if(core_rsp_generation!=lookup_generation||core_rsp_bank!=lookup_bank||core_rsp_plane!=lookup_plane||core_rsp_index!=lookup_index)local_fault<=1;
   end
   // V79 cancels its held success on abort. Preserve the receiver's accepted
   // token and return one exact-identity error so both receiver layers drain.
   if(kill&&lookup_pending)cancel_pending<=1;
   if(cancel_pending&&read_rsp_ready)begin cancel_pending<=0;lookup_pending<=0;end
   if(write_valid&&write_ready)begin
    write_pending<=1;accepted_generation<=write_generation;accepted_bank<=write_bank;accepted_plane<=write_plane;accepted_index<=write_index;
    if(!write_metadata_valid)begin local_fault<=1;completion_held<=1;completion_error<=1;completion_retired<=1;end
   end
   if(mem_done_valid&&mem_done_ready)begin
    if(completion_match)begin completion_held<=1;completion_error<=mem_done_error;completion_retired<=!core_active;end
    else begin
     local_fault<=1;
     if(write_pending)begin completion_held<=1;completion_error<=1;completion_retired<=1;end
    end
   end
   if(mem_write_aborted&&write_pending&&!completion_held)begin completion_held<=1;completion_error<=1;completion_retired<=1;end
   if(retire_valid&&retire_ready)begin completion_retired<=1;if(served_match)ledger_valid[served_slot]<=0;end
   if(write_done_valid&&write_done_ready)begin completion_held<=0;write_pending<=0;completion_retired<=0;end
   if(kill)ledger_valid<=0;
  end
 end
 cu81_reference_prefetch core(
  .clk,.rst,.abort_i(abort_i||local_fault),.epoch_valid(epoch_valid&&epoch_admissible),.epoch_ready(core_epoch_ready),.epoch_generation,.epoch_reference_bank,.lease_held,
  .lease_busy(core_busy),.epoch_active(core_active),.draining(unused_core_draining),.epoch_done,.epoch_aborted,.epoch_fault(core_fault),.fault_code(core_fault_code),
  .lookup_valid(core_read_valid),.lookup_ready(core_read_ready),.lookup_generation(read_generation),.lookup_reference_bank(read_bank),.lookup_plane(read_plane),.lookup_tile(read_index),
  .ref_valid(core_rsp_valid),.ref_ready(core_rsp_ready),.ref_generation(core_rsp_generation),.ref_reference_bank(core_rsp_bank),.ref_plane(core_rsp_plane),.ref_tile(core_rsp_index),.ref_pixels(core_rsp_pixels),
  .retire_valid,.retire_ready,.retire_generation(accepted_generation),.retire_reference_bank(reference_bank),.retire_plane(accepted_plane),.retire_tile(accepted_index),.retire_unused,
  .mem_req_valid(prefetch_req_valid),.mem_req_ready(prefetch_req_ready),.mem_req_address(prefetch_req_address),.mem_req_generation(prefetch_req_generation),.mem_req_bank(prefetch_req_bank),.mem_req_plane(prefetch_req_plane),.mem_req_index(prefetch_req_index),.mem_req_block(prefetch_req_block),
  .mem_rsp_valid(prefetch_rsp_valid),.mem_rsp_ready(prefetch_rsp_ready),.mem_rsp_data(prefetch_rsp_data),.mem_rsp_generation(prefetch_rsp_generation),.mem_rsp_bank(prefetch_rsp_bank),.mem_rsp_plane(prefetch_rsp_plane),.mem_rsp_index(prefetch_rsp_index),.mem_rsp_block(prefetch_rsp_block),.mem_rsp_error(prefetch_rsp_error),
  .block_commit(),.block_commit_address(),.mem_outstanding(unused_core_outstanding),.slot_occupied(unused_occupied),.slot_full(unused_full),.read_commands(prefetch_read_commands),.read_beats(prefetch_read_beats),.tiles_filled(prefetch_tiles_filled),.lookups(prefetch_lookups),.tiles_retired(prefetch_tiles_retired),.unused_retired(prefetch_unused_retired));
endmodule
