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
        FINISHED, FAILED, DRAIN, FLUSH_LINE, PREFETCH_DRAIN, BANK_WAIT, PREP_DONE} state_t;
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
    logic [31:0] candidate_word_address;
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
    logic signed [15:0] tile[0:1][0:63];
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
        (head_valid[read_band] || cursors[read_band]>=counts[read_band]) &&
        !(head_valid[read_band] && heads[read_band][31:19]==prepare_block[12:0]) && read_band==3;
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
        cancel=reset || (abort_valid && abort_epoch==active_epoch);
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
        input_bad=coef_epoch!=active_epoch || coef_band!=phase[1:0] ||
            coef_block>=16'(blocks) || coef_value < -2048 || coef_value > 2048 ||
            written>=counts[phase[1:0]];
        debug_write_enqueue=overlap_mode && !cancel && slot_available &&
            !(mem_rsp_valid && (!outstanding || mem_rsp_epoch!=request_epoch || mem_rsp_error)) &&
            ((state==APPEND && assembly_bytes+5'(pending_bytes)==16) || state==FLUSH_LINE ||
            (state==INGEST && !coef_valid && band_end_valid && assembly_bytes!=0 &&
             band_end_epoch==active_epoch && band_end_band==phase[1:0] && written==counts[phase[1:0]]));
        // Prefetch only a monotonically forward line whose old cache data is
        // fully consumed. Dense output is already owned by tile/raw_value.
        candidate_valid=0; candidate_segment=0; candidate_address=0;
        candidate_word_address=0;
        if(prefetch_mode && !tile_mode && sealed && !prefetch_offer && !outstanding && !cancel && error==0) begin
            if(state==EMIT && !raw_mode && 17'(output_block)+1<blocks) begin
                candidate_word_address=32+(32'(output_block)+1)*2;
                if(!cache_valid[0] || cache_address[0]!=18'(candidate_word_address & 32'hfffffff0)) begin
                    candidate_valid=1; candidate_segment=0;
                    candidate_address=18'(candidate_word_address & 32'hfffffff0);
                end
                for(integer b=1;b<=3;b=b+1) begin
                    candidate_word_address=starts[b]+cursors[b]*4;
                    if(!candidate_valid && cursors[b]<counts[b] &&
                       (!cache_valid[b] || cache_address[b]!=18'(candidate_word_address & 32'hfffffff0))) begin
                        candidate_valid=1; candidate_segment=2'(b);
                        candidate_address=18'(candidate_word_address & 32'hfffffff0);
                    end
                end
            end else if(state==RAW_EXTRACT && raw_mode &&
                32'(output_block)*64+32'(output_index)+1<32'(blocks)*64) begin
                candidate_word_address=32+(32'(output_block)*64+32'(output_index)+1)*2;
                if(!cache_valid[0] || cache_address[0]!=18'(candidate_word_address & 32'hfffffff0)) begin
                    candidate_valid=1; candidate_segment=0;
                    candidate_address=18'(candidate_word_address & 32'hfffffff0);
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
        if(raw_mode) input_bad=input_bad || input_position!=written;
        else if(phase==0) input_bad=input_bad || coef_index!=0 || 32'(coef_block)!=written;
        else input_bad=input_bad || !band_matches(coef_band,coef_index) || coef_value==0 ||
            (previous_valid && input_position<=previous_position);
    end

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

    always_ff @(posedge clk) begin
        // A reset is cancellation, not permission to discard an accepted write.
        if(reset || (abort_valid && abort_epoch==active_epoch)) begin
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
                IDLE: if(begin_valid) begin
                    sealed<=0; done<=0; error<=0;
                    if(epoch_seen && begin_epoch<=last_epoch) begin error<=2; begin state<=FAILED; busy_owned<=1'b0; end end
                    else if(begin_blocks==0 || begin_blocks>8192 ||
                        32'(begin_blocks)<begin_threshold1 || 32'(begin_blocks)<begin_threshold2 ||
                        32'(begin_blocks)<begin_threshold3 ||
                        (begin_raw && (begin_count1!=0 || begin_count2!=0 || begin_count3!=0)) ||
                        capacity_bad) begin error<=1; begin state<=FAILED; busy_owned<=1'b0; end end
                    else begin
                        epoch_seen<=1; last_epoch<=begin_epoch; active_epoch<=begin_epoch;
                        blocks<=begin_blocks; raw_mode<=begin_raw; tile_overlap_mode<=begin_tile_overlap; bank_ready<=0; tile_preparing<=0; prep_bank<=0; emit_bank<=0; prepare_block<=0; tile_emit_index<=0; tile_valid[0]<=0; tile_valid[1]<=0; serial_clear<=begin_serial_clear; overlap_mode<=begin_overlap; prefetch_mode<=begin_prefetch; prefetch_offer<=0; prefetched_valid<=0; write_slot_valid<=0; used_bytes<=19'(plan_used);
                        counts[0]<=begin_raw ? 32'(begin_blocks)*64 : 32'(begin_blocks);
                        counts[1]<=begin_count1; counts[2]<=begin_count2; counts[3]<=begin_count3;
                        starts[0]<=32; starts[1]<=plan_start1; starts[2]<=plan_start2; starts[3]<=plan_start3;
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
                            pending_record<=raw_mode || phase==0 ? {16'd0,coef_value} :
                                {coef_block[12:0],coef_index,coef_value[12:0]};
                            pending_bytes<=raw_mode || phase==0 ? 2 : 4;
                            pending_position<=input_position; begin state<=APPEND; busy_owned<=1'b1; end
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
                    if(serial_clear) tile[prep_bank][clear_index]<=0;
                    if(!serial_clear || clear_index==63) begin clear_index<=0; begin state<=DC_FETCH; busy_owned<=1'b1; end end
                    else clear_index<=clear_index+1;
                end
                DC_FETCH, RAW_FETCH: begin
                    read_address<=32+(raw_mode ? (32'(output_block)*64+32'(output_index))*2 : (tile_mode ? 32'(prepare_block) : 32'(output_block))*2);
                    read_segment<=0; begin state<=DC_EXTRACT; busy_owned<=1'b1; end
                end
                DC_EXTRACT: begin
                    if(!cache_valid[0] || cache_address[0]!=18'(read_address & 32'hfffffff0)) begin
                        transfer_address<=18'(read_address & 32'hfffffff0); return_state<=DC_EXTRACT; begin state<=READ_REQ; busy_owned<=1'b1; end
                    end else if(read_half < -2048 || read_half > 2048) begin
                        error<=3; sealed<=0; begin state<=FAILED; busy_owned<=1'b0; end
                    end else if(raw_mode) begin
                        raw_value<=16'(cache_data[0]>>(8*read_address[3:0])); begin state<=RAW_EXTRACT; busy_owned<=1'b1; end
                    end else begin
                        tile[prep_bank][0]<=16'(cache_data[0]>>(8*read_address[3:0])); tile_valid[prep_bank][0]<=1; read_band<=1; begin state<=AC_CHECK; busy_owned<=1'b1; end
                    end
                end
                AC_CHECK: begin
                    if(!head_valid[read_band] && cursors[read_band]<counts[read_band]) begin state<=AC_FETCH; busy_owned<=1'b1; end
                    else if(head_valid[read_band] && heads[read_band][31:19]==(tile_mode ? prepare_block[12:0] : output_block[12:0])) begin
                        tile[prep_bank][heads[read_band][18:13]]<={{3{heads[read_band][12]}},heads[read_band][12:0]};
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
                    read_segment<=read_band; read_address<=starts[read_band]+cursors[read_band]*4; begin state<=AC_EXTRACT; busy_owned<=1'b1; end
                end
                AC_EXTRACT: begin
                    if(!cache_valid[read_segment] || cache_address[read_segment]!=18'(read_address & 32'hfffffff0)) begin
                        transfer_address<=18'(read_address & 32'hfffffff0); return_state<=AC_EXTRACT; begin state<=READ_REQ; busy_owned<=1'b1; end
                    end else begin
                        if(ac_bank_invalid[read_segment]) begin
                            error<=3; sealed<=0; begin state<=FAILED; busy_owned<=1'b0; end
                        end else begin
                            heads[read_band]<=read_word;
                            head_positions[read_band]<=read_position[18:0];
                            head_valid[read_band]<=1; begin state<=AC_CHECK; busy_owned<=1'b1; end
                        end
                    end
                end
                EMIT, RAW_EXTRACT: if(dense_ready) begin
                    if(output_index==63) begin
                        if(17'(output_block)+1==blocks) begin done<=1; begin state<=FINISHED; busy_owned<=1'b0; end end
                        else begin
                            output_block<=output_block+1; output_index<=0;
                            if(prefetch_mode && (prefetch_launch || (prefetch_offer && !prefetch_complete))) begin
                                return_state<=raw_mode ? RAW_FETCH : CLEAR_TILE; begin state<=PREFETCH_DRAIN; busy_owned<=1'b1; end
                            end else begin state<=raw_mode ? RAW_FETCH : CLEAR_TILE; busy_owned<=1'b1; end
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
endmodule
