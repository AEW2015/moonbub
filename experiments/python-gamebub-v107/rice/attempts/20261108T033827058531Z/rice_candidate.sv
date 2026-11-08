// V107 fixed-tap Rice parser. MSB-aligned reservoir; public cycle schedule unchanged.
module rice_candidate (
    input  logic clk, reset, stream_start,
    input  logic [31:0] stream_bits,
    input  logic word16, serial_mode,
    input  logic in_valid,
    output logic in_ready,
    input  logic [31:0] in_data,
    input  logic [5:0] in_bits,
    input  logic in_last,
    input  logic req_valid,
    output logic req_ready,
    input  logic [4:0] req_k, req_escape,
    output logic out_valid,
    input  logic out_ready,
    output logic [23:0] out_value,
    output logic [31:0] out_consumed,
    output logic [3:0] out_error,
    output logic [63:0] count_cycles, count_inputs, count_symbols,
    output logic [63:0] count_bits, count_input_wait, count_output_stall,
    output logic [6:0] reservoir_bits
);
    localparam logic [1:0] IDLE=0, PREFIX=1, SUFFIX=2, RESPONSE=3;
    localparam logic [3:0] OK=0, BAD_PARAM=1, TRUNCATED=2, BAD_WORD=3;
    logic [1:0] state;
    logic active, use16, serial;
    logic [3:0] failed;
    logic [31:0] size_bits, loaded, consumed;
    logic [63:0] reservoir;
    logic [6:0] available;
    logic [4:0] k, escape_width, quotient, suffix_left;
    logic [23:0] suffix_acc;
    logic [31:0] remaining, load_remaining;
    logic [31:0] cached_remaining, cached_load_remaining;
    logic [5:0] expected_word, window, needed, take_bits;
    logic [4:0] zeros;
    logic found_one, prefix_empty, word_bad, can_step;
    logic [63:0] extracted;
    logic [23:0] suffix_value, decoded_value;
    logic [5:0] suffix_take_bits;
    logic [23:0] suffix_extracted;
    logic [15:0] prefix_candidates;
    logic [3:0] prefix_rank_pairs [0:7];
    logic [3:0] prefix_rank_quads [0:3];
    logic [3:0] prefix_rank_octets [0:1];
    logic [3:0] prefix_rank;
    integer i;

    always_comb begin
        remaining = cached_remaining;
        load_remaining = cached_load_remaining;
        expected_word = (load_remaining < (use16 ? 32'd16 : 32'd32)) ?
                        6'(load_remaining) : (use16 ? 6'd16 : 6'd32);
        window = remaining < 15 ? 6'(remaining) : 6'd15;
        // MSB-aligned storage gives fixed physical taps, independent of available.
        // Keep the original valid-bit guards and balanced first-one priority.
        prefix_candidates=16'd0;
        for (i=0; i<15; i=i+1) begin
            if (available > 7'(i) && reservoir[63-i])
                prefix_candidates[i]=1'b1;
        end
        // Balanced, fixed-position priority tree; rank 15 denotes no one.
        for (i=0; i<8; i=i+1)
            prefix_rank_pairs[i]=prefix_candidates[2*i]?4'(2*i):
                prefix_candidates[2*i+1]?4'(2*i+1):4'd15;
        for (i=0; i<4; i=i+1)
            prefix_rank_quads[i]=prefix_rank_pairs[2*i]!=15?
                prefix_rank_pairs[2*i]:prefix_rank_pairs[2*i+1];
        for (i=0; i<2; i=i+1)
            prefix_rank_octets[i]=prefix_rank_quads[2*i]!=15?
                prefix_rank_quads[2*i]:prefix_rank_quads[2*i+1];
        prefix_rank=prefix_rank_octets[0]!=15?prefix_rank_octets[0]:prefix_rank_octets[1];
        zeros=window<6'(prefix_rank)?5'(window):5'(prefix_rank);
        found_one=6'(prefix_rank)<window;
        prefix_empty = window==0;
        needed=0; take_bits=0;
        if (state==PREFIX) begin
            needed=serial ? 6'd1 : window;
            take_bits=serial ? 6'd1 :
                      (zeros==15 ? 6'd15 : (found_one ? 6'(zeros)+1'b1 : window));
        end else if (state==SUFFIX) begin
            needed=serial && suffix_left!=0 ? 6'd1 : 6'(suffix_left);
            take_bits=needed;
        end
        can_step=available >= 7'(needed);
        extracted=take_bits==0 ? 64'd0 : reservoir >> (7'd64-7'(take_bits));
        // SUFFIX extraction depends only on its bounded width, with no
        // available-to-value barrel selector or PREFIX dependency.
        suffix_take_bits=serial && suffix_left!=0 ? 6'd1 : 6'(suffix_left);
        suffix_extracted=suffix_take_bits==0 ? 24'd0 : 24'(reservoir >> (7'd64-7'(suffix_take_bits)));
        suffix_value=serial ? ((suffix_acc<<1) | 24'(suffix_extracted)) : 24'(suffix_extracted);
        decoded_value=quotient==15 ? suffix_value :
                      ((24'(quotient)<<k) | suffix_value);
        word_bad=(in_bits!=expected_word || in_bits==0 ||
                  in_last!=(cached_load_remaining==32'(in_bits)) ||
                  (in_bits<32 && (in_data & (32'hffffffff >> in_bits))!=0));
        req_ready=active && state==IDLE && !out_valid && !stream_start && !reset;
        in_ready=active && failed==0 && !out_valid && available<=32 &&
                 loaded<size_bits && !(state==IDLE && req_valid) &&
                 !stream_start && !reset;
        reservoir_bits=available;
    end

    task automatic respond_error(input logic [3:0] code);
        begin
            failed<=code; out_valid<=1; out_error<=code;
            out_value<=0; out_consumed<=consumed; state<=RESPONSE;
        end
    endtask

    always_ff @(posedge clk) begin
        if (reset || stream_start) begin
            active<=!reset; use16<=word16; serial<=serial_mode;
            size_bits<=stream_bits; loaded<=0; consumed<=0;
            cached_remaining<=stream_bits; cached_load_remaining<=stream_bits;
            reservoir<=0; available<=0; failed<=0; state<=IDLE;
            k<=0; escape_width<=0; quotient<=0; suffix_left<=0; suffix_acc<=0;
            out_valid<=0; out_value<=0; out_consumed<=0; out_error<=0;
            count_cycles<=0; count_inputs<=0; count_symbols<=0;
            count_bits<=0; count_input_wait<=0; count_output_stall<=0;
        end else if (active) begin
            count_cycles<=count_cycles+1'b1;
            if (out_valid && !out_ready) count_output_stall<=count_output_stall+1'b1;
            if ((state==PREFIX || state==SUFFIX) && needed!=0 &&
                !can_step && !(in_valid && in_ready) && remaining>=32'(needed))
                count_input_wait<=count_input_wait+1'b1;
            if (out_valid && out_ready) begin
                out_valid<=0; state<=IDLE;
                if (out_error==0) count_symbols<=count_symbols+1'b1;
            end
            if (req_valid && req_ready) begin
                if (failed!=0) respond_error(failed);
                else if (req_k>19 || req_escape>24) respond_error(BAD_PARAM);
                else begin
                    k<=req_k; escape_width<=req_escape; quotient<=0;
                    suffix_acc<=0; suffix_left<=0; state<=PREFIX;
                end
            end else if (in_valid && in_ready) begin
                count_inputs<=count_inputs+1'b1;
                if (word_bad) begin
                    failed<=BAD_WORD;
                    if (state!=IDLE) respond_error(BAD_WORD);
                end else begin
                    // Accepted input has zero padding. Its MSB follows existing valid bits.
                    reservoir<=reservoir | (64'(in_data) << (7'd32-available));
                    available<=available+7'(in_bits);
                    loaded<=loaded+32'(in_bits);
                    cached_load_remaining<=cached_load_remaining-32'(in_bits);
                end
            end else if (state==PREFIX && !out_valid) begin
                if (failed!=0) respond_error(failed);
                else if (prefix_empty) respond_error(TRUNCATED);
                else if (can_step) begin
                    reservoir<=reservoir << take_bits;
                    available<=available-7'(take_bits);
                    consumed<=consumed+32'(take_bits);
                    cached_remaining<=cached_remaining-32'(take_bits);
                    count_bits<=count_bits+64'(take_bits);
                    if (!serial && !found_one && window<15) begin
                        failed<=TRUNCATED; out_valid<=1; out_error<=TRUNCATED;
                        out_value<=0; out_consumed<=consumed+32'(take_bits); state<=RESPONSE;
                    end else if (serial && extracted==0 && quotient<14) begin
                        quotient<=quotient+1'b1;
                    end else begin
                        if (serial) begin
                            quotient<=extracted==0 ? 5'd15 : quotient;
                            suffix_left<=extracted==0 ? escape_width : k;
                        end else begin
                            quotient<=zeros; suffix_left<=zeros==15 ? escape_width : k;
                        end
                        state<=SUFFIX;
                    end
                end
            end else if (state==SUFFIX && !out_valid) begin
                if (remaining<32'(suffix_left)) respond_error(TRUNCATED);
                else if (can_step) begin
                    reservoir<=reservoir << take_bits;
                    available<=available-7'(take_bits);
                    consumed<=consumed+32'(take_bits);
                    cached_remaining<=cached_remaining-32'(take_bits);
                    count_bits<=count_bits+64'(take_bits);
                    if (!serial || suffix_left<=1) begin
                        out_valid<=1; out_error<=OK; out_value<=decoded_value;
                        out_consumed<=consumed+32'(take_bits); state<=RESPONSE;
                    end else begin
                        suffix_left<=suffix_left-1'b1; suffix_acc<=suffix_value;
                    end
                end
            end
        end
    end

`ifndef SYNTHESIS
    // Only SUFFIX selects this combinational result; other states may differ.
    always_ff @(posedge clk) if (state==SUFFIX) begin
        assert (suffix_value==(serial ? ((suffix_acc<<1) | 24'(extracted)) : 24'(extracted)))
            else $fatal(1,"selected suffix extraction mismatch");
    end
    // Private redundant-state invariants. These hold modulo 2^32 regardless
    // of stream size, including idle/failed cycles after initialization.
    always_ff @(posedge clk) if (!reset && !stream_start) begin
        assert (cached_remaining==size_bits-consumed) else $fatal(1,"remaining cache mismatch");
        assert (cached_load_remaining==size_bits-loaded) else $fatal(1,"load remaining cache mismatch");
    end
    always_ff @(posedge clk) if (!reset && !stream_start && active) begin
        assert (available<=64) else $fatal(1,"reservoir overflow");
        assert ((reservoir & (64'hffffffffffffffff >> available))==0)
            else $fatal(1,"aligned reservoir padding mismatch");
        assert (consumed<=loaded && loaded<=size_bits) else $fatal(1,"bit bound");
        assert (count_bits==64'(consumed)) else $fatal(1,"bit counter mismatch");
    end
`endif
endmodule
