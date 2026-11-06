// Original iterative SHA-256 RTL. Algorithm: NIST FIPS 180-4, sections 4..6.
// BUFFER_BLOCKS=1: input pauses during compression. =2: bounded ping-pong.
// This is an unkeyed content hash, not authentication or a bank controller.
module cu71_sha_pair #(
    parameter integer BUFFER_BLOCKS = 1
) (
    input logic clk, rst, abort_i,
    input logic start_valid,
    output logic start_ready,
    input logic [31:0] total_bytes,
    input logic data_valid,
    output logic data_ready,
    input logic [7:0] data,
    input logic data_last,
    output logic result_valid,
    input logic result_ready,
    output logic [255:0] digest,
    output logic busy, error, aborted,
    output logic [7:0] error_code,
    output logic [31:0] accepted_bytes,
    output logic [31:0] compressed_blocks,
    output logic [31:0] round_cycles,
    output logic [31:0] padding_bytes,
    output logic [31:0] input_stall_cycles,
    output logic [31:0] output_stall_cycles,
    output logic [2:0] debug_fill_state,
    output logic [1:0] debug_core_state,
    output logic mismatch_any,
    output logic [31:0] mismatch_fields,
    output logic [31:0] initial_word_reference,initial_word_candidate
);
logic  reference_start_ready;
logic  reference_data_ready;
logic  reference_result_valid;
logic [255:0] reference_digest;
logic  reference_busy;
logic  reference_error;
logic  reference_aborted;
logic [7:0] reference_error_code;
logic [31:0] reference_accepted_bytes;
logic [31:0] reference_compressed_blocks;
logic [31:0] reference_round_cycles;
logic [31:0] reference_padding_bytes;
logic [31:0] reference_input_stall_cycles;
logic [31:0] reference_output_stall_cycles;
logic [2:0] reference_debug_fill_state;
logic [1:0] reference_debug_core_state;
cu66_sha256_bytes #(.BUFFER_BLOCKS(BUFFER_BLOCKS)) reference(
 .clk(clk),
 .rst(rst),
 .abort_i(abort_i),
 .start_valid(start_valid),
 .start_ready(reference_start_ready),
 .total_bytes(total_bytes),
 .data_valid(data_valid),
 .data_ready(reference_data_ready),
 .data(data),
 .data_last(data_last),
 .result_valid(reference_result_valid),
 .result_ready(result_ready),
 .digest(reference_digest),
 .busy(reference_busy),
 .error(reference_error),
 .aborted(reference_aborted),
 .error_code(reference_error_code),
 .accepted_bytes(reference_accepted_bytes),
 .compressed_blocks(reference_compressed_blocks),
 .round_cycles(reference_round_cycles),
 .padding_bytes(reference_padding_bytes),
 .input_stall_cycles(reference_input_stall_cycles),
 .output_stall_cycles(reference_output_stall_cycles),
 .debug_fill_state(reference_debug_fill_state),
 .debug_core_state(reference_debug_core_state)
);
cu71_sha256_bytes_lookahead #(.BUFFER_BLOCKS(BUFFER_BLOCKS)) candidate(
 .clk(clk),
 .rst(rst),
 .abort_i(abort_i),
 .start_valid(start_valid),
 .start_ready(start_ready),
 .total_bytes(total_bytes),
 .data_valid(data_valid),
 .data_ready(data_ready),
 .data(data),
 .data_last(data_last),
 .result_valid(result_valid),
 .result_ready(result_ready),
 .digest(digest),
 .busy(busy),
 .error(error),
 .aborted(aborted),
 .error_code(error_code),
 .accepted_bytes(accepted_bytes),
 .compressed_blocks(compressed_blocks),
 .round_cycles(round_cycles),
 .padding_bytes(padding_bytes),
 .input_stall_cycles(input_stall_cycles),
 .output_stall_cycles(output_stall_cycles),
 .debug_fill_state(debug_fill_state),
 .debug_core_state(debug_core_state)
);
always_comb begin
 mismatch_fields=0;
 mismatch_fields[0]=(start_ready !== reference_start_ready);
 mismatch_fields[1]=(data_ready !== reference_data_ready);
 mismatch_fields[2]=(result_valid !== reference_result_valid);
 mismatch_fields[3]=(digest !== reference_digest);
 mismatch_fields[4]=(busy !== reference_busy);
 mismatch_fields[5]=(error !== reference_error);
 mismatch_fields[6]=(aborted !== reference_aborted);
 mismatch_fields[7]=(error_code !== reference_error_code);
 mismatch_fields[8]=(accepted_bytes !== reference_accepted_bytes);
 mismatch_fields[9]=(compressed_blocks !== reference_compressed_blocks);
 mismatch_fields[10]=(round_cycles !== reference_round_cycles);
 mismatch_fields[11]=(padding_bytes !== reference_padding_bytes);
 mismatch_fields[12]=(input_stall_cycles !== reference_input_stall_cycles);
 mismatch_fields[13]=(output_stall_cycles !== reference_output_stall_cycles);
 mismatch_fields[14]=(debug_fill_state !== reference_debug_fill_state);
 mismatch_fields[15]=(debug_core_state !== reference_debug_core_state);
 mismatch_any=|mismatch_fields;
end
assign initial_word_reference=reference.words[0][0];
assign initial_word_candidate=candidate.words[0][0];
endmodule
