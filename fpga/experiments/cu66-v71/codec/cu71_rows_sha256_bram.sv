// Actual RTL integration of canonical tile serialization and SHA256.
// Only serialization/hash. No inverse, external DDR, HUD or publication fence.
module cu71_rows_sha256_bram #(
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
    logic active,complete_rows,failed,internal_abort;
    logic rows_ready,sha_ready,rows_error,sha_error,rows_done,sha_valid;
    logic [7:0] rows_code,sha_code;
    assign busy=active;
    assign start_ready=!active&&rows_ready&&sha_ready&&!abort_i&&!rst;
    assign internal_abort=abort_i||(active&&(rows_error||sha_error));
    assign error=failed||rows_error||sha_error;
    assign error_code=rows_error?rows_code:(sha_error?(8'h80|sha_code):8'h00);
    assign result_valid=active&&complete_rows&&sha_valid&&!error&&!abort_i&&!rst;
    always_ff @(posedge clk)begin
        if(rst)begin active<=0;complete_rows<=0;failed<=0;done<=0;end
        else begin
            done<=0;
            if(abort_i)begin active<=0;complete_rows<=0;end
            else if(start_valid&&start_ready)begin active<=1;complete_rows<=0;failed<=0;end
            else if(active&&(rows_error||sha_error))begin active<=0;complete_rows<=0;failed<=1;end
            else begin
                if(rows_done)complete_rows<=1;
                if(result_valid&&result_ready)begin active<=0;complete_rows<=0;done<=1;end
            end
        end
    end
    cu71_tile_rows #(.STRIP_BANKS(STRIP_BANKS)) rows(
        .clk,.rst,.abort_i(internal_abort),.start_valid(start_valid&&sha_ready&&!active),.start_ready(rows_ready),.frame_id,.key,
        .tile_valid,.tile_ready,.tile_pixels,.tile_frame_id,.tile_key,.tile_plane,.tile_index,.tile_last,
        .data_valid,.data_ready,.data,.data_last,.busy(rows_busy),.done(rows_done),.error(rows_error),.aborted(rows_aborted),.error_code(rows_code),
        .accepted_tiles,.emitted_bytes,.strip_word_writes,.strip_word_reads,.input_stall_cycles,.output_stall_cycles,.write_busy,.expected_plane,.expected_index);
    cu66_sha256_bytes #(.BUFFER_BLOCKS(HASH_BLOCKS)) sha(
        .clk,.rst,.abort_i(internal_abort),.start_valid(start_valid&&rows_ready&&!active),.start_ready(sha_ready),.total_bytes(32'd518404),
        .data_valid,.data_ready,.data,.data_last,.result_valid(sha_valid),.result_ready(result_ready&&complete_rows&&active&&!error),.digest,
        .busy(hash_busy),.error(sha_error),.aborted(hash_aborted),.error_code(sha_code),.accepted_bytes(hash_bytes),.compressed_blocks(hash_blocks),.round_cycles(hash_rounds),
        .padding_bytes(hash_padding),.input_stall_cycles(hash_input_stalls),.output_stall_cycles(hash_output_stalls),.debug_fill_state(hash_fill_state),.debug_core_state(hash_core_state));
endmodule
