`timescale 1ns/1ps
`default_nettype none
module canonical_rgb565_tiled #(parameter bit RETAIN_ROWS=1)(
 input logic clk,power_on_reset,reset,start,cancel,
 input logic [31:0] start_epoch,start_generation,input logic [1:0] start_bank,
 output logic start_ready,busy,draining,done,output logic [7:0] error,
 output logic mem_req_valid,input logic mem_req_ready,output logic [18:0] mem_req_addr,
 output logic [1:0] mem_req_bank,output logic [31:0] mem_req_epoch,mem_req_generation,
 input logic mem_rsp_valid,output logic mem_rsp_ready,input logic [127:0] mem_rsp_data,
 input logic [18:0] mem_rsp_addr,input logic [1:0] mem_rsp_bank,
 input logic [31:0] mem_rsp_epoch,mem_rsp_generation,input logic mem_rsp_error,
 output logic line_req_valid,line_req_ready,output logic [18:0] line_req_addr,
 output logic [31:0] line_req_epoch,line_req_token,
 output logic line_rsp_valid,line_rsp_ready,output logic [127:0] line_rsp_data,
 output logic [18:0] line_rsp_addr,output logic [1:0] line_rsp_bank,
 output logic [31:0] line_rsp_epoch,line_rsp_generation,line_rsp_token,output logic [3:0] line_rsp_error,
 output logic [1:0] lease_bank,output logic [31:0] lease_epoch,lease_generation,
 output logic reader_active,reader_busy,reader_pending,output logic [3:0] reader_error,
 output logic [2:0] reader_state,output logic [7:0] valid_fragments,
 output logic [31:0] reader_requests,reader_responses,reader_errors,
 output logic [31:0] reader_physical_requests,reader_physical_responses,reader_row_hits,reader_scratch_hits,
 output logic core_ready,core_busy,core_draining,core_done,output logic [7:0] core_error,
    output logic out_valid,
    input logic out_ready,
    output logic [15:0] out_word,
    output logic [18:0] out_addr,
    output logic [31:0] out_epoch,
    output logic [3:0] state,
    output logic [63:0] count_reads, count_responses, count_pixels, count_cycles,
    output logic [63:0] count_luma_reads, count_chroma_reads, count_lookups,
    output logic [63:0] count_row_fills, count_cache_hits,
    output logic [1:0] row_valid,
    output logic [7:0] row_tag [0:1],
    output logic [7:0] fill_row,
    output logic fill_slot, fill_plane,
    output logic [8:0] fill_column,
    output logic lookup_launch, lookup_response, dbg_pending,
    output logic [1:0] adapter_state,
    output logic adapter_pending,adapter_byte_pending,adapter_busy,
    output logic [2:0] line_valid,
    output logic [18:0] line_address [0:2],
    output logic [63:0] count_byte_requests,count_hits,count_misses,
    output logic [63:0] count_physical_requests,count_physical_responses,
    output logic byte_req_valid,byte_req_ready,byte_rsp_valid,byte_rsp_ready,
    output logic [18:0] byte_req_addr,
    output logic [31:0] byte_req_epoch,byte_rsp_epoch,
    output logic [7:0] byte_rsp_data,
    output logic byte_rsp_error,
    output logic [63:0] count_direct_consumes,count_canonical_consumed,
    output logic direct_consume,
    output logic [18:0] direct_addr,
    output logic [31:0] direct_epoch,
    output logic [7:0] direct_data
);
 logic owned,fault_seen,reader_ready,accepted,accepted_good,kill_engines,finish_reader;
 logic core_req_valid,core_req_ready,core_rsp_error;
 logic [18:0] core_req_addr;
 logic [31:0] core_req_epoch,ticket;
 logic line_pending;
 logic [18:0] owned_line;
 logic [31:0] owned_ticket;
 assign accepted=start&&start_ready;
 assign accepted_good=accepted&&start_bank<3&&start_epoch!=0&&start_generation!=0;
 assign start_ready=!owned&&core_ready&&reader_ready&&!power_on_reset&&!reset&&!cancel;
 assign kill_engines=reset||cancel||(owned&&!fault_seen&&(core_error!=0||reader_error!=0));
 assign busy=owned||core_busy||reader_busy;
 assign draining=!owned&&(core_busy||reader_busy);
 assign finish_reader=owned&&core_done&&!core_busy;
 assign line_req_valid=core_req_valid&&owned;
 assign core_req_ready=line_req_ready&&owned;
 assign line_req_addr=core_req_addr;
 assign line_req_epoch=core_req_epoch;
 assign line_req_token=ticket;
 assign core_rsp_error=line_rsp_error!=0||line_rsp_bank!=lease_bank||line_rsp_generation!=lease_generation||line_rsp_addr!=owned_line||line_rsp_token!=owned_ticket;
 always_ff @(posedge clk)begin
  if(power_on_reset)begin
   owned<=0;fault_seen<=0;done<=0;error<=0;lease_bank<=0;lease_epoch<=0;lease_generation<=0;
  end else if(reset||cancel)begin owned<=0;fault_seen<=1;done<=0;error<=8'd2;end
  else if(accepted)begin
   owned<=accepted_good;fault_seen<=0;done<=0;error<=accepted_good?8'd0:8'd1;
   lease_bank<=start_bank;lease_epoch<=start_epoch;lease_generation<=start_generation;
  end else if(owned&&!fault_seen&&(core_error!=0||reader_error!=0))begin
   owned<=0;fault_seen<=1;done<=0;error<=reader_error!=0?(8'h80|{4'd0,reader_error}):core_error;
  end else if(owned&&core_done&&!core_busy&&!reader_busy)begin owned<=0;done<=1;end
 end
 always_ff @(posedge clk)begin
  if(power_on_reset)begin ticket<=0;line_pending<=0;owned_line<=0;owned_ticket<=0;end
  else begin
   if(accepted_good)ticket<=0;
   if(line_req_valid&&line_req_ready)begin
    ticket<=ticket+1;line_pending<=1;owned_line<=line_req_addr;owned_ticket<=ticket;
   end
   if(line_rsp_valid&&line_rsp_ready)line_pending<=0;
  end
 end
 canonical_rgb565_lines converter(
  .count_direct_consumes(count_direct_consumes),.count_canonical_consumed(count_canonical_consumed),
  .direct_consume(direct_consume),.direct_addr(direct_addr),.direct_epoch(direct_epoch),.direct_data(direct_data),

  .clk(clk),.reset(power_on_reset||reset),.start(accepted_good),.cancel(kill_engines&&!reset),.start_epoch(start_epoch),
  .start_ready(core_ready),.busy(core_busy),.draining(core_draining),.done(core_done),.error(core_error),
  .mem_req_valid(core_req_valid),.mem_req_ready(core_req_ready),.mem_req_addr(core_req_addr),.mem_req_epoch(core_req_epoch),
  .mem_rsp_valid(line_rsp_valid),.mem_rsp_ready(line_rsp_ready),.mem_rsp_data(line_rsp_data),.mem_rsp_epoch(line_rsp_epoch),.mem_rsp_error(core_rsp_error),
  .out_valid(out_valid),
  .out_ready(out_ready),
  .out_word(out_word),
  .out_addr(out_addr),
  .out_epoch(out_epoch),
  .state(state),
  .count_reads(count_reads),
  .count_responses(count_responses),
  .count_pixels(count_pixels),
  .count_cycles(count_cycles),
  .count_luma_reads(count_luma_reads),
  .count_chroma_reads(count_chroma_reads),
  .count_lookups(count_lookups),
  .count_row_fills(count_row_fills),
  .count_cache_hits(count_cache_hits),
  .row_valid(row_valid),
  .row_tag(row_tag),
  .fill_row(fill_row),
  .fill_slot(fill_slot),
  .fill_plane(fill_plane),
  .fill_column(fill_column),
  .lookup_launch(lookup_launch),
  .lookup_response(lookup_response),
  .dbg_pending(dbg_pending),
  .adapter_state(adapter_state),
  .adapter_pending(adapter_pending),
  .adapter_byte_pending(adapter_byte_pending),
  .adapter_busy(adapter_busy),
  .line_valid(line_valid),
  .line_address(line_address),
  .count_byte_requests(count_byte_requests),
  .count_hits(count_hits),
  .count_misses(count_misses),
  .count_physical_requests(count_physical_requests),
  .count_physical_responses(count_physical_responses),
  .byte_req_valid(byte_req_valid),
  .byte_req_ready(byte_req_ready),
  .byte_rsp_valid(byte_rsp_valid),
  .byte_rsp_ready(byte_rsp_ready),
  .byte_req_addr(byte_req_addr),
  .byte_req_epoch(byte_req_epoch),
  .byte_rsp_epoch(byte_rsp_epoch),
  .byte_rsp_data(byte_rsp_data),
  .byte_rsp_error(byte_rsp_error)
 );
 tile_rowpair_reader #(.RETAIN_ROWS(RETAIN_ROWS)) reader(
  .clk(clk),.power_on_reset(power_on_reset),.reset(reset),.cancel(kill_engines&&!reset),
  .start(accepted_good),.start_ready(reader_ready),.start_bank(start_bank),.start_epoch(start_epoch),.start_generation(start_generation),
  .finish(finish_reader),.active(reader_active),.busy(reader_busy),.session_error(reader_error),
  .req_valid(line_req_valid),.req_ready(line_req_ready),.req_addr(line_req_addr),.req_bank(lease_bank),.req_epoch(line_req_epoch),.req_generation(lease_generation),.req_token(line_req_token),
  .rsp_valid(line_rsp_valid),.rsp_ready(line_rsp_ready),.rsp_data(line_rsp_data),.rsp_addr(line_rsp_addr),.rsp_bank(line_rsp_bank),
  .rsp_epoch(line_rsp_epoch),.rsp_generation(line_rsp_generation),.rsp_token(line_rsp_token),.rsp_error(line_rsp_error),
  .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),.mem_req_addr(mem_req_addr),.mem_req_bank(mem_req_bank),.mem_req_epoch(mem_req_epoch),.mem_req_generation(mem_req_generation),
  .mem_rsp_valid(mem_rsp_valid),.mem_rsp_ready(mem_rsp_ready),.mem_rsp_data(mem_rsp_data),.mem_rsp_addr(mem_rsp_addr),.mem_rsp_bank(mem_rsp_bank),.mem_rsp_epoch(mem_rsp_epoch),.mem_rsp_generation(mem_rsp_generation),.mem_rsp_error(mem_rsp_error),
  .physical_pending(reader_pending),.state(reader_state),.count_requests(reader_requests),.count_responses(reader_responses),.count_errors(reader_errors),
  .count_physical_requests(reader_physical_requests),.count_physical_responses(reader_physical_responses),.count_row_hits(reader_row_hits),.count_scratch_hits(reader_scratch_hits),.valid_fragments(valid_fragments)
 );
 always_ff @(posedge clk)if(!power_on_reset)begin
  if(accepted_good)assert(!busy&&!line_pending&&!reader_pending)else $fatal(1,"joined start over owned lease");
  if(line_req_valid&&line_req_ready)assert(!line_pending&&line_req_epoch==lease_epoch)else $fatal(1,"joined line request lease");
  if(line_rsp_valid)assert(line_pending&&line_rsp_epoch==lease_epoch)else $fatal(1,"joined line response owner");
  if(done)assert(!busy&&!reader_pending&&!line_pending&&count_pixels==345600)else $fatal(1,"joined completion before full closure");
 end
endmodule
`default_nettype wire
