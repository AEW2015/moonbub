// Optional v70 11520-byte RGB-strip candidate; baseline cu70_painter is frozen.
// Fixed 720x480 canonical YUV420/HUD -> native portrait RGB565 presentation.
// Word addresses are x16, canonical samples are packed low-byte first.
// One scalar memory operation outstanding. A write reply means visible/drained.
`timescale 1ns/1ps
module cu71_painter_strip_burst (
    input logic clk,rst,abort_i,
    input logic start_valid,output logic start_ready,
    input logic [63:0] generation,
    input logic [31:0] frame_id,
    input logic [23:0] y_base,u_base,v_base,hud_base,rgb_base,
    output logic aux_req_valid,input logic aux_req_ready,
    output logic aux_req_write,
    output logic [23:0] aux_req_addr,
    output logic [15:0] aux_req_data,
    input logic aux_rsp_valid,output logic aux_rsp_ready,
    input logic [15:0] aux_rsp_data,input logic aux_rsp_error,
    output logic rgb_req_valid,input logic rgb_req_ready,
    output logic [23:0] rgb_req_addr,output logic [127:0] rgb_req_data,
    output logic [15:0] rgb_req_mask,
    input logic rgb_rsp_valid,output logic rgb_rsp_ready,input logic rgb_rsp_error,
    output logic rgb_abort_i,input logic rgb_busy,rgb_aborted,
    output logic result_valid,input logic result_ready,
    output logic [63:0] result_generation,
    output logic [31:0] result_frame_id,
    output logic busy,done,aborted,error,
    output logic [7:0] error_code,
    output logic [31:0] memory_reads,memory_writes,painted_pixels,cycle_count
);
    typedef enum logic [4:0] {IDLE,TOP_BAR,ROW_BEGIN,LOAD_REQ,LOAD_RSP,
        PIXEL_FETCH,PIXEL_COMPOSE,HUD_FETCH,WRITE_REQ,WRITE_RSP,
        BOTTOM_BAR,RESULT,DRAIN,STRIP_DRAIN,PIXEL_SAMPLE,COLOR_MUL,COLOR_SCALE,STRIP_WRITE} state_t;
    state_t state,after_load,after_write;
    logic [23:0] ub,vb,hb,rb,load_base,write_addr;
    logic [127:0] write_data,strip_burst;
    logic [1:0] load_kind;
    logic load_bank;
    logic [8:0] load_index,load_words;
    logic [9:0] x,y;
    logic [14:0] bar_index;
    logic [2:0] row_stage;
    (* ram_style="block" *) logic [15:0] y_words [0:359];
    logic [15:0] y_q;
    (* ram_style="block" *) logic [15:0] cb0 [0:179],cb1 [0:179],cr0 [0:179],cr1 [0:179];
    logic [15:0] cb0_q0,cb0_q1,cb1_q0,cb1_q1;
    logic [15:0] cr0_q0,cr0_q1,cr1_q0,cr1_q1;
    logic [15:0] hud_words [0:7];
    // Eight coded rows are transposed into short contiguous portrait runs.
    (* ram_style="block" *) logic [15:0] rgb_strip [0:5759];
    logic [15:0] strip_q;
    logic [9:0] drain_x;
    logic [2:0] drain_y;
    logic [23:0] hud_cache_tag;
    logic hud_cache_valid;
    logic pending,rgb_pending;
    logic [2:0] strip_read_lane;
    logic [7:0] ys,ct0,ct1,cb0s,cb1s,rt0,rt1,rb0s,rb1s;
    logic [8:0] cx,cx1;
    logic [7:0] cy;
    logic top_bank,bottom_bank;
    logic hud_hit;
    logic [14:0] hud_index;
    logic [23:0] hud_address;
    logic [7:0] cb_top,cb_bottom,cr_top,cr_bottom;
    logic signed [8:0] cb,cr;
    logic [14:0] hud_index_q;
    logic [4:0] hud_row;logic [8:0] hud_column;logic [1:0] hud_region;
    logic [23:0] y_row_address,u_next_row,v_next_row,canvas_base,strip_column_address;
    logic signed [8:0] cb_pipe,cr_pipe;
    logic [7:0] ys_pipe;
    logic signed [18:0] product_r,product_b,product_g_cb,product_g_cr;
    logic signed [10:0] rr,gg,bb,r_scaled,g_scaled,b_scaled;
    logic [15:0] converted;

    function automatic [7:0] average_byte(input logic[7:0] a,b,input logic blend);
        logic [8:0] unused_sum_lsb;
        begin unused_sum_lsb={1'b0,a}+{1'b0,b}+9'd1;average_byte=blend?unused_sum_lsb[8:1]:a;end
    endfunction
    function automatic [7:0] clip(input logic signed [31:0] n);
        if(n<0)clip=0;else if(n>255)clip=255;else clip=n[7:0];
    endfunction
    always_comb begin
        cx=9'(x>>1);cx1=cx==359?cx:cx+1;cy=8'(y>>1);
        top_bank=cy[0];bottom_bank=cy==239?cy[0]:!cy[0];
        hud_hit=0;hud_index=0;hud_row=0;hud_column=0;hud_region=0;
        if(x>=22&&x<182&&y>=54&&y<78)begin hud_hit=1;hud_row=5'(y)-5'd22;hud_column=9'(x)-9'd22;hud_region=0;end
        else if(x>=22&&x<182&&y>=82&&y<106)begin hud_hit=1;hud_row=5'(y)-5'd18;hud_column=9'(x)-9'd22;hud_region=1;end
        else if(x>=168&&x<488&&y>=360&&y<384)begin hud_hit=1;hud_row=5'(y)-5'd8;hud_column=9'(x)-9'd168;hud_region=2;end
        else if(x>=168&&x<408&&y>=390&&y<414)begin hud_hit=1;hud_row=5'(y)-5'd6;hud_column=9'(x)-9'd168;hud_region=3;end
        // Rectangle guards bound rows0..23 and columns0..319. Constant
        // shifts preserve the original packed index while avoiding chained
        // wide subtract/multiply/add DSPs on the control-address path.
        if(hud_hit)case(hud_region)
            0:hud_index={5'd0,hud_row,5'd0}+{3'd0,hud_row,7'd0}+15'(hud_column);
            1:hud_index=15'd3840+{5'd0,hud_row,5'd0}+{3'd0,hud_row,7'd0}+15'(hud_column);
            2:hud_index=15'd7680+{2'd0,hud_row,8'd0}+{4'd0,hud_row,6'd0}+15'(hud_column);
            3:hud_index=15'd15360+{2'd0,hud_row,8'd0}-{6'd0,hud_row,4'd0}+15'(hud_column);
        endcase
        // HUD address is registered across existing color stages below.
        // RAM outputs are clocked on PIXEL_FETCH. COMPOSE consumes the
        // same original samples one cycle later, without adding a state.
        ys=y_q[8*int'(x[0])+:8];
        ct0=8'((top_bank?cb1_q0:cb0_q0)>>(8*int'(cx[0])));
        ct1=8'((top_bank?cb1_q1:cb0_q1)>>(8*int'(cx1[0])));
        cb0s=8'((bottom_bank?cb1_q0:cb0_q0)>>(8*int'(cx[0])));
        cb1s=8'((bottom_bank?cb1_q1:cb0_q1)>>(8*int'(cx1[0])));
        rt0=8'((top_bank?cr1_q0:cr0_q0)>>(8*int'(cx[0])));
        rt1=8'((top_bank?cr1_q1:cr0_q1)>>(8*int'(cx1[0])));
        rb0s=8'((bottom_bank?cr1_q0:cr0_q0)>>(8*int'(cx[0])));
        rb1s=8'((bottom_bank?cr1_q1:cr0_q1)>>(8*int'(cx1[0])));
        cb_top=average_byte(ct0,ct1,x[0]);
        cb_bottom=average_byte(cb0s,cb1s,x[0]);
        cr_top=average_byte(rt0,rt1,x[0]);
        cr_bottom=average_byte(rb0s,rb1s,x[0]);
        cb=$signed({1'b0,average_byte(cb_top,cb_bottom,y[0])})-9'sd128;
        cr=$signed({1'b0,average_byte(cr_top,cr_bottom,y[0])})-9'sd128;
        // Bounds: interpolated chroma0..255; centered chroma-128..127.
        // Signed19-bit products/sums include all extrema and round+128.
        // Apply arithmetic shifts in the identical native operation order.
        r_scaled=11'($signed({1'b0,ys_pipe})+((product_r+19'sd128)>>>8));
        g_scaled=11'($signed({1'b0,ys_pipe})-((product_g_cb+product_g_cr+19'sd128)>>>8));
        b_scaled=11'($signed({1'b0,ys_pipe})+((product_b+19'sd128)>>>8));
        converted={5'(clip(32'(rr))>>3),6'(clip(32'(gg))>>2),5'(clip(32'(bb))>>3)};
        start_ready=state==IDLE&&!rst&&!abort_i&&!rgb_busy;
        busy=state!=IDLE||rgb_busy;
        result_valid=state==RESULT&&!rst&&!abort_i;
        aux_req_valid=state==LOAD_REQ&&!rst&&!abort_i;
        aux_req_write=0;
        aux_req_addr=load_base+24'(load_index);
        aux_req_data=0;
        aux_rsp_ready=pending&&!rgb_pending&&!rst;
        rgb_req_valid=state==WRITE_REQ&&!rst&&!abort_i;
        rgb_req_addr=write_addr;rgb_req_data=write_data;rgb_req_mask=0;
        rgb_rsp_ready=pending&&rgb_pending&&!rst;
        rgb_abort_i=rgb_pending&&(abort_i||state==DRAIN);
        strip_read_lane=(state==STRIP_DRAIN&&drain_y<7)?drain_y+1'b1:drain_y;
    end

    task automatic load(input logic [1:0] kind,input logic bank,
                         input logic [23:0] address,input logic [8:0] words,
                         input state_t return_state);
        begin load_kind<=kind;load_bank<=bank;load_base<=address;
            load_words<=words;load_index<=0;after_load<=return_state;state<=LOAD_REQ;end
    endtask
    task automatic write_burst(input logic [23:0] address,input logic [127:0] data,
                              input state_t return_state);
        begin write_addr<=address;write_data<=data;after_write<=return_state;state<=WRITE_REQ;end
    endtask
    task automatic emit_pixel;
        begin
            // RGB data is written by the separate unreset synchronous RAM port.
            painted_pixels<=painted_pixels+1;
            if(x==719)begin
                x<=0;y<=y+1;y_row_address<=y_row_address+24'd360;
                if(y[2:0]==7)begin
                    drain_x<=0;drain_y<=0;strip_column_address<=canvas_base+24'(y[8:0]-9'd7);state<=STRIP_DRAIN;
                end else state<=ROW_BEGIN;
            end else begin x<=x+1;state<=PIXEL_FETCH;end
        end
    endtask

    // Data pipeline registers intentionally have no reset. State ownership
    // makes each stage unreachable until its predecessor wrote all operands.
    always_ff @(posedge clk)begin
        if(!rst&&!abort_i)begin
            if(state==PIXEL_SAMPLE)begin
                cb_pipe<=cb;cr_pipe<=cr;ys_pipe<=ys;hud_index_q<=hud_index;
            end
            if(state==COLOR_MUL)begin
                product_r<=cr_pipe*10'sd359;hud_address<=hb+24'(hud_index_q);
                product_b<=cb_pipe*10'sd454;
                product_g_cb<=cb_pipe*10'sd88;
                product_g_cr<=cr_pipe*10'sd183;
            end
            if(state==COLOR_SCALE)begin rr<=r_scaled;gg<=g_scaled;bb<=b_scaled;end
        end
    end
    wire cache_write=!rst&&!abort_i&&state==LOAD_RSP&&aux_rsp_valid&&aux_rsp_ready&&!aux_rsp_error;
    wire strip_write=!rst&&!abort_i&&
        ((state==PIXEL_COMPOSE&&!hud_hit)||
         (state==HUD_FETCH&&hud_cache_valid&&hud_cache_tag=={hud_address[23:3],3'b000}));
    wire [15:0] strip_value=state==HUD_FETCH?hud_words[hud_address[2:0]]:converted;
    // One synchronous write port, one synchronous read port; no data reset.
    always_ff @(posedge clk)begin
        if(cache_write&&load_kind==0)y_words[load_index]<=aux_rsp_data;
        y_q<=y_words[x[9:1]];
        if(strip_write)rgb_strip[{x,y[2:0]}]<=strip_value;
        // Prime the first word throughout strip fill. At each later drain,
        // WRITE_REQ/RSP already provide synchronous-read latency for the
        // incremented address. This also prevents a stale last-word read
        // when the next eight-row strip resets its drain indices.
        strip_q<=rgb_strip[(state==STRIP_DRAIN||state==STRIP_WRITE||state==WRITE_REQ||state==WRITE_RSP)?{drain_x,strip_read_lane}:13'd0];
    end
    // Each chroma cache uses two synchronous ports. Port0 alternates writes
    // during LOAD and reads during pixel work; port1 is read-only. This is
    // a true dual-port RAM template, not a three-port asynchronous mux.
    always_ff @(posedge clk)begin
        if(cache_write&&load_kind==1&&!load_bank)cb0[load_index[7:0]]<=aux_rsp_data;
        else cb0_q0<=cb0[cx[8:1]];
    end
    always_ff @(posedge clk)cb0_q1<=cb0[cx1[8:1]];
    always_ff @(posedge clk)begin
        if(cache_write&&load_kind==1&&load_bank)cb1[load_index[7:0]]<=aux_rsp_data;
        else cb1_q0<=cb1[cx[8:1]];
    end
    always_ff @(posedge clk)cb1_q1<=cb1[cx1[8:1]];
    always_ff @(posedge clk)begin
        if(cache_write&&load_kind==2&&!load_bank)cr0[load_index[7:0]]<=aux_rsp_data;
        else cr0_q0<=cr0[cx[8:1]];
    end
    always_ff @(posedge clk)cr0_q1<=cr0[cx1[8:1]];
    always_ff @(posedge clk)begin
        if(cache_write&&load_kind==2&&load_bank)cr1[load_index[7:0]]<=aux_rsp_data;
        else cr1_q0<=cr1[cx[8:1]];
    end
    always_ff @(posedge clk)cr1_q1<=cr1[cx1[8:1]];

    always_ff @(posedge clk)begin
        if(rst)begin
            state<=IDLE;after_load<=IDLE;after_write<=IDLE;pending<=0;rgb_pending<=0;drain_x<=0;drain_y<=0;
            ub<=0;vb<=0;hb<=0;rb<=0;load_base<=0;write_addr<=0;write_data<=0;
            y_row_address<=0;u_next_row<=0;v_next_row<=0;canvas_base<=0;strip_column_address<=0;
            load_kind<=0;load_bank<=0;load_index<=0;load_words<=0;x<=0;y<=0;bar_index<=0;row_stage<=0;
            hud_cache_tag<=0;hud_cache_valid<=0;result_generation<=0;result_frame_id<=0;
            done<=0;aborted<=0;error<=0;error_code<=0;memory_reads<=0;memory_writes<=0;painted_pixels<=0;cycle_count<=0;
        end else begin
            done<=0;aborted<=0;
            if(busy)cycle_count<=cycle_count+1;
            if(aux_req_valid&&aux_req_ready)begin pending<=1;memory_reads<=memory_reads+1;end
            if(rgb_req_valid&&rgb_req_ready)begin pending<=1;rgb_pending<=1;memory_writes<=memory_writes+32'd8;end
            if(aux_rsp_valid&&aux_rsp_ready)pending<=0;
            if(rgb_rsp_valid&&rgb_rsp_ready)begin pending<=0;rgb_pending<=0;end
            if(rgb_aborted&&rgb_pending)begin pending<=0;rgb_pending<=0;end
            if(abort_i&&state!=IDLE&&state!=DRAIN)state<=DRAIN;
            else if(rgb_aborted&&rgb_pending&&state!=DRAIN)begin state<=DRAIN;error<=1;error_code<=8'd4;end
            else if(((aux_rsp_valid&&aux_rsp_ready&&aux_rsp_error)||
                     (rgb_rsp_valid&&rgb_rsp_ready&&rgb_rsp_error))&&state!=DRAIN)begin
                state<=DRAIN;error<=1;error_code<=8'd2;
            end else case(state)
                IDLE:if(start_valid&&start_ready)begin
                    result_generation<=generation;result_frame_id<=frame_id;
                    memory_reads<=0;memory_writes<=0;painted_pixels<=0;cycle_count<=0;
                    error<=0;error_code<=0;hud_cache_valid<=0;x<=0;y<=0;bar_index<=0;row_stage<=0;
                    ub<=u_base;vb<=v_base;hb<=hud_base;rb<=rgb_base;
                    y_row_address<=y_base;u_next_row<=u_base+24'd360;v_next_row<=v_base+24'd360;canvas_base<=rgb_base+24'd19200;
                    if(generation==0||frame_id==32'hffffffff||rgb_base[2:0]!=0||
                       {1'b0,y_base}+25'd172800>25'h1000000||
                       {1'b0,u_base}+25'd43200>25'h1000000||
                       {1'b0,v_base}+25'd43200>25'h1000000||
                       {1'b0,hud_base}+25'd21120>25'h1000000||
                       {1'b0,rgb_base}+25'd384000>25'h1000000)begin
                        error<=1;error_code<=1;state<=DRAIN;
                    end else state<=TOP_BAR;
                end
                TOP_BAR:begin
                    write_burst(rb+24'(bar_index),0,TOP_BAR);
                    if(bar_index==19192)begin after_write<=ROW_BEGIN;bar_index<=0;end
                    else bar_index<=bar_index+15'd8;
                end
                ROW_BEGIN:case(row_stage)
                    0:begin row_stage<=1;load(0,0,y_row_address,9'd360,ROW_BEGIN);end
                    1:begin
                        row_stage<=2;
                        if(y==0)load(1,0,ub,9'd180,ROW_BEGIN);
                        else if(!y[0]&&cy<239)begin load(1,!cy[0],u_next_row,9'd180,ROW_BEGIN);u_next_row<=u_next_row+24'd180;end
                    end
                    2:begin
                        row_stage<=3;
                        if(y==0)load(2,0,vb,9'd180,ROW_BEGIN);
                        else if(!y[0]&&cy<239)begin load(2,!cy[0],v_next_row,9'd180,ROW_BEGIN);v_next_row<=v_next_row+24'd180;end
                    end
                    3:begin row_stage<=4;if(y==0)load(1,1,ub+24'd180,9'd180,ROW_BEGIN);end
                    4:begin row_stage<=5;if(y==0)load(2,1,vb+24'd180,9'd180,ROW_BEGIN);end
                    default:begin row_stage<=0;state<=PIXEL_FETCH;end
                endcase
                LOAD_REQ:if(aux_req_valid&&aux_req_ready)state<=LOAD_RSP;
                LOAD_RSP:if(aux_rsp_valid&&aux_rsp_ready)begin
                    case(load_kind)
                        0,1,2:begin end // Separate synchronous cache RAM ports below.
                        3:hud_words[load_index[2:0]]<=aux_rsp_data;
                    endcase
                    if(load_index+9'd1==load_words)begin
                        state<=after_load;
                        if(load_kind==3)begin hud_cache_tag<=load_base;hud_cache_valid<=1;end
                    end else begin load_index<=load_index+1;state<=LOAD_REQ;end
                end
                PIXEL_FETCH:state<=PIXEL_SAMPLE;
                PIXEL_SAMPLE:state<=COLOR_MUL;
                COLOR_MUL:state<=COLOR_SCALE;
                COLOR_SCALE:state<=PIXEL_COMPOSE;
                PIXEL_COMPOSE:begin
                    if(hud_hit)state<=HUD_FETCH;
                    else emit_pixel();
                end
                HUD_FETCH:begin
                    if(hud_cache_valid&&hud_cache_tag=={hud_address[23:3],3'b000})
                        emit_pixel();
                    else load(3,0,{hud_address[23:3],3'b000},9'd8,HUD_FETCH);
                end
                STRIP_DRAIN:begin
                    strip_burst[16*drain_y+:16]<=strip_q;
                    if(drain_y==7)state<=STRIP_WRITE;
                    else drain_y<=drain_y+1'b1;
                end
                STRIP_WRITE:begin
                    write_burst(strip_column_address,strip_burst,STRIP_DRAIN);
                    drain_y<=0;
                    if(drain_x==719)begin
                        bar_index<=0;after_write<=y==480?BOTTOM_BAR:ROW_BEGIN;
                    end else begin
                        drain_x<=drain_x+1;strip_column_address<=strip_column_address+24'd480;
                    end
                end
                WRITE_REQ:if(rgb_req_valid&&rgb_req_ready)state<=WRITE_RSP;
                WRITE_RSP:if(rgb_rsp_valid&&rgb_rsp_ready)state<=after_write;
                BOTTOM_BAR:begin
                    write_burst(rb+24'd364800+24'(bar_index),0,BOTTOM_BAR);
                    if(bar_index==19192)after_write<=RESULT;
                    else bar_index<=bar_index+15'd8;
                end
                RESULT:if(result_valid&&result_ready)begin done<=1;state<=IDLE;end
                DRAIN:if(!pending&&!rgb_busy)begin aborted<=1;state<=IDLE;end
                default:begin state<=DRAIN;error<=1;error_code<=3;end
            endcase
        end
    end
endmodule
