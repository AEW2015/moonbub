module cu71_ab38_decoder_arithpipe_v4 #(
    parameter integer MAX_PACKET_BYTES = 49152,
    parameter integer MAX_BLOCKS = 8100
) (
    input  logic clk,
    input  logic rst,
    input  logic abort_i,
    input  logic cfg_valid,
    output logic cfg_ready,
    input  logic [2:0] cfg_dispatch,
    input  logic [15:0] cfg_packet_bytes,
    input  logic [16:0] cfg_blocks,
    input  logic [8:0] cfg_blocks_w,
    output logic rd_req_valid,
    input  logic rd_req_ready,
    output logic [15:0] rd_req_addr,
    input  logic rd_rsp_valid,
    output logic rd_rsp_ready,
    input  logic [7:0] rd_rsp_data,
    output logic tile_valid,
    input  logic tile_ready,
    output logic [1023:0] tile_coefficients,
    output logic [16:0] tile_index,
    output logic tile_last,
    output logic busy,
    output logic done,
    output logic aborted,
    output logic error,
    output logic [7:0] error_code,
    output logic [7:0] debug_state,
    output logic [31:0] decoded_decisions,
    output logic [31:0] renormalizations,
    output logic [31:0] memory_reads,
    output logic [31:0] output_stall_cycles
);
endmodule
module cu66_expand_tiles (
    input logic clk,rst,abort_i,
    input logic cfg_valid,
    output logic cfg_ready,
    input logic [1:0] cfg_plane,
    input logic [2:0] cfg_dispatch,
    input logic [16:0] cfg_blocks,
    input logic in_valid,
    output logic in_ready,
    input logic [1023:0] in_coefficients,
    input logic [16:0] in_index,
    input logic in_last,
    output logic out_valid,
    input logic out_ready,
    output logic [1023:0] out_coefficients,
    output logic [16:0] out_index,
    output logic [6:0] out_x,
    output logic [5:0] out_y,
    output logic out_hidden,out_last,
    output logic busy,done,error,
    output logic [7:0] error_code
);
endmodule
module cu71_dequant_resetlight (
    input logic clk, rst, abort_i,
    input logic in_valid, output logic in_ready,
    input logic [31:0] in_id,
    input logic [1023:0] in_coefficients,
    input logic in_chroma,
    input logic [1:0] in_scale_code,
    output logic out_valid, input logic out_ready,
    output logic [31:0] out_id,
    output logic [1279:0] out_dequantized,
    output logic out_error
);
endmodule
module cu71_idct_validpipe (
    input  logic clk,
    input  logic rst,
    input  logic abort_frame,
    input  logic in_valid,
    output logic in_ready,
    input  logic [31:0] in_id,
    input  logic [1279:0] in_tile,
    output logic out_valid,
    input  logic out_ready,
    output logic [31:0] out_id,
    output logic [1535:0] out_tile,
    output logic out_error,
    output logic [31:0] active_cycles
);
endmodule
module cu71_reconstruct_resetlight (
    input logic clk,rst,abort_i,
    input logic in_valid,
    output logic in_ready,
    input logic [31:0] in_id,
    input logic in_key,in_hidden,
    input logic [1535:0] in_residual,
    input logic ref_valid,
    output logic ref_ready,
    input logic [31:0] ref_tile_id,
    input logic [511:0] ref_pixels,
    output logic out_valid,
    input logic out_ready,
    output logic [31:0] out_id,
    output logic [511:0] out_pixels,
    output logic out_error
);
endmodule
module cu71_rows_sha256_fast #(
    parameter integer STRIP_BANKS=1,
    parameter integer HASH_BLOCKS=1
)(
    input logic clk,rst,abort_i,start_valid,
    output logic start_ready,
    input logic [31:0] frame_id,
    input logic key,
    input logic tile_valid,
    output logic tile_ready,
    input logic [511:0] tile_pixels,
    input logic [31:0] tile_frame_id,
    input logic tile_key,
    input logic [1:0] tile_plane,
    input logic [16:0] tile_index,
    input logic tile_last,
    output logic data_valid,data_ready,
    output logic [7:0] data,
    output logic data_last,
    output logic result_valid,
    input logic result_ready,
    output logic [255:0] digest,
    output logic busy,done,error,
    output logic [7:0] error_code,
    output logic [31:0] accepted_tiles,emitted_bytes,strip_word_writes,strip_word_reads,input_stall_cycles,output_stall_cycles,
    output logic write_busy,
    output logic [1:0] expected_plane,
    output logic [16:0] expected_index,
    output logic [31:0] hash_blocks,hash_rounds,hash_bytes,hash_padding,hash_input_stalls,hash_output_stalls,
    output logic rows_busy,rows_aborted,hash_busy,hash_aborted,
    output logic [2:0] hash_fill_state,
    output logic [1:0] hash_core_state
);
endmodule
