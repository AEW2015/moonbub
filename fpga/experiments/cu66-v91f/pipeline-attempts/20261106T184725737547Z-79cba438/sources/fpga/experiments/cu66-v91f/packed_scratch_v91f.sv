// V91c byte-identical packed scratch, sequential functional implementation.
module packed_scratch_v91f (
    input logic clk, reset,
    input logic begin_valid, output logic begin_ready,
    input logic [16:0] begin_blocks, input logic begin_raw, begin_serial_clear, begin_overlap,
    input logic [31:0] begin_count1, begin_count2, begin_count3, begin_epoch,
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
    output logic debug_write_slot_valid, debug_assembler_full, debug_write_enqueue,
    output logic [2:0] debug_head_valid
);
    typedef enum logic [4:0] {IDLE, INGEST, APPEND, NEXT_BAND, WAIT_SEAL,
        HEADER0, HEADER1, HEADER_DONE, WRITE_REQ, WRITE_WAIT, READ_REQ,
        READ_WAIT, DESC0, DESC1, CLEAR_TILE, DC_FETCH, DC_EXTRACT,
        AC_CHECK, AC_FETCH, AC_EXTRACT, EMIT, RAW_FETCH, RAW_EXTRACT,
        FINISHED, FAILED, DRAIN, FLUSH_LINE} state_t;
    state_t state=IDLE, return_state;
    logic outstanding=0, epoch_seen=0;
    logic [31:0] last_epoch=0;
    logic [16:0] blocks;
    logic raw_mode, serial_clear, overlap_mode;
    logic write_slot_valid=0;
    logic slot_available;
    logic [63:0] tile_valid;
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
    logic [17:0] cache_address[0:3];
    logic [3:0] cache_valid;
    logic [1:0] read_segment;
    logic [31:0] read_address;
    logic [31:0] heads[1:3], cursors[1:3];
    logic [3:1] head_valid;
    logic [1:0] read_band;
    logic signed [15:0] tile[0:63];
    logic [15:0] output_block;
    logic [5:0] output_index, clear_index;
    logic signed [15:0] raw_value;
    logic [31:0] plan_start1, plan_start2, plan_start3, plan_used;
    logic [31:0] input_position;
    logic [5:0] input_zigzag;
    logic input_bad;
    logic [31:0] read_word;
    logic signed [15:0] read_half;
    logic [31:0] read_position;
    logic cancel;

    function automatic logic [31:0] aligned(input logic [31:0] n);
        aligned=(n+15)&32'hfffffff0;
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
        plan_start1=32+aligned(32'(begin_blocks)*2);
        plan_start2=plan_start1+aligned(begin_count1*4);
        plan_start3=plan_start2+aligned(begin_count2*4);
        plan_used=begin_raw ? 32+32'(begin_blocks)*128 : plan_start3+aligned(begin_count3*4);
        read_word=32'(cache_data[read_segment]>>(8*read_address[3:0]));
        read_half=16'(cache_data[0]>>(8*read_address[3:0]));
        read_position=32'(read_word[31:19])*64+32'(zigzag(read_word[18:13]));
        cancel=reset || (abort_valid && abort_epoch==active_epoch);
        begin_ready=state==IDLE && !outstanding && !cancel;
        coef_ready=state==INGEST && !cancel;
        band_end_ready=state==INGEST && !coef_valid && !cancel;
        seal_ready=state==WAIT_SEAL && !cancel &&
            (!overlap_mode || (!write_slot_valid && !outstanding && assembly_bytes==0));
        slot_available=!write_slot_valid || (outstanding && mem_rsp_valid &&
            mem_rsp_epoch==request_epoch && !mem_rsp_error);
        busy=state!=IDLE && state!=FINISHED && state!=FAILED;
        dense_valid=(state==EMIT || state==RAW_EXTRACT) && !cancel;
        dense_block=output_block;
        dense_index=output_index;
        dense_value=raw_mode ? raw_value : (tile_valid[output_index] ? tile[output_index] : 16'sd0);
        dense_epoch=active_epoch;
        mem_req_valid=(state==WRITE_REQ || state==READ_REQ ||
            (write_slot_valid && !outstanding && state!=DRAIN && state!=FAILED)) && !cancel;
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
        if(raw_mode) input_bad=input_bad || input_position!=written;
        else if(phase==0) input_bad=input_bad || coef_index!=0 || 32'(coef_block)!=written;
        else input_bad=input_bad || !band_matches(coef_band,coef_index) || coef_value==0 ||
            (previous_valid && input_position<=previous_position);
    end

    always_ff @(posedge clk) begin
        // A reset is cancellation, not permission to discard an accepted write.
        if(reset || (abort_valid && abort_epoch==active_epoch)) begin
            sealed<=0; done<=0; error<=0; cache_valid<=0; head_valid<=0;
            assembly_bytes<=0; write_slot_valid<=0;
            if(outstanding && (!mem_rsp_valid || mem_rsp_epoch!=request_epoch)) begin
                state<=DRAIN;
                if(mem_rsp_valid) error<=6;
            end else begin state<=IDLE; outstanding<=0; end
        end else if(mem_rsp_valid && (!outstanding || mem_rsp_epoch!=request_epoch)) begin
            // A mismatched response cannot retire the real outstanding request.
            error<=6; sealed<=0; done<=0; write_slot_valid<=0; assembly_bytes<=0;
            state<=outstanding ? DRAIN : FAILED;
        end else if(state==DRAIN) begin
            if(mem_rsp_valid && outstanding) begin outstanding<=0; state<=IDLE; end
            else if(!outstanding) state<=IDLE;
        end else if(overlap_mode && write_slot_valid && outstanding && mem_rsp_valid && mem_rsp_error) begin
            outstanding<=0; write_slot_valid<=0; assembly_bytes<=0;
            error<=5; sealed<=0; done<=0; state<=FAILED;
        end else begin
            // Slot ownership ends only at physical matching ACK. The controller
            // may replace it with the assembled line on this same edge.
            if(overlap_mode && write_slot_valid) begin
                if(!outstanding && mem_req_valid && mem_req_ready) outstanding<=1;
                if(outstanding && mem_rsp_valid) begin outstanding<=0; write_slot_valid<=0; end
            end
            case(state)
                IDLE: if(begin_valid) begin
                    sealed<=0; done<=0; error<=0;
                    if(epoch_seen && begin_epoch<=last_epoch) begin error<=2; state<=FAILED; end
                    else if(begin_blocks==0 || begin_blocks>8192 ||
                        begin_count1>32'(begin_blocks)*5 || begin_count2>32'(begin_blocks)*15 ||
                        begin_count3>32'(begin_blocks)*43 ||
                        (begin_raw && (begin_count1!=0 || begin_count2!=0 || begin_count3!=0)) ||
                        plan_used>262144) begin error<=1; state<=FAILED; end
                    else begin
                        epoch_seen<=1; last_epoch<=begin_epoch; active_epoch<=begin_epoch;
                        blocks<=begin_blocks; raw_mode<=begin_raw; serial_clear<=begin_serial_clear; overlap_mode<=begin_overlap; write_slot_valid<=0; used_bytes<=19'(plan_used);
                        counts[0]<=begin_raw ? 32'(begin_blocks)*64 : 32'(begin_blocks);
                        counts[1]<=begin_count1; counts[2]<=begin_count2; counts[3]<=begin_count3;
                        starts[0]<=32; starts[1]<=plan_start1; starts[2]<=plan_start2; starts[3]<=plan_start3;
                        phase<=0; written<=0; previous_valid<=0; assembler<=0; assembly_bytes<=0;
                        write_address<=32; cache_valid<=0; head_valid<=0;
                        for(integer b=1;b<=3;b=b+1) cursors[b]<=0;
                        state<=INGEST;
                    end
                end
                INGEST: begin
                    if(coef_valid) begin
                        if(input_bad) begin
                            error<=coef_epoch!=active_epoch ? 2 : 3;
                            if(overlap_mode) begin
                                write_slot_valid<=0; assembly_bytes<=0;
                                state<=((outstanding && !mem_rsp_valid) ||
                                    (!outstanding && mem_req_valid && mem_req_ready)) ? DRAIN : FAILED;
                            end else state<=FAILED;
                        end
                        else begin
                            pending_record<=raw_mode || phase==0 ? {16'd0,coef_value} :
                                {coef_block[12:0],coef_index,coef_value[12:0]};
                            pending_bytes<=raw_mode || phase==0 ? 2 : 4;
                            pending_position<=input_position; state<=APPEND;
                        end
                    end else if(band_end_valid) begin
                        if(band_end_epoch!=active_epoch || band_end_band!=phase[1:0] || written!=counts[phase[1:0]]) begin
                            error<=band_end_epoch!=active_epoch ? 2 : 4;
                            if(overlap_mode) begin
                                write_slot_valid<=0; assembly_bytes<=0;
                                state<=((outstanding && !mem_rsp_valid) ||
                                    (!outstanding && mem_req_valid && mem_req_ready)) ? DRAIN : FAILED;
                            end else state<=FAILED;
                        end else if(assembly_bytes!=0) begin
                            if(overlap_mode) begin
                                return_state<=NEXT_BAND;
                                if(slot_available) begin
                                    transfer_data<=assembler; transfer_address<=18'(write_address);
                                    request_epoch<=active_epoch; write_slot_valid<=1;
                                    write_address<=write_address+16; state<=NEXT_BAND;
                                end else state<=FLUSH_LINE;
                            end else begin
                                transfer_data<=assembler; transfer_address<=18'(write_address);
                                request_epoch<=active_epoch; return_state<=NEXT_BAND; state<=WRITE_REQ;
                            end
                        end else state<=NEXT_BAND;
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
                                state<=INGEST; assembler<=0; assembly_bytes<=0;
                            end else begin assembly_bytes<=16; state<=FLUSH_LINE; end
                        end else begin
                            transfer_data<=assembler | (128'(pending_record) << (8*assembly_bytes));
                            transfer_address<=18'(write_address); request_epoch<=active_epoch;
                            state<=WRITE_REQ; assembler<=0; assembly_bytes<=0;
                        end
                    end else begin assembly_bytes<=assembly_bytes+5'(pending_bytes); state<=INGEST; end
                end
                FLUSH_LINE: if(slot_available) begin
                    transfer_data<=assembler; transfer_address<=18'(write_address);
                    request_epoch<=active_epoch; write_slot_valid<=1;
                    write_address<=write_address+16; assembler<=0; assembly_bytes<=0;
                    state<=return_state;
                end
                NEXT_BAND: begin
                    assembler<=0; assembly_bytes<=0; written<=0; previous_valid<=0;
                    if(raw_mode || phase==3) begin phase<=4; state<=WAIT_SEAL; end
                    else begin
                        phase<=phase+1; write_address<=starts[phase[1:0]+2'd1]; state<=INGEST;
                    end
                end
                WAIT_SEAL: if(seal_valid && seal_ready) begin
                    if(seal_epoch!=active_epoch) begin error<=2; state<=FAILED; end
                    else state<=HEADER0;
                end
                HEADER0: begin
                    transfer_data<={counts[1],31'd0,raw_mode,15'd0,blocks,32'h43393150};
                    transfer_address<=0; request_epoch<=active_epoch; return_state<=HEADER1; state<=WRITE_REQ;
                end
                HEADER1: begin
                    transfer_data<={32'd0,13'd0,used_bytes,counts[3],counts[2]};
                    transfer_address<=16; request_epoch<=active_epoch; return_state<=HEADER_DONE; state<=WRITE_REQ;
                end
                HEADER_DONE: begin
                    sealed<=1; transfer_address<=0; return_state<=DESC0; state<=READ_REQ;
                end
                WRITE_REQ: if(mem_req_ready) begin outstanding<=1; state<=WRITE_WAIT; end
                WRITE_WAIT: if(mem_rsp_valid) begin
                    outstanding<=0;
                    if(mem_rsp_error) begin error<=5; sealed<=0; state<=FAILED; end
                    else begin write_address<=write_address+16; state<=return_state; end
                end
                READ_REQ: if(mem_req_ready) begin outstanding<=1; state<=READ_WAIT; end
                READ_WAIT: if(mem_rsp_valid) begin
                    outstanding<=0;
                    if(mem_rsp_error) begin error<=5; sealed<=0; state<=FAILED; end
                    else begin
                        transfer_data<=mem_rsp_data;
                        if(return_state!=DESC0 && return_state!=DESC1) begin
                            cache_data[read_segment]<=mem_rsp_data;
                            cache_address[read_segment]<=transfer_address; cache_valid[read_segment]<=1;
                        end
                        state<=return_state;
                    end
                end
                DESC0: begin
                    descriptor_low<=transfer_data; transfer_address<=16;
                    return_state<=DESC1; state<=READ_REQ;
                end
                DESC1: begin
                    if(descriptor_low!={counts[1],31'd0,raw_mode,15'd0,blocks,32'h43393150} ||
                       transfer_data!={32'd0,13'd0,used_bytes,counts[3],counts[2]}) begin
                        error<=7; sealed<=0; state<=FAILED;
                    end else begin
                        output_block<=0; output_index<=0; clear_index<=0;
                        state<=raw_mode ? RAW_FETCH : CLEAR_TILE;
                    end
                end
                CLEAR_TILE: begin
                    tile_valid<=0;
                    if(serial_clear) tile[clear_index]<=0;
                    if(!serial_clear || clear_index==63) begin clear_index<=0; state<=DC_FETCH; end
                    else clear_index<=clear_index+1;
                end
                DC_FETCH, RAW_FETCH: begin
                    read_address<=32+(raw_mode ? (32'(output_block)*64+32'(output_index))*2 : 32'(output_block)*2);
                    read_segment<=0; state<=DC_EXTRACT;
                end
                DC_EXTRACT: begin
                    if(!cache_valid[0] || cache_address[0]!=18'(read_address & 32'hfffffff0)) begin
                        transfer_address<=18'(read_address & 32'hfffffff0); return_state<=DC_EXTRACT; state<=READ_REQ;
                    end else if(read_half < -2048 || read_half > 2048) begin
                        error<=3; sealed<=0; state<=FAILED;
                    end else if(raw_mode) begin
                        raw_value<=16'(cache_data[0]>>(8*read_address[3:0])); state<=RAW_EXTRACT;
                    end else begin
                        tile[0]<=16'(cache_data[0]>>(8*read_address[3:0])); tile_valid[0]<=1; read_band<=1; state<=AC_CHECK;
                    end
                end
                AC_CHECK: begin
                    if(!head_valid[read_band] && cursors[read_band]<counts[read_band]) state<=AC_FETCH;
                    else if(head_valid[read_band] && heads[read_band][31:19]==output_block[12:0]) begin
                        tile[heads[read_band][18:13]]<={{3{heads[read_band][12]}},heads[read_band][12:0]};
                        tile_valid[heads[read_band][18:13]]<=1; head_valid[read_band]<=0;
                    end else if(read_band==3) begin output_index<=0; state<=EMIT; end
                    else read_band<=read_band+1;
                end
                AC_FETCH: begin
                    read_segment<=read_band; read_address<=starts[read_band]+cursors[read_band]*4; state<=AC_EXTRACT;
                end
                AC_EXTRACT: begin
                    if(!cache_valid[read_segment] || cache_address[read_segment]!=18'(read_address & 32'hfffffff0)) begin
                        transfer_address<=18'(read_address & 32'hfffffff0); return_state<=AC_EXTRACT; state<=READ_REQ;
                    end else begin
                        if(17'(read_word[31:19])>=blocks || !band_matches(read_band,read_word[18:13]) ||
                           $signed(read_word[12:0])==0 || $signed(read_word[12:0]) < -2048 ||
                           $signed(read_word[12:0]) > 2048 ||
                           (cursors[read_band]!=0 && read_position<=32'(heads[read_band][31:19])*64+32'(zigzag(heads[read_band][18:13])))) begin
                            error<=3; sealed<=0; state<=FAILED;
                        end else begin
                            heads[read_band]<=read_word;
                            cursors[read_band]<=cursors[read_band]+1; head_valid[read_band]<=1; state<=AC_CHECK;
                        end
                    end
                end
                EMIT, RAW_EXTRACT: if(dense_ready) begin
                    if(output_index==63) begin
                        if(17'(output_block)+1==blocks) begin done<=1; state<=FINISHED; end
                        else begin
                            output_block<=output_block+1; output_index<=0;
                            state<=raw_mode ? RAW_FETCH : CLEAR_TILE;
                        end
                    end else begin output_index<=output_index+1; if(raw_mode) state<=RAW_FETCH; end
                end
                FINISHED, FAILED: ;
                default: state<=FAILED;
            endcase
        end
    end
    assert property (@(posedge clk) mem_req_valid |-> mem_req_addr[3:0]==0 &&
        19'(mem_req_addr)+16<=used_bytes && !outstanding);
    assert property (@(posedge clk) write_slot_valid && !cancel &&
        !(mem_rsp_valid && mem_rsp_epoch==request_epoch) |=>
        $stable({transfer_data,transfer_address,request_epoch}) || reset || abort_valid);
    assert property (@(posedge clk) assembly_bytes<=16);
    assert property (@(posedge clk) sealed |-> !write_slot_valid && !outstanding ||
        state==READ_WAIT || state==DRAIN);
    // Request and output payloads remain stable for arbitrarily long stalls.
    assert property (@(posedge clk) disable iff(reset || abort_valid)
        mem_req_valid && !mem_req_ready |=> $stable({mem_req_write,mem_req_addr,mem_req_data,mem_req_epoch}) || reset || abort_valid);
    assert property (@(posedge clk) disable iff(reset || abort_valid)
        dense_valid && !dense_ready |=> $stable({dense_block,dense_index,dense_value,dense_epoch}) || reset || abort_valid);
endmodule
