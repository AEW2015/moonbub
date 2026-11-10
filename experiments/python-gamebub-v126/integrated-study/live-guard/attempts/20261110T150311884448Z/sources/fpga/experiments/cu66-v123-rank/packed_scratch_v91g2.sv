// V91c byte-identical packed scratch, sequential functional implementation.
module packed_scratch_v91g2 (
    input logic clk, reset,
    input logic begin_valid, output logic begin_ready,
    input logic [16:0] begin_blocks, input logic begin_raw, begin_serial_clear, begin_overlap, begin_prefetch, begin_tile_overlap,
    input logic [31:0] begin_count1, begin_count2, begin_count3, begin_epoch,
    input logic [31:0] begin_prefix1, begin_prefix12, begin_prefix123,
    input logic [31:0] begin_threshold1, begin_threshold2, begin_threshold3,
    input logic [31:0] begin_capacity_upper, begin_capacity_lower,
    input logic begin_capacity_wrap,
    input logic coef_valid, output logic coef_ready,
    input logic [1:0] coef_band, input logic [15:0] coef_block,
    input logic [5:0] coef_index, input logic signed [15:0] coef_value,
    input logic [31:0] coef_epoch,
    input logic band_end_valid, output logic band_end_ready,
    input logic [1:0] band_end_band, input logic [31:0] band_end_epoch,
    input logic seal_valid, output logic seal_ready, input logic [31:0] seal_epoch,
    input logic abort_valid, input logic [31:0] abort_epoch,
    output logic busy, sealed, done, output logic [3:0] error,
    output logic [31:0] owned_abort_epoch,
    output logic [31:0] active_epoch=0, output logic [18:0] used_bytes,
    output logic dense_valid, input logic dense_ready,
    output logic [15:0] dense_block, output logic [5:0] dense_index,
    output logic signed [15:0] dense_value, output logic [31:0] dense_epoch,
    output logic mem_req_valid, input logic mem_req_ready,
    output logic mem_req_write, output logic [17:0] mem_req_addr,
    output logic [127:0] mem_req_data, output logic [31:0] mem_req_epoch,
    input logic mem_rsp_valid, output logic mem_rsp_ready,
    input logic [127:0] mem_rsp_data, input logic [31:0] mem_rsp_epoch,
    input logic mem_rsp_error,
    // Direct views of existing registers; observability adds no state changes.
    output logic [4:0] debug_state, debug_return_state,
    output logic debug_outstanding,
    output logic [2:0] debug_phase,
    output logic [4:0] debug_assembly_bytes,
    output logic [3:0] debug_cache_valid,
    output logic debug_prefetch_offer, debug_prefetch_launch, debug_prefetch_use,
    output logic debug_tile_mode, debug_tile_preparing, debug_prepare_bank, debug_emit_bank,
    output logic [1:0] debug_bank_ready, debug_bank_owned, debug_emitter_state,
    output logic [15:0] debug_prepare_block,
    output logic [15:0] debug_bank_block [0:1],
    output logic [31:0] debug_bank_epoch [0:1],
    output logic debug_tile_prepare_start, debug_tile_publish, debug_tile_release,
    output logic debug_write_slot_valid, debug_assembler_full, debug_write_enqueue,
    output logic [2:0] debug_head_valid
);
    typedef enum logic [4:0] {IDLE, INGEST, APPEND, NEXT_BAND, WAIT_SEAL,
        HEADER0, HEADER1, HEADER_DONE, WRITE_REQ, WRITE_WAIT, READ_REQ,
        READ_WAIT, DESC0, DESC1, CLEAR_TILE, DC_FETCH, DC_EXTRACT,
        AC_CHECK, AC_FETCH, AC_EXTRACT, EMIT, RAW_FETCH, RAW_EXTRACT,
        FINISHED, FAILED, DRAIN, FLUSH_LINE, PREFETCH_DRAIN, BANK_WAIT, PREP_DONE, BEGIN_PLAN, BEGIN_COMMIT} state_t;
    state_t state=IDLE, return_state;
    // Same-edge redundant quiescence predicate. Every original state write
    // below carries its own sibling update, including final override priority.
    logic busy_owned=0;
    logic outstanding=0, epoch_seen=0;
    logic [31:0] last_epoch=0;
    logic [16:0] blocks;
    logic raw_mode, serial_clear, overlap_mode, prefetch_mode;
    logic tile_overlap_mode=0, tile_mode;
    logic prep_bank, emit_bank, tile_preparing;
    logic [15:0] prepare_block;
    logic [5:0] tile_emit_index;
    logic [1:0] bank_ready;
    logic [15:0] bank_block[0:1];
    logic [31:0] bank_epoch[0:1];
    logic prefetch_offer=0;
    logic [3:0] prefetched_valid;
    logic [1:0] prefetch_segment, candidate_segment;
    logic [17:0] candidate_address;
    logic candidate_valid, prefetch_launch, prefetch_complete, response_failure;
    // V114: address arithmetic matures on existing fetch/check edges.
    // Payload registers are unowned outside eligible emission states.
    logic [17:0] prepared_dc_line, prepared_raw_line;
    logic [17:0] prepared_ac_line [1:3];
    logic prepared_sparse_more, prepared_raw_more;
    // One local next-block/terminal plan, matured on an existing edge while
    // output context is stable. This is metadata only, not another tile owner.
    typedef struct packed {
        logic [31:0] epoch;
        logic [15:0] block_id;
        logic [16:0] block_limit;
        logic raw;
        logic last_block;
        logic [15:0] next_block;
        state_t next_state;
    } output_plan_t;
    output_plan_t output_plan;
    logic [3:1] prepared_ac_more;
    logic write_slot_valid=0;
    logic slot_available;
    logic [63:0] tile_valid[0:1];
    logic [31:0] counts[0:3], starts[0:3];
    logic [31:0] written, previous_position;
    logic previous_valid;
    logic [2:0] phase;
    logic [127:0] assembler;
    logic [4:0] assembly_bytes;
    logic [31:0] write_address;
    logic [31:0] pending_record;
    logic [2:0] pending_bytes;
    logic [31:0] pending_position;
    // Two physical speculative banks represent ONE logical pending tuple.
    // Only the small view selector sees the original acceptance/kill priority.
    logic record_view_bank=0, record_view_seen=0;
    logic [31:0] record_payload [0:1], position_payload [0:1];
    logic [2:0] bytes_payload [0:1];
    logic [66:0] prospective_record;
    assign prospective_record={
        (raw_mode || phase==0 ? {16'd0,coef_value} : {coef_block[12:0],coef_index,coef_value[12:0]}),
        (raw_mode || phase==0 ? 3'd2 : 3'd4),input_position};
    for(genvar record_bank=0;record_bank<2;record_bank=record_bank+1)begin: pending_storage
        // Continuously refresh only the inactive bank. No reset, cancel,
        // input_bad, coef_valid, phase or format predicate gates this write.
        always_ff @(posedge clk)if(record_view_bank!=1'(record_bank))
            {record_payload[record_bank],bytes_payload[record_bank],position_payload[record_bank]}<=prospective_record;
    end
    // Before the first original write, the initialized two-state view is zero.
    // All warm reset/abort/error edges retain this logical view exactly.
    assign pending_record=record_view_seen ? record_payload[record_view_bank] : 32'd0;
    assign pending_bytes=record_view_seen ? bytes_payload[record_view_bank] : 3'd0;
    assign pending_position=record_view_seen ? position_payload[record_view_bank] : 32'd0;
    logic [127:0] transfer_data;
    logic [17:0] transfer_address;
    logic [31:0] request_epoch;
    logic [127:0] descriptor_low;
    logic [127:0] cache_data[0:3];
    logic [18:0] cache_positions[0:3][0:15];
    logic [18:0] head_positions[1:3];
    logic [17:0] cache_address[0:3];
    logic [3:0] cache_valid;
    logic [1:0] read_segment;
    logic [31:0] read_address;
    logic [31:0] heads[1:3], cursors[1:3];
    logic [3:1] head_valid;
    logic [1:0] read_band;
    // IV115.S2: tile is the original visible raw view, including the latest
    // accepted write. A single local tuple retires into private payload on the
    // next edge; forwarding preserves every original visible cycle/value.
    logic signed [15:0] tile[0:1][0:63];
    logic signed [15:0] tile_payload[0:1][0:63];
    logic tile_pending_valid=0, tile_pending_bank;
    logic [5:0] tile_pending_index;
    logic signed [15:0] tile_pending_value;
    logic tile_event_valid, tile_event_bank;
    logic [5:0] tile_event_index;
    logic signed [15:0] tile_event_value;
    logic tile_case_eligible;
    logic [15:0] output_block;
    logic [5:0] output_index, clear_index;
    logic signed [15:0] raw_value;
    logic [31:0] plan_start1, plan_start2, plan_start3, plan_used;
    // Only this constant control product is kept in slice logic.
    (* use_dsp = "no" *) logic [31:0] begin_limit43;
    assign begin_limit43=32'(begin_blocks)*43;
    logic [31:0] input_position;
    logic [5:0] input_zigzag;
    logic input_bad;
    logic [31:0] read_word;
    logic signed [15:0] read_half;
    logic [31:0] read_position;
    logic cancel;
    // Exact existing target; generic foreign-epoch abort semantics are unchanged.
    assign owned_abort_epoch=preparing_begin ? queued_epoch : active_epoch;
    logic capacity_bad;
    assign capacity_bad=begin_raw ? begin_blocks>17'd2047 :
        (32'(begin_blocks)>begin_capacity_upper ||
         (begin_capacity_wrap && 32'(begin_blocks)<=begin_capacity_lower));

    function automatic logic [31:0] aligned(input logic [31:0] n);
        aligned=(n+15)&32'hfffffff0;
    endfunction
    // Exact modulo-2^32 carry-save prefix sums; no registered stage or new owner.
    function automatic logic [31:0] sum3(input logic [31:0] a,b,c);
        return (a^b^c)+(((a&b)|(a&c)|(b&c))<<1);
    endfunction
    function automatic logic [31:0] sum4(input logic [31:0] a,b,c,d);
        logic [31:0] s,carry;
        begin
            s=a^b^c;carry=((a&b)|(a&c)|(b&c))<<1;
            return sum3(s,carry,d);
        end
    endfunction
    function automatic logic [31:0] sum5(input logic [31:0] a,b,c,d,e);
        logic [31:0] s0,c0,s1,c1;
        begin
            s0=a^b^c;c0=((a&b)|(a&c)|(b&c))<<1;
            s1=s0^d^e;c1=((s0&d)|(s0&e)|(d&e))<<1;
            return sum3(s1,c1,c0);
        end
    endfunction
    function automatic logic [5:0] zigzag(input logic [5:0] raster);
        integer rank;
        integer sum;
        integer row;
        begin
            rank=0; zigzag=0;
            for(integer diagonal=0;diagonal<15;diagonal=diagonal+1)
                for(integer step=0;step<8;step=step+1) begin
                    row=(diagonal%2==1) ? step : 7-step;
                    sum=diagonal-row;
                    if(sum>=0 && sum<8) begin
                        if(row*8+sum==integer'(raster)) zigzag=6'(rank);
                        rank=rank+1;
                    end
                end
        end
    endfunction
    function automatic logic band_matches(input logic [1:0] band, input logic [5:0] index);
        logic [5:0] z;
        begin
            z=zigzag(index);
            case(band)
                1: band_matches=z>=1 && z<6;
                2: band_matches=z>=6 && z<21;
                3: band_matches=z>=21;
                default: band_matches=index==0;
            endcase
        end
    endfunction
    // All 32-bit record values map exactly to a 19-bit block/rank position.
    function automatic logic [18:0] sparse_position(input logic [18:0] geometry);
        sparse_position={geometry[18:6],zigzag(geometry[5:0])};
    endfunction
    function automatic logic rank_matches(input logic [1:0] band,input logic [5:0] rank);
        case(band)
            1: rank_matches=rank>=1 && rank<6;
            2: rank_matches=rank>=6 && rank<21;
            3: rank_matches=rank>=21;
            default: rank_matches=rank==0;
        endcase
    endfunction
    assign tile_mode=tile_overlap_mode && !raw_mode;
    assign debug_tile_mode=tile_mode;
    assign debug_tile_preparing=tile_mode && tile_preparing;
    assign debug_prepare_bank=prep_bank;
    assign debug_emit_bank=emit_bank;
    assign debug_prepare_block=prepare_block;
    for(genvar b=0;b<2;b=b+1) begin: bank_views
        assign debug_bank_block[b]=bank_block[b];
        assign debug_bank_epoch[b]=bank_epoch[b];
        assert property (@(posedge clk) tile_mode && bank_ready[b] && !cancel && !response_failure &&
            !(debug_tile_release && emit_bank==1'(b)) |=>
            $stable({tile_valid[b],bank_block[b],bank_epoch[b]}) || reset || abort_valid);
        for(genvar k=0;k<64;k=k+1) begin: immutable_payload
            assert property (@(posedge clk) tile_mode && bank_ready[b] && !cancel && !response_failure &&
                !(debug_tile_release && emit_bank==1'(b)) |=>
                $stable(tile[b][k]) || reset || abort_valid);
        end
    end
    assign debug_bank_ready=tile_mode ? bank_ready : 2'b00;
    assign debug_bank_owned=tile_mode ? bank_ready | (tile_preparing ? (2'b01 << prep_bank) : 2'b00) : 2'b00;
    assign debug_emitter_state=!tile_mode ? 2'd3 : !dense_valid ? 2'd0 : dense_ready ? 2'd1 : 2'd2;
    assign debug_tile_prepare_start=tile_mode && !cancel && !response_failure &&
        ((state==DESC1 && descriptor_low=={counts[1],31'd0,raw_mode,15'd0,blocks,32'h43393150} &&
          transfer_data=={32'd0,13'd0,used_bytes,counts[3],counts[2]}) ||
         (state==BANK_WAIT && 17'(prepare_block)+1<blocks && !bank_ready[!prep_bank]));
    assign debug_tile_publish=tile_mode && !cancel && !response_failure && state==AC_CHECK &&
        !ac_check_fetch && !ac_check_apply && read_band==3;
    assign debug_tile_release=tile_mode && dense_valid && dense_ready && tile_emit_index==63;
    assign debug_prefetch_offer=prefetch_offer;
    assign debug_prefetch_launch=prefetch_launch;
    assign debug_write_slot_valid=write_slot_valid;
    assign debug_assembler_full=assembly_bytes==16;
    assign debug_state=state;
    assign debug_return_state=return_state;
    assign debug_outstanding=outstanding;
    assign debug_phase=phase;
    assign debug_assembly_bytes=assembly_bytes;
    assign debug_cache_valid=cache_valid;
    assign debug_head_valid=head_valid;
    always_ff @(posedge clk)begin
        prepared_dc_line<=18'((32+(32'(output_block)+1)*2)&32'hfffffff0);
        prepared_raw_line<=18'((32+(32'(output_block)*64+32'(output_index)+1)*2)&32'hfffffff0);
        prepared_sparse_more<=17'(output_block)+1<blocks;
        output_plan<='{epoch:active_epoch,block_id:output_block,block_limit:blocks,raw:raw_mode,
            last_block:17'(output_block)+1==blocks,next_block:16'(32'(output_block)+32'd1),
            next_state:raw_mode ? RAW_FETCH : CLEAR_TILE};
        prepared_raw_more<=32'(output_block)*64+32'(output_index)+1<32'(blocks)*64;
        for(integer band=1;band<=3;band=band+1)begin
            prepared_ac_line[band]<=18'((starts[band]+cursors[band]*4)&32'hfffffff0);
            prepared_ac_more[band]<=cursors[band]<counts[band];
        end
    end
    always_comb begin
        response_failure=mem_rsp_valid && (!outstanding || mem_rsp_epoch!=request_epoch || mem_rsp_error);
        plan_start1=32+aligned(32'(begin_blocks)*2);
        plan_start2=plan_start1+begin_prefix1;
        plan_start3=plan_start1+begin_prefix12;
        plan_used=begin_raw ? 32+32'(begin_blocks)*128 :
            plan_start1+begin_prefix123;
        read_word=32'(cache_data[read_segment]>>(8*read_address[3:0]));
        read_half=16'(cache_data[0]>>(8*read_address[3:0]));
        read_position={13'd0,cache_positions[read_segment][read_address[3:0]]};
        cancel=reset || (abort_valid && abort_epoch==owned_abort_epoch);
        begin_ready=state==IDLE && !outstanding && !cancel;
        coef_ready=state==INGEST && !cancel;
        band_end_ready=state==INGEST && !coef_valid && !cancel;
        seal_ready=state==WAIT_SEAL && !cancel &&
            (!overlap_mode || (!write_slot_valid && !outstanding && assembly_bytes==0));
        slot_available=!write_slot_valid || (outstanding && mem_rsp_valid &&
            mem_rsp_epoch==request_epoch && !mem_rsp_error);
        busy=busy_owned;
        dense_valid=tile_mode ? bank_ready[emit_bank] && sealed && error==0 &&
            state!=FAILED && state!=DRAIN && !cancel && !response_failure :
            (state==EMIT || state==RAW_EXTRACT) && !cancel && !(prefetch_offer && response_failure);
        dense_block=tile_mode ? bank_block[emit_bank] : output_block;
        dense_index=tile_mode ? tile_emit_index : output_index;
        dense_value=tile_mode ? (tile_valid[emit_bank][tile_emit_index] ? tile[emit_bank][tile_emit_index] : 16'sd0) :
            raw_mode ? raw_value : (tile_valid[0][output_index] ? tile[0][output_index] : 16'sd0);
        dense_epoch=tile_mode ? bank_epoch[emit_bank] : active_epoch;
        mem_req_valid=(state==WRITE_REQ || state==READ_REQ ||
            (write_slot_valid && !outstanding && state!=DRAIN && state!=FAILED) ||
            (prefetch_offer && !outstanding && state!=DRAIN && state!=FAILED)) && !cancel;
        mem_req_write=state==WRITE_REQ || write_slot_valid;
        mem_req_addr=transfer_address;
        mem_req_data=transfer_data;
        mem_req_epoch=request_epoch;
        mem_rsp_ready=1;
        input_zigzag=zigzag(coef_index);
        input_position=raw_mode ? (32'(coef_block)*64+32'(coef_index)) :
            (phase==0 ? 32'(coef_block) : (32'(coef_block)*64+32'(input_zigzag)));
        input_bad=phase_input_bad[phase];
        debug_write_enqueue=overlap_mode && !cancel && slot_available &&
            !(mem_rsp_valid && (!outstanding || mem_rsp_epoch!=request_epoch || mem_rsp_error)) &&
            ((state==APPEND && assembly_bytes+5'(pending_bytes)==16) || state==FLUSH_LINE ||
            (state==INGEST && !coef_valid && band_end_valid && assembly_bytes!=0 &&
             band_end_epoch==active_epoch && band_end_band==phase[1:0] && written==counts[phase[1:0]]));
        // Prefetch only a monotonically forward line whose old cache data is
        // fully consumed. Dense output is already owned by tile/raw_value.
        candidate_valid=0; candidate_segment=0; candidate_address=0;
        if(prefetch_mode && !tile_mode && sealed && !prefetch_offer && !outstanding && !cancel && error==0) begin
            if(state==EMIT && !raw_mode && prepared_sparse_more) begin
                if(!cache_valid[0] || cache_address[0]!=prepared_dc_line) begin
                    candidate_valid=1; candidate_segment=0; candidate_address=prepared_dc_line;
                end
                for(integer b=1;b<=3;b=b+1) begin
                    if(!candidate_valid && prepared_ac_more[b] &&
                       (!cache_valid[b] || cache_address[b]!=prepared_ac_line[b])) begin
                        candidate_valid=1; candidate_segment=2'(b); candidate_address=prepared_ac_line[b];
                    end
                end
            end else if(state==RAW_EXTRACT && raw_mode && prepared_raw_more) begin
                if(!cache_valid[0] || cache_address[0]!=prepared_raw_line) begin
                    candidate_valid=1; candidate_segment=0; candidate_address=prepared_raw_line;
                end
            end
        end
        debug_prefetch_use=!cancel && !response_failure &&
            ((state==DC_EXTRACT && cache_valid[0] && prefetched_valid[0] &&
              cache_address[0]==18'(read_address & 32'hfffffff0)) ||
             (state==AC_EXTRACT && cache_valid[read_segment] && prefetched_valid[read_segment] &&
              cache_address[read_segment]==18'(read_address & 32'hfffffff0)));
        prefetch_launch=candidate_valid;
        prefetch_complete=prefetch_offer && outstanding && mem_rsp_valid &&
            mem_rsp_epoch==request_epoch && !mem_rsp_error;

    end

    // V113_PHASE_VALIDATION: phase selects a complete one-bit decision after
    // constant-phase count/position validation. All eight phase encodings retain
    // the original low-two-bit count/band lookup and full phase==0 semantics.
    logic [7:0] phase_input_bad;
    // V119: spatial format lanes compare BEFORE raw/phase selects their
    // compact decisions. All positions remain full32; no input truncation or
    // delayed fault/publication boundary replaces the original INGEST check.
    logic [31:0] input_raster_position,input_sparse_position;
    logic input_raster_bad,input_dc_bad,input_ac_bad;
    // V123: APPEND prepares only the six-bit rank relation. The live full32
    // high/block terms preserve generic previous-position semantics.
    logic [63:0] rank_threshold_mask;
    logic input_sparse_order_bad;
    assign input_sparse_order_bad=(previous_position[31:22]!=0) ||
        (coef_block<previous_position[21:6]) ||
        ((coef_block==previous_position[21:6]) && rank_threshold_mask[coef_index]);
`ifndef SYNTHESIS
    logic rank_owner_valid=0;
    logic [5:0] rank_owner_threshold;
    logic [2:0] rank_owner_phase;
    logic [31:0] rank_owner_epoch;
    always_ff @(posedge clk)begin
        if(cancel || state==BEGIN_COMMIT || state==NEXT_BAND)rank_owner_valid<=0;
        else if(tile_case_eligible && state==APPEND)begin
            rank_owner_valid<=1;rank_owner_threshold<=pending_position[5:0];
            rank_owner_phase<=phase;rank_owner_epoch<=active_epoch;
        end
    end
    always_ff @(posedge clk)if(tile_case_eligible && state==INGEST &&
        coef_valid && previous_valid && !raw_mode)begin
        assert(rank_owner_valid && rank_owner_threshold==previous_position[5:0] &&
            rank_owner_phase==phase && rank_owner_epoch==active_epoch)
            else $fatal(1,"V123 sparse rank threshold mixed owner");
        for(integer rank_index=0;rank_index<64;rank_index=rank_index+1)
            assert(rank_threshold_mask[rank_index]==
                (zigzag(6'(rank_index))<=previous_position[5:0]))
                else $fatal(1,"V123 rank mask differs from literal zigzag threshold");
        assert(input_sparse_order_bad==(input_sparse_position<=previous_position))
            else $fatal(1,"V123 generic full32 sparse ordering mismatch");
    end
`endif
    assign input_raster_position={10'd0,coef_block,coef_index};
    assign input_sparse_position={10'd0,coef_block,input_zigzag};
    assign input_raster_bad=input_raster_position!=written;
    assign input_dc_bad=coef_index!=0 || 32'(coef_block)!=written;
    assign input_ac_bad=!band_matches(coef_band,coef_index) || coef_value==0 ||
        (previous_valid && input_sparse_order_bad);
    for(genvar checking_phase=0;checking_phase<8;checking_phase=checking_phase+1)begin: phase_validation
        wire [31:0] phase_position=raw_mode ? (32'(coef_block)*64+32'(coef_index)) :
            (checking_phase==0 ? 32'(coef_block) : (32'(coef_block)*64+32'(input_zigzag)));
        assign phase_input_bad[checking_phase]=coef_epoch!=active_epoch || coef_band!=2'(checking_phase) ||
            coef_block>=16'(blocks) || coef_value < -2048 || coef_value > 2048 ||
            written>=counts[checking_phase & 3] ||
            (raw_mode ? input_raster_bad : checking_phase==0 ? input_dc_bad : input_ac_bad);
`ifndef SYNTHESIS
        // Complete original expression certifies every phase lane, including
        // illegal full phase encodings whose count/band lookup uses low2 bits.
        always_ff @(posedge clk)if(!cancel && !response_failure && state==INGEST && coef_valid)
            assert(phase_input_bad[checking_phase]==(coef_epoch!=active_epoch || coef_band!=2'(checking_phase) ||
                coef_block>=16'(blocks) || coef_value < -2048 || coef_value > 2048 ||
                written>=counts[checking_phase & 3] ||
                (raw_mode ? phase_position!=written : checking_phase==0 ?
                 (coef_index!=0 || 32'(coef_block)!=written) :
                 (!band_matches(coef_band,coef_index) || coef_value==0 ||
                  (previous_valid && phase_position<=previous_position)))))
                else $fatal(1,"V119 full phase format decision mismatch");
`endif
    end
`ifndef SYNTHESIS
    logic input_bad_reference;
    always_comb begin
        input_bad_reference=coef_epoch!=active_epoch || coef_band!=phase[1:0] ||
            coef_block>=16'(blocks) || coef_value < -2048 || coef_value > 2048 ||
            written>=counts[phase[1:0]];
        if(raw_mode) input_bad_reference=input_bad_reference || input_position!=written;
        else if(phase==0) input_bad_reference=input_bad_reference || coef_index!=0 || 32'(coef_block)!=written;
        else input_bad_reference=input_bad_reference || !band_matches(coef_band,coef_index) || coef_value==0 ||
            (previous_valid && input_position<=previous_position);
    end
    always_ff @(posedge clk)if(!reset && !cancel && !response_failure && state==INGEST && coef_valid)
        assert(input_bad==input_bad_reference)else $fatal(1,"V113 phase validation mismatch");
`endif

    // V112_BANK_VALIDATION_BEGIN: each bank validates its own payload before
    // read_segment selects a one-bit result. Owner/state/drain priority and
    // selected data payload remain unchanged; no speculative failure is used.
    logic [3:0] ac_bank_invalid;
    for(genvar validation_bank=0;validation_bank<4;validation_bank=validation_bank+1)begin: local_ac_validation
        wire [31:0] bank_word=32'(cache_data[validation_bank]>>(8*read_address[3:0]));
        wire [31:0] bank_position={13'd0,cache_positions[validation_bank][read_address[3:0]]};
        assign ac_bank_invalid[validation_bank]=17'(bank_word[31:19])>=blocks ||
            !rank_matches(read_band,bank_position[5:0]) ||
            $signed(bank_word[12:0])==0 || $signed(bank_word[12:0]) < -2048 ||
            $signed(bank_word[12:0]) > 2048 ||
            (cursors[read_band]!=0 && bank_position<={13'd0,head_positions[read_band]});
    end
`ifndef SYNTHESIS
    always_ff @(posedge clk)if(!cancel&&!response_failure&&state==AC_EXTRACT &&
        cache_valid[read_segment]&&cache_address[read_segment]==18'(read_address & 32'hfffffff0))
        assert(ac_bank_invalid[read_segment]==(17'(read_word[31:19])>=blocks || !rank_matches(read_band,read_position[5:0]) ||
                           $signed(read_word[12:0])==0 || $signed(read_word[12:0]) < -2048 ||
                           $signed(read_word[12:0]) > 2048 ||
                           (cursors[read_band]!=0 && read_position<={13'd0,head_positions[read_band]})))
            else $fatal(1,"V112 local AC validation mismatch");
`endif
    // V112_BANK_VALIDATION_END

    // V117: one selected AC payload on existing acquisition edges. The
    // existing read_address/read_segment/read_band/active_epoch tuple is its
    // physical owner; no queue, public cycle or new cancellation boundary.
    logic [31:0] ac_fetch_address, ac_selected_word;
    logic [18:0] ac_selected_position;
    logic ac_selected_invalid;
    assign ac_fetch_address=starts[read_band]+cursors[read_band]*4;
    // Private payload may capture on a cancelled acquisition edge; state and
    // original read_tag_match prevent consumption, and the next owner replaces
    // it before use. Do not put the late validation/abort cone onto these CEs.
    always_ff @(posedge clk)begin
        if(state==AC_FETCH)begin
            if(prefetch_complete && prefetch_segment==read_band)begin
                // Original prefetch writes this bank on the SAME edge. Forward
                // the response instead of selecting the bank's old contents.
                ac_selected_word<=32'(mem_rsp_data>>(8*ac_fetch_address[3:0]));
                ac_selected_position<=sparse_position(19'(mem_rsp_data>>(8*ac_fetch_address[3:0]+13)));
            end else begin
                ac_selected_word<=32'(cache_data[read_band]>>(8*ac_fetch_address[3:0]));
                ac_selected_position<=cache_positions[read_band][ac_fetch_address[3:0]];
            end
        end else if(state==READ_WAIT && return_state==AC_EXTRACT && mem_rsp_valid)begin
            // A matching successful response is the only route to consumption.
            // Invalid/error responses may overwrite unowned private payload;
            // the original main priority still revokes/drains exactly as before.
            ac_selected_word<=32'(mem_rsp_data>>(8*read_address[3:0]));
            ac_selected_position<=sparse_position(19'(mem_rsp_data>>(8*read_address[3:0]+13)));
        end
    end
    assign ac_selected_invalid=17'(ac_selected_word[31:19])>=blocks ||
        !rank_matches(read_band,ac_selected_position[5:0]) ||
        $signed(ac_selected_word[12:0])==0 || $signed(ac_selected_word[12:0]) < -2048 ||
        $signed(ac_selected_word[12:0]) > 2048 ||
        (cursors[read_band]!=0 && {13'd0,ac_selected_position}<={13'd0,head_positions[read_band]});
`ifndef SYNTHESIS
    // Complete acquisition certificate. These duplicate owner fields are
    // verification-only: hardware already holds them in its existing read
    // transaction registers and advances only at the original consume edge.
    logic ac_cert_mature=0;
    logic [31:0] ac_cert_address,ac_cert_epoch,ac_cert_cursor;
    logic [1:0] ac_cert_segment,ac_cert_band;
    logic [18:0] ac_cert_head_position;
    logic [16:0] ac_cert_blocks;
    always_ff @(posedge clk)begin
        if(state==AC_FETCH || (state==READ_WAIT && return_state==AC_EXTRACT && mem_rsp_valid))begin
            ac_cert_mature<=1;
            ac_cert_address<=state==AC_FETCH ? ac_fetch_address : read_address;
            ac_cert_segment<=state==AC_FETCH ? read_band : read_segment;
            ac_cert_epoch<=active_epoch;ac_cert_band<=read_band;
            ac_cert_cursor<=cursors[read_band];
            ac_cert_head_position<=head_positions[read_band];ac_cert_blocks<=blocks;
        end
        // Mirror original main outer eligibility, including matching response
        // errors without prefetch/write ownership. No !response_failure shortcut.
        if(tile_case_eligible && state==AC_EXTRACT && read_tag_match)begin
            assert(ac_cert_mature && ac_cert_address==read_address &&
                ac_cert_segment==read_segment && ac_cert_epoch==active_epoch && ac_cert_band==read_band &&
                ac_cert_cursor==cursors[read_band] && ac_cert_head_position==head_positions[read_band] &&
                ac_cert_blocks==blocks)else $fatal(1,"V117 selected AC payload mixed acquisition owner");
            assert(ac_selected_word==read_word && ac_selected_position==read_position[18:0])
                else $fatal(1,"V117 selected AC payload differs from original cache selection");
            assert(ac_selected_invalid==ac_bank_invalid[read_segment])
                else $fatal(1,"V117 selected AC validation differs from original bank predicate");
        end
    end
`endif

    // V118: spatial per-band decisions mature ahead of AC_CHECK. Only the
    // compact owned predicates see read_band selection; no selected 32-bit
    // cursor/count carry chain feeds the broad tile publication controls.
    // Default refresh is safe outside AC_CHECK. The two same-edge head
    // transitions forward their complete poststate so consecutive checks keep
    // the original schedule, including consuming a head then fetching its next.
    logic [3:1] ac_lane_fetch, ac_lane_apply;
    logic ac_check_fetch, ac_check_apply;
    assign ac_check_fetch=ac_lane_fetch[read_band];
    assign ac_check_apply=ac_lane_apply[read_band];
    for(genvar check_band=1;check_band<=3;check_band=check_band+1)begin: local_head_decision
        wire [12:0] target_block=tile_mode ? prepare_block[12:0] : output_block[12:0];
        always_ff @(posedge clk)begin
            ac_lane_fetch[check_band]<=!head_valid[check_band] && cursors[check_band]<counts[check_band];
            ac_lane_apply[check_band]<=head_valid[check_band] && heads[check_band][31:19]==target_block;
            if(tile_case_eligible && state==AC_CHECK && read_band==2'(check_band) && ac_check_apply)begin
                ac_lane_fetch[check_band]<=cursors[check_band]<counts[check_band];
                ac_lane_apply[check_band]<=0;
            end
            if(tile_case_eligible && state==AC_EXTRACT && read_band==2'(check_band) &&
                read_tag_match && !ac_selected_invalid)begin
                ac_lane_fetch[check_band]<=0;
                ac_lane_apply[check_band]<=ac_selected_word[31:19]==target_block;
            end
        end
    end
`ifndef SYNTHESIS
    // These certificates compare with the full original expressions, without
    // clock skipping. No decision may become visible under a different owner.
    always_ff @(posedge clk)if(tile_case_eligible && state==AC_CHECK)begin
        assert(read_band>=1)else $fatal(1,"V118 AC check lacks a band owner");
        assert(ac_check_fetch==(!head_valid[read_band] && cursors[read_band]<counts[read_band]))
            else $fatal(1,"V118 prepared fetch decision differs from current whole owner");
        assert(ac_check_apply==(head_valid[read_band] && heads[read_band][31:19]==
            (tile_mode ? prepare_block[12:0] : output_block[12:0])))
            else $fatal(1,"V118 prepared apply decision differs from current whole owner");
    end
`endif

    // Cursor payload is unowned in IDLE/DRAIN/FINISHED/FAILED. Every new
    // owner enters through an IDLE edge, restoring all cursors before use.
    // A cache miss must hold: the matching read returns to this same ordinal.
    // Malformed/cancelled hit increments retire with the owner and cannot
    // change any later live use. Public/controller/head updates stay guarded.
    for(genvar cursor_bank=1;cursor_bank<=3;cursor_bank=cursor_bank+1)begin: cursor_payload
        always_ff @(posedge clk)begin
            if(state==IDLE)cursors[cursor_bank]<=0;
            else if(state==AC_EXTRACT && read_band==2'(cursor_bank) &&
                cache_valid[read_segment] &&
                cache_address[read_segment]==18'(read_address & 32'hfffffff0))
                cursors[cursor_bank]<=cursors[cursor_bank]+1;
        end
    end


    // IV115.S1: one bounded accepted descriptor, no physical request before commit.
    logic [16:0] queued_blocks;
    logic queued_raw;
    logic queued_serial_clear;
    logic queued_overlap;
    logic queued_prefetch;
    logic queued_tile_overlap;
    logic [31:0] queued_count1;
    logic [31:0] queued_count2;
    logic [31:0] queued_count3;
    logic [31:0] queued_epoch;
    logic [31:0] queued_prefix1;
    logic [31:0] queued_prefix12;
    logic [31:0] queued_prefix123;
    logic [31:0] queued_threshold1;
    logic [31:0] queued_threshold2;
    logic [31:0] queued_threshold3;
    logic [31:0] queued_capacity_upper;
    logic [31:0] queued_capacity_lower;
    logic queued_capacity_wrap;
    logic prepare_mature=0;
    logic prepared_bad_epoch, prepared_bad_geometry;
    logic [31:0] prepared_start1, prepared_start2, prepared_start3, prepared_used;
    logic preparing_begin;
    assign preparing_begin=state==BEGIN_PLAN || state==BEGIN_COMMIT;
    // Payload is private until BEGIN_COMMIT; do not reset wide payload registers.
    always_ff @(posedge clk)begin
        if(state==IDLE && begin_valid && !cancel && !response_failure)begin
            queued_blocks<=begin_blocks;
            queued_raw<=begin_raw;
            queued_serial_clear<=begin_serial_clear;
            queued_overlap<=begin_overlap;
            queued_prefetch<=begin_prefetch;
            queued_tile_overlap<=begin_tile_overlap;
            queued_count1<=begin_count1;
            queued_count2<=begin_count2;
            queued_count3<=begin_count3;
            queued_epoch<=begin_epoch;
            queued_prefix1<=begin_prefix1;
            queued_prefix12<=begin_prefix12;
            queued_prefix123<=begin_prefix123;
            queued_threshold1<=begin_threshold1;
            queued_threshold2<=begin_threshold2;
            queued_threshold3<=begin_threshold3;
            queued_capacity_upper<=begin_capacity_upper;
            queued_capacity_lower<=begin_capacity_lower;
            queued_capacity_wrap<=begin_capacity_wrap;
        end
        // First preparation edge computes the base and validation. Second edge
        // computes the dependent addresses; each wide sum has its own register.
        prepared_start1<=32+aligned(32'(queued_blocks)*2);
        prepared_start2<=prepared_start1+queued_prefix1;
        prepared_start3<=prepared_start1+queued_prefix12;
        prepared_used<=queued_raw ? 32+32'(queued_blocks)*128 : prepared_start1+queued_prefix123;
        prepared_bad_epoch<=epoch_seen && queued_epoch<=last_epoch;
        prepared_bad_geometry<=queued_blocks==0 || queued_blocks>8192 ||
            32'(queued_blocks)<queued_threshold1 || 32'(queued_blocks)<queued_threshold2 ||
            32'(queued_blocks)<queued_threshold3 ||
            (queued_raw && (queued_count1!=0 || queued_count2!=0 || queued_count3!=0)) ||
            (queued_raw ? queued_blocks>17'd2047 :
                (32'(queued_blocks)>queued_capacity_upper ||
                 (queued_capacity_wrap && 32'(queued_blocks)<=queued_capacity_lower)));
    end


    // Read-address/tag comparison matures on the existing fetch edge. No new
    // read-service edge: matching READ_WAIT response forwards the hit result.
    logic read_tag_match;
    logic [17:0] current_dc_line, selected_raw_line;
    always_ff @(posedge clk)begin
        current_dc_line<=18'((32+(tile_mode ? 32'(prepare_block) : 32'(output_block))*2)&32'hfffffff0);
        if(state==DESC1)selected_raw_line<=18'd32;
        else if(state==RAW_EXTRACT && dense_ready && !cancel && !response_failure)
            selected_raw_line<=prepared_raw_line;
        if(!cancel && !response_failure)begin
            if(state==DC_FETCH)read_tag_match<=cache_valid[0] && cache_address[0]==current_dc_line;
            if(state==RAW_FETCH)read_tag_match<=cache_valid[0] && cache_address[0]==selected_raw_line;
            if(state==AC_FETCH)read_tag_match<=cache_valid[read_band] && cache_address[read_band]==prepared_ac_line[read_band];
            if(state==READ_WAIT && outstanding && mem_rsp_valid &&
                (return_state==DC_EXTRACT || return_state==AC_EXTRACT))read_tag_match<=1;
        end
    end

    // Mirror the ORIGINAL outer main-branch priority, not !response_failure.
    // A matching response error without a prefetch/write owner can still reach
    // these case writes in the frozen source; preserve its raw payload effects.
    always_comb begin
        tile_case_eligible=!cancel &&
            !(mem_rsp_valid && (!outstanding || mem_rsp_epoch!=request_epoch)) &&
            state!=DRAIN &&
            !(prefetch_offer && outstanding && mem_rsp_valid && mem_rsp_error) &&
            !(overlap_mode && write_slot_valid && outstanding && mem_rsp_valid && mem_rsp_error);
        tile_event_valid=0;tile_event_bank=prep_bank;
        tile_event_index=0;tile_event_value=0;
        if(tile_case_eligible)begin
            case(state)
                CLEAR_TILE:if(serial_clear)begin
                    tile_event_valid=1;tile_event_index=clear_index;
                end
                DC_EXTRACT:if(read_tag_match && !(read_half < -2048 || read_half > 2048) && !raw_mode)begin
                    tile_event_valid=1;
                    tile_event_value=16'(cache_data[0]>>(8*read_address[3:0]));
                end
                AC_CHECK:if(ac_check_apply)begin
                    tile_event_valid=1;tile_event_index=heads[read_band][18:13];
                    tile_event_value={{3{heads[read_band][12]}},heads[read_band][12:0]};
                end
                default:begin end
            endcase
        end
    end
    // Retire the old tuple even on reset/cancel: its value was already visible
    // before the edge, and the original raw tile did not erase it on a kill.
    always_ff @(posedge clk)begin
        tile_pending_valid<=tile_event_valid;
        if(tile_event_valid)begin
            tile_pending_bank<=tile_event_bank;
            tile_pending_index<=tile_event_index;
            tile_pending_value<=tile_event_value;
        end
    end
    for(genvar payload_bank=0;payload_bank<2;payload_bank=payload_bank+1)begin: local_tile_bank
        for(genvar payload_word=0;payload_word<64;payload_word=payload_word+1)begin: local_tile_word
            wire pending_match=tile_pending_valid && tile_pending_bank==1'(payload_bank) &&
                tile_pending_index==6'(payload_word);
            always_ff @(posedge clk)if(pending_match)
                tile_payload[payload_bank][payload_word]<=tile_pending_value;
            assign tile[payload_bank][payload_word]=pending_match ? tile_pending_value :
                tile_payload[payload_bank][payload_word];
        end
    end
`ifndef SYNTHESIS
    // No disable on reset/abort: retirement of an already-visible write is
    // required across those edges, including immediate replacement on retry.
    assert property(@(posedge clk) tile_pending_valid |=>
        tile_payload[$past(tile_pending_bank)][$past(tile_pending_index)]==$past(tile_pending_value))
        else $fatal(1,"visible tile write was not physically retired");
    assert property(@(posedge clk) tile_event_valid |=> tile_pending_valid &&
        tile_pending_bank==$past(tile_event_bank) && tile_pending_index==$past(tile_event_index) &&
        tile_pending_value==$past(tile_event_value))
        else $fatal(1,"tile write tuple lost or mixed owner/value");
    assert property(@(posedge clk) !tile_event_valid |=> !tile_pending_valid)
        else $fatal(1,"tile slot created a write without an event");
`endif

    always_ff @(posedge clk) begin
        // A reset is cancellation, not permission to discard an accepted write.
        if(cancel) begin
            prepare_mature<=0;
            sealed<=0; done<=0; error<=0; cache_valid<=0; head_valid<=0;
            assembly_bytes<=0; write_slot_valid<=0; prefetch_offer<=0; prefetched_valid<=0;
            bank_ready<=0; tile_preparing<=0; tile_valid[0]<=0; tile_valid[1]<=0; tile_overlap_mode<=0;
            if(outstanding && (!mem_rsp_valid || mem_rsp_epoch!=request_epoch)) begin
                begin state<=DRAIN; busy_owned<=1'b1; end
                if(mem_rsp_valid) error<=6;
            end else begin begin state<=IDLE; busy_owned<=1'b0; end outstanding<=0; end
        end else if(mem_rsp_valid && (!outstanding || mem_rsp_epoch!=request_epoch)) begin
            // A mismatched response cannot retire the real outstanding request.
            error<=6; sealed<=0; done<=0; write_slot_valid<=0; assembly_bytes<=0; prefetch_offer<=0; cache_valid<=0; prefetched_valid<=0; bank_ready<=0; tile_preparing<=0;
            begin state<=outstanding ? DRAIN : FAILED; busy_owned<=(outstanding); end
        end else if(state==DRAIN) begin
            if(mem_rsp_valid && outstanding) begin outstanding<=0; begin state<=IDLE; busy_owned<=1'b0; end end
            else if(!outstanding) begin state<=IDLE; busy_owned<=1'b0; end
        end else if(prefetch_offer && outstanding && mem_rsp_valid && mem_rsp_error) begin
            outstanding<=0; prefetch_offer<=0; cache_valid<=0; prefetched_valid<=0;
            error<=5; sealed<=0; done<=0; begin state<=FAILED; busy_owned<=1'b0; end
        end else if(overlap_mode && write_slot_valid && outstanding && mem_rsp_valid && mem_rsp_error) begin
            outstanding<=0; write_slot_valid<=0; assembly_bytes<=0;
            error<=5; sealed<=0; done<=0; begin state<=FAILED; busy_owned<=1'b0; end
        end else begin
            // Consumer owns a ready bank until its sixty-fourth acceptance.
            // Producer writes only the other, unready bank; same-edge publish
            // and release update different per-bank ready bits.
            if(tile_mode && dense_valid && dense_ready) begin
                if(tile_emit_index==63) begin
                    bank_ready[emit_bank]<=0; tile_emit_index<=0; emit_bank<=!emit_bank;
                end else tile_emit_index<=tile_emit_index+1;
            end
            // Slot ownership ends only at physical matching ACK. The controller
            // may replace it with the assembled line on this same edge.
            if(overlap_mode && write_slot_valid) begin
                if(!outstanding && mem_req_valid && mem_req_ready) outstanding<=1;
                if(outstanding && mem_rsp_valid) begin outstanding<=0; write_slot_valid<=0; end
            end
            if(debug_prefetch_use) begin
                if(state==DC_EXTRACT) prefetched_valid[0]<=0;
                else prefetched_valid[read_segment]<=0;
            end
            if(prefetch_launch) begin
                transfer_address<=candidate_address; request_epoch<=active_epoch;
                prefetch_segment<=candidate_segment; prefetch_offer<=1;
            end
            if(prefetch_offer) begin
                if(!outstanding && mem_req_valid && mem_req_ready) outstanding<=1;
                if(prefetch_complete) begin
                    outstanding<=0; prefetch_offer<=0;
                    cache_data[prefetch_segment]<=mem_rsp_data;
                    if(prefetch_segment==2'd0)begin
                        cache_positions[0][0]<=sparse_position(19'(mem_rsp_data>>13));
                        cache_positions[0][1]<=sparse_position(19'(mem_rsp_data>>21));
                        cache_positions[0][2]<=sparse_position(19'(mem_rsp_data>>29));
                        cache_positions[0][3]<=sparse_position(19'(mem_rsp_data>>37));
                        cache_positions[0][4]<=sparse_position(19'(mem_rsp_data>>45));
                        cache_positions[0][5]<=sparse_position(19'(mem_rsp_data>>53));
                        cache_positions[0][6]<=sparse_position(19'(mem_rsp_data>>61));
                        cache_positions[0][7]<=sparse_position(19'(mem_rsp_data>>69));
                        cache_positions[0][8]<=sparse_position(19'(mem_rsp_data>>77));
                        cache_positions[0][9]<=sparse_position(19'(mem_rsp_data>>85));
                        cache_positions[0][10]<=sparse_position(19'(mem_rsp_data>>93));
                        cache_positions[0][11]<=sparse_position(19'(mem_rsp_data>>101));
                        cache_positions[0][12]<=sparse_position(19'(mem_rsp_data>>109));
                        cache_positions[0][13]<=sparse_position(19'(mem_rsp_data>>117));
                        cache_positions[0][14]<=sparse_position(19'(mem_rsp_data>>125));
                        cache_positions[0][15]<=sparse_position(19'(mem_rsp_data>>133));
                    end
                    if(prefetch_segment==2'd1)begin
                        cache_positions[1][0]<=sparse_position(19'(mem_rsp_data>>13));
                        cache_positions[1][1]<=sparse_position(19'(mem_rsp_data>>21));
                        cache_positions[1][2]<=sparse_position(19'(mem_rsp_data>>29));
                        cache_positions[1][3]<=sparse_position(19'(mem_rsp_data>>37));
                        cache_positions[1][4]<=sparse_position(19'(mem_rsp_data>>45));
                        cache_positions[1][5]<=sparse_position(19'(mem_rsp_data>>53));
                        cache_positions[1][6]<=sparse_position(19'(mem_rsp_data>>61));
                        cache_positions[1][7]<=sparse_position(19'(mem_rsp_data>>69));
                        cache_positions[1][8]<=sparse_position(19'(mem_rsp_data>>77));
                        cache_positions[1][9]<=sparse_position(19'(mem_rsp_data>>85));
                        cache_positions[1][10]<=sparse_position(19'(mem_rsp_data>>93));
                        cache_positions[1][11]<=sparse_position(19'(mem_rsp_data>>101));
                        cache_positions[1][12]<=sparse_position(19'(mem_rsp_data>>109));
                        cache_positions[1][13]<=sparse_position(19'(mem_rsp_data>>117));
                        cache_positions[1][14]<=sparse_position(19'(mem_rsp_data>>125));
                        cache_positions[1][15]<=sparse_position(19'(mem_rsp_data>>133));
                    end
                    if(prefetch_segment==2'd2)begin
                        cache_positions[2][0]<=sparse_position(19'(mem_rsp_data>>13));
                        cache_positions[2][1]<=sparse_position(19'(mem_rsp_data>>21));
                        cache_positions[2][2]<=sparse_position(19'(mem_rsp_data>>29));
                        cache_positions[2][3]<=sparse_position(19'(mem_rsp_data>>37));
                        cache_positions[2][4]<=sparse_position(19'(mem_rsp_data>>45));
                        cache_positions[2][5]<=sparse_position(19'(mem_rsp_data>>53));
                        cache_positions[2][6]<=sparse_position(19'(mem_rsp_data>>61));
                        cache_positions[2][7]<=sparse_position(19'(mem_rsp_data>>69));
                        cache_positions[2][8]<=sparse_position(19'(mem_rsp_data>>77));
                        cache_positions[2][9]<=sparse_position(19'(mem_rsp_data>>85));
                        cache_positions[2][10]<=sparse_position(19'(mem_rsp_data>>93));
                        cache_positions[2][11]<=sparse_position(19'(mem_rsp_data>>101));
                        cache_positions[2][12]<=sparse_position(19'(mem_rsp_data>>109));
                        cache_positions[2][13]<=sparse_position(19'(mem_rsp_data>>117));
                        cache_positions[2][14]<=sparse_position(19'(mem_rsp_data>>125));
                        cache_positions[2][15]<=sparse_position(19'(mem_rsp_data>>133));
                    end
                    if(prefetch_segment==2'd3)begin
                        cache_positions[3][0]<=sparse_position(19'(mem_rsp_data>>13));
                        cache_positions[3][1]<=sparse_position(19'(mem_rsp_data>>21));
                        cache_positions[3][2]<=sparse_position(19'(mem_rsp_data>>29));
                        cache_positions[3][3]<=sparse_position(19'(mem_rsp_data>>37));
                        cache_positions[3][4]<=sparse_position(19'(mem_rsp_data>>45));
                        cache_positions[3][5]<=sparse_position(19'(mem_rsp_data>>53));
                        cache_positions[3][6]<=sparse_position(19'(mem_rsp_data>>61));
                        cache_positions[3][7]<=sparse_position(19'(mem_rsp_data>>69));
                        cache_positions[3][8]<=sparse_position(19'(mem_rsp_data>>77));
                        cache_positions[3][9]<=sparse_position(19'(mem_rsp_data>>85));
                        cache_positions[3][10]<=sparse_position(19'(mem_rsp_data>>93));
                        cache_positions[3][11]<=sparse_position(19'(mem_rsp_data>>101));
                        cache_positions[3][12]<=sparse_position(19'(mem_rsp_data>>109));
                        cache_positions[3][13]<=sparse_position(19'(mem_rsp_data>>117));
                        cache_positions[3][14]<=sparse_position(19'(mem_rsp_data>>125));
                        cache_positions[3][15]<=sparse_position(19'(mem_rsp_data>>133));
                    end
                    cache_address[prefetch_segment]<=transfer_address;
                    cache_valid[prefetch_segment]<=1; prefetched_valid[prefetch_segment]<=1;
                end
            end
            case(state)
                IDLE: if(begin_valid)begin
                    sealed<=0; done<=0; error<=0; prepare_mature<=0; active_epoch<=begin_epoch;
                    begin state<=BEGIN_PLAN; busy_owned<=1'b1; end
                end
                BEGIN_PLAN: begin
                    prepare_mature<=1;
                    if(prepare_mature)begin state<=BEGIN_COMMIT; busy_owned<=1'b1; end
                end
                BEGIN_COMMIT: begin
                    if(prepared_bad_epoch) begin error<=2; begin state<=FAILED; busy_owned<=1'b0; end end
                    else if(prepared_bad_geometry) begin error<=1; begin state<=FAILED; busy_owned<=1'b0; end end
                    else begin
                        epoch_seen<=1; last_epoch<=queued_epoch; active_epoch<=queued_epoch;
                        blocks<=queued_blocks; raw_mode<=queued_raw; tile_overlap_mode<=queued_tile_overlap; bank_ready<=0; tile_preparing<=0; prep_bank<=0; emit_bank<=0; prepare_block<=0; tile_emit_index<=0; tile_valid[0]<=0; tile_valid[1]<=0; serial_clear<=queued_serial_clear; overlap_mode<=queued_overlap; prefetch_mode<=queued_prefetch; prefetch_offer<=0; prefetched_valid<=0; write_slot_valid<=0; used_bytes<=19'(prepared_used);
                        counts[0]<=queued_raw ? 32'(queued_blocks)*64 : 32'(queued_blocks);
                        counts[1]<=queued_count1; counts[2]<=queued_count2; counts[3]<=queued_count3;
                        starts[0]<=32; starts[1]<=prepared_start1; starts[2]<=prepared_start2; starts[3]<=prepared_start3;
                        phase<=0; written<=0; previous_valid<=0; assembler<=0; assembly_bytes<=0;
                        write_address<=32; cache_valid<=0; head_valid<=0;
                        // Private cursor payload clears on every original IDLE edge below.
                        begin state<=INGEST; busy_owned<=1'b1; end
                    end
                end
                INGEST: begin
                    if(coef_valid) begin
                        if(input_bad) begin
                            error<=coef_epoch!=active_epoch ? 2 : 3;
                            if(overlap_mode) begin
                                write_slot_valid<=0; assembly_bytes<=0;
                                begin state<=((outstanding && !mem_rsp_valid) ||
                                    (!outstanding && mem_req_valid && mem_req_ready)) ? DRAIN : FAILED; busy_owned<=(((outstanding && !mem_rsp_valid) ||
                                    (!outstanding && mem_req_valid && mem_req_ready))); end
                            end else begin state<=FAILED; busy_owned<=1'b0; end
                        end
                        else begin
                            record_view_bank<=!record_view_bank; record_view_seen<=1;
                            begin state<=APPEND; busy_owned<=1'b1; end
                        end
                    end else if(band_end_valid) begin
                        if(band_end_epoch!=active_epoch || band_end_band!=phase[1:0] || written!=counts[phase[1:0]]) begin
                            error<=band_end_epoch!=active_epoch ? 2 : 4;
                            if(overlap_mode) begin
                                write_slot_valid<=0; assembly_bytes<=0;
                                begin state<=((outstanding && !mem_rsp_valid) ||
                                    (!outstanding && mem_req_valid && mem_req_ready)) ? DRAIN : FAILED; busy_owned<=(((outstanding && !mem_rsp_valid) ||
                                    (!outstanding && mem_req_valid && mem_req_ready))); end
                            end else begin state<=FAILED; busy_owned<=1'b0; end
                        end else if(assembly_bytes!=0) begin
                            if(overlap_mode) begin
                                return_state<=NEXT_BAND;
                                if(slot_available) begin
                                    transfer_data<=assembler; transfer_address<=18'(write_address);
                                    request_epoch<=active_epoch; write_slot_valid<=1;
                                    write_address<=write_address+16; begin state<=NEXT_BAND; busy_owned<=1'b1; end
                                end else begin state<=FLUSH_LINE; busy_owned<=1'b1; end
                            end else begin
                                transfer_data<=assembler; transfer_address<=18'(write_address);
                                request_epoch<=active_epoch; return_state<=NEXT_BAND; begin state<=WRITE_REQ; busy_owned<=1'b1; end
                            end
                        end else begin state<=NEXT_BAND; busy_owned<=1'b1; end
                    end
                end
                APPEND: begin
                    // Same original edge and outer priority as previous_position.
                    for(integer rank_index=0;rank_index<64;rank_index=rank_index+1)
                        rank_threshold_mask[rank_index]<=
                            zigzag(6'(rank_index))<=pending_position[5:0];
                    if(pending_bytes==2) assembler[8*assembly_bytes+:16]<=pending_record[15:0];
                    else assembler[8*assembly_bytes+:32]<=pending_record;
                    written<=written+1; previous_position<=pending_position; previous_valid<=1;
                    if(assembly_bytes+5'(pending_bytes)==16) begin
                        return_state<=INGEST;
                        if(overlap_mode) begin
                            if(slot_available) begin
                                transfer_data<=assembler | (128'(pending_record) << (8*assembly_bytes));
                                transfer_address<=18'(write_address); request_epoch<=active_epoch;
                                write_slot_valid<=1; write_address<=write_address+16;
                                begin state<=INGEST; busy_owned<=1'b1; end assembler<=0; assembly_bytes<=0;
                            end else begin assembly_bytes<=16; begin state<=FLUSH_LINE; busy_owned<=1'b1; end end
                        end else begin
                            transfer_data<=assembler | (128'(pending_record) << (8*assembly_bytes));
                            transfer_address<=18'(write_address); request_epoch<=active_epoch;
                            begin state<=WRITE_REQ; busy_owned<=1'b1; end assembler<=0; assembly_bytes<=0;
                        end
                    end else begin assembly_bytes<=assembly_bytes+5'(pending_bytes); begin state<=INGEST; busy_owned<=1'b1; end end
                end
                FLUSH_LINE: if(slot_available) begin
                    transfer_data<=assembler; transfer_address<=18'(write_address);
                    request_epoch<=active_epoch; write_slot_valid<=1;
                    write_address<=write_address+16; assembler<=0; assembly_bytes<=0;
                    begin state<=return_state; busy_owned<=(return_state!=IDLE && return_state!=FINISHED && return_state!=FAILED); end
                end
                NEXT_BAND: begin
                    assembler<=0; assembly_bytes<=0; written<=0; previous_valid<=0;
                    if(raw_mode || phase==3) begin phase<=4; begin state<=WAIT_SEAL; busy_owned<=1'b1; end end
                    else begin
                        phase<=phase+1; write_address<=starts[phase[1:0]+2'd1]; begin state<=INGEST; busy_owned<=1'b1; end
                    end
                end
                WAIT_SEAL: if(seal_valid && seal_ready) begin
                    if(seal_epoch!=active_epoch) begin error<=2; begin state<=FAILED; busy_owned<=1'b0; end end
                    else begin state<=HEADER0; busy_owned<=1'b1; end
                end
                HEADER0: begin
                    transfer_data<={counts[1],31'd0,raw_mode,15'd0,blocks,32'h43393150};
                    transfer_address<=0; request_epoch<=active_epoch; return_state<=HEADER1; begin state<=WRITE_REQ; busy_owned<=1'b1; end
                end
                HEADER1: begin
                    transfer_data<={32'd0,13'd0,used_bytes,counts[3],counts[2]};
                    transfer_address<=16; request_epoch<=active_epoch; return_state<=HEADER_DONE; begin state<=WRITE_REQ; busy_owned<=1'b1; end
                end
                HEADER_DONE: begin
                    sealed<=1; transfer_address<=0; return_state<=DESC0; begin state<=READ_REQ; busy_owned<=1'b1; end
                end
                WRITE_REQ: if(mem_req_ready) begin outstanding<=1; begin state<=WRITE_WAIT; busy_owned<=1'b1; end end
                WRITE_WAIT: if(mem_rsp_valid) begin
                    outstanding<=0;
                    if(mem_rsp_error) begin error<=5; sealed<=0; begin state<=FAILED; busy_owned<=1'b0; end bank_ready<=0; tile_preparing<=0; end
                    else begin write_address<=write_address+16; begin state<=return_state; busy_owned<=(return_state!=IDLE && return_state!=FINISHED && return_state!=FAILED); end end
                end
                READ_REQ: if(mem_req_ready) begin outstanding<=1; begin state<=READ_WAIT; busy_owned<=1'b1; end end
                READ_WAIT: if(mem_rsp_valid) begin
                    outstanding<=0;
                    if(mem_rsp_error) begin error<=5; sealed<=0; begin state<=FAILED; busy_owned<=1'b0; end bank_ready<=0; tile_preparing<=0; end
                    else begin
                        transfer_data<=mem_rsp_data;
                        if(return_state!=DESC0 && return_state!=DESC1) begin
                            cache_data[read_segment]<=mem_rsp_data;
                            if(read_segment==2'd0)begin
                                cache_positions[0][0]<=sparse_position(19'(mem_rsp_data>>13));
                                cache_positions[0][1]<=sparse_position(19'(mem_rsp_data>>21));
                                cache_positions[0][2]<=sparse_position(19'(mem_rsp_data>>29));
                                cache_positions[0][3]<=sparse_position(19'(mem_rsp_data>>37));
                                cache_positions[0][4]<=sparse_position(19'(mem_rsp_data>>45));
                                cache_positions[0][5]<=sparse_position(19'(mem_rsp_data>>53));
                                cache_positions[0][6]<=sparse_position(19'(mem_rsp_data>>61));
                                cache_positions[0][7]<=sparse_position(19'(mem_rsp_data>>69));
                                cache_positions[0][8]<=sparse_position(19'(mem_rsp_data>>77));
                                cache_positions[0][9]<=sparse_position(19'(mem_rsp_data>>85));
                                cache_positions[0][10]<=sparse_position(19'(mem_rsp_data>>93));
                                cache_positions[0][11]<=sparse_position(19'(mem_rsp_data>>101));
                                cache_positions[0][12]<=sparse_position(19'(mem_rsp_data>>109));
                                cache_positions[0][13]<=sparse_position(19'(mem_rsp_data>>117));
                                cache_positions[0][14]<=sparse_position(19'(mem_rsp_data>>125));
                                cache_positions[0][15]<=sparse_position(19'(mem_rsp_data>>133));
                            end
                            if(read_segment==2'd1)begin
                                cache_positions[1][0]<=sparse_position(19'(mem_rsp_data>>13));
                                cache_positions[1][1]<=sparse_position(19'(mem_rsp_data>>21));
                                cache_positions[1][2]<=sparse_position(19'(mem_rsp_data>>29));
                                cache_positions[1][3]<=sparse_position(19'(mem_rsp_data>>37));
                                cache_positions[1][4]<=sparse_position(19'(mem_rsp_data>>45));
                                cache_positions[1][5]<=sparse_position(19'(mem_rsp_data>>53));
                                cache_positions[1][6]<=sparse_position(19'(mem_rsp_data>>61));
                                cache_positions[1][7]<=sparse_position(19'(mem_rsp_data>>69));
                                cache_positions[1][8]<=sparse_position(19'(mem_rsp_data>>77));
                                cache_positions[1][9]<=sparse_position(19'(mem_rsp_data>>85));
                                cache_positions[1][10]<=sparse_position(19'(mem_rsp_data>>93));
                                cache_positions[1][11]<=sparse_position(19'(mem_rsp_data>>101));
                                cache_positions[1][12]<=sparse_position(19'(mem_rsp_data>>109));
                                cache_positions[1][13]<=sparse_position(19'(mem_rsp_data>>117));
                                cache_positions[1][14]<=sparse_position(19'(mem_rsp_data>>125));
                                cache_positions[1][15]<=sparse_position(19'(mem_rsp_data>>133));
                            end
                            if(read_segment==2'd2)begin
                                cache_positions[2][0]<=sparse_position(19'(mem_rsp_data>>13));
                                cache_positions[2][1]<=sparse_position(19'(mem_rsp_data>>21));
                                cache_positions[2][2]<=sparse_position(19'(mem_rsp_data>>29));
                                cache_positions[2][3]<=sparse_position(19'(mem_rsp_data>>37));
                                cache_positions[2][4]<=sparse_position(19'(mem_rsp_data>>45));
                                cache_positions[2][5]<=sparse_position(19'(mem_rsp_data>>53));
                                cache_positions[2][6]<=sparse_position(19'(mem_rsp_data>>61));
                                cache_positions[2][7]<=sparse_position(19'(mem_rsp_data>>69));
                                cache_positions[2][8]<=sparse_position(19'(mem_rsp_data>>77));
                                cache_positions[2][9]<=sparse_position(19'(mem_rsp_data>>85));
                                cache_positions[2][10]<=sparse_position(19'(mem_rsp_data>>93));
                                cache_positions[2][11]<=sparse_position(19'(mem_rsp_data>>101));
                                cache_positions[2][12]<=sparse_position(19'(mem_rsp_data>>109));
                                cache_positions[2][13]<=sparse_position(19'(mem_rsp_data>>117));
                                cache_positions[2][14]<=sparse_position(19'(mem_rsp_data>>125));
                                cache_positions[2][15]<=sparse_position(19'(mem_rsp_data>>133));
                            end
                            if(read_segment==2'd3)begin
                                cache_positions[3][0]<=sparse_position(19'(mem_rsp_data>>13));
                                cache_positions[3][1]<=sparse_position(19'(mem_rsp_data>>21));
                                cache_positions[3][2]<=sparse_position(19'(mem_rsp_data>>29));
                                cache_positions[3][3]<=sparse_position(19'(mem_rsp_data>>37));
                                cache_positions[3][4]<=sparse_position(19'(mem_rsp_data>>45));
                                cache_positions[3][5]<=sparse_position(19'(mem_rsp_data>>53));
                                cache_positions[3][6]<=sparse_position(19'(mem_rsp_data>>61));
                                cache_positions[3][7]<=sparse_position(19'(mem_rsp_data>>69));
                                cache_positions[3][8]<=sparse_position(19'(mem_rsp_data>>77));
                                cache_positions[3][9]<=sparse_position(19'(mem_rsp_data>>85));
                                cache_positions[3][10]<=sparse_position(19'(mem_rsp_data>>93));
                                cache_positions[3][11]<=sparse_position(19'(mem_rsp_data>>101));
                                cache_positions[3][12]<=sparse_position(19'(mem_rsp_data>>109));
                                cache_positions[3][13]<=sparse_position(19'(mem_rsp_data>>117));
                                cache_positions[3][14]<=sparse_position(19'(mem_rsp_data>>125));
                                cache_positions[3][15]<=sparse_position(19'(mem_rsp_data>>133));
                            end
                            cache_address[read_segment]<=transfer_address; cache_valid[read_segment]<=1; prefetched_valid[read_segment]<=0;
                        end
                        begin state<=return_state; busy_owned<=(return_state!=IDLE && return_state!=FINISHED && return_state!=FAILED); end
                    end
                end
                DESC0: begin
                    descriptor_low<=transfer_data; transfer_address<=16;
                    return_state<=DESC1; begin state<=READ_REQ; busy_owned<=1'b1; end
                end
                DESC1: begin
                    if(descriptor_low!={counts[1],31'd0,raw_mode,15'd0,blocks,32'h43393150} ||
                       transfer_data!={32'd0,13'd0,used_bytes,counts[3],counts[2]}) begin
                        error<=7; sealed<=0; begin state<=FAILED; busy_owned<=1'b0; end
                    end else begin
                        output_block<=0; output_index<=0; clear_index<=0;
                        if(tile_mode) begin
                            prep_bank<=0; emit_bank<=0; prepare_block<=0; tile_emit_index<=0;
                            bank_ready<=0; tile_preparing<=1; bank_block[0]<=0; bank_epoch[0]<=active_epoch;
                        end
                        begin state<=raw_mode ? RAW_FETCH : CLEAR_TILE; busy_owned<=1'b1; end
                    end
                end
                CLEAR_TILE: begin
                    tile_valid[prep_bank]<=0;
                    // Payload write is captured by the local forwarded tuple.
                    if(!serial_clear || clear_index==63) begin clear_index<=0; begin state<=DC_FETCH; busy_owned<=1'b1; end end
                    else clear_index<=clear_index+1;
                end
                DC_FETCH, RAW_FETCH: begin
                    read_address<=32+(raw_mode ? (32'(output_block)*64+32'(output_index))*2 : (tile_mode ? 32'(prepare_block) : 32'(output_block))*2);
                    read_segment<=0; begin state<=DC_EXTRACT; busy_owned<=1'b1; end
                end
                DC_EXTRACT: begin
                    if(!read_tag_match) begin
                        transfer_address<=18'(read_address & 32'hfffffff0); return_state<=DC_EXTRACT; begin state<=READ_REQ; busy_owned<=1'b1; end
                    end else if(read_half < -2048 || read_half > 2048) begin
                        error<=3; sealed<=0; begin state<=FAILED; busy_owned<=1'b0; end
                    end else if(raw_mode) begin
                        raw_value<=16'(cache_data[0]>>(8*read_address[3:0])); begin state<=RAW_EXTRACT; busy_owned<=1'b1; end
                    end else begin
                        tile_valid[prep_bank][0]<=1; read_band<=1; begin state<=AC_CHECK; busy_owned<=1'b1; end
                    end
                end
                AC_CHECK: begin
                    if(ac_check_fetch) begin state<=AC_FETCH; busy_owned<=1'b1; end
                    else if(ac_check_apply) begin
                        // Payload write is captured by the local forwarded tuple.
                        tile_valid[prep_bank][heads[read_band][18:13]]<=1; head_valid[read_band]<=0;
                    end else if(read_band==3) begin
                        if(tile_mode) begin
                            bank_ready[prep_bank]<=1; tile_preparing<=0;
                            begin state<=BANK_WAIT; busy_owned<=1'b1; end
                        end else begin output_index<=0; begin state<=EMIT; busy_owned<=1'b1; end end
                    end
                    else read_band<=read_band+1;
                end
                AC_FETCH: begin
                    read_segment<=read_band; read_address<=ac_fetch_address; begin state<=AC_EXTRACT; busy_owned<=1'b1; end
                end
                AC_EXTRACT: begin
                    if(!read_tag_match) begin
                        transfer_address<=18'(read_address & 32'hfffffff0); return_state<=AC_EXTRACT; begin state<=READ_REQ; busy_owned<=1'b1; end
                    end else begin
                        if(ac_selected_invalid) begin
                            error<=3; sealed<=0; begin state<=FAILED; busy_owned<=1'b0; end
                        end else begin
                            heads[read_band]<=ac_selected_word;
                            head_positions[read_band]<=ac_selected_position;
                            head_valid[read_band]<=1; begin state<=AC_CHECK; busy_owned<=1'b1; end
                        end
                    end
                end
                EMIT, RAW_EXTRACT: if(dense_ready) begin
                    if(output_index==63) begin
                        if(output_plan.last_block) begin done<=1; begin state<=FINISHED; busy_owned<=1'b0; end end
                        else begin
                            output_block<=output_plan.next_block; output_index<=0;
                            if(prefetch_mode && (prefetch_launch || (prefetch_offer && !prefetch_complete))) begin
                                return_state<=output_plan.next_state; begin state<=PREFETCH_DRAIN; busy_owned<=1'b1; end
                            end else begin state<=output_plan.next_state; busy_owned<=1'b1; end
                        end
                    end else begin
                        output_index<=output_index+1;
                        if(raw_mode) begin
                            if(prefetch_mode && (prefetch_launch || (prefetch_offer && !prefetch_complete))) begin
                                return_state<=RAW_FETCH; begin state<=PREFETCH_DRAIN; busy_owned<=1'b1; end
                            end else begin state<=RAW_FETCH; busy_owned<=1'b1; end
                        end
                    end
                end
                PREFETCH_DRAIN: if(prefetch_complete || (!prefetch_offer && !outstanding)) begin state<=return_state; busy_owned<=(return_state!=IDLE && return_state!=FINISHED && return_state!=FAILED); end
                BANK_WAIT: begin
                    if(17'(prepare_block)+1==blocks) begin state<=PREP_DONE; busy_owned<=1'b1; end
                    else if(!bank_ready[!prep_bank]) begin
                        prep_bank<=!prep_bank; prepare_block<=prepare_block+1;
                        bank_block[!prep_bank]<=prepare_block+1; bank_epoch[!prep_bank]<=active_epoch;
                        tile_preparing<=1; clear_index<=0; begin state<=CLEAR_TILE; busy_owned<=1'b1; end
                    end
                end
                PREP_DONE: ;
                FINISHED, FAILED: ;
                default: begin state<=FAILED; busy_owned<=1'b0; end
            endcase
            if(tile_mode && dense_valid && dense_ready && tile_emit_index==63 &&
                17'(bank_block[emit_bank])+1==blocks) begin
                done<=1; begin state<=FINISHED; busy_owned<=1'b0; end
            end
        end
    end
`ifndef SYNTHESIS
    function automatic logic [31:0] capacity_expected_upper(input logic [27:0] units);
        logic [27:0] a,u;
        begin a=units+28'd2;u=28'd16384-a;return {1'b0,u,3'd0};end
    endfunction
    function automatic logic [31:0] capacity_expected_lower(input logic [27:0] units);
        logic [27:0] a,l;
        begin a=units+28'd2;l=~a;return {1'b0,l,3'd0};end
    endfunction
    function automatic logic capacity_expected_wrap(input logic [27:0] units);
        logic [27:0] a;
        begin a=units+28'd2;return a>28'd16384;end
    endfunction
    always_ff @(posedge clk)if(begin_valid&&begin_ready)begin
        assert(begin_prefix123[3:0]==0)else $fatal(1,"scratch capacity prefix alignment");
        assert(begin_capacity_upper==capacity_expected_upper(begin_prefix123[31:4]))else $fatal(1,"scratch capacity upper ownership mismatch");
        assert(begin_capacity_lower==capacity_expected_lower(begin_prefix123[31:4]))else $fatal(1,"scratch capacity lower ownership mismatch");
        assert(begin_capacity_wrap==capacity_expected_wrap(begin_prefix123[31:4]))else $fatal(1,"scratch capacity wrap ownership mismatch");
        assert(capacity_bad==(plan_used>32'd262144))else $fatal(1,"scratch capacity predicate mismatch");
        assert(plan_start2==plan_start1+begin_prefix1 && plan_start3==plan_start1+begin_prefix12)
            else $fatal(1,"original live plan equations changed");
    end
    always_ff @(posedge clk)if(begin_valid&&begin_ready)begin
        assert(begin_threshold1==begin_count1/32'd5+32'(begin_count1%32'd5!=0))else $fatal(1,"scratch threshold1 ownership mismatch");
        assert(begin_threshold2==begin_count2/32'd15+32'(begin_count2%32'd15!=0))else $fatal(1,"scratch threshold2 ownership mismatch");
        assert(begin_threshold3==begin_count3/32'd43+32'(begin_count3%32'd43!=0))else $fatal(1,"scratch threshold3 ownership mismatch");
        assert((32'(begin_blocks)<begin_threshold3)==(begin_count3>begin_limit43))else $fatal(1,"scratch43 threshold predicate mismatch");
        assert(begin_prefix1==aligned(begin_count1*4))else $fatal(1,"scratch prefix1 ownership mismatch");
        assert(begin_prefix12==aligned(begin_count1*4)+aligned(begin_count2*4))else $fatal(1,"scratch prefix12 ownership mismatch");
        assert(begin_prefix123==aligned(begin_count1*4)+aligned(begin_count2*4)+aligned(begin_count3*4))else $fatal(1,"scratch prefix123 ownership mismatch");
    end
    // IV115.S1: validate every consumed staged descriptor against full-width
    // original algebra. Prepare edges own no data or physical memory transfer.
    always_ff @(posedge clk)if(preparing_begin && !cancel && !response_failure)begin
        assert(active_epoch==queued_epoch && busy && !begin_ready && !coef_ready && !band_end_ready && !seal_ready &&
            !dense_valid && !mem_req_valid && !outstanding && !sealed && !done && error==0)
            else $fatal(1,"scratch preparation leaked eligibility/debt");
        if(state==BEGIN_COMMIT)begin
            assert(prepared_start1==32+aligned(32'(queued_blocks)*2));
            assert(prepared_start2==prepared_start1+queued_prefix1);
            assert(prepared_start3==prepared_start1+queued_prefix12);
            assert(prepared_used==(queued_raw ? 32+32'(queued_blocks)*128 : prepared_start1+queued_prefix123));
            assert(prepared_bad_epoch==(epoch_seen && queued_epoch<=last_epoch));
        end
    end
    // Check every registered read decision at its exact consumption edge.
    always_ff @(posedge clk)if(!cancel && !response_failure)begin
        if(state==DC_FETCH)assert(current_dc_line==18'((32+(tile_mode ? 32'(prepare_block) : 32'(output_block))*2)&32'hfffffff0));
        if(state==RAW_FETCH)assert(selected_raw_line==18'((32+(32'(output_block)*64+32'(output_index))*2)&32'hfffffff0));
        if(state==AC_FETCH)assert(prepared_ac_line[read_band]==18'((starts[read_band]+cursors[read_band]*4)&32'hfffffff0));
        if(state==DC_EXTRACT)assert(read_tag_match==(cache_valid[0] && cache_address[0]==18'(read_address & 32'hfffffff0)))
            else $fatal(1,"registered DC cache tag decision differs");
        if(state==AC_EXTRACT)assert(read_tag_match==(cache_valid[read_segment] && cache_address[read_segment]==18'(read_address & 32'hfffffff0)))
            else $fatal(1,"registered AC cache tag decision differs");
    end
    // Compare prepared values with the old full-width algebra precisely where
    // they can issue. Existing fetch/check transitions provide the warm-up edge.
    always_ff @(posedge clk)if(prefetch_mode && !tile_mode && sealed && !prefetch_offer &&
        !outstanding && !cancel && error==0)begin
        if(state==EMIT && !raw_mode)begin
            assert(prepared_sparse_more==(17'(output_block)+1<blocks));
            assert(prepared_dc_line==18'((32+(32'(output_block)+1)*2)&32'hfffffff0));
            for(integer band=1;band<=3;band=band+1)begin
                assert(prepared_ac_more[band]==(cursors[band]<counts[band]));
                assert(prepared_ac_line[band]==18'((starts[band]+cursors[band]*4)&32'hfffffff0));
            end
        end
        if(state==RAW_EXTRACT && raw_mode)begin
            assert(prepared_raw_more==(32'(output_block)*64+32'(output_index)+1<32'(blocks)*64));
            assert(prepared_raw_line==18'((32+(32'(output_block)*64+32'(output_index)+1)*2)&32'hfffffff0));
        end
    end
    // No claim is made about inactive private payloads after cancellation.
    always_ff @(posedge clk)if(!cancel && !response_failure)begin
        for(integer b=0;b<4;b=b+1)if(cache_valid[b])
            for(integer offset=0;offset<16;offset=offset+1)
                assert(cache_positions[b][offset]==sparse_position(19'(cache_data[b]>>(8*offset+13))));
        if(state==AC_EXTRACT && cache_valid[read_segment] &&
            cache_address[read_segment]==18'(read_address & 32'hfffffff0))begin
            assert(read_position==32'(read_word[31:19])*64+32'(zigzag(read_word[18:13])));
            if(cursors[read_band]!=0)
                assert(head_positions[read_band]==sparse_position(heads[read_band][31:13]));
        end
    end
`endif
    assert property (@(posedge clk) mem_req_valid |-> mem_req_addr[3:0]==0 &&
        19'(mem_req_addr)+16<=used_bytes && !outstanding);
    assert property (@(posedge clk) write_slot_valid && !cancel &&
        !(mem_rsp_valid && mem_rsp_epoch==request_epoch) |=>
        $stable({transfer_data,transfer_address,request_epoch}) || reset || abort_valid);
    assert property (@(posedge clk) assembly_bytes<=16);
    assert property (@(posedge clk) sealed |-> !write_slot_valid && !outstanding ||
        state==READ_WAIT || state==DRAIN || (prefetch_offer &&
        (state==EMIT || state==RAW_EXTRACT || state==PREFETCH_DRAIN)));
    assert property (@(posedge clk) prefetch_offer && !cancel && !mem_rsp_valid |=>
        $stable({transfer_address,request_epoch,prefetch_segment}) || reset || abort_valid);
    assert property (@(posedge clk) prefetch_launch |-> sealed && !outstanding && !write_slot_valid &&
        (state==EMIT || state==RAW_EXTRACT));
    assert property (@(posedge clk) tile_mode && tile_preparing |-> !bank_ready[prep_bank]);
    assert property (@(posedge clk) tile_mode && dense_valid |-> bank_ready[emit_bank] &&
        bank_epoch[emit_bank]==active_epoch && 17'(bank_block[emit_bank])<blocks);
    assert property (@(posedge clk) tile_mode && debug_tile_release &&
        17'(bank_block[emit_bank])+1==blocks |-> !outstanding && !prefetch_offer && !tile_preparing);
    assert property (@(posedge clk) state==FINISHED |-> !prefetch_offer && !outstanding);
    // Request and output payloads remain stable for arbitrarily long stalls.
    assert property (@(posedge clk) disable iff(reset || abort_valid)
        mem_req_valid && !mem_req_ready |=> $stable({mem_req_write,mem_req_addr,mem_req_data,mem_req_epoch}) || reset || abort_valid);
    assert property (@(posedge clk) disable iff(reset || abort_valid)
        dense_valid && !dense_ready |=> $stable({dense_block,dense_index,dense_value,dense_epoch}) || reset || abort_valid);
`ifndef SYNTHESIS
    logic busy_predicate_initialized=0;
    always_ff @(posedge clk)begin
        busy_predicate_initialized<=1;
        // Unconditional after the first clock, including reset, abort, DRAIN,
        // invalid cycles, error branches and final physical-response retirement.
        if(busy_predicate_initialized)
            assert(busy_owned==(state!=IDLE && state!=FINISHED && state!=FAILED))
                else $fatal(1,"scratch same-edge busy predicate mismatch");
    end
`endif
`ifndef SYNTHESIS
    // No reset/abort/response_failure disable: prove the owner relation through
    // the cancellation edge itself, including rejected descriptors and drains.
    always_ff @(posedge clk)begin
        if(state==IDLE)assert(!outstanding)
            else $fatal(1,"V116B IDLE retained physical debt");
        if(preparing_begin)begin
            assert(active_epoch==queued_epoch)
                else $fatal(1,"V116B preparing owner epochs diverged");
            assert(!outstanding)
                else $fatal(1,"V116B preparation acquired physical debt");
        end
        assert(owned_abort_epoch==(preparing_begin ? queued_epoch : active_epoch))
            else $fatal(1,"V116B selected abort target mismatch");
        assert(cancel==(reset || (abort_valid && abort_epoch==(preparing_begin ? queued_epoch : active_epoch))))
            else $fatal(1,"V116B generic abort-epoch semantics changed");
    end
`endif
`ifndef SYNTHESIS
    // Frozen old three-field shadow. Its eligibility independently spells out
    // the ORIGINAL main outer priority; response_failure is deliberately not
    // used because a matching error without prefetch/write ownership falls in.
    logic [31:0] record_shadow=0,position_shadow=0;
    logic [2:0] bytes_shadow=0;
    logic record_shadow_event;
    logic record_check_initialized=0,record_previous_bank,record_previous_event;
    logic [66:0] record_previous_prospective;
    logic [66:0] record_previous_physical [0:1];
    always_comb record_shadow_event=!cancel &&
        !(mem_rsp_valid && (!outstanding || mem_rsp_epoch!=request_epoch)) &&
        state!=DRAIN &&
        !(prefetch_offer && outstanding && mem_rsp_valid && mem_rsp_error) &&
        !(overlap_mode && write_slot_valid && outstanding && mem_rsp_valid && mem_rsp_error) &&
        state==INGEST && coef_valid && !input_bad;
    always_ff @(posedge clk)begin
        assert({pending_record,pending_bytes,pending_position}=={record_shadow,bytes_shadow,position_shadow})
            else $fatal(1,"V116C exact old pending tuple shadow mismatch");
        if(record_check_initialized)begin
            assert(record_view_bank==(record_previous_bank^record_previous_event))
                else $fatal(1,"V116C view selector changed outside original write");
            for(integer n=0;n<2;n=n+1)begin
                if(1'(n)==record_previous_bank)
                    assert({record_payload[n],bytes_payload[n],position_payload[n]}==record_previous_physical[n])
                        else $fatal(1,"V116C selected physical tuple was overwritten");
                else
                    assert({record_payload[n],bytes_payload[n],position_payload[n]}==record_previous_prospective)
                        else $fatal(1,"V116C inactive bank missed complete speculative tuple");
            end
            if(record_previous_event)assert(record_view_seen)
                else $fatal(1,"V116C original pending write not made visible");
        end
        if(record_shadow_event)begin
            record_shadow<=raw_mode || phase==0 ? {16'd0,coef_value} :
                {coef_block[12:0],coef_index,coef_value[12:0]};
            bytes_shadow<=raw_mode || phase==0 ? 2 : 4;
            position_shadow<=input_position;
        end
        record_check_initialized<=1;
        record_previous_bank<=record_view_bank;record_previous_event<=record_shadow_event;
        record_previous_prospective<=prospective_record;
        for(integer n=0;n<2;n=n+1)
            record_previous_physical[n]<={record_payload[n],bytes_payload[n],position_payload[n]};
    end
`endif
`ifndef SYNTHESIS
    always_ff @(posedge clk)if(!cancel && !response_failure &&
        (state==EMIT || state==RAW_EXTRACT))begin
        assert(output_plan.epoch==active_epoch && output_plan.block_id==output_block &&
            output_plan.block_limit==blocks && output_plan.raw==raw_mode)
            else $fatal(1,"V119 output plan mixed owner/context");
        assert(output_plan.last_block==(17'(output_block)+1==blocks) &&
            output_plan.next_block==16'(32'(output_block)+32'd1) &&
            output_plan.next_state==(raw_mode ? RAW_FETCH : CLEAR_TILE))
            else $fatal(1,"V119 output plan differs from full original expressions");
    end
`endif
endmodule
