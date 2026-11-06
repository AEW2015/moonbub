// Provisional 720x480 planar YUV420 -> RGB565. Explicit byte reads, no HUD.
// One accepted read remains owned across reset/cancel until its response drains.
module canonical_rgb565_v91k (
    input logic clk, reset, start, cancel,
    input logic [31:0] start_epoch,
    output logic start_ready, busy, draining, done,
    output logic [7:0] error,
    output logic mem_req_valid,
    input logic mem_req_ready,
    output logic [18:0] mem_req_addr,
    output logic [31:0] mem_req_epoch,
    input logic mem_rsp_valid,
    output logic mem_rsp_ready,
    input logic [7:0] mem_rsp_data,
    input logic [31:0] mem_rsp_epoch,
    input logic mem_rsp_error,
    output logic out_valid,
    input logic out_ready,
    output logic [15:0] out_word,
    output logic [18:0] out_addr,
    output logic [31:0] out_epoch,
    output logic [2:0] state,
    output logic [63:0] count_reads, count_responses, count_pixels, count_cycles
);
    localparam logic [2:0] IDLE=0, READ_REQ=1, READ_WAIT=2, CONVERT=3, EMIT=4;
    logic running;
    // 7-series configuration initialization; warm reset retains accepted reads.
    logic pending=1'b0;
    logic [31:0] epoch;
    logic [9:0] x;
    logic [8:0] y;
    logic [3:0] sample_index;
    logic [7:0] samples [0:8];
    logic [15:0] converted;
    integer cb_top, cb_bottom, cr_top, cr_bottom, cb_value, cr_value;
    integer r_value, g_value, b_value;

    function automatic logic [18:0] read_address(
        input logic [9:0] px, input logic [8:0] py, input logic [3:0] which);
        integer unsigned cx,cy,part;
        if(which==0)return 19'(32'(py)*720+32'(px));
        part=which<=4?32'(which)-1:32'(which)-5;
        cx=(32'(px)>>1)+(part&1);
        cy=(32'(py)>>1)+((part>>1)&1);
        if(cx>359)cx=359;
        if(cy>239)cy=239;
        return 19'((which<=4?345600:432000)+cy*360+cx);
    endfunction
    function automatic integer clip(input integer value);
        if(value<0)return 0;
        if(value>255)return 255;
        return value;
    endfunction
    always_comb begin
        cb_top=32'(samples[1]);cb_bottom=32'(samples[3]);
        cr_top=32'(samples[5]);cr_bottom=32'(samples[7]);
        if(x[0])begin
            cb_top=(32'(samples[1])+32'(samples[2])+1)/2;
            cb_bottom=(32'(samples[3])+32'(samples[4])+1)/2;
            cr_top=(32'(samples[5])+32'(samples[6])+1)/2;
            cr_bottom=(32'(samples[7])+32'(samples[8])+1)/2;
        end
        cb_value=(y[0]?(cb_top+cb_bottom+1)/2:cb_top)-128;
        cr_value=(y[0]?(cr_top+cr_bottom+1)/2:cr_top)-128;
        r_value=clip(32'(samples[0])+((359*cr_value+128)>>>8));
        g_value=clip(32'(samples[0])-((88*cb_value+183*cr_value+128)>>>8));
        b_value=clip(32'(samples[0])+((454*cb_value+128)>>>8));
        converted=16'(((r_value>>3)<<11)|((g_value>>2)<<5)|(b_value>>3));
    end
    assign busy=running||pending;
    assign draining=!running&&pending;
    assign start_ready=!busy&&!reset&&!cancel;
    assign mem_req_valid=running&&state==READ_REQ&&!pending&&!reset&&!cancel&&error==0;
    assign mem_req_addr=read_address(x,y,sample_index);
    assign mem_req_epoch=epoch;
    assign mem_rsp_ready=pending;
    assign out_valid=running&&state==EMIT&&!reset&&!cancel&&error==0;
    assign out_addr=19'(32'(y)*720+32'(x));
    assign out_epoch=epoch;

    always_ff @(posedge clk)begin
        if(reset||cancel)begin
            running<=0;state<=IDLE;done<=0;error<=0;
            x<=0;y<=0;sample_index<=0;out_word<=0;
            // Accepted bus work cannot be retracted by local reset.
            if(pending&&mem_rsp_valid&&mem_rsp_epoch==epoch)pending<=0;
            if(reset)begin count_reads<=0;count_responses<=0;count_pixels<=0;count_cycles<=0;end
        end else begin
            if(pending&&mem_rsp_valid)begin
                if(mem_rsp_epoch==epoch)pending<=0;
                if(running)begin
                    if(mem_rsp_epoch==epoch)count_responses<=count_responses+1;
                    if(mem_rsp_error||mem_rsp_epoch!=epoch)begin
                        running<=0;state<=IDLE;done<=0;error<=mem_rsp_error?8'd2:8'd1;
                    end else begin
                        samples[sample_index]<=mem_rsp_data;
                        if(sample_index==8)state<=CONVERT;
                        else begin sample_index<=sample_index+1;state<=READ_REQ;end
                    end
                end
            end
            if(start&&start_ready)begin
                running<=start_epoch!=0;epoch<=start_epoch;pending<=0;
                state<=start_epoch!=0?READ_REQ:IDLE;done<=0;error<=start_epoch!=0?8'd0:8'd3;
                x<=0;y<=0;sample_index<=0;out_word<=0;
                count_reads<=0;count_responses<=0;count_pixels<=0;count_cycles<=0;
            end else if(running)begin
                count_cycles<=count_cycles+1;
                if(mem_req_valid&&mem_req_ready)begin
                    pending<=1;state<=READ_WAIT;count_reads<=count_reads+1;
                end
                if(state==CONVERT)begin out_word<=converted;state<=EMIT;end
                if(out_valid&&out_ready)begin
                    count_pixels<=count_pixels+1;
                    if(x==719&&y==479)begin running<=0;state<=IDLE;done<=1;end
                    else begin
                        if(x==719)begin x<=0;y<=y+1;end else x<=x+1;
                        sample_index<=0;state<=READ_REQ;
                    end
                end
            end
        end
    end
`ifndef SYNTHESIS
    always_ff @(posedge clk)if(!reset&&!cancel)begin
        if(out_valid)assert(!pending&&state==EMIT)else $fatal(1,"RGB output with pending read");
        if(mem_req_valid)assert(!pending&&mem_req_addr<518400)else $fatal(1,"RGB read ownership/range");
        if(done)assert(!busy&&count_pixels==345600)else $fatal(1,"RGB completion before output drain");
    end
`endif
endmodule
