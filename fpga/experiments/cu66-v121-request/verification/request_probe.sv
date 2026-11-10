module request_probe (
    input logic  clk,
    input logic  reset,
    input logic  cancel,
    input logic  start,
    input logic  clear_stats,
    input logic [31:0] start_offset,
    input logic [31:0] start_length,
    input logic [31:0] start_epoch,
    input logic  req_ready,
    input logic  rsp_valid,
    input logic [31:0] rsp_addr,
    input logic [31:0] rsp_epoch,
    input logic [7:0] rsp_data,
    input logic  out_ready,
    output logic  req_valid,
    output logic [31:0] req_addr,
    output logic [31:0] req_epoch,
    output logic  out_valid,
    output logic [7:0] out_data,
    output logic  out_last,
    output logic  done,
    output logic [7:0] error,
    output logic  active,
    output logic [1:0] fifo_count,
    output logic  pending,
    output logic  push_event,
    output logic  pop_event,
    output logic [31:0] count_requests,
    output logic [31:0] count_responses,
    output logic [31:0] count_pops,
    output logic [31:0] count_stalls,
    output logic [31:0] count_cancel_queued,
    output logic [31:0] count_cancel_pending,
    output logic [1:0] max_count,
    output logic [1:0] max_owned,
    output logic mismatch
);
    logic  original_req_valid;
    logic [31:0] original_req_addr;
    logic [31:0] original_req_epoch;
    logic  original_out_valid;
    logic [7:0] original_out_data;
    logic  original_out_last;
    logic  original_done;
    logic [7:0] original_error;
    logic  original_active;
    logic [1:0] original_fifo_count;
    logic  original_pending;
    logic  original_push_event;
    logic  original_pop_event;
    logic [31:0] original_count_requests;
    logic [31:0] original_count_responses;
    logic [31:0] original_count_pops;
    logic [31:0] original_count_stalls;
    logic [31:0] original_count_cancel_queued;
    logic [31:0] original_count_cancel_pending;
    logic [1:0] original_max_count;
    logic [1:0] original_max_owned;
    request_original original(
        .clk(clk),
        .reset(reset),
        .cancel(cancel),
        .start(start),
        .clear_stats(clear_stats),
        .start_offset(start_offset),
        .start_length(start_length),
        .start_epoch(start_epoch),
        .req_ready(req_ready),
        .rsp_valid(rsp_valid),
        .rsp_addr(rsp_addr),
        .rsp_epoch(rsp_epoch),
        .rsp_data(rsp_data),
        .out_ready(out_ready),
        .req_valid(original_req_valid),
        .req_addr(original_req_addr),
        .req_epoch(original_req_epoch),
        .out_valid(original_out_valid),
        .out_data(original_out_data),
        .out_last(original_out_last),
        .done(original_done),
        .error(original_error),
        .active(original_active),
        .fifo_count(original_fifo_count),
        .pending(original_pending),
        .push_event(original_push_event),
        .pop_event(original_pop_event),
        .count_requests(original_count_requests),
        .count_responses(original_count_responses),
        .count_pops(original_count_pops),
        .count_stalls(original_count_stalls),
        .count_cancel_queued(original_count_cancel_queued),
        .count_cancel_pending(original_count_cancel_pending),
        .max_count(original_max_count),
        .max_owned(original_max_owned)
    );
    request_candidate candidate(
        .clk(clk),
        .reset(reset),
        .cancel(cancel),
        .start(start),
        .clear_stats(clear_stats),
        .start_offset(start_offset),
        .start_length(start_length),
        .start_epoch(start_epoch),
        .req_ready(req_ready),
        .rsp_valid(rsp_valid),
        .rsp_addr(rsp_addr),
        .rsp_epoch(rsp_epoch),
        .rsp_data(rsp_data),
        .out_ready(out_ready),
        .req_valid(req_valid),
        .req_addr(req_addr),
        .req_epoch(req_epoch),
        .out_valid(out_valid),
        .out_data(out_data),
        .out_last(out_last),
        .done(done),
        .error(error),
        .active(active),
        .fifo_count(fifo_count),
        .pending(pending),
        .push_event(push_event),
        .pop_event(pop_event),
        .count_requests(count_requests),
        .count_responses(count_responses),
        .count_pops(count_pops),
        .count_stalls(count_stalls),
        .count_cancel_queued(count_cancel_queued),
        .count_cancel_pending(count_cancel_pending),
        .max_count(max_count),
        .max_owned(max_owned)
    );
    assign mismatch=(original_req_valid!=req_valid) ||
        (original_req_addr!=req_addr) ||
        (original_req_epoch!=req_epoch) ||
        (original_out_valid!=out_valid) ||
        (original_out_data!=out_data) ||
        (original_out_last!=out_last) ||
        (original_done!=done) ||
        (original_error!=error) ||
        (original_active!=active) ||
        (original_fifo_count!=fifo_count) ||
        (original_pending!=pending) ||
        (original_push_event!=push_event) ||
        (original_pop_event!=pop_event) ||
        (original_count_requests!=count_requests) ||
        (original_count_responses!=count_responses) ||
        (original_count_pops!=count_pops) ||
        (original_count_stalls!=count_stalls) ||
        (original_count_cancel_queued!=count_cancel_queued) ||
        (original_count_cancel_pending!=count_cancel_pending) ||
        (original_max_count!=max_count) ||
        (original_max_owned!=max_owned);
endmodule
