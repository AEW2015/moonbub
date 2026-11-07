module dequant_probe (
    input logic clk,
    input logic rst,
    input logic abort_i,
    input logic in_valid,
    output logic original_in_ready,
    input logic [31:0] in_id,
    input logic [1023:0] in_coefficients,
    input logic in_chroma,
    input logic [1:0] in_scale_code,
    output logic original_out_valid,
    input logic out_ready,
    output logic [31:0] original_out_id,
    output logic [1279:0] original_out_dequantized,
    output logic original_out_error,
    output logic candidate_in_ready,
    output logic candidate_out_valid,
    output logic [31:0] candidate_out_id,
    output logic [1279:0] candidate_out_dequantized,
    output logic candidate_out_error
);
    dequant_original original (
        .clk(clk),
        .rst(rst),
        .abort_i(abort_i),
        .in_valid(in_valid),
        .in_ready(original_in_ready),
        .in_id(in_id),
        .in_coefficients(in_coefficients),
        .in_chroma(in_chroma),
        .in_scale_code(in_scale_code),
        .out_valid(original_out_valid),
        .out_ready(out_ready),
        .out_id(original_out_id),
        .out_dequantized(original_out_dequantized),
        .out_error(original_out_error)
    );
    dequant_candidate candidate (
        .clk(clk),
        .rst(rst),
        .abort_i(abort_i),
        .in_valid(in_valid),
        .in_ready(candidate_in_ready),
        .in_id(in_id),
        .in_coefficients(in_coefficients),
        .in_chroma(in_chroma),
        .in_scale_code(in_scale_code),
        .out_valid(candidate_out_valid),
        .out_ready(out_ready),
        .out_id(candidate_out_id),
        .out_dequantized(candidate_out_dequantized),
        .out_error(candidate_out_error)
    );
endmodule
