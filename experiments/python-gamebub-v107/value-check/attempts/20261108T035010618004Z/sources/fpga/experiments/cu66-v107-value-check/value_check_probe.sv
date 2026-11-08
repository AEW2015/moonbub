module value_check_probe(input logic signed [15:0] in_value, input logic [1:0] in_qscale, output logic baseline_bad, candidate_bad);
assign baseline_bad=in_qscale==3||in_value < -16'sd2048||in_value > 16'sd2048;
assign candidate_bad=in_qscale==3||!(in_value[15:11]==5'd0||in_value[15:11]==5'b11111||in_value==16'h0800);
endmodule
