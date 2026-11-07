// V91i2a provisional mode/scale retention and synchronous replay, forked from frozen V91i1.
// Structural admission is still not frame acceptance; no accepted-state commit.
module memory_probe (
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
    output logic [31:0] required_cells
, input logic probe_force_collision, output logic probe_outputs_equal, probe_ram_equal);
logic  old_replay_ready;
logic  old_replay_rsp_valid;
logic [7:0]  old_replay_data;
logic [31:0]  old_replay_rsp_addr;
logic [31:0]  old_replay_rsp_epoch;
logic  old_lookup_rsp_valid;
logic [1:0]  old_lookup_mode;
logic [1:0]  old_lookup_scale;
logic  old_in_ready;
logic  old_busy;
logic  old_receipt_valid;
logic [7:0]  old_error;
logic [31:0]  old_receipt_epoch;
logic [31:0]  old_fid;
logic [31:0]  old_refid;
logic [63:0]  old_generation;
logic  old_key_frame;
logic [31:0]  old_mode_bytes;
logic [31:0]  old_qmap_bytes;
logic [31:0]  old_hud_bytes;
logic [31:0]  old_data_bytes;
logic [31:0]  old_plane_blocks[0:2];
logic [31:0]  old_plane_offset[0:2];
logic [31:0]  old_plane_length[0:2];
logic [1:0]  old_plane_entropy[0:2];
logic  old_stage_read_req;
logic  old_stage_read_rsp;
logic  old_stage_write;
logic  old_stage_pending;
logic  old_stage_cancel;
logic [31:0]  old_stage_read_addr;
logic [31:0]  old_stage_rsp_addr;
logic [31:0]  old_stage_req_epoch;
logic [31:0]  old_stage_rsp_epoch;
logic [7:0]  old_stage_read_data;
logic [7:0]  old_debug_state;
logic [63:0]  old_count_cycles;
logic [63:0]  old_count_inputs;
logic [63:0]  old_count_stage_reads;
logic [63:0]  old_count_stage_responses;
logic [63:0]  old_count_receipt_wait;
logic [31:0]  old_required_cells;
memory_original old_dut(.clk(clk),.reset(reset),.start(start),.abort_packet(abort_packet),.cache_write(cache_write),.cache_index(cache_index),.cache_data(cache_data),.replay_req(replay_req),.replay_addr(replay_addr),.replay_ready(old_replay_ready),.replay_rsp_valid(old_replay_rsp_valid),.replay_data(old_replay_data),.replay_rsp_addr(old_replay_rsp_addr),.replay_rsp_epoch(old_replay_rsp_epoch),.lookup_req(lookup_req),.lookup_tile(lookup_tile),.lookup_cell(lookup_cell),.lookup_rsp_valid(old_lookup_rsp_valid),.lookup_mode(old_lookup_mode),.lookup_scale(old_lookup_scale),.packet_bytes(packet_bytes),.epoch(epoch),.accepted_ref_valid(accepted_ref_valid),.accepted_qcache_valid(accepted_qcache_valid),.accepted_ref_fid(accepted_ref_fid),.accepted_ref_generation(accepted_ref_generation),.in_valid(in_valid),.in_last(in_last),.in_data(in_data),.in_ready(old_in_ready),.busy(old_busy),.receipt_valid(old_receipt_valid),.receipt_ready(receipt_ready),.error(old_error),.receipt_epoch(old_receipt_epoch),.fid(old_fid),.refid(old_refid),.generation(old_generation),.key_frame(old_key_frame),.mode_bytes(old_mode_bytes),.qmap_bytes(old_qmap_bytes),.hud_bytes(old_hud_bytes),.data_bytes(old_data_bytes),.plane_blocks(old_plane_blocks),.plane_offset(old_plane_offset),.plane_length(old_plane_length),.plane_entropy(old_plane_entropy),.stage_read_req(old_stage_read_req),.stage_read_rsp(old_stage_read_rsp),.stage_write(old_stage_write),.stage_pending(old_stage_pending),.stage_cancel(old_stage_cancel),.stage_read_addr(old_stage_read_addr),.stage_rsp_addr(old_stage_rsp_addr),.stage_req_epoch(old_stage_req_epoch),.stage_rsp_epoch(old_stage_rsp_epoch),.stage_read_data(old_stage_read_data),.debug_state(old_debug_state),.count_cycles(old_count_cycles),.count_inputs(old_count_inputs),.count_stage_reads(old_count_stage_reads),.count_stage_responses(old_count_stage_responses),.count_receipt_wait(old_count_receipt_wait),.required_cells(old_required_cells));
memory_candidate new_dut(.clk(clk),.reset(reset),.start(start),.abort_packet(abort_packet),.cache_write(cache_write),.cache_index(cache_index),.cache_data(cache_data),.replay_req(replay_req),.replay_addr(replay_addr),.replay_ready(replay_ready),.replay_rsp_valid(replay_rsp_valid),.replay_data(replay_data),.replay_rsp_addr(replay_rsp_addr),.replay_rsp_epoch(replay_rsp_epoch),.lookup_req(lookup_req),.lookup_tile(lookup_tile),.lookup_cell(lookup_cell),.lookup_rsp_valid(lookup_rsp_valid),.lookup_mode(lookup_mode),.lookup_scale(lookup_scale),.packet_bytes(packet_bytes),.epoch(epoch),.accepted_ref_valid(accepted_ref_valid),.accepted_qcache_valid(accepted_qcache_valid),.accepted_ref_fid(accepted_ref_fid),.accepted_ref_generation(accepted_ref_generation),.in_valid(in_valid),.in_last(in_last),.in_data(in_data),.in_ready(in_ready),.busy(busy),.receipt_valid(receipt_valid),.receipt_ready(receipt_ready),.error(error),.receipt_epoch(receipt_epoch),.fid(fid),.refid(refid),.generation(generation),.key_frame(key_frame),.mode_bytes(mode_bytes),.qmap_bytes(qmap_bytes),.hud_bytes(hud_bytes),.data_bytes(data_bytes),.plane_blocks(plane_blocks),.plane_offset(plane_offset),.plane_length(plane_length),.plane_entropy(plane_entropy),.stage_read_req(stage_read_req),.stage_read_rsp(stage_read_rsp),.stage_write(stage_write),.stage_pending(stage_pending),.stage_cancel(stage_cancel),.stage_read_addr(stage_read_addr),.stage_rsp_addr(stage_rsp_addr),.stage_req_epoch(stage_req_epoch),.stage_rsp_epoch(stage_rsp_epoch),.stage_read_data(stage_read_data),.debug_state(debug_state),.count_cycles(count_cycles),.count_inputs(count_inputs),.count_stage_reads(count_stage_reads),.count_stage_responses(count_stage_responses),.count_receipt_wait(count_receipt_wait),.required_cells(required_cells));
assign probe_outputs_equal = (old_replay_ready == replay_ready) && (old_replay_rsp_valid == replay_rsp_valid) && (old_replay_data == replay_data) && (old_replay_rsp_addr == replay_rsp_addr) && (old_replay_rsp_epoch == replay_rsp_epoch) && (old_lookup_rsp_valid == lookup_rsp_valid) && (old_lookup_mode == lookup_mode) && (old_lookup_scale == lookup_scale) && (old_in_ready == in_ready) && (old_busy == busy) && (old_receipt_valid == receipt_valid) && (old_error == error) && (old_receipt_epoch == receipt_epoch) && (old_fid == fid) && (old_refid == refid) && (old_generation == generation) && (old_key_frame == key_frame) && (old_mode_bytes == mode_bytes) && (old_qmap_bytes == qmap_bytes) && (old_hud_bytes == hud_bytes) && (old_data_bytes == data_bytes) && (old_plane_blocks == plane_blocks) && (old_plane_offset == plane_offset) && (old_plane_length == plane_length) && (old_plane_entropy == plane_entropy) && (old_stage_read_req == stage_read_req) && (old_stage_read_rsp == stage_read_rsp) && (old_stage_write == stage_write) && (old_stage_pending == stage_pending) && (old_stage_cancel == stage_cancel) && (old_stage_read_addr == stage_read_addr) && (old_stage_rsp_addr == stage_rsp_addr) && (old_stage_req_epoch == stage_req_epoch) && (old_stage_rsp_epoch == stage_rsp_epoch) && (old_stage_read_data == stage_read_data) && (old_debug_state == debug_state) && (old_count_cycles == count_cycles) && (old_count_inputs == count_inputs) && (old_count_stage_reads == count_stage_reads) && (old_count_stage_responses == count_stage_responses) && (old_count_receipt_wait == count_receipt_wait) && (old_required_cells == required_cells);
assign probe_ram_equal = (old_dut.ram_data == new_dut.ram_data) && (old_dut.ram_addr == new_dut.ram_addr) && (old_dut.ram_epoch == new_dut.ram_epoch);
// Verification-only forces: reach RAM read-first collision while normal FSM forbids it.
always_comb begin
if(probe_force_collision) begin
force old_dut.stage_write=1'b1; force new_dut.stage_write=1'b1;
force old_dut.stage_read_req=1'b1; force new_dut.stage_read_req=1'b1;
end else begin
release old_dut.stage_write; release new_dut.stage_write;
release old_dut.stage_read_req; release new_dut.stage_read_req;
end
end
endmodule
