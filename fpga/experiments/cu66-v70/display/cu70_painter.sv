// Fixed 720x480 canonical YUV420/HUD -> native portrait RGB565 presentation.
// Word addresses are x16, canonical samples are packed low-byte first.
// One scalar memory operation outstanding. A write reply means visible/drained.
`timescale 1ns/1ps
module cu70_painter (
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
    output logic result_valid,input logic result_ready,
    output logic [63:0] result_generation,
    output logic [31:0] result_frame_id,
    output logic busy,done,aborted,error,
    output logic [7:0] error_code,
    output logic [31:0] memory_reads,memory_writes,painted_pixels,cycle_count
);
    typedef enum logic [4:0] {IDLE,TOP_BAR,ROW_BEGIN,LOAD_REQ,LOAD_RSP,
        PIXEL_FETCH,PIXEL_COMPOSE,HUD_FETCH,WRITE_REQ,WRITE_RSP,
        BOTTOM_BAR,RESULT,DRAIN} state_t;
    state_t state,after_load,after_write;
    logic [23:0] yb,ub,vb,hb,rb,load_base,write_addr;
    logic [15:0] write_data;
    logic [1:0] load_kind;
    logic load_bank;
    logic [8:0] load_index,load_words;
    logic [9:0] x,y;
    logic [14:0] bar_index;
    logic [2:0] row_stage;
    logic [15:0] y_words [0:359];
    logic [15:0] cb0 [0:179],cb1 [0:179],cr0 [0:179],cr1 [0:179];
    logic [15:0] hud_words [0:7];
    logic [23:0] hud_cache_tag;
    logic hud_cache_valid;
    logic pending;
    logic [7:0] ys,ct0,ct1,cb0s,cb1s,rt0,rt1,rb0s,rb1s;
    logic [8:0] cx,cx1;
    logic [7:0] cy;
    logic top_bank,bottom_bank;
    logic hud_hit;
    logic [14:0] hud_index;
    logic [23:0] hud_address;
    logic signed [31:0] cb_top,cb_bottom,cr_top,cr_bottom,cb,cr,rr,gg,bb;
    logic [15:0] converted;

    function automatic [7:0] clip(input logic signed [31:0] n);
        if(n<0)clip=0;else if(n>255)clip=255;else clip=n[7:0];
    endfunction
    always_comb begin
        cx=9'(x>>1);cx1=cx==359?cx:cx+1;cy=8'(y>>1);
        top_bank=cy[0];bottom_bank=cy==239?cy[0]:!cy[0];
        hud_hit=0;hud_index=0;
        if(x>=22&&x<182&&y>=54&&y<78)begin hud_hit=1;hud_index=15'((int'(y)-54)*160+int'(x)-22);end
        else if(x>=22&&x<182&&y>=82&&y<106)begin hud_hit=1;hud_index=15'(3840+(int'(y)-82)*160+int'(x)-22);end
        else if(x>=168&&x<488&&y>=360&&y<384)begin hud_hit=1;hud_index=15'(7680+(int'(y)-360)*320+int'(x)-168);end
        else if(x>=168&&x<408&&y>=390&&y<414)begin hud_hit=1;hud_index=15'(15360+(int'(y)-390)*240+int'(x)-168);end
        hud_address=hb+24'(hud_index);
        cb_top=x[0]?((32'(ct0)+32'(ct1)+1)>>1):32'(ct0);
        cb_bottom=x[0]?((32'(cb0s)+32'(cb1s)+1)>>1):32'(cb0s);
        cr_top=x[0]?((32'(rt0)+32'(rt1)+1)>>1):32'(rt0);
        cr_bottom=x[0]?((32'(rb0s)+32'(rb1s)+1)>>1):32'(rb0s);
        cb=(y[0]?((cb_top+cb_bottom+1)>>>1):cb_top)-128;
        cr=(y[0]?((cr_top+cr_bottom+1)>>>1):cr_top)-128;
        rr=$signed({24'd0,ys})+((359*cr+128)>>>8);
        gg=$signed({24'd0,ys})-((88*cb+183*cr+128)>>>8);
        bb=$signed({24'd0,ys})+((454*cb+128)>>>8);
        converted={5'(clip(rr)>>3),6'(clip(gg)>>2),5'(clip(bb)>>3)};
        start_ready=state==IDLE&&!rst&&!abort_i;
        busy=state!=IDLE;
        result_valid=state==RESULT&&!rst&&!abort_i;
        aux_req_valid=(state==LOAD_REQ||state==WRITE_REQ)&&!rst&&!abort_i;
        aux_req_write=state==WRITE_REQ;
        aux_req_addr=aux_req_write?write_addr:(load_base+24'(load_index));
        aux_req_data=write_data;
        aux_rsp_ready=pending&&!rst;
    end

    task automatic load(input logic [1:0] kind,input logic bank,
                         input logic [23:0] address,input logic [8:0] words,
                         input state_t return_state);
        begin load_kind<=kind;load_bank<=bank;load_base<=address;
            load_words<=words;load_index<=0;after_load<=return_state;state<=LOAD_REQ;end
    endtask
    task automatic write_word(input logic [23:0] address,input logic [15:0] data,
                              input state_t return_state);
        begin write_addr<=address;write_data<=data;after_write<=return_state;state<=WRITE_REQ;end
    endtask
    always_ff @(posedge clk)begin
        if(rst)begin
            state<=IDLE;after_load<=IDLE;after_write<=IDLE;pending<=0;
            yb<=0;ub<=0;vb<=0;hb<=0;rb<=0;load_base<=0;write_addr<=0;write_data<=0;
            load_kind<=0;load_bank<=0;load_index<=0;load_words<=0;x<=0;y<=0;bar_index<=0;row_stage<=0;
            hud_cache_tag<=0;hud_cache_valid<=0;ys<=0;ct0<=0;ct1<=0;cb0s<=0;cb1s<=0;
            rt0<=0;rt1<=0;rb0s<=0;rb1s<=0;result_generation<=0;result_frame_id<=0;
            done<=0;aborted<=0;error<=0;error_code<=0;memory_reads<=0;memory_writes<=0;painted_pixels<=0;cycle_count<=0;
        end else begin
            done<=0;aborted<=0;
            if(busy)cycle_count<=cycle_count+1;
            if(aux_req_valid&&aux_req_ready)begin
                pending<=1;
                if(aux_req_write)memory_writes<=memory_writes+1;
                else memory_reads<=memory_reads+1;
            end
            if(aux_rsp_valid&&aux_rsp_ready)pending<=0;
            if(abort_i&&state!=IDLE&&state!=DRAIN)state<=DRAIN;
            else if(aux_rsp_valid&&aux_rsp_ready&&aux_rsp_error&&state!=DRAIN)begin
                state<=DRAIN;error<=1;error_code<=8'd2;
            end else case(state)
                IDLE:if(start_valid&&start_ready)begin
                    result_generation<=generation;result_frame_id<=frame_id;
                    memory_reads<=0;memory_writes<=0;painted_pixels<=0;cycle_count<=0;
                    error<=0;error_code<=0;hud_cache_valid<=0;x<=0;y<=0;bar_index<=0;row_stage<=0;
                    yb<=y_base;ub<=u_base;vb<=v_base;hb<=hud_base;rb<=rgb_base;
                    if(generation==0||frame_id==32'hffffffff||
                       {1'b0,y_base}+25'd172800>25'h1000000||
                       {1'b0,u_base}+25'd43200>25'h1000000||
                       {1'b0,v_base}+25'd43200>25'h1000000||
                       {1'b0,hud_base}+25'd21120>25'h1000000||
                       {1'b0,rgb_base}+25'd384000>25'h1000000)begin
                        error<=1;error_code<=1;state<=DRAIN;
                    end else state<=TOP_BAR;
                end
                TOP_BAR:begin
                    write_word(rb+24'(bar_index),0,TOP_BAR);
                    if(bar_index==19199)begin after_write<=ROW_BEGIN;bar_index<=0;end
                    else bar_index<=bar_index+1;
                end
                ROW_BEGIN:case(row_stage)
                    0:begin row_stage<=1;load(0,0,yb+24'(int'(y)*360),9'd360,ROW_BEGIN);end
                    1:begin
                        row_stage<=2;
                        if(y==0)load(1,0,ub,9'd180,ROW_BEGIN);
                        else if(!y[0]&&cy<239)load(1,!cy[0],ub+24'((int'(cy)+1)*180),9'd180,ROW_BEGIN);
                    end
                    2:begin
                        row_stage<=3;
                        if(y==0)load(2,0,vb,9'd180,ROW_BEGIN);
                        else if(!y[0]&&cy<239)load(2,!cy[0],vb+24'((int'(cy)+1)*180),9'd180,ROW_BEGIN);
                    end
                    3:begin row_stage<=4;if(y==0)load(1,1,ub+24'd180,9'd180,ROW_BEGIN);end
                    4:begin row_stage<=5;if(y==0)load(2,1,vb+24'd180,9'd180,ROW_BEGIN);end
                    default:begin row_stage<=0;state<=PIXEL_FETCH;end
                endcase
                LOAD_REQ:if(aux_req_valid&&aux_req_ready)state<=LOAD_RSP;
                LOAD_RSP:if(aux_rsp_valid&&aux_rsp_ready)begin
                    case(load_kind)
                        0:y_words[load_index]<=aux_rsp_data;
                        1:if(load_bank)cb1[load_index[7:0]]<=aux_rsp_data;else cb0[load_index[7:0]]<=aux_rsp_data;
                        2:if(load_bank)cr1[load_index[7:0]]<=aux_rsp_data;else cr0[load_index[7:0]]<=aux_rsp_data;
                        3:hud_words[load_index[2:0]]<=aux_rsp_data;
                    endcase
                    if(load_index+9'd1==load_words)begin
                        state<=after_load;
                        if(load_kind==3)begin hud_cache_tag<=load_base;hud_cache_valid<=1;end
                    end else begin load_index<=load_index+1;state<=LOAD_REQ;end
                end
                PIXEL_FETCH:begin
                    ys<=y_words[x[9:1]][8*int'(x[0]) +:8];
                    ct0<=top_bank?cb1[cx[8:1]][8*int'(cx[0]) +:8]:cb0[cx[8:1]][8*int'(cx[0]) +:8];
                    ct1<=top_bank?cb1[cx1[8:1]][8*int'(cx1[0]) +:8]:cb0[cx1[8:1]][8*int'(cx1[0]) +:8];
                    cb0s<=bottom_bank?cb1[cx[8:1]][8*int'(cx[0]) +:8]:cb0[cx[8:1]][8*int'(cx[0]) +:8];
                    cb1s<=bottom_bank?cb1[cx1[8:1]][8*int'(cx1[0]) +:8]:cb0[cx1[8:1]][8*int'(cx1[0]) +:8];
                    rt0<=top_bank?cr1[cx[8:1]][8*int'(cx[0]) +:8]:cr0[cx[8:1]][8*int'(cx[0]) +:8];
                    rt1<=top_bank?cr1[cx1[8:1]][8*int'(cx1[0]) +:8]:cr0[cx1[8:1]][8*int'(cx1[0]) +:8];
                    rb0s<=bottom_bank?cr1[cx[8:1]][8*int'(cx[0]) +:8]:cr0[cx[8:1]][8*int'(cx[0]) +:8];
                    rb1s<=bottom_bank?cr1[cx1[8:1]][8*int'(cx1[0]) +:8]:cr0[cx1[8:1]][8*int'(cx1[0]) +:8];
                    state<=PIXEL_COMPOSE;
                end
                PIXEL_COMPOSE:begin
                    if(hud_hit)state<=HUD_FETCH;
                    else write_word(rb+24'((int'(x)+40)*480+int'(y)),converted,PIXEL_FETCH);
                    if(!hud_hit)begin
                        painted_pixels<=painted_pixels+1;
                        if(x==719)begin
                            x<=0;
                            if(y==479)begin after_write<=BOTTOM_BAR;bar_index<=0;end
                            else begin y<=y+1;after_write<=ROW_BEGIN;end
                        end else x<=x+1;
                    end
                end
                HUD_FETCH:begin
                    if(hud_cache_valid&&hud_cache_tag=={hud_address[23:3],3'b000})begin
                        write_word(rb+24'((int'(x)+40)*480+int'(y)),hud_words[hud_address[2:0]],PIXEL_FETCH);
                        painted_pixels<=painted_pixels+1;
                        if(x==719)begin
                            x<=0;
                            if(y==479)begin after_write<=BOTTOM_BAR;bar_index<=0;end
                            else begin y<=y+1;after_write<=ROW_BEGIN;end
                        end else x<=x+1;
                    end else load(3,0,{hud_address[23:3],3'b000},9'd8,HUD_FETCH);
                end
                WRITE_REQ:if(aux_req_valid&&aux_req_ready)state<=WRITE_RSP;
                WRITE_RSP:if(aux_rsp_valid&&aux_rsp_ready)state<=after_write;
                BOTTOM_BAR:begin
                    write_word(rb+24'd364800+24'(bar_index),0,BOTTOM_BAR);
                    if(bar_index==19199)after_write<=RESULT;
                    else bar_index<=bar_index+1;
                end
                RESULT:if(result_valid&&result_ready)begin done<=1;state<=IDLE;end
                DRAIN:if(!pending)begin aborted<=1;state<=IDLE;end
                default:begin state<=DRAIN;error<=1;error_code<=3;end
            endcase
        end
    end
endmodule
