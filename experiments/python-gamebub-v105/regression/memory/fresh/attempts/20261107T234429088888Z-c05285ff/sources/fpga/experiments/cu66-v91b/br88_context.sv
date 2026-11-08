// One validated BR88 context. Sparse outputs remain speculative until done.
module br88_context (
    input logic clk, reset, start, abort_context,
    input logic [16:0] blocks,
    input logic [7:0] band, k0, k1,
    input logic [31:0] event_count, stream_bits, epoch,
    input logic word16, serial_mode,
    input logic in_valid,
    output logic in_ready,
    input logic [31:0] in_data,
    input logic [5:0] in_bits,
    input logic in_last,
    output logic out_valid,
    input logic out_ready,
    output logic [15:0] out_block,
    output logic [5:0] out_index,
    output logic signed [15:0] out_coefficient,
    output logic [31:0] out_epoch,
    output logic done,
    output logic [3:0] error,
    output logic [31:0] consumed_bits,
    output logic [63:0] count_cycles, count_inputs, count_symbols,
    output logic [63:0] count_outputs, count_output_stall, count_input_wait,
    output logic [63:0] count_parser_cycles, count_parser_output_stall,
    output logic [3:0] debug_state,
    output logic [6:0] reservoir_bits
);
    localparam logic [3:0] IDLE=0, REQ_DC=1, WAIT_DC=2, REQ_RUN=3,
        WAIT_RUN=4, REQ_LEVEL=5, WAIT_LEVEL=6, HELD=7, FINISHED=8, FAILED=9;
    localparam logic [5:0] ZIGZAG [0:63]='{6'd0,6'd1,6'd8,6'd16,6'd9,6'd2,6'd3,6'd10,6'd17,6'd24,6'd32,6'd25,6'd18,6'd11,6'd4,6'd5,6'd12,6'd19,6'd26,6'd33,6'd40,6'd48,6'd41,6'd34,6'd27,6'd20,6'd13,6'd6,6'd7,6'd14,6'd21,6'd28,6'd35,6'd42,6'd49,6'd56,6'd57,6'd50,6'd43,6'd36,6'd29,6'd22,6'd15,6'd23,6'd30,6'd37,6'd44,6'd51,6'd58,6'd59,6'd52,6'd45,6'd38,6'd31,6'd39,6'd46,6'd53,6'd60,6'd61,6'd54,6'd47,6'd55,6'd62,6'd63};
    logic [3:0] state;
    logic [7:0] context_band;
    logic [4:0] run_k, level_k;
    logic [31:0] size_bits, context_epoch, target, emitted, position, limit;
    logic [15:0] sparse_block;
    logic [5:0] sparse_index;
    logic active, req_valid, req_ready, parser_valid, parser_ready, parser_in_ready;
    logic [4:0] req_k, req_escape;
    logic [23:0] parser_value;
    logic [31:0] parser_consumed;
    logic [3:0] parser_error;
    logic [63:0] parser_bits;
    logic [32:0] next_position;
    logic [24:0] unsigned_coefficient;
    logic signed [25:0] signed_coefficient;
    logic [5:0] start_width;
    logic [31:0] start_limit;

    always_comb begin
        case (band)
            1: begin start_width=5; end
            2: begin start_width=15; end
            3: begin start_width=43; end
            default: begin start_width=1; end
        endcase
        start_limit=32'(blocks)*32'(start_width);
        // Literal divisors permit constant arithmetic implementation; this is
        // behavioral RTL evidence only, without synthesis/resource claims.
        case(context_band)
            1: begin sparse_block=16'(position/32'd5); sparse_index=ZIGZAG[6'(32'd1+position%32'd5)]; end
            2: begin sparse_block=16'(position/32'd15); sparse_index=ZIGZAG[6'(32'd6+position%32'd15)]; end
            3: begin sparse_block=16'(position/32'd43); sparse_index=ZIGZAG[6'(32'd21+position%32'd43)]; end
            default: begin sparse_block=16'(emitted); sparse_index=0; end
        endcase
        active=state!=IDLE && state!=FINISHED && state!=FAILED;
        req_valid=active && (state==REQ_DC || state==REQ_RUN || state==REQ_LEVEL) && !start && !abort_context && !reset;
        req_k=state==REQ_LEVEL ? level_k : run_k;
        req_escape=state==REQ_DC ? 5'd14 : (state==REQ_RUN ? 5'd24 : 5'd12);
        parser_ready=(state==WAIT_DC || state==WAIT_RUN || state==WAIT_LEVEL) && !start && !abort_context && !reset;
        next_position={1'b0,position}+33'(parser_value)+1'b1;
        unsigned_coefficient={1'b0,parser_value}+(state==WAIT_LEVEL ? 25'd1 : 25'd0);
        signed_coefficient=unsigned_coefficient[0] ? -(26'(unsigned_coefficient)>>1)-26'sd1 : (26'(unsigned_coefficient)>>1);
        consumed_bits=32'(parser_bits);
        debug_state=state;
    end

    assign in_ready=parser_in_ready && active && !start && !abort_context && !reset;

    br88_rice_elastic parser (
        .clk(clk), .reset(reset || abort_context), .stream_start(start && !abort_context),
        .stream_bits(stream_bits), .word16(word16), .serial_mode(serial_mode),
        .in_valid(in_valid && active && !start && !abort_context), .in_ready(parser_in_ready),
        .in_data(in_data), .in_bits(in_bits), .in_last(in_last),
        .req_valid(req_valid), .req_ready(req_ready), .req_k(req_k), .req_escape(req_escape),
        .out_valid(parser_valid), .out_ready(parser_ready), .out_value(parser_value),
        .out_consumed(parser_consumed), .out_error(parser_error), .count_cycles(count_parser_cycles),
        .count_inputs(count_inputs), .count_symbols(count_symbols), .count_bits(parser_bits),
        .count_input_wait(count_input_wait), .count_output_stall(count_parser_output_stall), .reservoir_bits(reservoir_bits)
    );

    task automatic fail_context(input logic [3:0] code);
        begin error<=code; state<=FAILED; out_valid<=0; done<=0; end
    endtask

    always_ff @(posedge clk) begin
        if (reset || abort_context) begin
            state<=IDLE; context_band<=0; run_k<=0; level_k<=0; size_bits<=0;
            context_epoch<=0; target<=0; emitted<=0; position<=0; limit<=0;
            out_valid<=0; out_block<=0; out_index<=0;
            out_coefficient<=0; out_epoch<=0; done<=0; error<=0;
            count_cycles<=0; count_outputs<=0; count_output_stall<=0;
        end else if (start) begin
            context_band<=band; run_k<=k0[4:0]; level_k<=k1[4:0]; size_bits<=stream_bits;
            context_epoch<=epoch; target<=band==0 ? 32'(blocks) : event_count;
            emitted<=0; position<=32'hffffffff; limit<=start_limit;
            out_valid<=0; out_block<=0;
            out_index<=0; out_coefficient<=0; out_epoch<=epoch; done<=0; error<=0;
            count_cycles<=0; count_outputs<=0; count_output_stall<=0;
            if (blocks==0 || blocks>65536 || band>3 ||
                (band==0 && (k0>13 || k1!=255 || event_count!=32'(blocks))) ||
                (band!=0 && (k0>19 || k1>11 || event_count>start_limit))) begin
                state<=FAILED; error<=4;
            end else if (band!=0 && event_count==0) begin
                if (stream_bits!=0) begin state<=FAILED; error<=7; end
                else begin state<=FINISHED; done<=1; end
            end else state<=band==0 ? REQ_DC : REQ_RUN;
        end else if (active) begin
            count_cycles<=count_cycles+1'b1;
            if (out_valid && !out_ready) count_output_stall<=count_output_stall+1'b1;
            if (req_valid && req_ready) begin
                case(state)
                    REQ_DC: state<=WAIT_DC;
                    REQ_RUN: state<=WAIT_RUN;
                    default: state<=WAIT_LEVEL;
                endcase
            end
            if (parser_valid && parser_ready) begin
                if (parser_error!=0) fail_context(parser_error);
                else if (state==WAIT_RUN) begin
                    // The initial -1 is represented as all ones; use a separate
                    // first-event expression so the carry never wraps a bad run.
                    if ((emitted==0 ? 33'(parser_value) : next_position)>=33'(limit)) fail_context(6);
                    else begin
                        position<=emitted==0 ? 32'(parser_value) : 32'(next_position);
                        state<=REQ_LEVEL;
                    end
                end else if (signed_coefficient < -2048 || signed_coefficient > 2048 ||
                             (state==WAIT_LEVEL && signed_coefficient==0)) fail_context(5);
                else if (emitted+1==target && parser_consumed!=size_bits) fail_context(7);
                else begin
                    out_valid<=1; out_epoch<=context_epoch;
                    out_coefficient<=16'(signed_coefficient);
                    out_block<=16'(sparse_block); out_index<=sparse_index;
                    state<=HELD;
                end
            end
            if (out_valid && out_ready) begin
                out_valid<=0; count_outputs<=count_outputs+1'b1; emitted<=emitted+1'b1;
                if (emitted+1==target) begin done<=1; state<=FINISHED; end
                else state<=context_band==0 ? REQ_DC : REQ_RUN;
            end
        end
    end
`ifndef SYNTHESIS
    always_ff @(posedge clk) if (!reset && !abort_context && !start) begin
        assert (parser_bits<=64'(size_bits)) else $fatal(1,"parser bits exceed bound");
        assert (!(done && out_valid)) else $fatal(1,"done before final acceptance");
        assert (!out_valid || state==HELD) else $fatal(1,"output slot state");
        assert (!out_valid || !req_valid) else $fatal(1,"request while slot occupied");
        assert (count_outputs<=64'(target)) else $fatal(1,"output credit overflow");
    end
`endif
endmodule
