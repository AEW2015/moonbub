// V91i2b bounded refill overlap; compile-time mode 0 retains V91i2a scheduling.
module ready_candidate #(parameter integer REFILL_OVERLAP=1) (
    input logic clk, reset, start, abort_packet,
    input logic reconstruct_lookup_req,
    input logic [12:0] reconstruct_lookup_tile,
    input logic [10:0] reconstruct_lookup_cell,
    output logic reconstruct_lookup_ready, reconstruct_lookup_rsp,
    output logic [1:0] reconstruct_lookup_mode, reconstruct_lookup_scale,
    output logic admitted_ready, admitted_key,
    output logic [31:0] admitted_fid,
    output logic [63:0] admitted_generation,
    output logic start_ready,
    input logic cache_valid, cache_last,
    output logic cache_ready, cache_complete,
    input logic [1:0] cache_data,
    input logic [31:0] cache_ref_fid,
    input logic [63:0] cache_ref_generation,
    output logic [7:0] cache_error,
    input logic accepted_ref_valid, accepted_qcache_valid,
    input logic [31:0] accepted_ref_fid,
    input logic [63:0] accepted_ref_generation,
    output logic [1:0] out_plane,
    output logic [12:0] out_tile,
    output logic [10:0] out_qcell,
    output logic [1:0] out_qscale,
    output logic [7:0] frame_state,
    output logic [31:0] frame_fid,
    output logic [31:0] core_starts, refill_bytes, blocked_starts,
    output logic [31:0] current_child_epoch,
    output logic [63:0] admission_reads,
    output logic [31:0] replay_reads,
    output logic [7:0] admission_error,
    output logic frame_read_req, frame_read_rsp,
    output logic [31:0] frame_read_addr, frame_rsp_addr, frame_rsp_epoch,
    output logic [7:0] frame_read_data,
    output logic [1:0] queue_count, queue_max_count, queue_max_owned,
    output logic queue_pending, queue_active, queue_push, queue_pop, queue_stall,
    output logic [31:0] queue_requests, queue_responses, queue_pops, queue_stalls,
    output logic [31:0] queue_cancel_queued, queue_cancel_pending,

    input logic [31:0] packet_bytes, epoch,
    input logic serial_clear, write_overlap, read_prefetch, tile_overlap,
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
    // Same-edge next-status predicate, never a delayed sample of error.
    output logic fault_o,
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
    output logic [15:0] dbg_coef_block,
    output logic [5:0] dbg_coef_index,
    output logic signed [15:0] dbg_coef_value,
    output logic [31:0] dbg_coef_epoch,
    output logic dbg_meta_valid, dbg_meta_ready, dbg_meta_raw,
    output logic dbg_band_end_valid, dbg_band_end_ready,
    output logic [1:0] dbg_band_end_band,
    output logic dbg_seal_valid, dbg_seal_ready,
    output logic [4:0] dbg_scratch_state, dbg_scratch_return_state,
    output logic dbg_scratch_outstanding,
    output logic dbg_prefetch_offer, dbg_prefetch_launch, dbg_prefetch_use,
    output logic dbg_tile_mode, dbg_tile_preparing, dbg_prepare_bank, dbg_emit_bank,
    output logic [1:0] dbg_bank_ready, dbg_bank_owned, dbg_emitter_state,
    output logic [15:0] dbg_prepare_block,
    output logic [15:0] dbg_bank_block [0:1],
    output logic [31:0] dbg_bank_epoch [0:1],
    output logic dbg_tile_prepare_start, dbg_tile_publish, dbg_tile_release,
    output logic [63:0] count_emitter_state [0:3],
    output logic [63:0] count_tile_starts, count_tile_publishes, count_tile_releases,
    output logic [63:0] count_prepare_output_overlap, count_prepare_output_hold,
    output logic [63:0] count_tile_read_output_overlap, count_tile_bank_wait, count_both_ready_wait, count_tile_prep_done_wait, count_output_valid,
    output logic [63:0] count_publish_release_same_edge,
    output logic [1:0] max_tile_owned, max_tile_ready,
    output logic [63:0] count_prefetch_offers, count_prefetch_accepts, count_prefetch_acks,
    output logic [63:0] count_prefetch_uses, count_dense_during_read_pending, count_prefetch_drain_wait,
    output logic max_prefetch_offer,
    output logic dbg_write_slot_valid, dbg_assembler_full, dbg_write_enqueue,
    output logic [63:0] count_write_enqueues, count_write_accepts, count_write_acks, count_full_wait, count_packing_during_write_pending,
    output logic max_write_slot,
    output logic [1:0] max_owned_lines,
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
    output logic max_outstanding,
    output logic stage_read_req, stage_read_rsp, stage_write, stage_pending, stage_context_active, stage_cancel, stage_word_valid, stage_word_ready,
    output logic [31:0] stage_read_addr, stage_rsp_addr, stage_write_addr, stage_req_epoch, stage_rsp_epoch,
    output logic [7:0] stage_read_data, stage_write_data,
    output logic [5:0] stage_buffer_bytes, stage_buffer_highwater,
    output logic [2:0] stage_purpose,
    output logic [63:0] count_stage_reads, count_stage_responses, count_stage_writes,
    output logic [63:0] count_stage_fetch_wait, count_stage_word_hold
);

    localparam logic [7:0] IDLE=0, ADMIT=1, CHECK_ENTROPY=2, PREP_PLANE=3,
        ALLOCATE=4, CORE_START=5, REFILL_REQ=6, REFILL_WAIT=7, REFILL_SEND=8,
        MAP_REQ=9, MAP_WAIT=10, DISPATCH=11, WAIT_DONE=12, NEXT_PLANE=13,
        FINISHED=14, FAILED=15, REFILL_STREAM=16;
    logic [7:0] state;
    logic frame_running, accepted_start;
    logic frame_running_owned, cache_nonzero_owned;
    logic [31:0] frame_epoch, latched_size;
    logic [31:0] last_frame_epoch=0, child_nonce=0;
    logic [1:0] plane;
    logic [12:0] tile_cursor, mapped_tile;
    logic [10:0] mapped_cell;
    logic [10:0] producer_cell_cache;
    logic [1:0] mapped_scale;
    logic [15:0] expected_block;
    logic [31:0] refill_cursor, selected_offset, selected_length;
    logic [16:0] selected_blocks;
    logic [7:0] refill_data;
    logic refill_valid, refill_last, child_in_ready;
    logic [7:0] child_input_data;
    logic queue_req_valid, queue_done;
    logic [7:0] queue_error, queue_data;
    logic queue_valid, queue_last;
    logic [31:0] queue_req_addr, queue_req_epoch;
    logic child_start, child_abort, child_out_valid, child_out_ready, child_done;
    logic [7:0] child_error;
    logic child_busy, child_draining, child_owned;
    logic [31:0] child_out_epoch;
    logic local_abort;
    logic [10:0] cache_count;
    logic [31:0] cached_fid;
    logic [63:0] cached_generation;
    logic snapshot_cache_eligible;
    logic [31:0] unused_fork_epoch, fork_fid, unused_fork_refid;
    logic [63:0] unused_fork_generation;
    logic unused_fork_key;
    logic coefficient_lookup_req, lookup_owner_reconstruct, physical_lookup_rsp;
    logic [1:0] physical_lookup_mode, physical_lookup_scale;
    logic [31:0] unused_fork_mode_bytes, unused_fork_qmap_bytes, unused_fork_hud_bytes, unused_fork_data_bytes;
    logic [31:0] fork_blocks [0:2], fork_offsets [0:2], fork_lengths [0:2];
    logic [1:0] fork_entropy [0:2];
    logic fork_in_ready, unused_fork_busy, fork_receipt;
    logic replay_ready, replay_rsp;
    logic [7:0] replay_data;
    logic [31:0] replay_rsp_addr, replay_rsp_epoch;
    // V118 dormant hypothesis: record the actual accepted physical read owner.
    // This is one synchronous response lease, not a new byte queue or buffer.
    // No reset payload is needed: REFILL_WAIT follows a real accepted request.
    // A response compares with immutable request tags, never a later cursor.
    logic [31:0] accepted_replay_address, accepted_replay_epoch;
    always_ff @(posedge clk)if(frame_read_req)begin
        accepted_replay_address<=frame_read_addr;
        accepted_replay_epoch<=frame_epoch;
    end
