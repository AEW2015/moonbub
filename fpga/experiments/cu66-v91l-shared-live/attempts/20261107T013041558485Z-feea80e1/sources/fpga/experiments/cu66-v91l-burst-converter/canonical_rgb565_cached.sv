// Bounded two-row chroma cache, exact native YUV420 -> RGB565 arithmetic.
// Cache payload is four 180x16 row/parity banks; RAM reads are registered.
module canonical_rgb565_cached (
    input logic clk, reset, start, cancel,
    input logic [31:0] start_epoch,
    output logic start_ready, busy, draining, done,
    output logic [7:0] error,
    input logic probe_hit,
    input logic [7:0] probe_data,
    output logic probe_valid,
    output logic [18:0] probe_addr,
    output logic [31:0] probe_epoch,
    output logic [63:0] count_direct_consumes,count_canonical_consumed,
    output logic direct_consume,
    output logic [18:0] direct_addr,
    output logic [31:0] direct_epoch,
    output logic [7:0] direct_data,
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
    output logic [3:0] state,
    output logic [63:0] count_reads, count_responses, count_pixels, count_cycles,
    output logic [63:0] count_luma_reads, count_chroma_reads, count_lookups,
    output logic [63:0] count_row_fills, count_cache_hits,
    output logic [1:0] row_valid,
    output logic [7:0] row_tag [0:1],
    output logic [7:0] fill_row,
    output logic fill_slot, fill_plane,
    output logic [8:0] fill_column,
    output logic lookup_launch, lookup_response, dbg_pending
);
    localparam logic [3:0] IDLE=0, CHECK_ROWS=1, FILL_REQ=2, FILL_WAIT=3,
        LUMA_REQ=4, LUMA_WAIT=5, LOOKUP_REQ=6, LOOKUP_WAIT=7, CONVERT=8, EMIT=9;
    logic running;
    logic fill_write;
    logic [7:0] fill_data;
    // Configuration initialization establishes empty power-on ownership only.
    // Local reset/cancel must not retract an accepted physical read.
    logic pending=1'b0;
    logic [31:0] epoch;
    logic [9:0] x;
    logic [8:0] y;
    logic [7:0] luma;
    logic [7:0] cy, bottom_row;
    logic [8:0] cx;
    logic rows_match, kill;
    logic [7:0] even_address,odd_address;
    logic [15:0] slot0_even [0:179];
    logic [15:0] slot0_odd [0:179];
    logic [15:0] slot1_even [0:179];
    logic [15:0] slot1_odd [0:179];
    logic [15:0] read0_even,read0_odd,read1_even,read1_odd;
    logic [15:0] top_left,top_right,bottom_left,bottom_right;
    logic [7:0] cb_tl,cb_tr,cb_bl,cb_br,cr_tl,cr_tr,cr_bl,cr_br;
    integer cb_top,cb_bottom,cr_top,cr_bottom,cb_value,cr_value;
    integer y_value,r_value,g_value,b_value;
    logic [15:0] converted;

    function automatic integer clip(input integer value);
        if(value<0)return 0;
        if(value>255)return 255;
        return value;
    endfunction
    task automatic fail(input logic [7:0] reason);
        running<=0;state<=IDLE;done<=0;error<=reason;row_valid<=0;
    endtask

    assign kill=reset||cancel||error!=0;
    assign cy=y[8:1];
    assign cx=x[9:1];
    assign bottom_row=cy==239?8'd239:cy+8'd1;
    assign rows_match=row_valid[cy[0]]&&row_tag[cy[0]]==cy&&
        row_valid[bottom_row[0]]&&row_tag[bottom_row[0]]==bottom_row;
    assign even_address=cx[0]&&cx<359?cx[8:1]+8'd1:cx[8:1];
    assign odd_address=cx[8:1];
    assign lookup_launch=running&&state==LOOKUP_REQ&&rows_match&&!kill;
    assign lookup_response=running&&state==LOOKUP_WAIT&&!kill;
    assign dbg_pending=pending;
    assign busy=running||pending;
    assign draining=!running&&pending;
    assign start_ready=!busy&&!reset&&!cancel;
    // Probe eligibility is independent of the hit-gated external request.
    assign probe_valid=running&&(state==FILL_REQ||state==LUMA_REQ)&&!pending&&!kill&&!start;
    assign probe_addr=mem_req_addr;
    assign probe_epoch=epoch;
    assign direct_consume=probe_valid&&probe_hit;
    assign direct_addr=probe_addr;
    assign direct_epoch=epoch;
    assign direct_data=probe_data;
    assign mem_req_valid=probe_valid&&!probe_hit;
    assign fill_write=(pending&&mem_rsp_valid&&mem_rsp_epoch==epoch&&running&&
        state==FILL_WAIT&&!mem_rsp_error&&!kill)||(direct_consume&&state==FILL_REQ);
    assign fill_data=direct_consume?probe_data:mem_rsp_data;
    assign mem_req_addr=state==FILL_REQ?
        19'((fill_plane?432000:345600)+32'(fill_row)*360+32'(fill_column)):
        19'(32'(y)*720+32'(x));
    assign mem_req_epoch=epoch;
    assign mem_rsp_ready=pending;
    assign out_valid=running&&state==EMIT&&!kill;
    assign out_addr=19'(32'(y)*720+32'(x));
    assign out_epoch=epoch;

    // Each bank has one registered read port. Neighbor columns have opposite
    // parity; top/bottom rows have separate slots except replicated last row.
    always_ff @(posedge clk)begin
        if(lookup_launch)begin
            read0_even<=slot0_even[even_address];read0_odd<=slot0_odd[odd_address];
            read1_even<=slot1_even[even_address];read1_odd<=slot1_odd[odd_address];
        end
        // Independent byte enables preserve the other component during fill.
        // Fill and lookup states are disjoint, and no payload bulk reset occurs.
        if(fill_write)begin
            if(!fill_slot&&!fill_column[0])begin
                if(!fill_plane)slot0_even[fill_column[8:1]][7:0]<=fill_data;
                else slot0_even[fill_column[8:1]][15:8]<=fill_data;
            end else if(!fill_slot&&fill_column[0])begin
                if(!fill_plane)slot0_odd[fill_column[8:1]][7:0]<=fill_data;
                else slot0_odd[fill_column[8:1]][15:8]<=fill_data;
            end else if(fill_slot&&!fill_column[0])begin
                if(!fill_plane)slot1_even[fill_column[8:1]][7:0]<=fill_data;
                else slot1_even[fill_column[8:1]][15:8]<=fill_data;
            end else begin
                if(!fill_plane)slot1_odd[fill_column[8:1]][7:0]<=fill_data;
                else slot1_odd[fill_column[8:1]][15:8]<=fill_data;
            end
        end
    end
    always_comb begin
        if(!cy[0])begin
            top_left=cx[0]?read0_odd:read0_even;
            top_right=cx==359?top_left:(cx[0]?read0_even:read0_odd);
        end else begin
            top_left=cx[0]?read1_odd:read1_even;
            top_right=cx==359?top_left:(cx[0]?read1_even:read1_odd);
        end
        if(!bottom_row[0])begin
            bottom_left=cx[0]?read0_odd:read0_even;
            bottom_right=cx==359?bottom_left:(cx[0]?read0_even:read0_odd);
        end else begin
            bottom_left=cx[0]?read1_odd:read1_even;
            bottom_right=cx==359?bottom_left:(cx[0]?read1_even:read1_odd);
        end
        cb_top=32'(cb_tl);cb_bottom=32'(cb_bl);
        cr_top=32'(cr_tl);cr_bottom=32'(cr_bl);
        if(x[0])begin
            cb_top=(32'(cb_tl)+32'(cb_tr)+1)/2;
            cb_bottom=(32'(cb_bl)+32'(cb_br)+1)/2;
            cr_top=(32'(cr_tl)+32'(cr_tr)+1)/2;
            cr_bottom=(32'(cr_bl)+32'(cr_br)+1)/2;
        end
        cb_value=(y[0]?(cb_top+cb_bottom+1)/2:cb_top)-128;
        cr_value=(y[0]?(cr_top+cr_bottom+1)/2:cr_top)-128;
        y_value=32'(luma);
        r_value=clip(y_value+((359*cr_value+128)>>>8));
        g_value=clip(y_value-((88*cb_value+183*cr_value+128)>>>8));
        b_value=clip(y_value+((454*cb_value+128)>>>8));
        converted=16'(((r_value>>3)<<11)|((g_value>>2)<<5)|(b_value>>3));
    end

    always_ff @(posedge clk)begin
        if(reset||cancel)begin
            running<=0;state<=IDLE;done<=0;error<=0;row_valid<=0;
            x<=0;y<=0;fill_row<=0;fill_slot<=0;fill_plane<=0;fill_column<=0;
            out_word<=0;
            if(pending&&mem_rsp_valid&&mem_rsp_epoch==epoch)pending<=0;
            if(reset)begin
                count_reads<=0;count_responses<=0;count_pixels<=0;count_cycles<=0;
                count_luma_reads<=0;count_chroma_reads<=0;count_lookups<=0;
                count_row_fills<=0;count_cache_hits<=0;
                count_direct_consumes<=0;count_canonical_consumed<=0;
            end
        end else begin
            if(pending&&mem_rsp_valid)begin
                if(mem_rsp_epoch==epoch)pending<=0;
                if(running)begin
                    if(mem_rsp_epoch==epoch)count_responses<=count_responses+1;
                    if(mem_rsp_epoch==epoch&&!mem_rsp_error&&(state==FILL_WAIT||state==LUMA_WAIT))
                        count_canonical_consumed<=count_canonical_consumed+1;
                    if(mem_rsp_error||mem_rsp_epoch!=epoch)fail(mem_rsp_error?8'd2:8'd1);
                    else if(state==FILL_WAIT)begin
                        if(fill_column==359)begin
                            fill_column<=0;
                            if(!fill_plane)begin fill_plane<=1;state<=FILL_REQ;end
                            else begin
                                row_tag[fill_slot]<=fill_row;row_valid[fill_slot]<=1;
                                count_row_fills<=count_row_fills+1;state<=CHECK_ROWS;
                            end
                        end else begin fill_column<=fill_column+1;state<=FILL_REQ;end
                    end else if(state==LUMA_WAIT)begin luma<=mem_rsp_data;state<=LOOKUP_REQ;end
                    else fail(4);
                end
            end
            if(start&&start_ready)begin
                running<=start_epoch!=0;epoch<=start_epoch;pending<=0;
                state<=start_epoch!=0?CHECK_ROWS:IDLE;done<=0;error<=start_epoch!=0?8'd0:8'd3;
                row_valid<=0;x<=0;y<=0;fill_row<=0;fill_slot<=0;fill_plane<=0;fill_column<=0;
                out_word<=0;
                count_reads<=0;count_responses<=0;count_pixels<=0;count_cycles<=0;
                count_luma_reads<=0;count_chroma_reads<=0;count_lookups<=0;
                count_row_fills<=0;count_cache_hits<=0;
                count_direct_consumes<=0;count_canonical_consumed<=0;
            end else if(running)begin
                count_cycles<=count_cycles+1;
                if(direct_consume)begin
                    count_direct_consumes<=count_direct_consumes+1;
                    count_canonical_consumed<=count_canonical_consumed+1;
                    if(state==FILL_REQ)begin
                        if(fill_column==359)begin
                            fill_column<=0;
                            if(!fill_plane)begin fill_plane<=1;state<=FILL_REQ;end
                            else begin
                                row_tag[fill_slot]<=fill_row;row_valid[fill_slot]<=1;
                                count_row_fills<=count_row_fills+1;state<=CHECK_ROWS;
                            end
                        end else begin fill_column<=fill_column+1;state<=FILL_REQ;end
                    end else begin luma<=probe_data;state<=LOOKUP_REQ;end
                end
                if(mem_req_valid&&mem_req_ready)begin
                    pending<=1;count_reads<=count_reads+1;
                    if(state==FILL_REQ)begin state<=FILL_WAIT;count_chroma_reads<=count_chroma_reads+1;end
                    else begin state<=LUMA_WAIT;count_luma_reads<=count_luma_reads+1;end
                end
                case(state)
                    CHECK_ROWS:begin
                        if(!row_valid[cy[0]]||row_tag[cy[0]]!=cy)begin
                            fill_row<=cy;fill_slot<=cy[0];fill_plane<=0;fill_column<=0;
                            row_valid[cy[0]]<=0;state<=FILL_REQ;
                        end else if(!row_valid[bottom_row[0]]||row_tag[bottom_row[0]]!=bottom_row)begin
                            fill_row<=bottom_row;fill_slot<=bottom_row[0];fill_plane<=0;fill_column<=0;
                            row_valid[bottom_row[0]]<=0;state<=FILL_REQ;
                        end else state<=LUMA_REQ;
                    end
                    LOOKUP_REQ:begin
                        if(!rows_match)fail(4);
                        else begin count_lookups<=count_lookups+1;count_cache_hits<=count_cache_hits+1;state<=LOOKUP_WAIT;end
                    end
                    LOOKUP_WAIT:begin
                        cb_tl<=top_left[7:0];cr_tl<=top_left[15:8];
                        cb_tr<=top_right[7:0];cr_tr<=top_right[15:8];
                        cb_bl<=bottom_left[7:0];cr_bl<=bottom_left[15:8];
                        cb_br<=bottom_right[7:0];cr_br<=bottom_right[15:8];
                        state<=CONVERT;
                    end
                    CONVERT:begin out_word<=converted;state<=EMIT;end
                    EMIT:if(out_ready)begin
                        count_pixels<=count_pixels+1;
                        if(x==719&&y==479)begin running<=0;state<=IDLE;done<=1;end
                        else if(x==719)begin x<=0;y<=y+1;state<=CHECK_ROWS;end
                        else begin x<=x+1;state<=LUMA_REQ;end
                    end
                    default:begin end
                endcase
            end
        end
    end
`ifndef SYNTHESIS
    always_ff @(posedge clk)if(!reset&&!cancel)begin
        if(direct_consume)assert(!pending&&!mem_req_valid&&probe_valid&&probe_addr<518400&&(state==FILL_REQ||state==LUMA_REQ))else $fatal(1,"direct consume ownership");
        if(mem_req_valid)assert(!pending&&mem_req_addr<518400)else $fatal(1,"cached RGB read ownership/range");
        if(lookup_launch)assert(rows_match&&even_address<180&&odd_address<180&&!pending)else $fatal(1,"cached RGB lookup without owned rows");
        if(out_valid)assert(!pending&&rows_match)else $fatal(1,"cached RGB output without valid row lease");
        if(state==FILL_REQ&&running)assert(!row_valid[fill_slot]&&fill_row<240&&fill_column<360)else $fatal(1,"cached RGB fill publishes incomplete row");
        if(done)assert(!busy&&count_pixels==345600&&count_canonical_consumed==518400&&count_reads==count_responses&&count_reads+count_direct_consumes==count_canonical_consumed&&count_row_fills==240)else $fatal(1,"cached RGB completion before drain");
    end
`endif
endmodule
