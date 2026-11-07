module row_miter #(parameter BANKS=1)(input clk,rst,abort_i,start_valid,key,tile_valid,tile_key,tile_last,data_ready,input[31:0]frame_id,tile_frame_id,input[511:0]tile_pixels,input[1:0]tile_plane,input[16:0]tile_index,output ok,owned);
wire[511:0]a_control,b_control,a_payload,b_payload;wire a_busy,b_busy,a_validity,b_validity;
cu71_tile_rows_reference_proof #(.STRIP_BANKS(BANKS)) a(.clk,.rst,.abort_i,.start_valid,.key,.tile_valid,.tile_key,.tile_last,.data_ready,.frame_id,.tile_frame_id,.tile_pixels,.tile_plane,.tile_index,.proof_control(a_control),.proof_payload(a_payload),.proof_validity(a_validity),.write_busy(a_busy));
cu71_tile_rows_proof #(.STRIP_BANKS(BANKS)) b(.clk,.rst,.abort_i,.start_valid,.key,.tile_valid,.tile_key,.tile_last,.data_ready,.frame_id,.tile_frame_id,.tile_pixels,.tile_plane,.tile_index,.proof_control(b_control),.proof_payload(b_payload),.proof_validity(b_validity),.write_busy(b_busy));
assign owned=a_busy;assign ok=a_validity && b_validity && a_control==b_control && a_busy==b_busy && (!a_busy || a_payload==b_payload);
endmodule
