// Isolated research prototype: one row-major 8x8 RGB565 block in, eight
// aligned row-contained address runs out. Not connected to the SDRAM core.
// A block starts at its top-left word address and arrives x-fastest. Output
// is x-outer/y-inner to match the rotated framebuffer address mapping.
// Invalid input poisons the whole block; abort/reset discards buffered output.
module moonbub_tile_transpose (
 input wire clk, reset, abort,
 input wire in_valid, output wire in_ready,
 input wire [23:0] in_address, input wire [15:0] in_data,
 output wire out_valid, input wire out_ready,
 output wire [23:0] out_address, output wire [15:0] out_data,
 output wire out_burst_first, output wire out_burst_last,
 output reg fault
);
 localparam COLLECT=2'd0, EMIT=2'd1, ERROR=2'd2;
 reg [1:0] state;
 reg [5:0] input_index, output_index;
 reg [23:0] base;
 reg [15:0] words [0:63];
 wire [23:0] input_expected = base + (input_index[2:0] * 24'd480) + input_index[5:3];
 assign in_ready = state == COLLECT;
 assign out_valid = state == EMIT;
 assign out_address = base + (output_index[5:3] * 24'd480) + output_index[2:0];
 assign out_data = words[output_index];
 assign out_burst_first = out_valid && output_index[2:0] == 3'd0;
 assign out_burst_last = out_valid && output_index[2:0] == 3'd7;
 always @(posedge clk) begin
  if (reset || abort) begin
   state <= COLLECT; input_index <= 0; output_index <= 0; base <= 0; fault <= 0;
  end else if (state == COLLECT && in_valid) begin
   if ((input_index == 0 && (in_address[2:0] != 0 || in_address > 24'hfff2d8)) ||
       (input_index != 0 && in_address != input_expected)) begin
    state <= ERROR; fault <= 1;
   end else begin
    if (input_index == 0) base <= in_address;
    words[{input_index[2:0],input_index[5:3]}] <= in_data;
    if (input_index == 63) begin state <= EMIT; output_index <= 0; input_index <= 0; end
    else input_index <= input_index + 1'b1;
   end
  end else if (state == EMIT && out_ready) begin
   if (output_index == 63) begin state <= COLLECT; output_index <= 0; end
   else output_index <= output_index + 1'b1;
  end
 end
endmodule
