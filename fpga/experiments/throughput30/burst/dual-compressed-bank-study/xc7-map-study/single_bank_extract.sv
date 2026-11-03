// Standalone representation of moonshine_core's original compressed array.
// The original expressions are preserved; control signals are exposed as
// primary inputs. This is not the complete production core.
module single_bank_extract #(parameter integer MAX_BYTES=262144)(
 input wire clk,bus_write,receiving,decoding,decoder_reset,decoder_valid,read_wait,
 input wire [11:0] bus_address,input wire [31:0] bus_wdata,
 input wire [31:0] received,length,read_offset,
 output reg [31:0] decoder_ram_data
);
 localparam integer WORDS=(MAX_BYTES+3)/4;
 (* ram_style="block" *) reg [31:0] compressed[0:WORDS-1];
 always @(posedge clk) begin
  if(bus_write && bus_address=='h100 && receiving && received<length && received<MAX_BYTES)
   compressed[received[17:2]][received[1:0]*8+:8]<=bus_wdata[7:0];
  if(decoding && !decoder_reset && !decoder_valid && !read_wait && read_offset<length)
   decoder_ram_data<=compressed[read_offset[17:2]];
 end
endmodule
