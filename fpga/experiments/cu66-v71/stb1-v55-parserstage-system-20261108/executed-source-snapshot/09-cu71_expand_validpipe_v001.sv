// Expand dispatch6 hidden omissions and validate dispatch5 hidden zero tiles.
// Fixed canonical normalization footprint from the frozen epoch25 HUD profile.
module cu71_expand_validpipe_v001 (
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
    logic running,compact;
    logic [1:0] plane;
    logic [16:0] encoded_total,encoded_count,full_count,full_total;
    logic [6:0] x,width;
    logic [5:0] y;
    logic hidden,slot,omit;
    // Unconditional private sampling: no metadata/zero-validation CE on payload.
    logic pending_valid;
    logic [1023:0] payload_sample;
    logic [16:0] index_sample;
    logic [6:0] x_sample;
    logic [5:0] y_sample;
    logic hidden_sample,last_sample;
    always_ff @(posedge clk)begin
        payload_sample<=omit?1024'd0:in_coefficients;
        index_sample<=full_count;x_sample<=x;y_sample<=y;
        hidden_sample<=hidden;last_sample<=full_count+17'd1==full_total;
    end
    always_comb begin
        hidden=0;
        if(plane==0)begin
            hidden=((x>=3&&x<22)&&((y>=7&&y<9)||(y>=11&&y<13))) ||
                   ((x>=21&&x<61)&&(y>=45&&y<48)) ||
                   ((x>=21&&x<51)&&(y>=49&&y<51));
        end else hidden=(x>=11&&x<30&&y==23);
        slot=(!out_valid||out_ready)&&!pending_valid;
        omit=compact&&hidden;
        cfg_ready=!rst&&!abort_i&&!running&&!out_valid&&!pending_valid&&!error;
        in_ready=!rst&&!abort_i&&running&&!error&&slot&&!omit;
        busy=running||out_valid||pending_valid;
    end
    always_ff @(posedge clk)begin
        if(rst||abort_i)begin
            pending_valid<=0;running<=0;compact<=0;plane<=0;encoded_total<=0;encoded_count<=0;
            full_count<=0;full_total<=0;x<=0;y<=0;width<=0;
            out_valid<=0;out_coefficients<=0;out_index<=0;out_x<=0;out_y<=0;
            out_hidden<=0;out_last<=0;done<=0;error<=0;error_code<=0;
        end else begin
            done<=0;pending_valid<=0;
            if(pending_valid)begin
                out_valid<=1;out_coefficients<=payload_sample;
                out_index<=index_sample;out_x<=x_sample;out_y<=y_sample;
                out_hidden<=hidden_sample;out_last<=last_sample;
            end
            if(out_valid&&out_ready)begin
                out_valid<=0;
                if(out_last)done<=1;
            end
            if(cfg_valid&&cfg_ready)begin
                if(cfg_plane>2||(cfg_dispatch!=5&&cfg_dispatch!=6) ||
                   cfg_blocks!=((cfg_plane==0)?((cfg_dispatch==6)?17'd5144:17'd5400):
                                                         ((cfg_dispatch==6)?17'd1331:17'd1350)))begin
                    error<=1;error_code<=8'd1;
                end else begin
                    running<=1;compact<=cfg_dispatch==6;plane<=cfg_plane;
                    encoded_total<=cfg_blocks;encoded_count<=0;
                    full_count<=0;full_total<=cfg_plane==0?17'd5400:17'd1350;
                    x<=0;y<=0;width<=cfg_plane==0?7'd90:7'd45;
                end
            end else if(running&&!error&&slot&&(omit||in_valid))begin
                if(!omit&&(in_index!=encoded_count ||
                     in_last!=(encoded_count+17'd1==encoded_total) ||
                     (hidden&&in_coefficients!=0)))begin
                    running<=0;out_valid<=0;error<=1;error_code<=8'd2;
                end else begin
                    pending_valid<=1;
                    if(!omit)encoded_count<=encoded_count+17'd1;
                    if(full_count+17'd1==full_total)running<=0;
                    else begin
                        full_count<=full_count+17'd1;
                        if(x+7'd1==width)begin x<=0;y<=y+6'd1;end
                        else x<=x+7'd1;
                    end
                end
            end
        end
    end
endmodule
