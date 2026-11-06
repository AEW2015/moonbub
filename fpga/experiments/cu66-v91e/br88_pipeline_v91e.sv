// V91e observed coefficient pipeline: packet validation -> packed scratch -> dense tiles.
// This is not the pixel/reference/HUD/publication or physical memory controller.
module br88_pipeline_v91e (
    input logic clk, reset, start, abort_packet,
    input logic [31:0] packet_bytes, epoch,
    input logic [16:0] blocks,
    input logic serial_clear,
    input logic in_valid,
    output logic in_ready,
    input logic [7:0] in_data,
    input logic in_last,
    output logic out_valid,
    input logic out_ready,
    output logic [15:0] out_block,
    output logic [5:0] out_index,
    output logic signed [15:0] out_value,
    output logic [31:0] out_epoch,
    output logic done,
    output logic [7:0] error,
    output logic busy, draining, scratch_sealed,
    output logic [18:0] used_bytes,
    output logic [63:0] count_cycles, count_input_bytes, count_dense,
    output logic [63:0] count_reads, count_writes, count_dense_stall,
    output logic mem_req_valid,
    input logic mem_req_ready,
    output logic mem_req_write,
    output logic [17:0] mem_req_addr,
    output logic [127:0] mem_req_data,
    output logic [31:0] mem_req_epoch,
    input logic mem_rsp_valid,
    output logic mem_rsp_ready,
    input logic [127:0] mem_rsp_data,
    input logic [31:0] mem_rsp_epoch,
    input logic mem_rsp_error,
    output logic [3:0] packet_state,
    output logic metadata_wait,
    output logic dbg_running, dbg_allocation, dbg_seal_sent, dbg_packet_done,
    output logic dbg_coef_valid, dbg_coef_ready,
    output logic [1:0] dbg_coef_band,
    output logic dbg_meta_valid, dbg_meta_ready, dbg_meta_raw,
    output logic dbg_band_end_valid, dbg_band_end_ready,
    output logic [1:0] dbg_band_end_band,
    output logic dbg_seal_valid, dbg_seal_ready,
    output logic [4:0] dbg_scratch_state, dbg_scratch_return_state,
    output logic dbg_scratch_outstanding,
    output logic [2:0] dbg_scratch_phase,
    output logic [4:0] dbg_scratch_assembly_bytes,
    output logic [3:0] dbg_scratch_cache_valid,
    output logic [2:0] dbg_scratch_head_valid,
    output logic [63:0] count_packet_state [0:15],
    output logic [63:0] count_scratch_state [0:31],
    output logic [63:0] count_coef_stall, count_metadata_wait, count_band_end_stall,
    output logic [63:0] count_mem_req_stall, count_mem_pending, count_input_starved,
    output logic [63:0] ts_first_input, ts_last_input, ts_metadata_accept,
    output logic [63:0] ts_last_sparse_coef, ts_packet_done_observed,
    output logic [63:0] ts_seal_accepted, ts_scratch_sealed_observed,
    output logic [63:0] ts_first_dense, ts_last_dense, ts_integrated_done,
    output logic [63:0] ts_first_coef_band [0:3], ts_last_coef_band [0:3], ts_band_end [0:3],
    output logic [4:0] max_assembly_bytes,
    output logic [2:0] max_cache_valid, max_head_valid,
    output logic max_outstanding
);
    logic running, allocation, seal_sent, use_serial_clear;
    logic cancelled, packet_abort, store_abort;
    logic packet_ready, packet_done;
    logic [3:0] packet_error, store_error;
    logic meta_valid, meta_ready, meta_raw;
    logic [16:0] meta_blocks;
    logic [31:0] meta_count1, meta_count2, meta_count3, meta_epoch;
    logic coef_valid, coef_ready;
    logic [1:0] coef_band;
    logic [15:0] coef_block;
    logic [5:0] coef_index;
    logic signed [15:0] coef_value;
    logic [31:0] coef_epoch;
    logic end_valid, end_ready;
    logic [1:0] end_band;
    logic [31:0] end_epoch;
    logic store_busy, store_done, seal_ready;
    logic dense_valid;
    logic [31:0] store_epoch;
    logic [63:0] packet_cycles, packet_inputs, packet_outputs, packet_stall;

    assign cancelled=reset || start || abort_packet;
    // A replacement start owns this edge. Old-owner error cancellation must
    // not defeat ingress start while the outer controller accepts the restart.
    assign packet_abort=abort_packet || (!start && running && store_error!=0);
    assign store_abort=start || abort_packet || (running && packet_error!=0);
    assign in_ready=packet_ready && running && error==0 && !cancelled;
    assign out_valid=dense_valid && running && error==0 && !cancelled;
    assign busy=running || store_busy;
    assign draining=store_busy && !running;
    assign metadata_wait=meta_valid && !meta_ready;

    assign dbg_running=running;
    assign dbg_allocation=allocation;
    assign dbg_seal_sent=seal_sent;
    assign dbg_packet_done=packet_done;
    assign dbg_coef_valid=coef_valid;
    assign dbg_coef_ready=coef_ready;
    assign dbg_coef_band=coef_band;
    assign dbg_meta_valid=meta_valid;
    assign dbg_meta_ready=meta_ready;
    assign dbg_meta_raw=meta_raw;
    assign dbg_band_end_valid=end_valid;
    assign dbg_band_end_ready=end_ready;
    assign dbg_band_end_band=end_band;
    assign dbg_seal_valid=packet_done && allocation && !seal_sent && running && error==0;
    assign dbg_seal_ready=seal_ready;

    br88_packet_ingress packet_decoder (
        .clk(clk), .reset(reset), .start(start), .abort_packet(packet_abort),
        .packet_bytes(packet_bytes), .blocks(blocks), .epoch(epoch),
        .word16(1'b0), .serial_mode(1'b0),
        .in_valid(in_valid && running && error==0), .in_ready(packet_ready),
        .in_data(in_data), .in_last(in_last),
        .out_valid(coef_valid), .out_ready(coef_ready), .out_block(coef_block),
        .out_index(coef_index), .out_coefficient(coef_value), .out_epoch(coef_epoch),
        .out_band(coef_band), .meta_valid(meta_valid), .meta_ready(meta_ready),
        .meta_blocks(meta_blocks), .meta_count1(meta_count1), .meta_count2(meta_count2),
        .meta_count3(meta_count3), .meta_epoch(meta_epoch), .meta_raw(meta_raw),
        .band_end_valid(end_valid), .band_end_ready(end_ready),
        .band_end_band(end_band), .band_end_epoch(end_epoch),
        .done(packet_done), .error(packet_error), .count_cycles(packet_cycles),
        .count_inputs(packet_inputs), .count_outputs(packet_outputs),
        .count_output_stall(packet_stall), .debug_state(packet_state)
    );

    packed_scratch_v91e scratch (
        .clk(clk), .reset(reset),
        .begin_valid(meta_valid && running && error==0), .begin_ready(meta_ready),
        .begin_blocks(meta_blocks), .begin_raw(meta_raw),
        .begin_count1(meta_count1), .begin_count2(meta_count2), .begin_count3(meta_count3),
        .begin_epoch(meta_epoch), .begin_serial_clear(use_serial_clear),
        .coef_valid(coef_valid && running && error==0), .coef_ready(coef_ready),
        .coef_band(coef_band), .coef_block(coef_block), .coef_index(coef_index),
        .coef_value(coef_value), .coef_epoch(coef_epoch),
        .band_end_valid(end_valid && running && error==0), .band_end_ready(end_ready),
        .band_end_band(end_band), .band_end_epoch(end_epoch),
        .seal_valid(packet_done && allocation && !seal_sent && running && error==0),
        .seal_ready(seal_ready), .seal_epoch(meta_epoch),
        .abort_valid(store_abort), .abort_epoch(store_epoch),
        .busy(store_busy), .sealed(scratch_sealed), .done(store_done), .error(store_error),
        .active_epoch(store_epoch), .used_bytes(used_bytes),
        .dense_valid(dense_valid), .dense_ready(out_ready && running && error==0 && !cancelled),
        .dense_block(out_block), .dense_index(out_index), .dense_value(out_value), .dense_epoch(out_epoch),
        .mem_req_valid(mem_req_valid), .mem_req_ready(mem_req_ready), .mem_req_write(mem_req_write),
        .mem_req_addr(mem_req_addr), .mem_req_data(mem_req_data), .mem_req_epoch(mem_req_epoch),
        .mem_rsp_valid(mem_rsp_valid), .mem_rsp_ready(mem_rsp_ready), .mem_rsp_data(mem_rsp_data),
        .mem_rsp_epoch(mem_rsp_epoch), .mem_rsp_error(mem_rsp_error),
        .debug_state(dbg_scratch_state), .debug_return_state(dbg_scratch_return_state),
        .debug_outstanding(dbg_scratch_outstanding), .debug_phase(dbg_scratch_phase),
        .debug_assembly_bytes(dbg_scratch_assembly_bytes),
        .debug_cache_valid(dbg_scratch_cache_valid), .debug_head_valid(dbg_scratch_head_valid)
    );

    // All telemetry samples the pre-edge registered states on each running
    // edge, including the edge observing store_done. Start is excluded.
    always_ff @(posedge clk) begin
        if(reset || abort_packet || start) begin
            for(integer i=0;i<16;i=i+1) count_packet_state[i]<=0;
            for(integer i=0;i<32;i=i+1) count_scratch_state[i]<=0;
            count_coef_stall<=0; count_metadata_wait<=0; count_band_end_stall<=0;
            count_mem_req_stall<=0; count_mem_pending<=0; count_input_starved<=0;
            ts_first_input<=0; ts_last_input<=0; ts_metadata_accept<=0;
            ts_last_sparse_coef<=0; ts_packet_done_observed<=0;
            ts_seal_accepted<=0; ts_scratch_sealed_observed<=0;
            ts_first_dense<=0; ts_last_dense<=0; ts_integrated_done<=0;
            for(integer i=0;i<4;i=i+1) begin
                ts_first_coef_band[i]<=0; ts_last_coef_band[i]<=0; ts_band_end[i]<=0;
            end
            max_assembly_bytes<=0; max_cache_valid<=0; max_head_valid<=0; max_outstanding<=0;
        end else if(running) begin
            count_packet_state[packet_state]<=count_packet_state[packet_state]+1'b1;
            count_scratch_state[dbg_scratch_state]<=count_scratch_state[dbg_scratch_state]+1'b1;
            if(coef_valid && !coef_ready) count_coef_stall<=count_coef_stall+1'b1;
            if(meta_valid && !meta_ready) count_metadata_wait<=count_metadata_wait+1'b1;
            if(end_valid && !end_ready) count_band_end_stall<=count_band_end_stall+1'b1;
            if(mem_req_valid && !mem_req_ready) count_mem_req_stall<=count_mem_req_stall+1'b1;
            if(dbg_scratch_outstanding) count_mem_pending<=count_mem_pending+1'b1;
            if(in_ready && !in_valid) count_input_starved<=count_input_starved+1'b1;
            if(in_valid && in_ready) begin
                if(ts_first_input==0) ts_first_input<=count_cycles+1'b1;
                ts_last_input<=count_cycles+1'b1;
            end
            if(meta_valid && meta_ready) ts_metadata_accept<=count_cycles+1'b1;
            if(coef_valid && coef_ready) begin
                ts_last_sparse_coef<=count_cycles+1'b1;
                if(ts_first_coef_band[coef_band]==0) ts_first_coef_band[coef_band]<=count_cycles+1'b1;
                ts_last_coef_band[coef_band]<=count_cycles+1'b1;
            end
            if(end_valid && end_ready) ts_band_end[end_band]<=count_cycles+1'b1;
            if(dbg_scratch_assembly_bytes>max_assembly_bytes) max_assembly_bytes<=dbg_scratch_assembly_bytes;
            if(3'($countones(dbg_scratch_cache_valid))>max_cache_valid) max_cache_valid<=3'($countones(dbg_scratch_cache_valid));
            if(3'($countones(dbg_scratch_head_valid))>max_head_valid) max_head_valid<=3'($countones(dbg_scratch_head_valid));
            if(dbg_scratch_outstanding) max_outstanding<=1;
            if(packet_done && ts_packet_done_observed==0) ts_packet_done_observed<=count_cycles+1'b1;
            if(dbg_seal_valid && seal_ready) ts_seal_accepted<=count_cycles+1'b1;
            if(scratch_sealed && ts_scratch_sealed_observed==0) ts_scratch_sealed_observed<=count_cycles+1'b1;
            if(out_valid && out_ready) begin
                if(ts_first_dense==0) ts_first_dense<=count_cycles+1'b1;
                ts_last_dense<=count_cycles+1'b1;
            end
            if(store_done) ts_integrated_done<=count_cycles+1'b1;
        end
    end
    always_ff @(posedge clk) begin
        if(reset || abort_packet) begin
            running<=0; allocation<=0; seal_sent<=0; use_serial_clear<=0;
            done<=0; error<=0; count_cycles<=0; count_input_bytes<=0; count_dense<=0;
            count_reads<=0; count_writes<=0; count_dense_stall<=0;
        end else if(start) begin
            running<=1; allocation<=0; seal_sent<=0; use_serial_clear<=serial_clear;
            done<=0; error<=0; count_cycles<=0; count_input_bytes<=0; count_dense<=0;
            count_reads<=0; count_writes<=0; count_dense_stall<=0;
        end else if(running) begin
            count_cycles<=count_cycles+1'b1;
            if(in_valid && in_ready) count_input_bytes<=count_input_bytes+1'b1;
            if(out_valid && out_ready) count_dense<=count_dense+1'b1;
            if(out_valid && !out_ready) count_dense_stall<=count_dense_stall+1'b1;
            if(mem_req_valid && mem_req_ready) begin
                if(mem_req_write) count_writes<=count_writes+1'b1;
                else count_reads<=count_reads+1'b1;
            end
            if(meta_valid && meta_ready) allocation<=1;
            if(packet_done && allocation && !seal_sent && seal_ready) seal_sent<=1;
            if(packet_error!=0) begin error<={4'h1,packet_error}; running<=0; end
            else if(store_error!=0) begin error<={4'h2,store_error}; running<=0; end
            else if(store_done) begin done<=1; running<=0; end
        end
    end
`ifndef SYNTHESIS
    always_ff @(posedge clk) if(!cancelled) begin
        assert(!out_valid || (scratch_sealed && seal_sent && allocation))
            else $fatal(1,"dense output before packet/store validation");
        assert(!done || (!out_valid && !running)) else $fatal(1,"terminal publication fence");
        assert(packet_inputs==count_input_bytes || !running) else $fatal(1,"packet ingress counter");
        assert(packet_outputs<=packet_inputs*64'd64+64'd64) else $fatal(1,"diagnostic range");
        assert(packet_cycles>=packet_stall) else $fatal(1,"packet stall diagnostic");
    end
`endif
endmodule
