module ingress_candidate #(
    parameter integer MAX_PACKET_BYTES=49152
) (
    input logic clk, reset, start, abort_packet,
    input logic [31:0] packet_bytes,
    input logic [16:0] blocks,
    input logic [31:0] epoch,
    input logic word16, serial_mode,
    input logic in_valid,
    output logic in_ready,
    input logic [7:0] in_data,
    input logic in_last,
    output logic out_valid,
    input logic out_ready,
    output logic [15:0] out_block,
    output logic [5:0] out_index,
    output logic signed [15:0] out_coefficient,
    output logic [31:0] out_epoch,
    output logic meta_valid,
    input logic meta_ready,
    output logic [16:0] meta_blocks,
    output logic [31:0] meta_count1, meta_count2, meta_count3, meta_epoch,
    output logic [31:0] meta_prefix1, meta_prefix12, meta_prefix123,
    output logic [31:0] meta_threshold1, meta_threshold2, meta_threshold3,
    output logic [31:0] meta_capacity_upper, meta_capacity_lower,
    output logic meta_capacity_wrap,
    output logic meta_raw,
    output logic [1:0] out_band,
    output logic band_end_valid,
    input logic band_end_ready,
    output logic [1:0] band_end_band,
    output logic [31:0] band_end_epoch,
    output logic done,
    output logic [3:0] error,
    output logic [63:0] count_cycles, count_inputs, count_outputs,
    output logic [63:0] count_output_stall,
    output logic [3:0] debug_state,
    output logic stage_read_req, stage_read_rsp, stage_write, stage_pending, stage_context_active, stage_cancel, stage_word_valid, stage_word_ready,
    output logic [31:0] stage_read_addr, stage_rsp_addr, stage_write_addr, stage_req_epoch, stage_rsp_epoch,
    output logic [7:0] stage_read_data, stage_write_data,
    output logic [5:0] stage_buffer_bytes, stage_buffer_highwater,
    output logic [2:0] stage_purpose,
    output logic [63:0] count_stage_reads, count_stage_responses, count_stage_writes,
    output logic [63:0] count_stage_fetch_wait, count_stage_word_hold
);
    localparam logic [3:0] IDLE=0, RECEIVE=1, HEADER=2, DESCRIPTOR=3,
        CONTEXT_START=4, CONTEXT_RUN=5, RAW=6, FINISHED=7, FAILED=8,
        METADATA=9, CONTEXT_END=10, RAW_END=11, FETCH_REQ=12, FETCH_WAIT=13;
    localparam logic [2:0] F_HEADER=0, F_DESCRIPTOR=1, F_REPLAY=2, F_RAW=3;
    localparam integer AW=$clog2(MAX_PACKET_BYTES);
    logic [3:0] state, fetch_return;
    // The only backing-store accesses are the write and registered read below.
    logic [7:0] memory [0:MAX_PACKET_BYTES-1];
    logic ram_valid;
    logic [7:0] ram_data;
    logic [31:0] ram_addr, ram_epoch;
    logic [7:0] fetch_bytes [0:45];
    logic [5:0] fetch_index, fetch_count, buffer_bytes;
    logic [2:0] fetch_kind;
    logic [31:0] fetch_base, fetch_address, fetched_word;
    logic [31:0] size_bytes, context_epoch, received, crc, cursor;
    logic [16:0] context_blocks;
    logic mode16, mode_serial, raw_mode, descriptor_ready, word_valid, raw_valid, context_active;
    logic [1:0] band;
    logic [31:0] lengths[0:3], counts[0:3], offsets[0:3], sizes[0:3];
    logic [7:0] k0s[0:3], k1s[0:3];
    logic [31:0] descriptor_bits, descriptor_bytes, descriptor_limit;
    // Only this constant control product is kept in slice logic.
    (* use_dsp = "no" *) logic [31:0] context_limit43;
    assign context_limit43=32'(context_blocks)*43;
    logic [31:0] replay_bits, raw_position, replay_word;
    logic [31:0] cached_replay_remaining;
    logic [31:0] ctx_data;
    logic [5:0] ctx_bits;
    logic ctx_last, ctx_valid, ctx_ready, ctx_out_valid, ctx_done;
    logic [15:0] ctx_block;
    logic [5:0] ctx_index;
    logic signed [15:0] ctx_coefficient, raw_coefficient;
    logic [31:0] ctx_epoch;
    logic [3:0] ctx_error;
    logic [31:0] unused_consumed;
    logic [63:0] unused_cycles, unused_inputs, unused_symbols, unused_outputs,
        unused_stall, unused_wait, unused_parser_cycles, unused_parser_stall;
    logic [3:0] unused_debug;
    logic [6:0] unused_reservoir;
    logic cancelled, context_failure;

    // Unowned until this packet reaches METADATA; no payload reset.
    logic [31:0] plan_align1, plan_align2, plan_align3;
    logic [31:0] plan_prefix12, plan_prefix123;
    logic prefix_header_capture;
    function automatic logic [31:0] count_aligned(input logic [31:0] n);
        return ((n<<2)+32'd15)&32'hfffffff0;
    endfunction
    assign meta_prefix1=plan_align1;
    assign meta_prefix12=plan_prefix12;
    assign meta_prefix123=plan_prefix123;
    // Match the actual FETCH_WAIT store guard, including wrong-response and
    // active context done/failure priority. Forward the current high byte.
    assign prefix_header_capture=!cancelled&&!context_failure&&
        !(context_active&&ctx_done)&&state==FETCH_WAIT&&stage_read_rsp&&
        ram_epoch==context_epoch&&ram_addr==fetch_address&&fetch_kind==F_HEADER;
    always_ff @(posedge clk)begin
        if(prefix_header_capture)begin
            if(fetch_index==6'd33)plan_align1<=count_aligned({ram_data,fetch_bytes[32],fetch_bytes[31],fetch_bytes[30]});
            if(fetch_index==6'd37)plan_align2<=count_aligned({ram_data,fetch_bytes[36],fetch_bytes[35],fetch_bytes[34]});
            if(fetch_index==6'd41)plan_align3<=count_aligned({ram_data,fetch_bytes[40],fetch_bytes[39],fetch_bytes[38]});
        end
        plan_prefix12<=plan_align1+plan_align2;
        plan_prefix123<=plan_prefix12+plan_align3;
    end


    // COUNT_THRESHOLD_PIPELINE_BEGIN: nine registered positions E0..E8.
    // Capture at WAIT33/37/41; latest commit WAIT45, before HEADER.
    // Private payload has no reset or global CE; validity owns each packet.
    logic [31:0] count_threshold[0:2];
    logic [2:0] threshold_live;
    logic descriptor_count_bad;
    assign meta_threshold1=count_threshold[0];
    assign meta_threshold2=count_threshold[1];
    assign meta_threshold3=count_threshold[2];
    for(genvar tb=0;tb<3;tb=tb+1)begin: threshold_pipes
        localparam integer DIVISOR=tb==0?5:tb==1?15:43;
        localparam integer LAST=33+4*tb;
        localparam logic [31:0] RECIP=32'(64'h100000000/64'(DIVISOR));
        logic [31:0] forwarded_count;
        logic [7:0] valid_pipe;
        logic [31:0] captured_count;
        logic flush, capture;
        function automatic logic [32:0] partial_product(input logic [15:0] a,input logic [16:0] b);
            return a*b;
        endfunction
        (* use_dsp = "yes" *) logic [15:0] mul00_hi;
        (* use_dsp = "yes" *) logic [31:0] mul01, mul10, mul11, check_lo;
        (* use_dsp = "yes" *) logic [15:0] check_hi;
        logic [32:0] cross_s1;
        logic [16:0] cross_carry_s2;
        logic [15:0] low_carry_s1;
        logic [31:0] high_s1, high_s2;
        logic [31:0] n_delay[0:5];
        logic [31:0] q_s3, q_s4, q_s5, q_s6;
        logic [31:0] product_s5, remainder_s6;
        logic [1:0] correction;
        assign forwarded_count={ram_data,fetch_bytes[LAST-1],fetch_bytes[LAST-2],fetch_bytes[LAST-3]};
        assign capture=prefix_header_capture&&fetch_index==6'(LAST);
        assign flush=cancelled||context_failure||(context_active&&ctx_done);
        assign correction=remainder_s6==0?2'd0:(remainder_s6>32'(DIVISOR)?2'd2:2'd1);
        always_ff @(posedge clk)begin
            if(flush)begin valid_pipe<=0;threshold_live[tb]<=0;end
            else begin
                valid_pipe<={valid_pipe[6:0],capture};
                if(valid_pipe[7])threshold_live[tb]<=1;
            end
        end
        always_ff @(posedge clk)begin
            // E0: register the forwarded word before any multiplication.
            captured_count<=forwarded_count;
            // E1: exact unsigned16 x unsigned17 reciprocal products.
            mul00_hi<=16'(partial_product(captured_count[15:0],{1'b0,RECIP[15:0]})>>16);
            mul01<=32'(partial_product(captured_count[15:0],{1'b0,RECIP[31:16]}));
            mul10<=32'(partial_product(captured_count[31:16],{1'b0,RECIP[15:0]}));
            mul11<=32'(partial_product(captured_count[31:16],{1'b0,RECIP[31:16]}));
            n_delay[0]<=captured_count;
            for(integer j=1;j<6;j=j+1)n_delay[j]<=n_delay[j-1];
            // E2/E3: split the three-term cross sum across two edges.
            cross_s1<={1'b0,mul01}+{1'b0,mul10};
            low_carry_s1<=mul00_hi;high_s1<=mul11;
            cross_carry_s2<=17'((cross_s1+{17'd0,low_carry_s1})>>16);high_s2<=high_s1;
            // E4: high32 of n*M, q0 is floor(n/d) or one less.
            q_s3<=high_s2+{15'd0,cross_carry_s2};
            // E5: bounded q0*d, again using16 x17 registered products.
            check_lo<=32'(partial_product(q_s3[15:0],17'(DIVISOR)));
            check_hi<=16'(partial_product(q_s3[31:16],17'(DIVISOR)));q_s4<=q_s3;
            // E6/E7: full product is <=n, so its low32 are exact.
            product_s5<=check_lo+{check_hi,16'd0};q_s5<=q_s4;
            remainder_s6<=n_delay[5]-product_s5;q_s6<=q_s5;
            // E8: one carry chain, with a bounded0/1/2 correction.
            if(valid_pipe[7])count_threshold[tb]<=q_s6+{30'd0,correction};
        end
`ifndef SYNTHESIS
        always_ff @(posedge clk)if(!flush&&valid_pipe[7])begin
            assert(remainder_s6<32'(2*DIVISOR))else $fatal(1,"count reciprocal remainder bound");
        end
`endif
    end
    always_comb begin
        case(band)
            1:descriptor_count_bad=32'(context_blocks)<count_threshold[0];
            2:descriptor_count_bad=32'(context_blocks)<count_threshold[1];
            3:descriptor_count_bad=32'(context_blocks)<count_threshold[2];
            default:descriptor_count_bad=counts[0]>32'(context_blocks);
        endcase
    end
    // COUNT_THRESHOLD_PIPELINE_END


    // CAPACITY_BOUND_PIPELINE_BEGIN: E0 capture through E4 owned commit.
    // P12 is settled before WAIT41. Forward count3's current high byte.
    // Actual plan/start/used_bytes arithmetic remains unchanged downstream.
    logic [27:0] capacity_prefix12_s0, capacity_align3_s0, capacity_prefix_s1;
    logic [27:0] capacity_a_s2, capacity_upper_s3, capacity_lower_s3;
    logic capacity_wrap_s3;
    logic [31:0] capacity_upper, capacity_lower;
    logic capacity_wrap, capacity_live;
    logic [3:0] capacity_valid_pipe;
    logic capacity_capture, capacity_flush;
    assign capacity_capture=prefix_header_capture&&fetch_index==6'd41;
    assign capacity_flush=cancelled||context_failure||(context_active&&ctx_done);
    assign meta_capacity_upper=capacity_upper;
    assign meta_capacity_lower=capacity_lower;
    assign meta_capacity_wrap=capacity_wrap;
    always_ff @(posedge clk)begin
        if(capacity_flush)begin capacity_valid_pipe<=0;capacity_live<=0;end
        else begin
            capacity_valid_pipe<={capacity_valid_pipe[2:0],capacity_capture};
            if(capacity_valid_pipe[3])capacity_live<=1;
        end
    end
    always_ff @(posedge clk)begin
        // E0: capture owned operands separately, with no input carry chain added.
        capacity_prefix12_s0<=plan_prefix12[31:4];
        capacity_align3_s0<=28'(count_aligned({ram_data,fetch_bytes[40],fetch_bytes[39],fetch_bytes[38]})>>4);
        // E1: exact modulo2^28 units; both original low nibbles are zero.
        capacity_prefix_s1<=capacity_prefix12_s0+capacity_align3_s0;
        // E2: add the32-byte scratch header in units of16, modulo2^28.
        capacity_a_s2<=capacity_prefix_s1+28'd2;
        // E3: a normal or wrapped interval; the strict lower bound is essential.
        capacity_upper_s3<=28'd16384-capacity_a_s2;
        capacity_lower_s3<=~capacity_a_s2;
        capacity_wrap_s3<=capacity_a_s2>28'd16384;
        // E4: cache the whole tuple. A simultaneous flush makes it unowned.
        if(capacity_valid_pipe[3])begin
            capacity_upper<={1'b0,capacity_upper_s3,3'd0};
            capacity_lower<={1'b0,capacity_lower_s3,3'd0};
            capacity_wrap<=capacity_wrap_s3;
        end
    end
    // CAPACITY_BOUND_PIPELINE_END

    function automatic logic [31:0] cached32(input integer at);
        cached32={fetch_bytes[at+3],fetch_bytes[at+2],fetch_bytes[at+1],fetch_bytes[at]};
    endfunction
    function automatic logic [31:0] crc_byte(input logic [31:0] previous_crc, input logic [7:0] value);
        logic [31:0] c;
        begin
            c=previous_crc^{24'd0,value};
            for(integer j=0;j<8;j=j+1) c=c[0] ? (c>>1)^32'hedb88320 : c>>1;
            crc_byte=c;
        end
    endfunction
    task automatic fail_packet(input logic [3:0] code);
        begin state<=FAILED; error<=code; done<=0; context_active<=0; word_valid<=0; raw_valid<=0; end
    endtask
    task automatic begin_fetch(input logic [2:0] kind, input logic [5:0] bytes_to_fetch,
                               input logic [31:0] base, input logic [3:0] continuation);
        begin
            fetch_kind<=kind; fetch_count<=bytes_to_fetch; fetch_index<=0;
            fetch_base<=base; fetch_return<=continuation; buffer_bytes<=0; state<=FETCH_REQ;
        end
    endtask

    always_comb begin
        cancelled=reset || abort_packet || start;
        context_failure=context_active && ctx_error!=0;
        in_ready=state==RECEIVE && !cancelled;
        fetch_address=fetch_base+32'(fetch_index);
        if(fetch_kind==F_HEADER && fetch_index>=42) fetch_address=size_bytes-4+32'(fetch_index)-42;
        if(fetch_kind==F_DESCRIPTOR && fetch_index==6) fetch_address=fetch_base+lengths[band]-1;
        stage_read_req=state==FETCH_REQ && !cancelled && fetch_address<size_bytes &&
            fetch_address<32'(MAX_PACKET_BYTES) && !(context_active && (ctx_error!=0 || ctx_done));
        stage_read_rsp=ram_valid && !cancelled && !context_failure;
        stage_write=in_valid && in_ready;
        stage_pending=state==FETCH_WAIT;
        stage_context_active=context_active; stage_cancel=cancelled || context_failure;
        stage_read_addr=fetch_address; stage_rsp_addr=ram_addr; stage_write_addr=received;
        stage_req_epoch=context_epoch; stage_rsp_epoch=ram_epoch;
        stage_read_data=ram_data; stage_write_data=in_data;
        stage_buffer_bytes=buffer_bytes; stage_purpose=fetch_kind;
        descriptor_bits=cached32(2);
        descriptor_bytes=(descriptor_bits>>3)+32'(descriptor_bits[2:0]!=0);
        case(band)
            1: descriptor_limit=32'(context_blocks)*5;
            2: descriptor_limit=32'(context_blocks)*15;
            3: descriptor_limit=context_limit43;
            default: descriptor_limit=32'(context_blocks);
        endcase
        fetched_word=0;
        for(integer j=0;j<4;j=j+1)
            if(j<integer'(fetch_count))
                fetched_word[31-8*j-:8]=(j==integer'(fetch_index)) ? ram_data : fetch_bytes[j];
        ctx_data=replay_word;
        ctx_bits=6'(cached_replay_remaining<(mode16 ? 16 : 32) ? cached_replay_remaining : (mode16 ? 16 : 32));
        ctx_last=cached_replay_remaining==32'(ctx_bits);
        ctx_valid=state==CONTEXT_RUN && word_valid && replay_bits<sizes[band] && !cancelled && !context_failure;
        stage_word_valid=ctx_valid; stage_word_ready=ctx_ready;
        out_valid=!cancelled && ((context_active && ctx_out_valid) ||
            (state==RAW && raw_valid && raw_coefficient>=-2048 && raw_coefficient<=2048));
        out_block=raw_mode ? 16'(raw_position>>6) : ctx_block;
        out_index=raw_mode ? raw_position[5:0] : ctx_index;
        out_coefficient=raw_mode ? raw_coefficient : ctx_coefficient;
        out_epoch=raw_mode ? context_epoch : ctx_epoch;
        meta_valid=state==METADATA && !cancelled;
        meta_blocks=context_blocks; meta_count1=counts[1]; meta_count2=counts[2]; meta_count3=counts[3];
        meta_epoch=context_epoch; meta_raw=raw_mode;
        out_band=raw_mode ? 2'd0 : band;
        band_end_valid=(state==CONTEXT_END || state==RAW_END) && !cancelled;
        band_end_band=state==RAW_END ? 2'd0 : band;
        band_end_epoch=context_epoch;
        debug_state=state;
    end

    // One byte write port and one byte synchronous read port. No backing-array
    // reset, combinational lookup, replicated read lane or software byte access.
    always_ff @(posedge clk) begin
        if(stage_write) memory[AW'(received)]<=in_data;
        if(cancelled || context_failure) ram_valid<=0;
        else begin
            ram_valid<=stage_read_req;
            if(stage_read_req) begin
                ram_data<=memory[AW'(fetch_address)]; ram_addr<=fetch_address; ram_epoch<=context_epoch;
            end
        end
    end

    br88_context context_decoder (
        .clk(clk), .reset(reset), .start(state==CONTEXT_START && !cancelled),
        .abort_context(abort_packet || start), .blocks(context_blocks),
        .band({6'd0,band}), .k0(k0s[band]), .k1(k1s[band]),
        .event_count(counts[band]), .stream_bits(sizes[band]), .epoch(context_epoch),
        .word16(mode16), .serial_mode(mode_serial), .in_valid(ctx_valid), .in_ready(ctx_ready),
        .in_data(ctx_data), .in_bits(ctx_bits), .in_last(ctx_last),
        .out_valid(ctx_out_valid), .out_ready(out_ready && context_active && !cancelled),
        .out_block(ctx_block), .out_index(ctx_index), .out_coefficient(ctx_coefficient),
        .out_epoch(ctx_epoch), .done(ctx_done), .error(ctx_error),
        .consumed_bits(unused_consumed), .count_cycles(unused_cycles), .count_inputs(unused_inputs),
        .count_symbols(unused_symbols), .count_outputs(unused_outputs),
        .count_output_stall(unused_stall), .count_input_wait(unused_wait),
        .count_parser_cycles(unused_parser_cycles), .count_parser_output_stall(unused_parser_stall),
        .debug_state(unused_debug), .reservoir_bits(unused_reservoir)
    );

    always_ff @(posedge clk) begin
        if(reset || abort_packet) begin
            state<=IDLE; size_bytes<=0; context_epoch<=0; context_blocks<=0;
            received<=0; crc<=32'hffffffff; cursor<=0; band<=0;
            mode16<=0; mode_serial<=0; raw_mode<=0; replay_bits<=0; raw_position<=0;
            cached_replay_remaining<=0;
            descriptor_ready<=0; word_valid<=0; raw_valid<=0; context_active<=0;
            fetch_kind<=F_HEADER; fetch_count<=0; fetch_index<=0; fetch_base<=0; fetch_return<=IDLE;
            replay_word<=0; raw_coefficient<=0; buffer_bytes<=0; stage_buffer_highwater<=0;
            done<=0; error<=0; count_cycles<=0; count_inputs<=0; count_outputs<=0; count_output_stall<=0;
            count_stage_reads<=0; count_stage_responses<=0; count_stage_writes<=0;
            count_stage_fetch_wait<=0; count_stage_word_hold<=0;
            for(integer j=0;j<46;j=j+1) fetch_bytes[j]<=0;
            for(integer j=0;j<4;j=j+1) begin
                lengths[j]<=0; counts[j]<=0; offsets[j]<=0; sizes[j]<=0; k0s[j]<=0; k1s[j]<=0;
            end
        end else if(start) begin
            size_bytes<=packet_bytes; context_epoch<=epoch; context_blocks<=blocks;
            mode16<=word16; mode_serial<=serial_mode; raw_mode<=0; received<=0; crc<=32'hffffffff;
            cursor<=42; band<=0; replay_bits<=0; raw_position<=0;
            cached_replay_remaining<=0;
            descriptor_ready<=0; word_valid<=0; raw_valid<=0; context_active<=0;
            fetch_kind<=F_HEADER; fetch_count<=0; fetch_index<=0; fetch_base<=0; fetch_return<=IDLE;
            replay_word<=0; raw_coefficient<=0; buffer_bytes<=0; stage_buffer_highwater<=0;
            done<=0; error<=0; count_cycles<=0; count_inputs<=0; count_outputs<=0; count_output_stall<=0;
            count_stage_reads<=0; count_stage_responses<=0; count_stage_writes<=0;
            count_stage_fetch_wait<=0; count_stage_word_hold<=0;
            if(blocks==0 || blocks>65536 || packet_bytes<46 ||
                packet_bytes>32'(MAX_PACKET_BYTES) || packet_bytes>46+128*32'(blocks)) begin
                state<=FAILED; error<=1;
            end else state<=RECEIVE;
        end else if(state!=IDLE && state!=FINISHED && state!=FAILED) begin
            count_cycles<=count_cycles+1'b1;
            if(stage_read_req) count_stage_reads<=count_stage_reads+1'b1;
            if(stage_read_rsp) count_stage_responses<=count_stage_responses+1'b1;
            if(stage_write) count_stage_writes<=count_stage_writes+1'b1;
            if(state==FETCH_WAIT) count_stage_fetch_wait<=count_stage_fetch_wait+1'b1;
            if(ctx_valid && !ctx_ready) count_stage_word_hold<=count_stage_word_hold+1'b1;
            if(out_valid && !out_ready) count_output_stall<=count_output_stall+1'b1;
            if(out_valid && out_ready) count_outputs<=count_outputs+1'b1;
            if(context_active && ctx_error!=0) fail_packet(ctx_error);
            else if(context_active && ctx_done) begin
                context_active<=0; word_valid<=0; state<=CONTEXT_END;
            end else case(state)
                RECEIVE: if(in_valid && in_ready) begin
                    received<=received+1'b1; count_inputs<=count_inputs+1'b1;
                    if(received<size_bytes-4) crc<=crc_byte(crc,in_data);
                    if(in_last!=(received+1==size_bytes)) fail_packet(2);
                    else if(received+1==size_bytes) begin_fetch(F_HEADER,46,0,HEADER);
                end
                HEADER: begin
                    if((crc^32'hffffffff)!=cached32(42)) fail_packet(3);
                    else if(cached32(0)!=32'h38385242 || fetch_bytes[4]!=1 || fetch_bytes[5]>1 ||
                        cached32(6)!=32'(context_blocks) || {fetch_bytes[11],fetch_bytes[10]}!=1 ||
                        {fetch_bytes[13],fetch_bytes[12]}!=0) fail_packet(4);
                    else if({2'd0,cached32(14)}+{2'd0,cached32(18)}+{2'd0,cached32(22)}+{2'd0,cached32(26)}!=({2'd0,size_bytes}-34'd46)) fail_packet(4);
                    else begin
                        for(integer j=0;j<4;j=j+1) lengths[j]<=cached32(14+j*4);
                        counts[0]<=32'(context_blocks); raw_mode<=fetch_bytes[5]==1;
                        for(integer j=1;j<4;j=j+1) counts[j]<=cached32(26+j*4);
                        if(fetch_bytes[5]==1) begin
                            if(cached32(14)!=128*32'(context_blocks) || cached32(18)!=0 || cached32(22)!=0 || cached32(26)!=0 ||
                                cached32(30)!=0 || cached32(34)!=0 || cached32(38)!=0) fail_packet(4);
                            else state<=METADATA;
                        end else state<=DESCRIPTOR;
                    end
                end
                DESCRIPTOR: begin
                    if(!descriptor_ready) begin
                        if(lengths[band]<6 || cursor>size_bytes-4 || lengths[band]>size_bytes-4-cursor) fail_packet(4);
                        else begin_fetch(F_DESCRIPTOR,7,cursor,DESCRIPTOR);
                    end else begin
                        descriptor_ready<=0;
                        if(descriptor_bytes!=lengths[band]-6 || descriptor_bits>8*(size_bytes-46)) fail_packet(4);
                        else if((band==0 && (fetch_bytes[0]>13 || fetch_bytes[1]!=255)) ||
                            (band!=0 && (fetch_bytes[0]>19 || fetch_bytes[1]>11 || descriptor_count_bad))) fail_packet(4);
                        else if(band!=0 && counts[band]==0 && descriptor_bits!=0) fail_packet(7);
                        else if(descriptor_bits[2:0]!=0 && (fetch_bytes[6] & (8'hff >> descriptor_bits[2:0]))!=0) fail_packet(7);
                        else begin
                            k0s[band]<=fetch_bytes[0]; k1s[band]<=fetch_bytes[1];
                            sizes[band]<=descriptor_bits; offsets[band]<=cursor+6;
                            cursor<=cursor+lengths[band];
                            if(band==3) begin band<=0; state<=METADATA; end
                            else band<=band+1'b1;
                        end
                    end
                end
                METADATA: if(meta_valid && meta_ready) state<=raw_mode ? RAW : CONTEXT_START;
                CONTEXT_START: begin replay_bits<=0; cached_replay_remaining<=sizes[band]; word_valid<=0; context_active<=1; state<=CONTEXT_RUN; end
                CONTEXT_RUN: begin
                    if(ctx_valid && ctx_ready) begin replay_bits<=replay_bits+32'(ctx_bits); cached_replay_remaining<=cached_replay_remaining-32'(ctx_bits); word_valid<=0; end
                    else if(!word_valid && replay_bits<sizes[band])
                        begin_fetch(F_REPLAY,6'((32'(ctx_bits)+7)>>3),offsets[band]+(replay_bits>>3),CONTEXT_RUN);
                end
                RAW: begin
                    if(!raw_valid) begin_fetch(F_RAW,2,42+2*raw_position,RAW);
                    else if(raw_coefficient < -2048 || raw_coefficient > 2048) fail_packet(5);
                    else if(out_valid && out_ready) begin
                        raw_valid<=0; raw_position<=raw_position+1'b1;
                        if(raw_position+1==32'(context_blocks)*64) state<=RAW_END;
                    end
                end
                FETCH_REQ: begin
                    if(stage_read_req) state<=FETCH_WAIT;
                    else if(fetch_address>=size_bytes || fetch_address>=32'(MAX_PACKET_BYTES)) fail_packet(4);
                end
                FETCH_WAIT: if(stage_read_rsp) begin
                    if(ram_epoch!=context_epoch || ram_addr!=fetch_address) fail_packet(4);
                    else begin
                        fetch_bytes[fetch_index]<=ram_data; buffer_bytes<=fetch_index+1'b1;
                        if(fetch_index+1'b1>stage_buffer_highwater) stage_buffer_highwater<=fetch_index+1'b1;
                        if(fetch_index+6'd1==fetch_count) begin
                            if(fetch_kind==F_DESCRIPTOR) descriptor_ready<=1;
                            if(fetch_kind==F_REPLAY) begin replay_word<=fetched_word; word_valid<=1; end
                            if(fetch_kind==F_RAW) begin raw_coefficient<=$signed({ram_data,fetch_bytes[0]}); raw_valid<=1; end
                            state<=fetch_return;
                        end else begin fetch_index<=fetch_index+1'b1; state<=FETCH_REQ; end
                    end
                end
                CONTEXT_END: if(band_end_valid && band_end_ready) begin
                    if(band==3) begin done<=1; state<=FINISHED; end
                    else begin band<=band+1'b1; state<=CONTEXT_START; end
                end
                RAW_END: if(band_end_valid && band_end_ready) begin done<=1; state<=FINISHED; end
                default: fail_packet(4);
            endcase
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
    always_ff @(posedge clk)if(meta_valid)begin
        assert(capacity_live)else $fatal(1,"capacity bounds not live before metadata");
        assert(meta_prefix123[3:0]==0)else $fatal(1,"capacity prefix unit alignment");
        assert(meta_capacity_upper==capacity_expected_upper(meta_prefix123[31:4]))else $fatal(1,"capacity upper stale owner");
        assert(meta_capacity_lower==capacity_expected_lower(meta_prefix123[31:4]))else $fatal(1,"capacity lower stale owner");
        assert(meta_capacity_wrap==capacity_expected_wrap(meta_prefix123[31:4]))else $fatal(1,"capacity wrap stale owner");
    end
    assert property (@(posedge clk)disable iff(cancelled)
        meta_valid&&!meta_ready |=> cancelled || (meta_valid&&$stable({meta_capacity_upper,meta_capacity_lower,meta_capacity_wrap})))
        else $fatal(1,"held capacity tuple changed");
    always_ff @(posedge clk)if(meta_valid)begin
        assert(&threshold_live)else $fatal(1,"count threshold not live before metadata");
        assert(meta_threshold1==meta_count1/32'd5+32'(meta_count1%32'd5!=0))else $fatal(1,"count threshold1 stale owner");
        assert(meta_threshold2==meta_count2/32'd15+32'(meta_count2%32'd15!=0))else $fatal(1,"count threshold2 stale owner");
        assert(meta_threshold3==meta_count3/32'd43+32'(meta_count3%32'd43!=0))else $fatal(1,"count threshold3 stale owner");
    end
    always_ff @(posedge clk)if(!cancelled&&!context_failure&&!(context_active&&ctx_done)&&state==DESCRIPTOR&&band!=0)begin
        assert(threshold_live[band-1'b1])else $fatal(1,"descriptor count threshold not live");
        assert(descriptor_count_bad==(counts[band]>descriptor_limit))else $fatal(1,"descriptor count threshold mismatch");
    end
    assert property (@(posedge clk) disable iff(cancelled)
        meta_valid&&!meta_ready |=> cancelled || (meta_valid&&$stable({meta_threshold1,meta_threshold2,meta_threshold3})))
        else $fatal(1,"held count threshold changed");
    always_ff @(posedge clk)if(meta_valid)begin
        assert(meta_prefix1==count_aligned(meta_count1))else $fatal(1,"prefix1 stale metadata owner");
        assert(meta_prefix12==count_aligned(meta_count1)+count_aligned(meta_count2))else $fatal(1,"prefix12 stale metadata owner");
        assert(meta_prefix123==count_aligned(meta_count1)+count_aligned(meta_count2)+count_aligned(meta_count3))else $fatal(1,"prefix123 stale metadata owner");
    end
    assert property (@(posedge clk)disable iff(cancelled)
        meta_valid&&!meta_ready |=> cancelled || (meta_valid&&$stable({meta_prefix1,meta_prefix12,meta_prefix123})))
        else $fatal(1,"held metadata prefixes changed");
    always_ff @(posedge clk) if(!cancelled) begin
        if(state==CONTEXT_RUN)
            assert(cached_replay_remaining==sizes[band]-replay_bits) else $fatal(1,"live replay remaining cache");
        assert(received<=size_bytes) else $fatal(1,"packet staging overflow");
        assert(!done || (!out_valid && state==FINISHED)) else $fatal(1,"completion credit fence");
        assert(count_outputs<=64'(context_blocks)*64) else $fatal(1,"coefficient credit overflow");
        assert(!stage_read_req || (!stage_write && fetch_address<size_bytes && fetch_address<32'(MAX_PACKET_BYTES)))
            else $fatal(1,"staging port request bound");
        assert(!stage_read_rsp || (state==FETCH_WAIT && ram_epoch==context_epoch && ram_addr==fetch_address))
            else $fatal(1,"stale staging response");
        assert(buffer_bytes<=46) else $fatal(1,"staging register cache overflow");
    end
    assert property (@(posedge clk) disable iff(cancelled)
        out_valid && !out_ready |=> out_valid && $stable({out_band,out_block,out_index,out_coefficient,out_epoch}) || cancelled);
`endif
endmodule
