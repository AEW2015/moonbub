// One elastic canonical tile. Reference is a leased, immutable bank input.
// IDs are full-grid tile-address tags, not video frame IDs. Key/hidden tiles
// need no reference read. This is not a general motion compensator.
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
    logic slot_ready;
    logic signed [24:0] combined [0:63];
    always_comb begin
        slot_ready=!out_valid||out_ready;
        in_ready=!rst&&!abort_i&&slot_ready&&(in_key||in_hidden||ref_valid);
        ref_ready=!rst&&!abort_i&&slot_ready&&in_valid&&!in_key&&!in_hidden;
        for(integer i=0;i<64;i=i+1)
            combined[i]=$signed({in_residual[i*24+23],in_residual[i*24 +:24]})+
                (in_key?25'sd128:$signed({17'd0,ref_pixels[i*8 +:8]}));
    end
    always_ff @(posedge clk)begin
        if(rst||abort_i)begin out_valid<=0;out_id<=0;out_error<=0;end
        else if(slot_ready)begin
            out_valid<=in_valid&&(in_key||in_hidden||ref_valid);
            if(in_valid&&(in_key||in_hidden||ref_valid))begin
                out_id<=in_id;out_error<=!in_key&&!in_hidden&&(ref_tile_id!=in_id);
                for(integer i=0;i<64;i=i+1)begin
                    if(in_hidden)out_pixels[i*8 +:8]<=8'd128;
                    else if(combined[i]<0)out_pixels[i*8 +:8]<=0;
                    else if(combined[i]>255)out_pixels[i*8 +:8]<=8'd255;
                    else out_pixels[i*8 +:8]<=combined[i][7:0];
                end
            end
        end
    end
endmodule
