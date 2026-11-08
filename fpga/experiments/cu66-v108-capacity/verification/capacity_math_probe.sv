module capacity_math_probe (
 input logic clk,reset,take,
 input logic [27:0] prefix12_units,input logic [31:0] count3,
 input logic [16:0] blocks,input logic raw,
 output logic [31:0] meta_capacity_upper,meta_capacity_lower,
 output logic meta_capacity_wrap,output logic live,bad,
 output logic [31:0] plan_prefix12
);
 logic prefix_header_capture,cancelled,context_failure,context_active,ctx_done;
 logic [5:0] fetch_index;logic [7:0] ram_data,fetch_bytes[38:40];
 assign prefix_header_capture=take&&!reset;assign cancelled=reset;
 assign context_failure=0;assign context_active=0;assign ctx_done=0;
 assign fetch_index=6'd41;assign plan_prefix12={prefix12_units,4'd0};
 assign ram_data=count3[31:24];assign fetch_bytes[38]=count3[7:0];
 assign fetch_bytes[39]=count3[15:8];assign fetch_bytes[40]=count3[23:16];
 function automatic logic [31:0] count_aligned(input logic [31:0] n);
  return ((n<<2)+32'd15)&32'hfffffff0;
 endfunction
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
 logic capacity_bad;logic [16:0] begin_blocks;logic begin_raw;
 logic [31:0] begin_capacity_upper,begin_capacity_lower;logic begin_capacity_wrap;
 assign begin_blocks=blocks;assign begin_raw=raw;
 assign begin_capacity_upper=meta_capacity_upper;assign begin_capacity_lower=meta_capacity_lower;
 assign begin_capacity_wrap=meta_capacity_wrap;
    assign capacity_bad=begin_raw ? begin_blocks>17'd2047 :
        (32'(begin_blocks)>begin_capacity_upper ||
         (begin_capacity_wrap && 32'(begin_blocks)<=begin_capacity_lower));
 assign live=capacity_live;assign bad=capacity_bad;
endmodule
