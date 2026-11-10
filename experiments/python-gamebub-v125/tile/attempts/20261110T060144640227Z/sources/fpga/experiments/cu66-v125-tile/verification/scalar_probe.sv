module scalar_probe (
    input logic clk,reset,start,abort_packet,capture,group_capture,group_begin,
    input logic key_terminal_capture,plane_clear_capture,
    input logic [1:0] plane,input logic [31:0] tile,group_end,receipt_epoch,
    output logic out_hidden,out_terminal,out_group,
    output logic tile_valid,group_valid,
    output logic [31:0] tile_epoch,tile_key,group_epoch,group_key,group_end_key,
    output logic [1:0] tile_plane,group_plane
);
    function automatic logic hidden(input logic [1:0] p, input logic [31:0] t);
        if(p!=0)return t>=1046&&t<=1064;
        return (t>=633&&t<=651)||(t>=723&&t<=741)||
            (t>=993&&t<=1011)||(t>=1083&&t<=1101)||
            (t>=4071&&t<=4110)||(t>=4161&&t<=4200)||
            (t>=4251&&t<=4290)||(t>=4431&&t<=4460)||
            (t>=4521&&t<=4550);
    endfunction
    function automatic logic [31:0] tile_count(input logic [1:0] p);
        return p==0?32'd5400:32'd1350;
    endfunction
    logic prepared_tile_hidden, prepared_tile_terminal, prepared_group_terminal;
`ifndef SYNTHESIS
    logic tile_pred_owner_valid, group_pred_owner_valid;
    logic [31:0] tile_pred_owner_epoch, tile_pred_owner_tile;
    logic [1:0] tile_pred_owner_plane;
    logic [31:0] group_pred_owner_epoch, group_pred_owner_tile, group_pred_owner_end;
    logic [1:0] group_pred_owner_plane;
`endif
    task automatic prepare_tile_key(input logic [1:0] next_plane,
                                    input logic [31:0] next_tile);
        prepared_tile_hidden<=hidden(next_plane,next_tile);
        prepared_tile_terminal<=next_tile==tile_count(next_plane);
`ifndef SYNTHESIS
        tile_pred_owner_valid<=1;
        tile_pred_owner_epoch<=receipt_epoch;
        tile_pred_owner_plane<=next_plane;tile_pred_owner_tile<=next_tile;
        group_pred_owner_valid<=0;
`endif
    endtask
    task automatic prepare_group_key(input logic [1:0] next_plane,
                                     input logic [31:0] next_tile,
                                     input logic [31:0] owned_end);
        // Atomic group snapshot intentionally refreshes all three scalars,
        // including tile decisions when the tag commit leaves tile unchanged.
        prepare_tile_key(next_plane,next_tile);
        prepared_group_terminal<=next_tile==owned_end;
`ifndef SYNTHESIS
        group_pred_owner_valid<=1;
        group_pred_owner_epoch<=receipt_epoch;
        group_pred_owner_plane<=next_plane;group_pred_owner_tile<=next_tile;
        group_pred_owner_end<=owned_end;
`endif
    endtask

    always_ff @(posedge clk)begin
        if(reset||start||abort_packet)begin
            tile_pred_owner_valid<=0;group_pred_owner_valid<=0;
        end else begin
            if(group_begin)group_pred_owner_valid<=0;
            if(capture)begin
                if(key_terminal_capture)prepare_tile_key(plane==2?plane:plane+2'd1,32'd0);
                else if(plane_clear_capture)begin
                    if(plane!=2)prepare_tile_key(plane+2'd1,32'd0);
                end else if(group_capture)prepare_group_key(plane,tile,group_end);
                else prepare_tile_key(plane,tile);
            end
        end
    end
    assign out_hidden=prepared_tile_hidden;
    assign out_terminal=prepared_tile_terminal;
    assign out_group=prepared_group_terminal;
    assign tile_valid=tile_pred_owner_valid;assign group_valid=group_pred_owner_valid;
    assign tile_epoch=tile_pred_owner_epoch;assign tile_key=tile_pred_owner_tile;
    assign tile_plane=tile_pred_owner_plane;
    assign group_epoch=group_pred_owner_epoch;assign group_key=group_pred_owner_tile;
    assign group_end_key=group_pred_owner_end;assign group_plane=group_pred_owner_plane;
endmodule
