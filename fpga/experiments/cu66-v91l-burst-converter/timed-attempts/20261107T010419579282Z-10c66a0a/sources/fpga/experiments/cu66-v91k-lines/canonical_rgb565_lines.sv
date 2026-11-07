// Frozen chroma converter joined to a bounded 128-bit read gatherer.
module canonical_rgb565_lines (
    input logic clk, reset, start, cancel,
    input logic [31:0] start_epoch,
    output logic start_ready, busy, draining, done,
    output logic [7:0] error,
    output logic mem_req_valid,
    input logic mem_req_ready,
    output logic [18:0] mem_req_addr,
    output logic [31:0] mem_req_epoch,
    input logic mem_rsp_valid,
    output logic mem_rsp_ready,
    input logic [127:0] mem_rsp_data,
    input logic [31:0] mem_rsp_epoch,
    input logic mem_rsp_error,
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
    output logic byte_rsp_error
);
    logic core_ready,adapter_ready,core_done,core_busy,core_draining;
    logic [7:0] core_error,adapter_error;
    logic accepted_start,cancel_core,fault_ack,adapter_draining;
    assign accepted_start=start&&start_ready;
    assign start_ready=core_ready&&adapter_ready&&!reset&&!cancel;
    assign cancel_core=cancel||(adapter_error!=0&&!fault_ack);
    assign error=adapter_error!=0?(8'h80|adapter_error):core_error;
    assign busy=core_busy||adapter_busy;
    assign draining=core_draining||adapter_draining;
    assign done=core_done&&!adapter_busy&&error==0;
    always_ff @(posedge clk)begin
        if(reset||accepted_start)fault_ack<=0;
        else if(adapter_error!=0)fault_ack<=1;
    end
    canonical_rgb565_cached core (
        .clk(clk),
        .reset(reset),
        .start(accepted_start),
        .cancel(cancel_core),
        .start_epoch(start_epoch),
        .start_ready(core_ready),
        .busy(core_busy),
        .draining(core_draining),
        .done(core_done),
        .error(core_error),
        .mem_req_valid(byte_req_valid),
        .mem_req_ready(byte_req_ready),
        .mem_req_addr(byte_req_addr),
        .mem_req_epoch(byte_req_epoch),
        .mem_rsp_valid(byte_rsp_valid),
        .mem_rsp_ready(byte_rsp_ready),
        .mem_rsp_data(byte_rsp_data),
        .mem_rsp_epoch(byte_rsp_epoch),
        .mem_rsp_error(byte_rsp_error),
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
        .dbg_pending(dbg_pending));
    canonical_line_reader reader (
        .clk(clk),.reset(reset),.start(accepted_start),.cancel(cancel),.finish(core_done||core_error!=0),.start_epoch(start_epoch),
        .start_ready(adapter_ready),.busy(adapter_busy),.draining(adapter_draining),.error(adapter_error),
        .byte_req_valid(byte_req_valid),.byte_req_ready(byte_req_ready),.byte_req_addr(byte_req_addr),.byte_req_epoch(byte_req_epoch),
        .byte_rsp_valid(byte_rsp_valid),.byte_rsp_ready(byte_rsp_ready),.byte_rsp_data(byte_rsp_data),.byte_rsp_epoch(byte_rsp_epoch),.byte_rsp_error(byte_rsp_error),
        .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),.mem_req_addr(mem_req_addr),.mem_req_epoch(mem_req_epoch),
        .mem_rsp_valid(mem_rsp_valid),.mem_rsp_ready(mem_rsp_ready),.mem_rsp_data(mem_rsp_data),.mem_rsp_epoch(mem_rsp_epoch),.mem_rsp_error(mem_rsp_error),
        .state(adapter_state),.physical_pending(adapter_pending),.byte_pending(adapter_byte_pending),.line_valid(line_valid),.line_address(line_address),
        .count_byte_requests(count_byte_requests),.count_hits(count_hits),.count_misses(count_misses),
        .count_physical_requests(count_physical_requests),.count_physical_responses(count_physical_responses));
endmodule
