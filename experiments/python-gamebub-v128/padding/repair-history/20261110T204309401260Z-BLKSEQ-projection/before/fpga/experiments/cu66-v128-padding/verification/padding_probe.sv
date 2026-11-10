module padding_probe(
    input logic clk,reset,start,abort_packet,
    input logic [7:0] state,byte_value,
    input logic [31:0] header_index,receipt_epoch,size_bytes,snapshot_fid,
    input logic snapshot_valid,
    input logic [63:0] snapshot_generation,
    input logic [34:0] header_packet_total,
    output logic old_padding,new_padding,new_cache,new_owner_complete,mismatch,
    output logic [7:0] old_error,new_error
);
    padding_original_kernel original(
        .clk(clk),.reset(reset),.start(start),.abort_packet(abort_packet),
        .state(state),.byte_value(byte_value),.header_index(header_index),
        .receipt_epoch(receipt_epoch),.size_bytes(size_bytes),.snapshot_fid(snapshot_fid),
        .snapshot_valid(snapshot_valid),.snapshot_generation(snapshot_generation),
        .header_packet_total(header_packet_total),
        .observed_padding(old_padding),.error(old_error)
    );
    padding_candidate_kernel candidate(
        .clk(clk),.reset(reset),.start(start),.abort_packet(abort_packet),
        .state(state),.byte_value(byte_value),.header_index(header_index),
        .receipt_epoch(receipt_epoch),.size_bytes(size_bytes),.snapshot_fid(snapshot_fid),
        .snapshot_valid(snapshot_valid),.snapshot_generation(snapshot_generation),
        .header_packet_total(header_packet_total),
        .observed_padding(new_padding),.error(new_error),.observed_cache(new_cache),.owner_complete(new_owner_complete)
    );
    assign mismatch=(old_padding!=new_padding)||(old_error!=new_error);
endmodule
