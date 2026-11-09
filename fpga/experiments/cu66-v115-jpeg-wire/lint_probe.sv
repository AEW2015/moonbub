`timescale 1ns/1ps
module lint_probe (
 input wire [15:0] lookup,
 output wire [4:0] width,
 output wire [7:0] value
);
 jpeg_dht_std_y_dc actual_baseline (
  .lookup_input_i(lookup),.lookup_width_o(width),.lookup_value_o(value));
endmodule
