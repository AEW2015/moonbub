// V91 component experiment: generic bounded BR88 symbol parser.
module rice_probe (
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
, output logic probe_outputs_equal, probe_internal_equal, probe_word_bad, output logic [31:0] probe_size, probe_loaded, probe_consumed, probe_cache_remaining, probe_cache_load, output logic [63:0] probe_reservoir, output logic [1:0] probe_state, output logic [3:0] probe_failed, output logic [4:0] probe_suffix_left);
logic old_in_ready;
logic old_req_ready;
logic old_out_valid;
logic [23:0] old_out_value;
logic [31:0] old_out_consumed;
logic [3:0] old_out_error;
logic [63:0] old_count_cycles;
logic [63:0] old_count_inputs;
logic [63:0] old_count_symbols;
logic [63:0] old_count_bits;
logic [63:0] old_count_input_wait;
logic [63:0] old_count_output_stall;
logic [6:0] old_reservoir_bits;
rice_original old_dut(.clk(clk),.reset(reset),.stream_start(stream_start),.stream_bits(stream_bits),.word16(word16),.serial_mode(serial_mode),.in_valid(in_valid),.in_ready(old_in_ready),.in_data(in_data),.in_bits(in_bits),.in_last(in_last),.req_valid(req_valid),.req_ready(old_req_ready),.req_k(req_k),.req_escape(req_escape),.out_valid(old_out_valid),.out_ready(out_ready),.out_value(old_out_value),.out_consumed(old_out_consumed),.out_error(old_out_error),.count_cycles(old_count_cycles),.count_inputs(old_count_inputs),.count_symbols(old_count_symbols),.count_bits(old_count_bits),.count_input_wait(old_count_input_wait),.count_output_stall(old_count_output_stall),.reservoir_bits(old_reservoir_bits));
rice_candidate new_dut(.clk(clk),.reset(reset),.stream_start(stream_start),.stream_bits(stream_bits),.word16(word16),.serial_mode(serial_mode),.in_valid(in_valid),.in_ready(in_ready),.in_data(in_data),.in_bits(in_bits),.in_last(in_last),.req_valid(req_valid),.req_ready(req_ready),.req_k(req_k),.req_escape(req_escape),.out_valid(out_valid),.out_ready(out_ready),.out_value(out_value),.out_consumed(out_consumed),.out_error(out_error),.count_cycles(count_cycles),.count_inputs(count_inputs),.count_symbols(count_symbols),.count_bits(count_bits),.count_input_wait(count_input_wait),.count_output_stall(count_output_stall),.reservoir_bits(reservoir_bits));
assign probe_outputs_equal = (old_in_ready==in_ready) && (old_req_ready==req_ready) && (old_out_valid==out_valid) && (old_out_value==out_value) && (old_out_consumed==out_consumed) && (old_out_error==out_error) && (old_count_cycles==count_cycles) && (old_count_inputs==count_inputs) && (old_count_symbols==count_symbols) && (old_count_bits==count_bits) && (old_count_input_wait==count_input_wait) && (old_count_output_stall==count_output_stall) && (old_reservoir_bits==reservoir_bits);
assign probe_internal_equal = (old_dut.state==new_dut.state) && (old_dut.active==new_dut.active) && (old_dut.use16==new_dut.use16) && (old_dut.serial==new_dut.serial) && (old_dut.failed==new_dut.failed) && (old_dut.size_bits==new_dut.size_bits) && (old_dut.loaded==new_dut.loaded) && (old_dut.consumed==new_dut.consumed) && (old_dut.available==new_dut.available) && (old_dut.k==new_dut.k) && (old_dut.escape_width==new_dut.escape_width) && (old_dut.quotient==new_dut.quotient) && (old_dut.suffix_left==new_dut.suffix_left) && (old_dut.suffix_acc==new_dut.suffix_acc) && (old_dut.remaining==new_dut.remaining) && (old_dut.load_remaining==new_dut.load_remaining) && (old_dut.word_bad==new_dut.word_bad) && (old_dut.cached_remaining==new_dut.cached_remaining) && (old_dut.cached_load_remaining==new_dut.cached_load_remaining);
assign probe_word_bad=new_dut.word_bad;
assign probe_size=new_dut.size_bits;
assign probe_loaded=new_dut.loaded;
assign probe_consumed=new_dut.consumed;
assign probe_cache_remaining=new_dut.cached_remaining;
assign probe_cache_load=new_dut.cached_load_remaining;
assign probe_reservoir=(new_dut.available==0 ? 64'd0 : new_dut.reservoir >> (7'd64-new_dut.available));
assign probe_state=new_dut.state;
assign probe_failed=new_dut.failed;
assign probe_suffix_left=new_dut.suffix_left;
endmodule
