// V91i2b bounded refill overlap; compile-time mode 0 retains V91i2a scheduling.
module cs88_pipeline_v91i2b #(parameter integer REFILL_OVERLAP=1) (
    input logic clk, reset, start, abort_packet,
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
    logic [31:0] frame_epoch, latched_size;
    logic [31:0] last_frame_epoch=0, child_nonce=0;
    logic [1:0] plane;
    logic [12:0] tile_cursor, mapped_tile;
    logic [10:0] mapped_cell;
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
    logic [31:0] unused_fork_mode_bytes, unused_fork_qmap_bytes, unused_fork_hud_bytes, unused_fork_data_bytes;
    logic [31:0] fork_blocks [0:2], fork_offsets [0:2], fork_lengths [0:2];
    logic [1:0] fork_entropy [0:2];
    logic fork_in_ready, unused_fork_busy, fork_receipt;
    logic replay_ready, replay_rsp;
    logic [7:0] replay_data;
    logic [31:0] replay_rsp_addr, replay_rsp_epoch;
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
        logic [12:0] row, column, cell_value;
        begin
            row=t/13'd90;column=t%13'd90;
            cell_value=(row>>1)*13'd45+(column>>1);
            return p==0?cell_value[10:0]:t[10:0];
        end
    endfunction
    assign frame_running=state!=IDLE&&state!=FINISHED&&state!=FAILED;
    assign busy=frame_running||child_busy||cache_count!=0;
    assign draining=child_draining;
    assign start_ready=!frame_running&&!child_busy&&!child_draining&&cache_count==0&&!reset&&!abort_packet;
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
    assign lookup_cell=quant_cell(plane,tile_cursor);
    assign frame_read_req=REFILL_OVERLAP!=0?(queue_req_valid&&replay_ready):(state==REFILL_REQ&&replay_ready&&!reset&&!abort_packet);
    assign frame_read_rsp=replay_rsp;
    assign frame_read_addr=REFILL_OVERLAP!=0?queue_req_addr:(selected_offset+refill_cursor);
    assign frame_rsp_addr=replay_rsp_addr;
    assign frame_rsp_epoch=replay_rsp_epoch;
    assign frame_read_data=replay_data;
    assign admission_reads=fork_count_reads;

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
        .lookup_req(state==MAP_REQ&&tile_cursor<tiles(plane)&&!reset&&!abort_packet),.lookup_tile(lookup_tile),.lookup_cell(lookup_cell),
        .lookup_rsp_valid(lookup_rsp),.lookup_mode(lookup_mode),.lookup_scale(lookup_scale)
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
            cache_count<=0;cached_fid<=0;cached_generation<=0;cache_complete<=0;cache_error<=0;
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
                cache_count<=0;
                if(cache_last&&cache_count==1349&&cache_data<3&&(cache_count==0||cache_error==0))cache_complete<=1;
            end else cache_count<=cache_count+1;
        end
    end

    always_ff @(posedge clk) begin
        if(reset||abort_packet)begin
            state<=IDLE;error<=0;done<=0;plane<=0;tile_cursor<=0;mapped_tile<=0;mapped_cell<=0;mapped_scale<=0;
            expected_block<=0;refill_cursor<=0;selected_offset<=0;selected_length<=0;selected_blocks<=0;
            frame_epoch<=0;latched_size<=0;current_child_epoch<=0;refill_data<=0;child_owned<=0;
            core_starts<=0;refill_bytes<=0;blocked_starts<=0;replay_reads<=0;
        end else begin
            if(start&&!start_ready)blocked_starts<=blocked_starts+1;
            if(accepted_start)begin
                state<=ADMIT;error<=0;done<=0;frame_epoch<=epoch;latched_size<=packet_bytes;
                plane<=0;tile_cursor<=0;expected_block<=0;child_owned<=0;core_starts<=0;refill_bytes<=0;replay_reads<=0;
                if(epoch==0||epoch<=last_frame_epoch)begin state<=FAILED;error<=65;end
                else last_frame_epoch<=epoch;
            end else begin
                if(frame_read_req)replay_reads<=replay_reads+1;
                if(child_start)begin core_starts<=core_starts+1;child_owned<=1;end
                else if(child_done)child_owned<=0;
                if(refill_valid&&child_in_ready)refill_bytes<=refill_bytes+1;
                if(REFILL_OVERLAP!=0&&frame_running&&queue_error!=0)begin
                    state<=FAILED;error<=67;child_owned<=0;
                end else if(frame_running&&child_owned&&child_error!=0)begin
                    state<=FAILED;error<=8'h80|child_error;child_owned<=0;
                end else case(state)
                    ADMIT:begin
                        if(admission_error!=0)begin state<=FAILED;error<=admission_error;end
                        else if(fork_receipt)state<=CHECK_ENTROPY;
                    end
                    CHECK_ENTROPY:begin
                        if((fork_blocks[0]!=0&&fork_entropy[0]!=2)||(fork_blocks[1]!=0&&fork_entropy[1]!=2)||(fork_blocks[2]!=0&&fork_entropy[2]!=2))begin
                            state<=FAILED;error<=64;
                        end else if({32'd0,child_nonce}+64'(fork_blocks[0]!=0)+64'(fork_blocks[1]!=0)+64'(fork_blocks[2]!=0)>64'hffffffff)begin
                            state<=FAILED;error<=66;
                        end else begin plane<=0;state<=PREP_PLANE;end
                    end
                    PREP_PLANE:begin
                        if(fork_blocks[plane]==0)state<=NEXT_PLANE;
                        else begin
                            selected_offset<=fork_offsets[plane];selected_length<=fork_lengths[plane];selected_blocks<=17'(fork_blocks[plane]);
                            tile_cursor<=0;expected_block<=0;refill_cursor<=0;state<=ALLOCATE;
                        end
                    end
                    ALLOCATE:begin
                        if(child_busy||child_draining)begin end
                        else if(child_nonce==32'hffffffff)begin state<=FAILED;error<=66;end
                        else begin current_child_epoch<=child_nonce+1;child_nonce<=child_nonce+1;state<=CORE_START;end
                    end
                    CORE_START:state<=REFILL_OVERLAP!=0?REFILL_STREAM:REFILL_REQ;
                    REFILL_REQ:if(replay_ready)state<=REFILL_WAIT;
                    REFILL_WAIT:if(replay_rsp)begin
                        if(replay_rsp_addr!=selected_offset+refill_cursor||replay_rsp_epoch!=frame_epoch)begin state<=FAILED;error<=67;end
                        else begin refill_data<=replay_data;state<=REFILL_SEND;end
                    end
                    REFILL_SEND:if(child_in_ready)begin
                        if(refill_last)state<=MAP_REQ;
                        else begin refill_cursor<=refill_cursor+1;state<=REFILL_REQ;end
                    end
                    REFILL_STREAM:if(queue_done)state<=MAP_REQ;
                    MAP_REQ:begin
                        if(tile_cursor>=tiles(plane))begin state<=FAILED;error<=67;end
                        else state<=MAP_WAIT;
                    end
                    MAP_WAIT:if(lookup_rsp)begin
                        if(lookup_mode==2)begin
                            mapped_tile<=tile_cursor;mapped_cell<=quant_cell(plane,tile_cursor);mapped_scale<=lookup_scale;state<=DISPATCH;
                        end else begin tile_cursor<=tile_cursor+1;state<=MAP_REQ;end
                    end
                    DISPATCH:begin
                        if(child_out_valid&&(child_out_epoch!=current_child_epoch||out_block!=expected_block))begin state<=FAILED;error<=67;end
                        else if(out_valid&&out_ready&&out_index==63)begin
                            expected_block<=expected_block+1;
                            if(32'(expected_block)+1==32'(selected_blocks))state<=WAIT_DONE;
                            else begin tile_cursor<=tile_cursor+1;state<=MAP_REQ;end
                        end
                    end
                    WAIT_DONE:if(child_done&&!child_busy&&!child_draining)state<=NEXT_PLANE;
                    NEXT_PLANE:begin
                        if(plane==2)begin done<=1;state<=FINISHED;end
                        else begin plane<=plane+1;state<=PREP_PLANE;end
                    end
                    default:begin end
                endcase
            end
        end
    end
`ifndef SYNTHESIS
    always_ff @(posedge clk) if(!reset&&!abort_packet)begin
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
endmodule
