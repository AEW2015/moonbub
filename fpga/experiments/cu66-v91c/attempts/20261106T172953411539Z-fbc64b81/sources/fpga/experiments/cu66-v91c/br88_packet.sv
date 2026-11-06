// Bounded complete-packet staging and autonomous BR88 context replay.
// Outputs are provisional until done; consumer supplies implicit zero semantics.
module br88_packet #(
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
    output logic done,
    output logic [3:0] error,
    output logic [63:0] count_cycles, count_inputs, count_outputs,
    output logic [63:0] count_output_stall,
    output logic [3:0] debug_state
);
    localparam logic [3:0] IDLE=0, RECEIVE=1, HEADER=2, DESCRIPTOR=3,
        CONTEXT_START=4, CONTEXT_RUN=5, RAW=6, FINISHED=7, FAILED=8;
    logic [3:0] state;
    logic [7:0] memory [0:MAX_PACKET_BYTES-1];
    logic [31:0] size_bytes, context_epoch, received, crc, cursor;
    logic [16:0] context_blocks;
    logic mode16, mode_serial;
    logic [1:0] band;
    logic [31:0] lengths[0:3], counts[0:3], offsets[0:3], sizes[0:3];
    logic [7:0] k0s[0:3], k1s[0:3];
    logic [31:0] descriptor_bits, descriptor_bytes, descriptor_limit;
    logic [31:0] replay_bits, raw_position;
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
    logic cancelled;

    function automatic logic [31:0] le32(input logic [31:0] at);
        le32={memory[at+3],memory[at+2],memory[at+1],memory[at]};
    endfunction
    function automatic logic [31:0] crc_byte(input logic [31:0] previous_crc, input logic [7:0] value);
        logic [31:0] c;
        begin
            c=previous_crc^{24'd0,value};
            for(integer j=0;j<8;j=j+1) c=c[0] ? (c>>1)^32'hedb88320 : c>>1;
            crc_byte=c;
        end
    endfunction
    always_comb begin
        cancelled=reset || abort_packet || start;
        in_ready=state==RECEIVE && !cancelled;
        descriptor_bits=le32(cursor+2);
        descriptor_bytes=(descriptor_bits>>3)+32'(descriptor_bits[2:0]!=0);
        case(band)
            1: descriptor_limit=32'(context_blocks)*5;
            2: descriptor_limit=32'(context_blocks)*15;
            3: descriptor_limit=32'(context_blocks)*43;
            default: descriptor_limit=32'(context_blocks);
        endcase
        ctx_data=0;
        ctx_bits=6'((sizes[band]-replay_bits)<(mode16 ? 16 : 32) ? sizes[band]-replay_bits : (mode16 ? 16 : 32));
        for(integer j=0;j<32;j=j+1)
            if(j<32'(ctx_bits) && state==CONTEXT_RUN)
                ctx_data[31-j]=memory[offsets[band]+((replay_bits+32'(j))>>3)][7-((replay_bits+32'(j))&7)];
        ctx_last=replay_bits+32'(ctx_bits)==sizes[band];
        ctx_valid=state==CONTEXT_RUN && replay_bits<sizes[band] && !cancelled;
        raw_coefficient=$signed({memory[42+2*raw_position+1],memory[42+2*raw_position]});
        out_valid=!cancelled && ((state==CONTEXT_RUN && ctx_out_valid) ||
            (state==RAW && raw_coefficient>=-2048 && raw_coefficient<=2048));
        out_block=state==RAW ? 16'(raw_position>>6) : ctx_block;
        out_index=state==RAW ? raw_position[5:0] : ctx_index;
        out_coefficient=state==RAW ? raw_coefficient : ctx_coefficient;
        out_epoch=state==RAW ? context_epoch : ctx_epoch;
        debug_state=state;
    end

    br88_context context_decoder (
        .clk(clk), .reset(reset), .start(state==CONTEXT_START && !cancelled),
        .abort_context(abort_packet || start), .blocks(context_blocks),
        .band({6'd0,band}), .k0(k0s[band]), .k1(k1s[band]),
        .event_count(counts[band]), .stream_bits(sizes[band]), .epoch(context_epoch),
        .word16(mode16), .serial_mode(mode_serial), .in_valid(ctx_valid), .in_ready(ctx_ready),
        .in_data(ctx_data), .in_bits(ctx_bits), .in_last(ctx_last),
        .out_valid(ctx_out_valid), .out_ready(out_ready && state==CONTEXT_RUN && !cancelled),
        .out_block(ctx_block), .out_index(ctx_index), .out_coefficient(ctx_coefficient),
        .out_epoch(ctx_epoch), .done(ctx_done), .error(ctx_error),
        .consumed_bits(unused_consumed), .count_cycles(unused_cycles), .count_inputs(unused_inputs),
        .count_symbols(unused_symbols), .count_outputs(unused_outputs),
        .count_output_stall(unused_stall), .count_input_wait(unused_wait),
        .count_parser_cycles(unused_parser_cycles), .count_parser_output_stall(unused_parser_stall),
        .debug_state(unused_debug), .reservoir_bits(unused_reservoir)
    );
    task automatic fail_packet(input logic [3:0] code);
        begin state<=FAILED; error<=code; done<=0; end
    endtask
    always_ff @(posedge clk) begin
        if(reset || abort_packet) begin
            state<=IDLE; size_bytes<=0; context_epoch<=0; context_blocks<=0;
            received<=0; crc<=32'hffffffff; cursor<=0; band<=0;
            mode16<=0; mode_serial<=0; replay_bits<=0; raw_position<=0;
            done<=0; error<=0; count_cycles<=0; count_inputs<=0;
            count_outputs<=0; count_output_stall<=0;
            for(integer j=0;j<4;j=j+1) begin
                lengths[j]<=0; counts[j]<=0; offsets[j]<=0; sizes[j]<=0; k0s[j]<=0; k1s[j]<=0;
            end
        end else if(start) begin
            size_bytes<=packet_bytes; context_epoch<=epoch; context_blocks<=blocks;
            mode16<=word16; mode_serial<=serial_mode; received<=0; crc<=32'hffffffff;
            cursor<=42; band<=0; replay_bits<=0; raw_position<=0;
            done<=0; error<=0; count_cycles<=0; count_inputs<=0;
            count_outputs<=0; count_output_stall<=0;
            if(blocks==0 || blocks>65536 || packet_bytes<46 ||
                packet_bytes>32'(MAX_PACKET_BYTES) || packet_bytes>46+128*32'(blocks)) begin
                state<=FAILED; error<=1;
            end else state<=RECEIVE;
        end else if(state!=IDLE && state!=FINISHED && state!=FAILED) begin
            count_cycles<=count_cycles+1'b1;
            if(out_valid && !out_ready) count_output_stall<=count_output_stall+1'b1;
            if(out_valid && out_ready) count_outputs<=count_outputs+1'b1;
            case(state)
                RECEIVE: if(in_valid && in_ready) begin
                    memory[received]<=in_data; received<=received+1'b1; count_inputs<=count_inputs+1'b1;
                    if(received<size_bytes-4) crc<=crc_byte(crc,in_data);
                    if(in_last!=(received+1==size_bytes)) fail_packet(2);
                    else if(received+1==size_bytes) state<=HEADER;
                end
                HEADER: begin
                    if((crc^32'hffffffff)!=le32(size_bytes-4)) fail_packet(3);
                    else if(le32(0)!=32'h38385242 || memory[4]!=1 || memory[5]>1 ||
                        le32(6)!=32'(context_blocks) || {memory[11],memory[10]}!=1 ||
                        {memory[13],memory[12]}!=0) fail_packet(4);
                    else if({2'd0,le32(14)}+{2'd0,le32(18)}+{2'd0,le32(22)}+{2'd0,le32(26)}!=34'(size_bytes-46)) fail_packet(4);
                    else begin
                        for(integer j=0;j<4;j=j+1) lengths[j]<=le32(14+32'(j)*4);
                        counts[0]<=32'(context_blocks);
                        for(integer j=1;j<4;j=j+1) counts[j]<=le32(26+32'(j)*4);
                        if(memory[5]==1) begin
                            if(le32(14)!=128*32'(context_blocks) || le32(18)!=0 || le32(22)!=0 || le32(26)!=0 ||
                                le32(30)!=0 || le32(34)!=0 || le32(38)!=0) fail_packet(4);
                            else state<=RAW;
                        end else state<=DESCRIPTOR;
                    end
                end
                DESCRIPTOR: begin
                    if(lengths[band]<6 || cursor>size_bytes-4 || lengths[band]>size_bytes-4-cursor) fail_packet(4);
                    else if(descriptor_bytes!=lengths[band]-6 || descriptor_bits>8*(size_bytes-46)) fail_packet(4);
                    else if((band==0 && (memory[cursor]>13 || memory[cursor+1]!=255)) ||
                        (band!=0 && (memory[cursor]>19 || memory[cursor+1]>11 || counts[band]>descriptor_limit))) fail_packet(4);
                    else if(band!=0 && counts[band]==0 && descriptor_bits!=0) fail_packet(7);
                    else if(descriptor_bits[2:0]!=0 &&
                        (memory[cursor+lengths[band]-1] & (8'hff >> descriptor_bits[2:0]))!=0) fail_packet(7);
                    else begin
                        k0s[band]<=memory[cursor]; k1s[band]<=memory[cursor+1];
                        sizes[band]<=descriptor_bits; offsets[band]<=cursor+6;
                        cursor<=cursor+lengths[band];
                        if(band==3) begin band<=0; state<=CONTEXT_START; end
                        else band<=band+1'b1;
                    end
                end
                CONTEXT_START: begin replay_bits<=0; state<=CONTEXT_RUN; end
                CONTEXT_RUN: begin
                    if(ctx_valid && ctx_ready) replay_bits<=replay_bits+32'(ctx_bits);
                    if(ctx_error!=0) fail_packet(ctx_error);
                    else if(ctx_done) begin
                        if(band==3) begin done<=1; state<=FINISHED; end
                        else begin band<=band+1'b1; state<=CONTEXT_START; end
                    end
                end
                RAW: begin
                    if(raw_coefficient < -2048 || raw_coefficient > 2048) fail_packet(5);
                    else if(out_valid && out_ready) begin
                        raw_position<=raw_position+1'b1;
                        if(raw_position+1==32'(context_blocks)*64) begin done<=1; state<=FINISHED; end
                    end
                end
                default: fail_packet(4);
            endcase
        end
    end
`ifndef SYNTHESIS
    always_ff @(posedge clk) if(!cancelled) begin
        assert(received<=size_bytes) else $fatal(1,"packet staging overflow");
        assert(!done || (!out_valid && state==FINISHED)) else $fatal(1,"completion credit fence");
        assert(!(out_valid && state!=RAW && state!=CONTEXT_RUN)) else $fatal(1,"output before validation");
        assert(count_outputs<=64'(context_blocks)*64) else $fatal(1,"coefficient credit overflow");
    end
`endif
endmodule