`ifndef SYNTHESIS
    always_ff @(posedge clk)if(!reset && !abort_packet && state==REFILL_WAIT && REFILL_OVERLAP==0)begin
        assert(accepted_replay_address==selected_offset+refill_cursor && accepted_replay_epoch==frame_epoch)
            else $fatal(1,"V118 physical replay lease differs from original stable refill owner");
    end
`endif
    logic lookup_rsp;
    logic [1:0] lookup_mode, lookup_scale;
    logic [12:0] lookup_tile;
    logic [10:0] lookup_cell;
    logic [63:0] fork_count_reads;
    logic unused_fork_read_req, unused_fork_read_rsp, unused_fork_write,
        unused_fork_pending, unused_fork_cancel;
    logic [31:0] unused_fork_read_addr, unused_fork_rsp_addr,
        unused_fork_req_epoch, unused_fork_rsp_epoch, unused_fork_required;
    logic [7:0] unused_fork_data, unused_fork_state;
    logic [63:0] unused_fork_cycles, unused_fork_inputs,
        unused_fork_responses, unused_fork_wait;

    function automatic logic [12:0] tiles(input logic [1:0] p);
        return p==0?13'd5400:13'd1350;
    endfunction
    function automatic logic [10:0] quant_cell(input logic [1:0] p,input logic [12:0] t);
        // Exact combinational Y truth table: paired tiles share a cell (90 is even).
        // 64 banks of LUT6-sized bit tables; native mapping/area are measured separately.
        logic [63:0] lut0;
        logic [63:0] lut1;
        logic [63:0] lut2;
        logic [63:0] lut3;
        logic [63:0] lut4;
        logic [63:0] lut5;
        logic [63:0] lut6;
        logic [63:0] lut7;
        logic [63:0] lut8;
        logic [63:0] lut9;
        logic [63:0] lut10;
        begin
            case(t[12:7])
                6'd0:begin
                    lut0=64'h55554aaaaaaaaaaa;
                    lut1=64'h99998ccccccccccc;
                    lut2=64'h1e1e10f0f0f0f0f0;
                    lut3=64'h1fe01f00ff00ff00;
                    lut4=64'he0000000ffff0000;
                    lut5=64'h00001fff00000000;
                    lut6=64'h0000000000000000;
                    lut7=64'h0000000000000000;
                    lut8=64'h0000000000000000;
                    lut9=64'h0000000000000000;
                    lut10=64'h0000000000000000;
                end
                6'd1:begin
                    lut0=64'h5555555555555555;
                    lut1=64'h9999999999999999;
                    lut2=64'h1e1e1e1e1e1e1e1e;
                    lut3=64'h1fe01fe01fe01fe0;
                    lut4=64'he0001fffe0001fff;
                    lut5=64'h00001fffffffe000;
                    lut6=64'hffffe00000000000;
                    lut7=64'h0000000000000000;
                    lut8=64'h0000000000000000;
                    lut9=64'h0000000000000000;
                    lut10=64'h0000000000000000;
                end
                6'd2:begin
                    lut0=64'haaaaaaaaaaaaaad5;
                    lut1=64'h3333333333333319;
                    lut2=64'hc3c3c3c3c3c3c39e;
                    lut3=64'h03fc03fc03fc03e0;
                    lut4=64'h03fffc0003fffc7f;
                    lut5=64'hfc00000003ffff80;
                    lut6=64'hfffffffffc00007f;
                    lut7=64'h0000000000000000;
                    lut8=64'h0000000000000000;
                    lut9=64'h0000000000000000;
                    lut10=64'h0000000000000000;
                end
                6'd3:begin
                    lut0=64'h55555554aaaaaaaa;
                    lut1=64'h6666666733333333;
                    lut2=64'h78787879c3c3c3c3;
                    lut3=64'h807f807e03fc03fc;
                    lut4=64'hff80007e03fffc00;
                    lut5=64'hffffff8003ffffff;
                    lut6=64'hfffffffe03ffffff;
                    lut7=64'h00000001fc000000;
                    lut8=64'h0000000000000000;
                    lut9=64'h0000000000000000;
                    lut10=64'h0000000000000000;
                end
                6'd4:begin
                    lut0=64'had55555555555555;
                    lut1=64'hce66666666666666;
                    lut2=64'h0878787878787878;
                    lut3=64'hf07f807f807f807f;
                    lut4=64'h0780007fff80007f;
                    lut5=64'h07ffff800000007f;
                    lut6=64'h000000000000007f;
                    lut7=64'hffffffffffffff80;
                    lut8=64'h0000000000000000;
                    lut9=64'h0000000000000000;
                    lut10=64'h0000000000000000;
                end
                6'd5:begin
                    lut0=64'haaaaaaaaaaaaaaaa;
                    lut1=64'hcccccccccccccccc;
                    lut2=64'h0f0f0f0f0f0f0f0f;
                    lut3=64'hf00ff00ff00ff00f;
                    lut4=64'h000ffff0000ffff0;
                    lut5=64'h000ffffffff00000;
                    lut6=64'hfff0000000000000;
                    lut7=64'hffffffffffffffff;
                    lut8=64'h0000000000000000;
                    lut9=64'h0000000000000000;
                    lut10=64'h0000000000000000;
                end
                6'd6:begin
                    lut0=64'h55555555554aaaaa;
                    lut1=64'h99999999998ccccc;
                    lut2=64'he1e1e1e1e1ef0f0f;
                    lut3=64'hfe01fe01fe0ff00f;
                    lut4=64'hfffe0001ffeffff0;
                    lut5=64'h00000001fff00000;
                    lut6=64'hfffffffe001fffff;
                    lut7=64'hffffffffffffffff;
                    lut8=64'h0000000000000000;
                    lut9=64'h0000000000000000;
                    lut10=64'h0000000000000000;
                end
                6'd7:begin
                    lut0=64'haaaad55555555555;
                    lut1=64'h3333199999999999;
                    lut2=64'h3c3c61e1e1e1e1e1;
                    lut3=64'h3fc07e01fe01fe01;
                    lut4=64'hc0000001fffe0001;
                    lut5=64'hffff8001fffffffe;
                    lut6=64'hffff8001ffffffff;
                    lut7=64'hffff8001ffffffff;
                    lut8=64'h00007ffe00000000;
                    lut9=64'h0000000000000000;
                    lut10=64'h0000000000000000;
                end
                6'd8:begin
                    lut0=64'haaaaaaaaaaaaaaaa;
                    lut1=64'h3333333333333333;
                    lut2=64'h3c3c3c3c3c3c3c3c;
                    lut3=64'h3fc03fc03fc03fc0;
                    lut4=64'hc0003fffc0003fff;
                    lut5=64'hffffc00000003fff;
                    lut6=64'h0000000000003fff;
                    lut7=64'h0000000000003fff;
                    lut8=64'hffffffffffffc000;
                    lut9=64'h0000000000000000;
                    lut10=64'h0000000000000000;
                end
                6'd9:begin
                    lut0=64'h55555555555554aa;
                    lut1=64'h6666666666666733;
                    lut2=64'h878787878787863c;
                    lut3=64'h07f807f807f807c0;
                    lut4=64'h07fff80007fff9ff;
                    lut5=64'h07fffffff80001ff;
                    lut6=64'hf800000000000000;
                    lut7=64'h0000000000000000;
                    lut8=64'hffffffffffffffff;
                    lut9=64'h0000000000000000;
                    lut10=64'h0000000000000000;
                end
                6'd10:begin
                    lut0=64'haaaaaaad55555555;
                    lut1=64'hccccccce66666666;
                    lut2=64'hf0f0f0f787878787;
                    lut3=64'h00ff00f807f807f8;
                    lut4=64'hff0000f807fff800;
                    lut5=64'h000000fff8000000;
                    lut6=64'hffffff07ffffffff;
                    lut7=64'h0000000000000000;
                    lut8=64'hffffffffffffffff;
                    lut9=64'h0000000000000000;
                    lut10=64'h0000000000000000;
                end
                6'd11:begin
                    lut0=64'h4aaaaaaaaaaaaaaa;
                    lut1=64'h8ccccccccccccccc;
                    lut2=64'h10f0f0f0f0f0f0f0;
                    lut3=64'he0ff00ff00ff00ff;
                    lut4=64'h1f0000ffff0000ff;
                    lut5=64'he00000ffffffff00;
                    lut6=64'he00000ffffffffff;
                    lut7=64'h1fffff0000000000;
                    lut8=64'hffffffffffffffff;
                    lut9=64'h0000000000000000;
                    lut10=64'h0000000000000000;
                end
                6'd12:begin
                    lut0=64'h5555555555555555;
                    lut1=64'h9999999999999999;
                    lut2=64'h1e1e1e1e1e1e1e1e;
                    lut3=64'he01fe01fe01fe01f;
                    lut4=64'h001fffe0001fffe0;
                    lut5=64'hffe00000001fffff;
                    lut6=64'h00000000001fffff;
                    lut7=64'hffffffffffe00000;
                    lut8=64'hffffffffffffffff;
                    lut9=64'h0000000000000000;
                    lut10=64'h0000000000000000;
                end
                6'd13:begin
                    lut0=64'haaaaaaaaaad55555;
                    lut1=64'h3333333333199999;
                    lut2=64'hc3c3c3c3c39e1e1e;
                    lut3=64'hfc03fc03fc1fe01f;
                    lut4=64'hfffc0003ff9fffe0;
                    lut5=64'hfffffffc001fffff;
                    lut6=64'h0000000000600000;
                    lut7=64'hffffffffffffffff;
                    lut8=64'hffffffffffffffff;
                    lut9=64'h0000000000000000;
                    lut10=64'h0000000000000000;
                end
                6'd14:begin
                    lut0=64'h5554aaaaaaaaaaaa;
                    lut1=64'h6667333333333333;
                    lut2=64'h7879c3c3c3c3c3c3;
                    lut3=64'h7f81fc03fc03fc03;
                    lut4=64'h80000003fffc0003;
                    lut5=64'h0001fffc00000003;
                    lut6=64'hfffffffffffffffc;
                    lut7=64'hffffffffffffffff;
                    lut8=64'hffffffffffffffff;
                    lut9=64'h0000000000000000;
                    lut10=64'h0000000000000000;
                end
                6'd15:begin
                    lut0=64'h5555555555555555;
                    lut1=64'h6666666666666666;
                    lut2=64'h7878787878787878;
                    lut3=64'h7f807f807f807f80;
                    lut4=64'h80007fff80007fff;
                    lut5=64'h00007fffffff8000;
                    lut6=64'h00007fffffffffff;
                    lut7=64'h00007fffffffffff;
                    lut8=64'h00007fffffffffff;
                    lut9=64'hffff800000000000;
                    lut10=64'h0000000000000000;
                end
                6'd16:begin
                    lut0=64'haaaaaaaaaaaaad55;
                    lut1=64'hccccccccccccce66;
                    lut2=64'h0f0f0f0f0f0f0878;
                    lut3=64'h0ff00ff00ff00f80;
                    lut4=64'h0ffff0000ffff7ff;
                    lut5=64'hf00000000ffff800;
                    lut6=64'h000000000ffff800;
                    lut7=64'h000000000ffff800;
                    lut8=64'h000000000ffff800;
                    lut9=64'hfffffffff00007ff;
                    lut10=64'h0000000000000000;
                end
                6'd17:begin
                    lut0=64'h5555554aaaaaaaaa;
                    lut1=64'h9999998ccccccccc;
                    lut2=64'he1e1e1ef0f0f0f0f;
                    lut3=64'h01fe01f00ff00ff0;
                    lut4=64'hfe0001e00ffff000;
                    lut5=64'hfffffe000fffffff;
                    lut6=64'h0000001ff0000000;
                    lut7=64'h0000000000000000;
                    lut8=64'h0000000000000000;
                    lut9=64'hffffffffffffffff;
                    lut10=64'h0000000000000000;
                end
                6'd18:begin
                    lut0=64'hd555555555555555;
                    lut1=64'h1999999999999999;
                    lut2=64'h61e1e1e1e1e1e1e1;
                    lut3=64'h81fe01fe01fe01fe;
                    lut4=64'h7e0001fffe0001ff;
                    lut5=64'h7ffffe00000001ff;
                    lut6=64'hfffffffffffffe00;
                    lut7=64'h0000000000000000;
                    lut8=64'h0000000000000000;
                    lut9=64'hffffffffffffffff;
                    lut10=64'h0000000000000000;
                end
                6'd19:begin
                    lut0=64'haaaaaaaaaaaaaaaa;
                    lut1=64'h3333333333333333;
                    lut2=64'h3c3c3c3c3c3c3c3c;
                    lut3=64'hc03fc03fc03fc03f;
                    lut4=64'h003fffc0003fffc0;
                    lut5=64'h003fffffffc00000;
                    lut6=64'h003fffffffffffff;
                    lut7=64'hffc0000000000000;
                    lut8=64'h0000000000000000;
                    lut9=64'hffffffffffffffff;
                    lut10=64'h0000000000000000;
                end
                6'd20:begin
                    lut0=64'h5555555554aaaaaa;
                    lut1=64'h6666666667333333;
                    lut2=64'h87878787863c3c3c;
                    lut3=64'hf807f807f83fc03f;
                    lut4=64'hfff80007fe3fffc0;
                    lut5=64'h00000007ffc00000;
                    lut6=64'h00000007fe000000;
                    lut7=64'hfffffff801ffffff;
                    lut8=64'h0000000000000000;
                    lut9=64'hffffffffffffffff;
                    lut10=64'h0000000000000000;
                end
                6'd21:begin
                    lut0=64'haaad555555555555;
                    lut1=64'hccce666666666666;
                    lut2=64'hf0f7878787878787;
                    lut3=64'hff07f807f807f807;
                    lut4=64'h00000007fff80007;
                    lut5=64'hfff80007fffffff8;
                    lut6=64'h0007fff800000000;
                    lut7=64'hffffffffffffffff;
                    lut8=64'h0000000000000000;
                    lut9=64'hffffffffffffffff;
                    lut10=64'h0000000000000000;
                end
                6'd22:begin
                    lut0=64'haaaaaaaaaaaaaaaa;
                    lut1=64'hcccccccccccccccc;
                    lut2=64'hf0f0f0f0f0f0f0f0;
                    lut3=64'hff00ff00ff00ff00;
                    lut4=64'h0000ffff0000ffff;
                    lut5=64'hffff00000000ffff;
                    lut6=64'hffffffffffff0000;
                    lut7=64'hffffffffffffffff;
                    lut8=64'h0000000000000000;
                    lut9=64'hffffffffffffffff;
                    lut10=64'h0000000000000000;
                end
                6'd23:begin
                    lut0=64'h5555555555554aaa;
                    lut1=64'h9999999999998ccc;
                    lut2=64'h1e1e1e1e1e1e10f0;
                    lut3=64'h1fe01fe01fe01f00;
                    lut4=64'h1fffe0001fffffff;
                    lut5=64'h1fffffffe0001fff;
                    lut6=64'h1fffffffffffffff;
                    lut7=64'h1fffffffffffffff;
                    lut8=64'he000000000000000;
                    lut9=64'hffffffffffffffff;
                    lut10=64'h0000000000000000;
                end
                6'd24:begin
                    lut0=64'haaaaaad555555555;
                    lut1=64'h3333331999999999;
                    lut2=64'hc3c3c39e1e1e1e1e;
                    lut3=64'h03fc03e01fe01fe0;
                    lut4=64'hfc0003801fffe000;
                    lut5=64'h000003ffe0000000;
                    lut6=64'h0000038000000000;
                    lut7=64'h0000038000000000;
                    lut8=64'hfffffc7fffffffff;
                    lut9=64'hffffffffffffffff;
                    lut10=64'h0000000000000000;
                end
                6'd25:begin
                    lut0=64'haaaaaaaaaaaaaaaa;
                    lut1=64'h3333333333333333;
                    lut2=64'hc3c3c3c3c3c3c3c3;
                    lut3=64'h03fc03fc03fc03fc;
                    lut4=64'hfc0003fffc0003ff;
                    lut5=64'h000003fffffffc00;
                    lut6=64'hfffffc0000000000;
                    lut7=64'h0000000000000000;
                    lut8=64'hffffffffffffffff;
                    lut9=64'hffffffffffffffff;
                    lut10=64'h0000000000000000;
                end
                6'd26:begin
                    lut0=64'h5555555555555554;
                    lut1=64'h6666666666666667;
                    lut2=64'h7878787878787879;
                    lut3=64'h807f807f807f807e;
                    lut4=64'h007fff80007fff81;
                    lut5=64'hff800000007ffffe;
                    lut6=64'hffffffffff800001;
                    lut7=64'h0000000000000000;
                    lut8=64'hffffffffffffffff;
                    lut9=64'hffffffffffffffff;
                    lut10=64'h0000000000000000;
                end
                6'd27:begin
                    lut0=64'haaaaaaaaad555555;
                    lut1=64'hccccccccce666666;
                    lut2=64'h0f0f0f0f08787878;
                    lut3=64'hf00ff00ff07f807f;
                    lut4=64'hfff0000ff87fff80;
                    lut5=64'hfffffff0007fffff;
                    lut6=64'hfffffffff87fffff;
                    lut7=64'h0000000007800000;
                    lut8=64'hffffffffffffffff;
                    lut9=64'hffffffffffffffff;
                    lut10=64'h0000000000000000;
                end
                6'd28:begin
                    lut0=64'h554aaaaaaaaaaaaa;
                    lut1=64'h998ccccccccccccc;
                    lut2=64'he1ef0f0f0f0f0f0f;
                    lut3=64'hfe0ff00ff00ff00f;
                    lut4=64'h0010000ffff0000f;
                    lut5=64'h001ffff00000000f;
                    lut6=64'h000000000000000f;
                    lut7=64'hfffffffffffffff0;
                    lut8=64'hffffffffffffffff;
                    lut9=64'hffffffffffffffff;
                    lut10=64'h0000000000000000;
                end
                6'd29:begin
                    lut0=64'h5555555555555555;
                    lut1=64'h9999999999999999;
                    lut2=64'he1e1e1e1e1e1e1e1;
                    lut3=64'hfe01fe01fe01fe01;
                    lut4=64'h0001fffe0001fffe;
                    lut5=64'h0001fffffffe0000;
                    lut6=64'hfffe000000000000;
                    lut7=64'hffffffffffffffff;
                    lut8=64'hffffffffffffffff;
                    lut9=64'hffffffffffffffff;
                    lut10=64'h0000000000000000;
                end
                6'd30:begin
                    lut0=64'haaaaaaaaaaaad555;
                    lut1=64'h3333333333331999;
                    lut2=64'h3c3c3c3c3c3c61e1;
                    lut3=64'h3fc03fc03fc07e01;
                    lut4=64'h3fffc0003ffffffe;
                    lut5=64'hc00000003fff8000;
                    lut6=64'hffffffffc0007fff;
                    lut7=64'hffffffffffffffff;
                    lut8=64'hffffffffffffffff;
                    lut9=64'hffffffffffffffff;
                    lut10=64'h0000000000000000;
                end
                6'd31:begin
                    lut0=64'h555554aaaaaaaaaa;
                    lut1=64'h6666673333333333;
                    lut2=64'h8787863c3c3c3c3c;
                    lut3=64'h07f807c03fc03fc0;
                    lut4=64'hf80006003fffc000;
                    lut5=64'hfffff8003fffffff;
                    lut6=64'hfffffe003fffffff;
                    lut7=64'hfffffe003fffffff;
                    lut8=64'hfffffe003fffffff;
                    lut9=64'hfffffe003fffffff;
                    lut10=64'h000001ffc0000000;
                end
                6'd32:begin
                    lut0=64'h5555555555555555;
                    lut1=64'h6666666666666666;
                    lut2=64'h8787878787878787;
                    lut3=64'h07f807f807f807f8;
                    lut4=64'hf80007fff80007ff;
                    lut5=64'hfffff800000007ff;
                    lut6=64'h00000000000007ff;
                    lut7=64'h00000000000007ff;
                    lut8=64'h00000000000007ff;
                    lut9=64'h00000000000007ff;
                    lut10=64'hfffffffffffff800;
                end
                6'd33:begin
                    lut0=64'haaaaaaaaaaaaaaad;
                    lut1=64'hccccccccccccccce;
                    lut2=64'hf0f0f0f0f0f0f0f7;
                    lut3=64'h00ff00ff00ff00f8;
                    lut4=64'h00ffff0000ffff07;
                    lut5=64'h00ffffffff000007;
                    lut6=64'hff00000000000000;
                    lut7=64'h0000000000000000;
                    lut8=64'h0000000000000000;
                    lut9=64'h0000000000000000;
                    lut10=64'hffffffffffffffff;
                end
                6'd34:begin
                    lut0=64'h555555554aaaaaaa;
                    lut1=64'h999999998ccccccc;
                    lut2=64'h1e1e1e1e10f0f0f0;
                    lut3=64'he01fe01fe0ff00ff;
                    lut4=64'hffe0001fe0ffff00;
                    lut5=64'h0000001fff000000;
                    lut6=64'hffffffe01fffffff;
                    lut7=64'h0000000000000000;
                    lut8=64'h0000000000000000;
                    lut9=64'h0000000000000000;
                    lut10=64'hffffffffffffffff;
                end
                6'd35:begin
                    lut0=64'haad5555555555555;
                    lut1=64'h3319999999999999;
                    lut2=64'hc39e1e1e1e1e1e1e;
                    lut3=64'hfc1fe01fe01fe01f;
                    lut4=64'h0060001fffe0001f;
                    lut5=64'hff80001fffffffe0;
                    lut6=64'hff80001fffffffff;
                    lut7=64'h007fffe000000000;
                    lut8=64'h0000000000000000;
                    lut9=64'h0000000000000000;
                    lut10=64'hffffffffffffffff;
                end
                6'd36:begin
                    lut0=64'haaaaaaaaaaaaaaaa;
                    lut1=64'h3333333333333333;
                    lut2=64'hc3c3c3c3c3c3c3c3;
                    lut3=64'hfc03fc03fc03fc03;
                    lut4=64'h0003fffc0003fffc;
                    lut5=64'hfffc00000003ffff;
                    lut6=64'h000000000003ffff;
                    lut7=64'hfffffffffffc0000;
                    lut8=64'h0000000000000000;
                    lut9=64'h0000000000000000;
                    lut10=64'hffffffffffffffff;
                end
                6'd37:begin
                    lut0=64'h555555555554aaaa;
                    lut1=64'h6666666666673333;
                    lut2=64'h787878787879c3c3;
                    lut3=64'h7f807f807f81fc03;
                    lut4=64'h7fff80007ffffffc;
                    lut5=64'h7fffffff8001ffff;
                    lut6=64'h8000000000000000;
                    lut7=64'hffffffffffffffff;
                    lut8=64'h0000000000000000;
                    lut9=64'h0000000000000000;
                    lut10=64'hffffffffffffffff;
                end
                6'd38:begin
                    lut0=64'haaaaad5555555555;
                    lut1=64'hccccce6666666666;
                    lut2=64'h0f0f087878787878;
                    lut3=64'h0ff00f807f807f80;
                    lut4=64'hf00008007fff8000;
                    lut5=64'h00000fff80000000;
                    lut6=64'hfffff7ffffffffff;
                    lut7=64'hffffffffffffffff;
                    lut8=64'h0000000000000000;
                    lut9=64'h0000000000000000;
                    lut10=64'hffffffffffffffff;
                end
                6'd39:begin
                    lut0=64'haaaaaaaaaaaaaaaa;
                    lut1=64'hcccccccccccccccc;
                    lut2=64'h0f0f0f0f0f0f0f0f;
                    lut3=64'h0ff00ff00ff00ff0;
                    lut4=64'hf0000ffff0000fff;
                    lut5=64'h00000ffffffff000;
                    lut6=64'h00000fffffffffff;
                    lut7=64'h00000fffffffffff;
                    lut8=64'hfffff00000000000;
                    lut9=64'h0000000000000000;
                    lut10=64'hffffffffffffffff;
                end
                6'd40:begin
                    lut0=64'h555555555555554a;
                    lut1=64'h999999999999998c;
                    lut2=64'he1e1e1e1e1e1e1ef;
                    lut3=64'h01fe01fe01fe01f0;
                    lut4=64'h01fffe0001fffe1f;
                    lut5=64'hfe00000001ffffe0;
                    lut6=64'h0000000001ffffe0;
                    lut7=64'h0000000001ffffe0;
                    lut8=64'hfffffffffe00001f;
                    lut9=64'h0000000000000000;
                    lut10=64'hffffffffffffffff;
                end
                6'd41:begin
                    lut0=64'haaaaaaaad5555555;
                    lut1=64'h3333333319999999;
                    lut2=64'h3c3c3c3c61e1e1e1;
                    lut3=64'hc03fc03f81fe01fe;
                    lut4=64'hffc0003f81fffe00;
                    lut5=64'hffffffc001ffffff;
                    lut6=64'h000000007e000000;
                    lut7=64'h0000000000000000;
                    lut8=64'hffffffffffffffff;
                    lut9=64'h0000000000000000;
                    lut10=64'hffffffffffffffff;
                end
                6'd42:begin
                    lut0=64'h54aaaaaaaaaaaaaa;
                    lut1=64'h6733333333333333;
                    lut2=64'h863c3c3c3c3c3c3c;
                    lut3=64'hf83fc03fc03fc03f;
                    lut4=64'h01c0003fffc0003f;
                    lut5=64'h01ffffc00000003f;
                    lut6=64'hffffffffffffffc0;
                    lut7=64'h0000000000000000;
                    lut8=64'hffffffffffffffff;
                    lut9=64'h0000000000000000;
                    lut10=64'hffffffffffffffff;
                end
                6'd43:begin
                    lut0=64'h5555555555555555;
                    lut1=64'h6666666666666666;
                    lut2=64'h8787878787878787;
                    lut3=64'hf807f807f807f807;
                    lut4=64'h0007fff80007fff8;
                    lut5=64'h0007fffffff80000;
                    lut6=64'h0007ffffffffffff;
                    lut7=64'hfff8000000000000;
                    lut8=64'hffffffffffffffff;
                    lut9=64'h0000000000000000;
                    lut10=64'hffffffffffffffff;
                end
                6'd44:begin
                    lut0=64'haaaaaaaaaaad5555;
                    lut1=64'hccccccccccce6666;
                    lut2=64'hf0f0f0f0f0f78787;
                    lut3=64'hff00ff00ff07f807;
                    lut4=64'hffff0000fffffff8;
                    lut5=64'h00000000fff80000;
                    lut6=64'h00000000fff80000;
                    lut7=64'hffffffff0007ffff;
                    lut8=64'hffffffffffffffff;
                    lut9=64'h0000000000000000;
                    lut10=64'hffffffffffffffff;
                end
                6'd45:begin
                    lut0=64'h55554aaaaaaaaaaa;
                    lut1=64'h99998ccccccccccc;
                    lut2=64'h1e1e10f0f0f0f0f0;
                    lut3=64'h1fe01f00ff00ff00;
                    lut4=64'he0000000ffff0000;
                    lut5=64'hffffe000ffffffff;
                    lut6=64'h00001fff00000000;
                    lut7=64'hffffffffffffffff;
                    lut8=64'hffffffffffffffff;
                    lut9=64'h0000000000000000;
                    lut10=64'hffffffffffffffff;
                end
                6'd46:begin
                    lut0=64'h5555555555555555;
                    lut1=64'h9999999999999999;
                    lut2=64'h1e1e1e1e1e1e1e1e;
                    lut3=64'h1fe01fe01fe01fe0;
                    lut4=64'he0001fffe0001fff;
                    lut5=64'hffffe00000001fff;
                    lut6=64'hffffffffffffe000;
                    lut7=64'hffffffffffffffff;
                    lut8=64'hffffffffffffffff;
                    lut9=64'h0000000000000000;
                    lut10=64'hffffffffffffffff;
                end
                6'd47:begin
                    lut0=64'haaaaaaaaaaaaaad5;
                    lut1=64'h3333333333333319;
                    lut2=64'hc3c3c3c3c3c3c39e;
                    lut3=64'h03fc03fc03fc03e0;
                    lut4=64'h03fffc0003fffc7f;
                    lut5=64'h03fffffffc00007f;
                    lut6=64'h03ffffffffffffff;
                    lut7=64'h03ffffffffffffff;
                    lut8=64'h03ffffffffffffff;
                    lut9=64'hfc00000000000000;
                    lut10=64'hffffffffffffffff;
                end
                6'd48:begin
                    lut0=64'h55555554aaaaaaaa;
                    lut1=64'h6666666733333333;
                    lut2=64'h78787879c3c3c3c3;
                    lut3=64'h807f807e03fc03fc;
                    lut4=64'hff80007e03fffc00;
                    lut5=64'h0000007ffc000000;
                    lut6=64'h0000007e00000000;
                    lut7=64'h0000007e00000000;
                    lut8=64'h0000007e00000000;
                    lut9=64'hffffff81ffffffff;
                    lut10=64'hffffffffffffffff;
                end
                6'd49:begin
                    lut0=64'had55555555555555;
                    lut1=64'hce66666666666666;
                    lut2=64'h0878787878787878;
                    lut3=64'hf07f807f807f807f;
                    lut4=64'h0780007fff80007f;
                    lut5=64'hf800007fffffff80;
                    lut6=64'h07ffff8000000000;
                    lut7=64'h0000000000000000;
                    lut8=64'h0000000000000000;
                    lut9=64'hffffffffffffffff;
                    lut10=64'hffffffffffffffff;
                end
                6'd50:begin
                    lut0=64'haaaaaaaaaaaaaaaa;
                    lut1=64'hcccccccccccccccc;
                    lut2=64'h0f0f0f0f0f0f0f0f;
                    lut3=64'hf00ff00ff00ff00f;
                    lut4=64'h000ffff0000ffff0;
                    lut5=64'hfff00000000fffff;
                    lut6=64'hfffffffffff00000;
                    lut7=64'h0000000000000000;
                    lut8=64'h0000000000000000;
                    lut9=64'hffffffffffffffff;
                    lut10=64'hffffffffffffffff;
                end
                6'd51:begin
                    lut0=64'h55555555554aaaaa;
                    lut1=64'h99999999998ccccc;
                    lut2=64'he1e1e1e1e1ef0f0f;
                    lut3=64'hfe01fe01fe0ff00f;
                    lut4=64'hfffe0001ffeffff0;
                    lut5=64'hfffffffe000fffff;
                    lut6=64'hffffffffffefffff;
                    lut7=64'h0000000000100000;
                    lut8=64'h0000000000000000;
                    lut9=64'hffffffffffffffff;
                    lut10=64'hffffffffffffffff;
                end
                6'd52:begin
                    lut0=64'haaaad55555555555;
                    lut1=64'h3333199999999999;
                    lut2=64'h3c3c61e1e1e1e1e1;
                    lut3=64'h3fc07e01fe01fe01;
                    lut4=64'hc0000001fffe0001;
                    lut5=64'h00007ffe00000001;
                    lut6=64'h0000000000000001;
                    lut7=64'hfffffffffffffffe;
                    lut8=64'h0000000000000000;
                    lut9=64'hffffffffffffffff;
                    lut10=64'hffffffffffffffff;
                end
                6'd53:begin
                    lut0=64'haaaaaaaaaaaaaaaa;
                    lut1=64'h3333333333333333;
                    lut2=64'h3c3c3c3c3c3c3c3c;
                    lut3=64'h3fc03fc03fc03fc0;
                    lut4=64'hc0003fffc0003fff;
                    lut5=64'h00003fffffffc000;
                    lut6=64'hffffc00000000000;
                    lut7=64'hffffffffffffffff;
                    lut8=64'h0000000000000000;
                    lut9=64'hffffffffffffffff;
                    lut10=64'hffffffffffffffff;
                end
                6'd54:begin
                    lut0=64'h55555555555554aa;
                    lut1=64'h6666666666666733;
                    lut2=64'h878787878787863c;
                    lut3=64'h07f807f807f807c0;
                    lut4=64'h07fff80007fff9ff;
                    lut5=64'hf800000007fffe00;
                    lut6=64'hfffffffff80001ff;
                    lut7=64'hffffffffffffffff;
                    lut8=64'h0000000000000000;
                    lut9=64'hffffffffffffffff;
                    lut10=64'hffffffffffffffff;
                end
                6'd55:begin
                    lut0=64'haaaaaaad55555555;
                    lut1=64'hccccccce66666666;
                    lut2=64'hf0f0f0f787878787;
                    lut3=64'h00ff00f807f807f8;
                    lut4=64'hff0000f807fff800;
                    lut5=64'hffffff0007ffffff;
                    lut6=64'hfffffff807ffffff;
                    lut7=64'hfffffff807ffffff;
                    lut8=64'h00000007f8000000;
                    lut9=64'hffffffffffffffff;
                    lut10=64'hffffffffffffffff;
                end
                6'd56:begin
                    lut0=64'h4aaaaaaaaaaaaaaa;
                    lut1=64'h8ccccccccccccccc;
                    lut2=64'h10f0f0f0f0f0f0f0;
                    lut3=64'he0ff00ff00ff00ff;
                    lut4=64'h1f0000ffff0000ff;
                    lut5=64'h1fffff00000000ff;
                    lut6=64'h00000000000000ff;
                    lut7=64'h00000000000000ff;
                    lut8=64'hffffffffffffff00;
                    lut9=64'hffffffffffffffff;
                    lut10=64'hffffffffffffffff;
                end
                6'd57:begin
                    lut0=64'h5555555555555555;
                    lut1=64'h9999999999999999;
                    lut2=64'h1e1e1e1e1e1e1e1e;
                    lut3=64'he01fe01fe01fe01f;
                    lut4=64'h001fffe0001fffe0;
                    lut5=64'h001fffffffe00000;
                    lut6=64'hffe0000000000000;
                    lut7=64'h0000000000000000;
                    lut8=64'hffffffffffffffff;
                    lut9=64'hffffffffffffffff;
                    lut10=64'hffffffffffffffff;
                end
                6'd58:begin
                    lut0=64'haaaaaaaaaad55555;
                    lut1=64'h3333333333199999;
                    lut2=64'hc3c3c3c3c39e1e1e;
                    lut3=64'hfc03fc03fc1fe01f;
                    lut4=64'hfffc0003ff9fffe0;
                    lut5=64'h00000003ffe00000;
                    lut6=64'hfffffffc007fffff;
                    lut7=64'h0000000000000000;
                    lut8=64'hffffffffffffffff;
                    lut9=64'hffffffffffffffff;
                    lut10=64'hffffffffffffffff;
                end
                6'd59:begin
                    lut0=64'h5554aaaaaaaaaaaa;
                    lut1=64'h6667333333333333;
                    lut2=64'h7879c3c3c3c3c3c3;
                    lut3=64'h7f81fc03fc03fc03;
                    lut4=64'h80000003fffc0003;
                    lut5=64'hfffe0003fffffffc;
                    lut6=64'hfffe0003ffffffff;
                    lut7=64'h0001fffc00000000;
                    lut8=64'hffffffffffffffff;
                    lut9=64'hffffffffffffffff;
                    lut10=64'hffffffffffffffff;
                end
                6'd60:begin
                    lut0=64'h5555555555555555;
                    lut1=64'h6666666666666666;
                    lut2=64'h7878787878787878;
                    lut3=64'h7f807f807f807f80;
                    lut4=64'h80007fff80007fff;
                    lut5=64'hffff800000007fff;
                    lut6=64'h0000000000007fff;
                    lut7=64'hffffffffffff8000;
                    lut8=64'hffffffffffffffff;
                    lut9=64'hffffffffffffffff;
                    lut10=64'hffffffffffffffff;
                end
                6'd61:begin
                    lut0=64'haaaaaaaaaaaaad55;
                    lut1=64'hccccccccccccce66;
                    lut2=64'h0f0f0f0f0f0f0878;
                    lut3=64'h0ff00ff00ff00f80;
                    lut4=64'h0ffff0000ffff7ff;
                    lut5=64'h0ffffffff00007ff;
                    lut6=64'hf000000000000000;
                    lut7=64'hffffffffffffffff;
                    lut8=64'hffffffffffffffff;
                    lut9=64'hffffffffffffffff;
                    lut10=64'hffffffffffffffff;
                end
                6'd62:begin
                    lut0=64'h5555554aaaaaaaaa;
                    lut1=64'h9999998ccccccccc;
                    lut2=64'he1e1e1ef0f0f0f0f;
                    lut3=64'h01fe01f00ff00ff0;
                    lut4=64'hfe0001e00ffff000;
                    lut5=64'h000001fff0000000;
                    lut6=64'hfffffe1fffffffff;
                    lut7=64'hffffffffffffffff;
                    lut8=64'hffffffffffffffff;
                    lut9=64'hffffffffffffffff;
                    lut10=64'hffffffffffffffff;
                end
                6'd63:begin
                    lut0=64'hd555555555555555;
                    lut1=64'h1999999999999999;
                    lut2=64'h61e1e1e1e1e1e1e1;
                    lut3=64'h81fe01fe01fe01fe;
                    lut4=64'h7e0001fffe0001ff;
                    lut5=64'h800001fffffffe00;
                    lut6=64'h800001ffffffffff;
                    lut7=64'h800001ffffffffff;
                    lut8=64'h800001ffffffffff;
                    lut9=64'h800001ffffffffff;
                    lut10=64'h800001ffffffffff;
                end
            endcase
            return p==0?{lut10[t[6:1]], lut9[t[6:1]], lut8[t[6:1]], lut7[t[6:1]], lut6[t[6:1]], lut5[t[6:1]], lut4[t[6:1]], lut3[t[6:1]], lut2[t[6:1]], lut1[t[6:1]], lut0[t[6:1]]}:t[10:0];
        end
    endfunction
    assign frame_running=frame_running_owned;
    assign busy=frame_running||child_busy||cache_nonzero_owned;
    assign draining=child_draining;
    assign start_ready=!frame_running&&!child_busy&&!child_draining&&!cache_nonzero_owned&&!reset&&!abort_packet;
    assign accepted_start=start&&start_ready;
    assign cache_ready=!frame_running&&!child_busy&&!child_draining&&!reset&&!abort_packet&&!start;
    assign snapshot_cache_eligible=accepted_qcache_valid&&cache_complete&&cached_fid==accepted_ref_fid&&cached_generation==accepted_ref_generation;
    assign in_ready=state==ADMIT&&fork_in_ready&&!reset&&!abort_packet;
    assign local_abort=abort_packet||(state==FAILED);
    assign child_start=state==CORE_START&&!reset&&!abort_packet;
    assign child_abort=local_abort;
    assign refill_valid=REFILL_OVERLAP!=0?queue_valid:(state==REFILL_SEND&&!reset&&!abort_packet);
    assign refill_last=REFILL_OVERLAP!=0?queue_last:(refill_cursor+1==selected_length);
    assign child_input_data=REFILL_OVERLAP!=0?queue_data:refill_data;
    assign child_out_ready=state==DISPATCH&&out_ready&&child_out_epoch==current_child_epoch&&out_block==expected_block&&!reset&&!abort_packet;
    assign out_valid=state==DISPATCH&&child_out_valid&&child_out_epoch==current_child_epoch&&out_block==expected_block&&!reset&&!abort_packet;
    assign out_epoch=frame_epoch;
    assign out_plane=plane;
    assign out_tile=mapped_tile;
    assign out_qcell=mapped_cell;
    assign out_qscale=mapped_scale;
    assign frame_state=state;
    assign frame_fid=fork_fid;
    assign lookup_tile=13'((plane==0?0:plane==1?5400:6750)+32'(tile_cursor));
    assign lookup_cell=producer_cell_cache;
    assign frame_read_req=REFILL_OVERLAP!=0?(queue_req_valid&&replay_ready):(state==REFILL_REQ&&replay_ready&&!reset&&!abort_packet);
    assign frame_read_rsp=replay_rsp;
    assign frame_read_addr=REFILL_OVERLAP!=0?queue_req_addr:(selected_offset+refill_cursor);
    assign frame_rsp_addr=replay_rsp_addr;
    assign frame_rsp_epoch=replay_rsp_epoch;
    assign frame_read_data=replay_data;
    assign admission_reads=fork_count_reads;

    assign coefficient_lookup_req=state==MAP_REQ&&tile_cursor<tiles(plane)&&!reset&&!abort_packet;
    assign reconstruct_lookup_ready=admitted_ready&&!coefficient_lookup_req&&!reset&&!abort_packet;
    assign admitted_ready=state>=PREP_PLANE&&state!=FAILED;
    assign admitted_key=unused_fork_key;
    assign admitted_fid=fork_fid;
    assign admitted_generation=unused_fork_generation;
    assign lookup_rsp=physical_lookup_rsp&&!lookup_owner_reconstruct;
    assign lookup_mode=physical_lookup_mode;assign lookup_scale=physical_lookup_scale;
    assign reconstruct_lookup_rsp=physical_lookup_rsp&&lookup_owner_reconstruct&&!reset&&!abort_packet;
    assign reconstruct_lookup_mode=physical_lookup_mode;assign reconstruct_lookup_scale=physical_lookup_scale;
    always_ff @(posedge clk)begin
        if(reset||abort_packet||accepted_start)lookup_owner_reconstruct<=0;
        else if(coefficient_lookup_req||(reconstruct_lookup_req&&reconstruct_lookup_ready))
            lookup_owner_reconstruct<=!coefficient_lookup_req;
    end

    cs88_admission_v91i2a admission (
        .clk(clk),.reset(reset),.start(accepted_start),.abort_packet(abort_packet),
        .cache_write(cache_valid&&cache_ready&&cache_data<3),.cache_index(cache_count),.cache_data(cache_data),
        .packet_bytes(packet_bytes),.epoch(epoch),
        .accepted_ref_valid(accepted_ref_valid),.accepted_qcache_valid(snapshot_cache_eligible),
        .accepted_ref_fid(accepted_ref_fid),.accepted_ref_generation(accepted_ref_generation),
        .in_valid(in_valid&&state==ADMIT),.in_last(in_last),.in_data(in_data),.in_ready(fork_in_ready),.busy(unused_fork_busy),
        .receipt_valid(fork_receipt),.receipt_ready(state==ADMIT),.error(admission_error),
        .receipt_epoch(unused_fork_epoch),.fid(fork_fid),.refid(unused_fork_refid),.generation(unused_fork_generation),.key_frame(unused_fork_key),
        .mode_bytes(unused_fork_mode_bytes),.qmap_bytes(unused_fork_qmap_bytes),.hud_bytes(unused_fork_hud_bytes),.data_bytes(unused_fork_data_bytes),
        .plane_blocks(fork_blocks),.plane_offset(fork_offsets),.plane_length(fork_lengths),.plane_entropy(fork_entropy),
        .stage_read_req(unused_fork_read_req),.stage_read_rsp(unused_fork_read_rsp),.stage_write(unused_fork_write),
        .stage_pending(unused_fork_pending),.stage_cancel(unused_fork_cancel),
        .stage_read_addr(unused_fork_read_addr),.stage_rsp_addr(unused_fork_rsp_addr),
        .stage_req_epoch(unused_fork_req_epoch),.stage_rsp_epoch(unused_fork_rsp_epoch),.stage_read_data(unused_fork_data),
        .debug_state(unused_fork_state),.count_cycles(unused_fork_cycles),.count_inputs(unused_fork_inputs),
        .count_stage_reads(fork_count_reads),.count_stage_responses(unused_fork_responses),.count_receipt_wait(unused_fork_wait),.required_cells(unused_fork_required),
        .replay_req(REFILL_OVERLAP!=0?queue_req_valid:(state==REFILL_REQ&&!reset&&!abort_packet)),.replay_addr(frame_read_addr),
        .replay_ready(replay_ready),.replay_rsp_valid(replay_rsp),.replay_data(replay_data),
        .replay_rsp_addr(replay_rsp_addr),.replay_rsp_epoch(replay_rsp_epoch),
        .lookup_req(coefficient_lookup_req||(reconstruct_lookup_req&&reconstruct_lookup_ready)),
        .lookup_tile(coefficient_lookup_req?lookup_tile:reconstruct_lookup_tile),
        .lookup_cell(coefficient_lookup_req?lookup_cell:reconstruct_lookup_cell),
        .lookup_rsp_valid(physical_lookup_rsp),.lookup_mode(physical_lookup_mode),.lookup_scale(physical_lookup_scale)
    );

    assign queue_stall=REFILL_OVERLAP!=0&&queue_valid&&!child_in_ready;

    generate if(REFILL_OVERLAP!=0) begin : refill_overlap_enabled
        byte_refill_queue_v91i2b refill_queue (
            .clk(clk),.reset(reset),.cancel(abort_packet||local_abort),
            .start(child_start),.clear_stats(accepted_start),
            .start_offset(selected_offset),.start_length(selected_length),.start_epoch(frame_epoch),
            .req_valid(queue_req_valid),.req_ready(replay_ready),.req_addr(queue_req_addr),.req_epoch(queue_req_epoch),
            .rsp_valid(replay_rsp),.rsp_addr(replay_rsp_addr),.rsp_epoch(replay_rsp_epoch),.rsp_data(replay_data),
            .out_valid(queue_valid),.out_ready(child_in_ready),.out_data(queue_data),.out_last(queue_last),
            .done(queue_done),.error(queue_error),.active(queue_active),.fifo_count(queue_count),.pending(queue_pending),
            .push_event(queue_push),.pop_event(queue_pop),
            .count_requests(queue_requests),.count_responses(queue_responses),.count_pops(queue_pops),.count_stalls(queue_stalls),
            .count_cancel_queued(queue_cancel_queued),.count_cancel_pending(queue_cancel_pending),
            .max_count(queue_max_count),.max_owned(queue_max_owned)
        );
    end else begin : refill_overlap_disabled
        assign queue_req_valid=0;assign queue_req_addr=0;assign queue_req_epoch=0;
        assign queue_done=0;assign queue_error=0;assign queue_data=0;assign queue_valid=0;assign queue_last=0;
        assign queue_active=0;assign queue_count=0;assign queue_pending=0;assign queue_push=0;assign queue_pop=0;
        assign queue_requests=0;assign queue_responses=0;assign queue_pops=0;assign queue_stalls=0;
        assign queue_cancel_queued=0;assign queue_cancel_pending=0;assign queue_max_count=0;assign queue_max_owned=0;
    end endgenerate

    always_ff @(posedge clk) begin
        if(reset||abort_packet)begin
            begin cache_count<=0;cache_nonzero_owned<=1'b0; end cached_fid<=0;cached_generation<=0;cache_complete<=0;cache_error<=0;
        end else if(accepted_start)begin
            // One-shot trusted cache: QM2 may overwrite the same provisional
            // scale RAM. Its old tag must never authorize a later transaction.
            cache_complete<=0;
        end else if(cache_valid&&cache_ready)begin
            if(cache_count==0)begin
                cached_fid<=cache_ref_fid;cached_generation<=cache_ref_generation;
                cache_complete<=0;cache_error<=0;
            end
            if(cache_data==3)cache_error<=3;
            else if(cache_last!=(cache_count==1349))cache_error<=1;
            if(cache_last||cache_count==1349)begin
                begin cache_count<=0;cache_nonzero_owned<=1'b0; end 
                if(cache_last&&cache_count==1349&&cache_data<3&&(cache_count==0||cache_error==0))cache_complete<=1;
            end else begin cache_count<=cache_count+1;cache_nonzero_owned<=(11'(cache_count+11'd1)!=11'd0); end 
        end
    end

    always_ff @(posedge clk) begin
        if(reset||abort_packet)begin
            begin state<=IDLE;frame_running_owned<=1'b0; end error<=0;fault_o<=(0)!=0;done<=0;plane<=0;tile_cursor<=0;producer_cell_cache<=0;mapped_tile<=0;mapped_cell<=0;mapped_scale<=0;
            expected_block<=0;refill_cursor<=0;selected_offset<=0;selected_length<=0;selected_blocks<=0;
            frame_epoch<=0;latched_size<=0;current_child_epoch<=0;refill_data<=0;child_owned<=0;
            core_starts<=0;refill_bytes<=0;blocked_starts<=0;replay_reads<=0;
        end else begin
            if(start&&!start_ready)blocked_starts<=blocked_starts+1;
            if(accepted_start)begin
                begin state<=ADMIT;frame_running_owned<=1'b1; end error<=0;fault_o<=(0)!=0;done<=0;frame_epoch<=epoch;latched_size<=packet_bytes;
                plane<=0;tile_cursor<=0;producer_cell_cache<=0;expected_block<=0;child_owned<=0;core_starts<=0;refill_bytes<=0;replay_reads<=0;
                if(epoch==0||epoch<=last_frame_epoch)begin begin state<=FAILED;frame_running_owned<=1'b0; end error<=65;fault_o<=(65)!=0;end
                else last_frame_epoch<=epoch;
            end else begin
                if(frame_read_req)replay_reads<=replay_reads+1;
                if(child_start)begin core_starts<=core_starts+1;child_owned<=1;end
                else if(child_done)child_owned<=0;
                if(refill_valid&&child_in_ready)refill_bytes<=refill_bytes+1;
                if(REFILL_OVERLAP!=0&&frame_running&&queue_error!=0)begin
                    begin state<=FAILED;frame_running_owned<=1'b0; end error<=67;fault_o<=(67)!=0;child_owned<=0;
                end else if(frame_running&&child_owned&&child_error!=0)begin
                    begin state<=FAILED;frame_running_owned<=1'b0; end error<=8'h80|child_error;fault_o<=(8'h80|child_error)!=0;child_owned<=0;
                end else case(state)
                    ADMIT:begin
                        if(admission_error!=0)begin begin state<=FAILED;frame_running_owned<=1'b0; end error<=admission_error;fault_o<=(admission_error)!=0;end
                        else if(fork_receipt)begin state<=CHECK_ENTROPY;frame_running_owned<=1'b1; end 
                    end
                    CHECK_ENTROPY:begin
                        if((fork_blocks[0]!=0&&fork_entropy[0]!=2)||(fork_blocks[1]!=0&&fork_entropy[1]!=2)||(fork_blocks[2]!=0&&fork_entropy[2]!=2))begin
                            begin state<=FAILED;frame_running_owned<=1'b0; end error<=64;fault_o<=(64)!=0;
                        end else if({32'd0,child_nonce}+64'(fork_blocks[0]!=0)+64'(fork_blocks[1]!=0)+64'(fork_blocks[2]!=0)>64'hffffffff)begin
                            begin state<=FAILED;frame_running_owned<=1'b0; end error<=66;fault_o<=(66)!=0;
                        end else begin plane<=0;producer_cell_cache<=quant_cell(0,tile_cursor);begin state<=PREP_PLANE;frame_running_owned<=1'b1; end end
                    end
                    PREP_PLANE:begin
                        if(fork_blocks[plane]==0)begin state<=NEXT_PLANE;frame_running_owned<=1'b1; end 
                        else begin
                            selected_offset<=fork_offsets[plane];selected_length<=fork_lengths[plane];selected_blocks<=17'(fork_blocks[plane]);
                            tile_cursor<=0;producer_cell_cache<=0;expected_block<=0;refill_cursor<=0;begin state<=ALLOCATE;frame_running_owned<=1'b1; end 
                        end
                    end
                    ALLOCATE:begin
                        if(child_busy||child_draining)begin end
                        else if(child_nonce==32'hffffffff)begin begin state<=FAILED;frame_running_owned<=1'b0; end error<=66;fault_o<=(66)!=0;end
                        else begin current_child_epoch<=child_nonce+1;child_nonce<=child_nonce+1;begin state<=CORE_START;frame_running_owned<=1'b1; end end
                    end
                    CORE_START:begin state<=REFILL_OVERLAP!=0?REFILL_STREAM:REFILL_REQ;frame_running_owned<=1'b1; end 
                    REFILL_REQ:if(replay_ready)begin state<=REFILL_WAIT;frame_running_owned<=1'b1; end 
                    REFILL_WAIT:if(replay_rsp)begin
                        if(replay_rsp_addr!=accepted_replay_address||replay_rsp_epoch!=accepted_replay_epoch)begin begin state<=FAILED;frame_running_owned<=1'b0; end error<=67;fault_o<=(67)!=0;end
                        else begin refill_data<=replay_data;begin state<=REFILL_SEND;frame_running_owned<=1'b1; end end
                    end
                    REFILL_SEND:if(child_in_ready)begin
                        if(refill_last)begin state<=MAP_REQ;frame_running_owned<=1'b1; end 
                        else begin refill_cursor<=refill_cursor+1;begin state<=REFILL_REQ;frame_running_owned<=1'b1; end end
                    end
                    REFILL_STREAM:if(queue_done)begin state<=MAP_REQ;frame_running_owned<=1'b1; end 
                    MAP_REQ:begin
                        if(tile_cursor>=tiles(plane))begin begin state<=FAILED;frame_running_owned<=1'b0; end error<=67;fault_o<=(67)!=0;end
                        else begin state<=MAP_WAIT;frame_running_owned<=1'b1; end 
                    end
                    MAP_WAIT:if(lookup_rsp)begin
                        if(lookup_mode==2)begin
                            mapped_tile<=tile_cursor;mapped_cell<=producer_cell_cache;mapped_scale<=lookup_scale;begin state<=DISPATCH;frame_running_owned<=1'b1; end 
                        end else begin tile_cursor<=tile_cursor+1;producer_cell_cache<=quant_cell(plane,tile_cursor+13'd1);begin state<=MAP_REQ;frame_running_owned<=1'b1; end end
                    end
                    DISPATCH:begin
                        if(child_out_valid&&(child_out_epoch!=current_child_epoch||out_block!=expected_block))begin begin state<=FAILED;frame_running_owned<=1'b0; end error<=67;fault_o<=(67)!=0;end
                        else if(out_valid&&out_ready&&out_index==63)begin
                            expected_block<=expected_block+1;
                            if(32'(expected_block)+1==32'(selected_blocks))begin state<=WAIT_DONE;frame_running_owned<=1'b1; end 
                            else begin tile_cursor<=tile_cursor+1;producer_cell_cache<=quant_cell(plane,tile_cursor+13'd1);begin state<=MAP_REQ;frame_running_owned<=1'b1; end end
                        end
                    end
                    WAIT_DONE:if(child_done&&!child_busy&&!child_draining)begin state<=NEXT_PLANE;frame_running_owned<=1'b1; end 
                    NEXT_PLANE:begin
                        if(plane==2)begin done<=1;begin state<=FINISHED;frame_running_owned<=1'b0; end end
                        else begin plane<=plane+1;producer_cell_cache<=quant_cell(plane+2'd1,tile_cursor);begin state<=PREP_PLANE;frame_running_owned<=1'b1; end end
                    end
                    default:begin end
                endcase
            end
        end
    end
`ifndef SYNTHESIS
    always_ff @(posedge clk) if(!reset&&!abort_packet)begin
        assert(producer_cell_cache==quant_cell(plane,tile_cursor))else $fatal(1,"producer quant-cell cache mismatch");
        assert(!(child_start&&(child_busy||child_draining)))else $fatal(1,"start before prior child ownership drain");
        assert(!out_valid||state==DISPATCH)else $fatal(1,"coefficient without positional binding");
        assert(!frame_read_req||frame_read_addr<latched_size)else $fatal(1,"outer packet replay bound");
        if(REFILL_OVERLAP!=0&&frame_read_req)assert(queue_req_epoch==frame_epoch)else $fatal(1,"refill request frame epoch mismatch");
        assert(!done||(!out_valid&&!child_busy))else $fatal(1,"frame coefficient completion before child quiescence");
        assert(!cache_ready||(!frame_running&&!child_busy&&!child_draining))else $fatal(1,"qcache write while owned");
    end
`endif

    br88_pipeline_v91h #(.SYNC_STAGING(1)) child (
        .clk(clk),
        .reset(reset),
        .start(child_start),
        .abort_packet(child_abort),
        .packet_bytes(selected_length),
        .epoch(current_child_epoch),
        .blocks(selected_blocks),
        .serial_clear(serial_clear),
        .write_overlap(write_overlap),
        .read_prefetch(read_prefetch),
        .tile_overlap(tile_overlap),
        .in_valid(refill_valid),
        .in_ready(child_in_ready),
        .in_data(child_input_data),
        .in_last(refill_last),
        .out_valid(child_out_valid),
        .out_ready(child_out_ready),
        .out_block(out_block),
        .out_index(out_index),
        .out_value(out_value),
        .out_epoch(child_out_epoch),
        .done(child_done),
        .error(child_error),
        .busy(child_busy),
        .draining(child_draining),
        .scratch_sealed(scratch_sealed),
        .used_bytes(used_bytes),
        .count_cycles(count_cycles),
        .count_input_bytes(count_input_bytes),
        .count_dense(count_dense),
        .count_reads(count_reads),
        .count_writes(count_writes),
        .count_dense_stall(count_dense_stall),
        .mem_req_valid(mem_req_valid),
        .mem_req_ready(mem_req_ready),
        .mem_req_write(mem_req_write),
        .mem_req_addr(mem_req_addr),
        .mem_req_data(mem_req_data),
        .mem_req_epoch(mem_req_epoch),
        .mem_rsp_valid(mem_rsp_valid),
        .mem_rsp_ready(mem_rsp_ready),
        .mem_rsp_data(mem_rsp_data),
        .mem_rsp_epoch(mem_rsp_epoch),
        .mem_rsp_error(mem_rsp_error),
        .packet_state(packet_state),
        .metadata_wait(metadata_wait),
        .dbg_running(dbg_running),
        .dbg_allocation(dbg_allocation),
        .dbg_seal_sent(dbg_seal_sent),
        .dbg_packet_done(dbg_packet_done),
        .dbg_coef_valid(dbg_coef_valid),
        .dbg_coef_ready(dbg_coef_ready),
        .dbg_coef_band(dbg_coef_band),
        .dbg_coef_block(dbg_coef_block),
        .dbg_coef_index(dbg_coef_index),
        .dbg_coef_value(dbg_coef_value),
        .dbg_coef_epoch(dbg_coef_epoch),
        .dbg_meta_valid(dbg_meta_valid),
        .dbg_meta_ready(dbg_meta_ready),
        .dbg_meta_raw(dbg_meta_raw),
        .dbg_band_end_valid(dbg_band_end_valid),
        .dbg_band_end_ready(dbg_band_end_ready),
        .dbg_band_end_band(dbg_band_end_band),
        .dbg_seal_valid(dbg_seal_valid),
        .dbg_seal_ready(dbg_seal_ready),
        .dbg_scratch_state(dbg_scratch_state),
        .dbg_scratch_return_state(dbg_scratch_return_state),
        .dbg_scratch_outstanding(dbg_scratch_outstanding),
        .dbg_prefetch_offer(dbg_prefetch_offer),
        .dbg_prefetch_launch(dbg_prefetch_launch),
        .dbg_prefetch_use(dbg_prefetch_use),
        .dbg_tile_mode(dbg_tile_mode),
        .dbg_tile_preparing(dbg_tile_preparing),
        .dbg_prepare_bank(dbg_prepare_bank),
        .dbg_emit_bank(dbg_emit_bank),
        .dbg_bank_ready(dbg_bank_ready),
        .dbg_bank_owned(dbg_bank_owned),
        .dbg_emitter_state(dbg_emitter_state),
        .dbg_prepare_block(dbg_prepare_block),
        .dbg_bank_block(dbg_bank_block),
        .dbg_bank_epoch(dbg_bank_epoch),
        .dbg_tile_prepare_start(dbg_tile_prepare_start),
        .dbg_tile_publish(dbg_tile_publish),
        .dbg_tile_release(dbg_tile_release),
        .count_emitter_state(count_emitter_state),
        .count_tile_starts(count_tile_starts),
        .count_tile_publishes(count_tile_publishes),
        .count_tile_releases(count_tile_releases),
        .count_prepare_output_overlap(count_prepare_output_overlap),
        .count_prepare_output_hold(count_prepare_output_hold),
        .count_tile_read_output_overlap(count_tile_read_output_overlap),
        .count_tile_bank_wait(count_tile_bank_wait),
        .count_both_ready_wait(count_both_ready_wait),
        .count_tile_prep_done_wait(count_tile_prep_done_wait),
        .count_output_valid(count_output_valid),
        .count_publish_release_same_edge(count_publish_release_same_edge),
        .max_tile_owned(max_tile_owned),
        .max_tile_ready(max_tile_ready),
        .count_prefetch_offers(count_prefetch_offers),
        .count_prefetch_accepts(count_prefetch_accepts),
        .count_prefetch_acks(count_prefetch_acks),
        .count_prefetch_uses(count_prefetch_uses),
        .count_dense_during_read_pending(count_dense_during_read_pending),
        .count_prefetch_drain_wait(count_prefetch_drain_wait),
        .max_prefetch_offer(max_prefetch_offer),
        .dbg_write_slot_valid(dbg_write_slot_valid),
        .dbg_assembler_full(dbg_assembler_full),
        .dbg_write_enqueue(dbg_write_enqueue),
        .count_write_enqueues(count_write_enqueues),
        .count_write_accepts(count_write_accepts),
        .count_write_acks(count_write_acks),
        .count_full_wait(count_full_wait),
        .count_packing_during_write_pending(count_packing_during_write_pending),
        .max_write_slot(max_write_slot),
        .max_owned_lines(max_owned_lines),
        .dbg_scratch_phase(dbg_scratch_phase),
        .dbg_scratch_assembly_bytes(dbg_scratch_assembly_bytes),
        .dbg_scratch_cache_valid(dbg_scratch_cache_valid),
        .dbg_scratch_head_valid(dbg_scratch_head_valid),
        .count_packet_state(count_packet_state),
        .count_scratch_state(count_scratch_state),
        .count_coef_stall(count_coef_stall),
        .count_metadata_wait(count_metadata_wait),
        .count_band_end_stall(count_band_end_stall),
        .count_mem_req_stall(count_mem_req_stall),
        .count_mem_pending(count_mem_pending),
        .count_input_starved(count_input_starved),
        .ts_first_input(ts_first_input),
        .ts_last_input(ts_last_input),
        .ts_metadata_accept(ts_metadata_accept),
        .ts_last_sparse_coef(ts_last_sparse_coef),
        .ts_packet_done_observed(ts_packet_done_observed),
        .ts_seal_accepted(ts_seal_accepted),
        .ts_scratch_sealed_observed(ts_scratch_sealed_observed),
        .ts_first_dense(ts_first_dense),
        .ts_last_dense(ts_last_dense),
        .ts_integrated_done(ts_integrated_done),
        .ts_first_coef_band(ts_first_coef_band),
        .ts_last_coef_band(ts_last_coef_band),
        .ts_band_end(ts_band_end),
        .max_assembly_bytes(max_assembly_bytes),
        .max_cache_valid(max_cache_valid),
        .max_head_valid(max_head_valid),
        .max_outstanding(max_outstanding),
        .stage_read_req(stage_read_req),
        .stage_read_rsp(stage_read_rsp),
        .stage_write(stage_write),
        .stage_pending(stage_pending),
        .stage_context_active(stage_context_active),
        .stage_cancel(stage_cancel),
        .stage_word_valid(stage_word_valid),
        .stage_word_ready(stage_word_ready),
        .stage_read_addr(stage_read_addr),
        .stage_rsp_addr(stage_rsp_addr),
        .stage_write_addr(stage_write_addr),
        .stage_req_epoch(stage_req_epoch),
        .stage_rsp_epoch(stage_rsp_epoch),
        .stage_read_data(stage_read_data),
        .stage_write_data(stage_write_data),
        .stage_buffer_bytes(stage_buffer_bytes),
        .stage_buffer_highwater(stage_buffer_highwater),
        .stage_purpose(stage_purpose),
        .count_stage_reads(count_stage_reads),
        .count_stage_responses(count_stage_responses),
        .count_stage_writes(count_stage_writes),
        .count_stage_fetch_wait(count_stage_fetch_wait),
        .count_stage_word_hold(count_stage_word_hold)
    );
`ifndef SYNTHESIS
    // Checked in all cycles, including sticky failure and retry/abort edges.
    always_ff @(posedge clk)begin
        assert(fault_o==(error!=0)) else $fatal(1,"same-edge fault/status mismatch");
    end
`endif
`ifndef SYNTHESIS
    // Once reset/abort has initialized both original and redundant state,
    // compare every edge, including reset, failure, abort, start and sticky hold.
    logic readiness_initialized=0;
    always_ff @(posedge clk)begin
        if(reset||abort_packet)readiness_initialized<=1;
        if(readiness_initialized)begin
            assert(frame_running_owned==(state!=IDLE&&state!=FINISHED&&state!=FAILED)) else $fatal(1,"producer running predicate mismatch");
            assert(cache_nonzero_owned==(cache_count!=0)) else $fatal(1,"producer cache predicate mismatch");
        end
    end
`endif
endmodule
