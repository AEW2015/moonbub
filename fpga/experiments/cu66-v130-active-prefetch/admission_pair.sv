module admission_pair (

    input logic clk, reset, start, abort_packet,
    input logic cache_write,
    input logic [10:0] cache_index,
    input logic [1:0] cache_data,
    input logic replay_req,
    input logic [31:0] replay_addr,
    output logic replay_ready, replay_rsp_valid,
    output logic [7:0] replay_data,
    output logic [31:0] replay_rsp_addr, replay_rsp_epoch,
    input logic lookup_req,
    input logic [12:0] lookup_tile,
    input logic [10:0] lookup_cell,
    output logic lookup_rsp_valid,
    output logic [1:0] lookup_mode, lookup_scale,
    input logic [31:0] packet_bytes, epoch,
    input logic accepted_ref_valid, accepted_qcache_valid,
    input logic [31:0] accepted_ref_fid,
    input logic [63:0] accepted_ref_generation,
    input logic in_valid, in_last,
    input logic [7:0] in_data,
    output logic in_ready, busy,
    output logic receipt_valid,
    input logic receipt_ready,
    output logic [7:0] error,
    output logic [31:0] receipt_epoch, fid, refid,
    output logic [63:0] generation,
    output logic key_frame,
    output logic [31:0] mode_bytes, qmap_bytes, hud_bytes, data_bytes,
    output logic [31:0] plane_blocks [0:2],
    output logic [31:0] plane_offset [0:2],
    output logic [31:0] plane_length [0:2],
    output logic [1:0] plane_entropy [0:2],
    output logic stage_read_req, stage_read_rsp, stage_write, stage_pending, stage_cancel,
    output logic [31:0] stage_read_addr, stage_rsp_addr, stage_req_epoch, stage_rsp_epoch,
    output logic [7:0] stage_read_data,
    output logic [7:0] debug_state,
    output logic [63:0] count_cycles, count_inputs, count_stage_reads,
    output logic [63:0] count_stage_responses, count_receipt_wait,
    output logic [31:0] required_cells,
    output logic mismatch
 );
    logic  old_replay_ready ;
    logic  new_replay_ready ;
    logic  old_replay_rsp_valid ;
    logic  new_replay_rsp_valid ;
    logic [7:0] old_replay_data ;
    logic [7:0] new_replay_data ;
    logic [31:0] old_replay_rsp_addr ;
    logic [31:0] new_replay_rsp_addr ;
    logic [31:0] old_replay_rsp_epoch ;
    logic [31:0] new_replay_rsp_epoch ;
    logic  old_lookup_rsp_valid ;
    logic  new_lookup_rsp_valid ;
    logic [1:0] old_lookup_mode ;
    logic [1:0] new_lookup_mode ;
    logic [1:0] old_lookup_scale ;
    logic [1:0] new_lookup_scale ;
    logic  old_in_ready ;
    logic  new_in_ready ;
    logic  old_busy ;
    logic  new_busy ;
    logic  old_receipt_valid ;
    logic  new_receipt_valid ;
    logic [7:0] old_error ;
    logic [7:0] new_error ;
    logic [31:0] old_receipt_epoch ;
    logic [31:0] new_receipt_epoch ;
    logic [31:0] old_fid ;
    logic [31:0] new_fid ;
    logic [31:0] old_refid ;
    logic [31:0] new_refid ;
    logic [63:0] old_generation ;
    logic [63:0] new_generation ;
    logic  old_key_frame ;
    logic  new_key_frame ;
    logic [31:0] old_mode_bytes ;
    logic [31:0] new_mode_bytes ;
    logic [31:0] old_qmap_bytes ;
    logic [31:0] new_qmap_bytes ;
    logic [31:0] old_hud_bytes ;
    logic [31:0] new_hud_bytes ;
    logic [31:0] old_data_bytes ;
    logic [31:0] new_data_bytes ;
    logic [31:0] old_plane_blocks [0:2];
    logic [31:0] new_plane_blocks [0:2];
    logic [31:0] old_plane_offset [0:2];
    logic [31:0] new_plane_offset [0:2];
    logic [31:0] old_plane_length [0:2];
    logic [31:0] new_plane_length [0:2];
    logic [1:0] old_plane_entropy [0:2];
    logic [1:0] new_plane_entropy [0:2];
    logic  old_stage_read_req ;
    logic  new_stage_read_req ;
    logic  old_stage_read_rsp ;
    logic  new_stage_read_rsp ;
    logic  old_stage_write ;
    logic  new_stage_write ;
    logic  old_stage_pending ;
    logic  new_stage_pending ;
    logic  old_stage_cancel ;
    logic  new_stage_cancel ;
    logic [31:0] old_stage_read_addr ;
    logic [31:0] new_stage_read_addr ;
    logic [31:0] old_stage_rsp_addr ;
    logic [31:0] new_stage_rsp_addr ;
    logic [31:0] old_stage_req_epoch ;
    logic [31:0] new_stage_req_epoch ;
    logic [31:0] old_stage_rsp_epoch ;
    logic [31:0] new_stage_rsp_epoch ;
    logic [7:0] old_stage_read_data ;
    logic [7:0] new_stage_read_data ;
    logic [7:0] old_debug_state ;
    logic [7:0] new_debug_state ;
    logic [63:0] old_count_cycles ;
    logic [63:0] new_count_cycles ;
    logic [63:0] old_count_inputs ;
    logic [63:0] new_count_inputs ;
    logic [63:0] old_count_stage_reads ;
    logic [63:0] new_count_stage_reads ;
    logic [63:0] old_count_stage_responses ;
    logic [63:0] new_count_stage_responses ;
    logic [63:0] old_count_receipt_wait ;
    logic [63:0] new_count_receipt_wait ;
    logic [31:0] old_required_cells ;
    logic [31:0] new_required_cells ;
    admission_original original (.clk(clk), .reset(reset), .start(start), .abort_packet(abort_packet), .cache_write(cache_write), .cache_index(cache_index), .cache_data(cache_data), .replay_req(replay_req), .replay_addr(replay_addr), .lookup_req(lookup_req), .lookup_tile(lookup_tile), .lookup_cell(lookup_cell), .packet_bytes(packet_bytes), .epoch(epoch), .accepted_ref_valid(accepted_ref_valid), .accepted_qcache_valid(accepted_qcache_valid), .accepted_ref_fid(accepted_ref_fid), .accepted_ref_generation(accepted_ref_generation), .in_valid(in_valid), .in_last(in_last), .in_data(in_data), .receipt_ready(receipt_ready), .replay_ready(old_replay_ready), .replay_rsp_valid(old_replay_rsp_valid), .replay_data(old_replay_data), .replay_rsp_addr(old_replay_rsp_addr), .replay_rsp_epoch(old_replay_rsp_epoch), .lookup_rsp_valid(old_lookup_rsp_valid), .lookup_mode(old_lookup_mode), .lookup_scale(old_lookup_scale), .in_ready(old_in_ready), .busy(old_busy), .receipt_valid(old_receipt_valid), .error(old_error), .receipt_epoch(old_receipt_epoch), .fid(old_fid), .refid(old_refid), .generation(old_generation), .key_frame(old_key_frame), .mode_bytes(old_mode_bytes), .qmap_bytes(old_qmap_bytes), .hud_bytes(old_hud_bytes), .data_bytes(old_data_bytes), .plane_blocks(old_plane_blocks), .plane_offset(old_plane_offset), .plane_length(old_plane_length), .plane_entropy(old_plane_entropy), .stage_read_req(old_stage_read_req), .stage_read_rsp(old_stage_read_rsp), .stage_write(old_stage_write), .stage_pending(old_stage_pending), .stage_cancel(old_stage_cancel), .stage_read_addr(old_stage_read_addr), .stage_rsp_addr(old_stage_rsp_addr), .stage_req_epoch(old_stage_req_epoch), .stage_rsp_epoch(old_stage_rsp_epoch), .stage_read_data(old_stage_read_data), .debug_state(old_debug_state), .count_cycles(old_count_cycles), .count_inputs(old_count_inputs), .count_stage_reads(old_count_stage_reads), .count_stage_responses(old_count_stage_responses), .count_receipt_wait(old_count_receipt_wait), .required_cells(old_required_cells));
    admission_candidate candidate (.clk(clk), .reset(reset), .start(start), .abort_packet(abort_packet), .cache_write(cache_write), .cache_index(cache_index), .cache_data(cache_data), .replay_req(replay_req), .replay_addr(replay_addr), .lookup_req(lookup_req), .lookup_tile(lookup_tile), .lookup_cell(lookup_cell), .packet_bytes(packet_bytes), .epoch(epoch), .accepted_ref_valid(accepted_ref_valid), .accepted_qcache_valid(accepted_qcache_valid), .accepted_ref_fid(accepted_ref_fid), .accepted_ref_generation(accepted_ref_generation), .in_valid(in_valid), .in_last(in_last), .in_data(in_data), .receipt_ready(receipt_ready), .replay_ready(new_replay_ready), .replay_rsp_valid(new_replay_rsp_valid), .replay_data(new_replay_data), .replay_rsp_addr(new_replay_rsp_addr), .replay_rsp_epoch(new_replay_rsp_epoch), .lookup_rsp_valid(new_lookup_rsp_valid), .lookup_mode(new_lookup_mode), .lookup_scale(new_lookup_scale), .in_ready(new_in_ready), .busy(new_busy), .receipt_valid(new_receipt_valid), .error(new_error), .receipt_epoch(new_receipt_epoch), .fid(new_fid), .refid(new_refid), .generation(new_generation), .key_frame(new_key_frame), .mode_bytes(new_mode_bytes), .qmap_bytes(new_qmap_bytes), .hud_bytes(new_hud_bytes), .data_bytes(new_data_bytes), .plane_blocks(new_plane_blocks), .plane_offset(new_plane_offset), .plane_length(new_plane_length), .plane_entropy(new_plane_entropy), .stage_read_req(new_stage_read_req), .stage_read_rsp(new_stage_read_rsp), .stage_write(new_stage_write), .stage_pending(new_stage_pending), .stage_cancel(new_stage_cancel), .stage_read_addr(new_stage_read_addr), .stage_rsp_addr(new_stage_rsp_addr), .stage_req_epoch(new_stage_req_epoch), .stage_rsp_epoch(new_stage_rsp_epoch), .stage_read_data(new_stage_read_data), .debug_state(new_debug_state), .count_cycles(new_count_cycles), .count_inputs(new_count_inputs), .count_stage_reads(new_count_stage_reads), .count_stage_responses(new_count_stage_responses), .count_receipt_wait(new_count_receipt_wait), .required_cells(new_required_cells));
    assign replay_ready=old_replay_ready;
    assign replay_rsp_valid=old_replay_rsp_valid;
    assign replay_data=old_replay_data;
    assign replay_rsp_addr=old_replay_rsp_addr;
    assign replay_rsp_epoch=old_replay_rsp_epoch;
    assign lookup_rsp_valid=old_lookup_rsp_valid;
    assign lookup_mode=old_lookup_mode;
    assign lookup_scale=old_lookup_scale;
    assign in_ready=old_in_ready;
    assign busy=old_busy;
    assign receipt_valid=old_receipt_valid;
    assign error=old_error;
    assign receipt_epoch=old_receipt_epoch;
    assign fid=old_fid;
    assign refid=old_refid;
    assign generation=old_generation;
    assign key_frame=old_key_frame;
    assign mode_bytes=old_mode_bytes;
    assign qmap_bytes=old_qmap_bytes;
    assign hud_bytes=old_hud_bytes;
    assign data_bytes=old_data_bytes;
    assign plane_blocks=old_plane_blocks;
    assign plane_offset=old_plane_offset;
    assign plane_length=old_plane_length;
    assign plane_entropy=old_plane_entropy;
    assign stage_read_req=old_stage_read_req;
    assign stage_read_rsp=old_stage_read_rsp;
    assign stage_write=old_stage_write;
    assign stage_pending=old_stage_pending;
    assign stage_cancel=old_stage_cancel;
    assign stage_read_addr=old_stage_read_addr;
    assign stage_rsp_addr=old_stage_rsp_addr;
    assign stage_req_epoch=old_stage_req_epoch;
    assign stage_rsp_epoch=old_stage_rsp_epoch;
    assign stage_read_data=old_stage_read_data;
    assign debug_state=old_debug_state;
    assign count_cycles=old_count_cycles;
    assign count_inputs=old_count_inputs;
    assign count_stage_reads=old_count_stage_reads;
    assign count_stage_responses=old_count_stage_responses;
    assign count_receipt_wait=old_count_receipt_wait;
    assign required_cells=old_required_cells;
    assign mismatch = (old_replay_ready != new_replay_ready) ||
        (old_replay_rsp_valid != new_replay_rsp_valid) ||
        (old_replay_rsp_valid && old_replay_data != new_replay_data) ||
        (old_replay_rsp_addr != new_replay_rsp_addr) ||
        (old_replay_rsp_epoch != new_replay_rsp_epoch) ||
        (old_lookup_rsp_valid != new_lookup_rsp_valid) ||
        (old_lookup_mode != new_lookup_mode) ||
        (old_lookup_scale != new_lookup_scale) ||
        (old_in_ready != new_in_ready) ||
        (old_busy != new_busy) ||
        (old_receipt_valid != new_receipt_valid) ||
        (old_error != new_error) ||
        (old_receipt_epoch != new_receipt_epoch) ||
        (old_fid != new_fid) ||
        (old_refid != new_refid) ||
        (old_generation != new_generation) ||
        (old_key_frame != new_key_frame) ||
        (old_mode_bytes != new_mode_bytes) ||
        (old_qmap_bytes != new_qmap_bytes) ||
        (old_hud_bytes != new_hud_bytes) ||
        (old_data_bytes != new_data_bytes) ||
        (old_plane_blocks[0] != new_plane_blocks[0]) || (old_plane_blocks[1] != new_plane_blocks[1]) || (old_plane_blocks[2] != new_plane_blocks[2]) ||
        (old_plane_offset[0] != new_plane_offset[0]) || (old_plane_offset[1] != new_plane_offset[1]) || (old_plane_offset[2] != new_plane_offset[2]) ||
        (old_plane_length[0] != new_plane_length[0]) || (old_plane_length[1] != new_plane_length[1]) || (old_plane_length[2] != new_plane_length[2]) ||
        (old_plane_entropy[0] != new_plane_entropy[0]) || (old_plane_entropy[1] != new_plane_entropy[1]) || (old_plane_entropy[2] != new_plane_entropy[2]) ||
        (old_stage_read_req != new_stage_read_req) ||
        (old_stage_read_rsp != new_stage_read_rsp) ||
        (old_stage_write != new_stage_write) ||
        (old_stage_pending != new_stage_pending) ||
        (old_stage_cancel != new_stage_cancel) ||
        (old_stage_read_addr != new_stage_read_addr) ||
        (old_stage_rsp_addr != new_stage_rsp_addr) ||
        (old_stage_req_epoch != new_stage_req_epoch) ||
        (old_stage_rsp_epoch != new_stage_rsp_epoch) ||
        (old_stage_read_rsp && old_stage_read_data != new_stage_read_data) ||
        (old_debug_state != new_debug_state) ||
        (old_count_cycles != new_count_cycles) ||
        (old_count_inputs != new_count_inputs) ||
        (old_count_stage_reads != new_count_stage_reads) ||
        (old_count_stage_responses != new_count_stage_responses) ||
        (old_count_receipt_wait != new_count_receipt_wait) ||
        (old_required_cells != new_required_cells);
endmodule
