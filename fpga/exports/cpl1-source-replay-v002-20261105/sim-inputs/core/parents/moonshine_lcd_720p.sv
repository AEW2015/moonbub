// Native Rev4 timing derived from the existing lcd_native_colorbars_core.
// The two banks have explicit toggle ownership across unrelated clocks.
// A late line is black for its entire scan; a writer never touches a bank
// currently used for a good line. Framebuffer words are portrait row-major.
`timescale 1ns/1ps
`default_nettype none
module moonshine_lcd_720p (
    input wire pixel_clk, input wire reset_n,
    input wire mem_clk, input wire mem_reset,
    input wire front_valid, input wire front_buffer, input wire pattern_enable, input wire front_720p,
    input wire[6:0]display_margin,output wire frame_origin,
    input wire[9:0]timing_hsync,timing_vsync,timing_hstart,timing_vstart,timing_htotal,timing_vtotal,
    output reg line_req_valid, input wire line_req_ready,
    output reg [23:0] line_req_address,
    input wire line_data_valid, input wire [15:0] line_data,
    output reg frame_boundary,
    output wire [31:0] underruns,
    output reg hsync, output reg vsync, output reg data_enable,
    output reg [9:0] physical_x, output reg [9:0] physical_y,
    output wire [7:0] red, output wire [7:0] green, output wire [7:0] blue
);
    wire[9:0]H_TOTAL=timing_htotal,V_TOTAL=timing_vtotal,H_START=timing_hstart,V_START=timing_vstart;
    (* ram_style="block" *) reg [15:0] bank0 [0:479];
    (* ram_style="block" *) reg [15:0] bank1 [0:479];
    reg [9:0] x=0, y=0;
    wire [9:0] py=y-V_START;
    wire [9:0] px=x-H_START;
    wire active=(x>=H_START && x<H_START+480 && y>=V_START && y<V_START+800);
    wire[9:0] source_py=py-{3'd0,display_margin};
    wire canvas=(source_py<720);
    wire[10:0] prefetch_first_y={1'b0,V_START}+{4'd0,display_margin}-11'd2;
    wire[10:0] prefetch_limit_y={1'b0,V_START}+{4'd0,display_margin}+11'd718;
    assign frame_origin=(x==0 && y==0);
    reg [15:0] read0,read1;
    // An unconditional read in its own process infers the pixel-clock BRAM
    // read port. Reset/enable/mux logic around the array read can instead
    // produce an asynchronous LUTRAM crossing from the write clock.
    always @(posedge pixel_clk) begin
/*CPL_READ_GUARD_BEGIN*/        if(reset_n)begin
/*CPL_READ_GUARD_END*/        read0<=bank0[px[8:0]];
        read1<=bank1[px[8:0]];/*CPL_READ_GUARD_BEGIN*/
        end/*CPL_READ_GUARD_END*/
    end
    reg [15:0] pattern_pixel=0;
    reg scan_content=0,scan_good=0,scan_pattern=0,scan_odd=0;
    wire [15:0] pixel=!scan_content ? 16'd0 : scan_pattern ? pattern_pixel :
                     scan_good ? (scan_odd ? read1:read0):16'd0;
    assign red={pixel[15:11],pixel[15:13]};
    assign green={pixel[10:5],pixel[10:9]};
    assign blue={pixel[4:0],pixel[4:2]};

    reg request0=0,request1=0;
    (* DONT_TOUCH="TRUE" *) reg [9:0] request_line0=0,request_line1=0;
    reg request_epoch0=0,request_epoch1=0;
    reg frame_toggle=0;
    reg done0=0,done1=0;
    (* ASYNC_REG="TRUE" *) reg [1:0] done_sync0=0,done_sync1=0;
    (* ASYNC_REG="TRUE" *) reg [1:0] valid_sync=0,pattern_sync=0,mode_sync=0;
    reg busy0=0,busy1=0,loaded0=0,loaded1=0;
    reg [9:0] tag0=0,tag1=0;
    reg line_good=0;
    reg [31:0] underrun_count=0;
    reg [31:0] underrun_gray=0;
    (* ASYNC_REG="TRUE" *) reg [31:0] underrun_sync1=0,underrun_sync2=0;
    function automatic [31:0] ungray(input [31:0] value);
        integer i;
        begin ungray[31]=value[31]; for(i=30;i>=0;i=i-1) ungray[i]=ungray[i+1]^value[i]; end
    endfunction
    assign underruns=ungray(underrun_sync2);

    // Payload buses (line number/epoch) remain stable from request until done.
    // Only the request and completion tokens pass through synchronizers.
    always @(posedge pixel_clk) begin
        if(!reset_n) begin
            x<=0;y<=0;request0<=0;request1<=0;frame_toggle<=0;
            request_line0<=0;request_line1<=0;request_epoch0<=0;request_epoch1<=0;
            done_sync0<=0;done_sync1<=0;valid_sync<=0;pattern_sync<=0;mode_sync<=0;
            busy0<=0;busy1<=0;loaded0<=0;loaded1<=0;tag0<=0;tag1<=0;
            line_good<=0;underrun_count<=0;underrun_gray<=0;
            pattern_pixel<=0;scan_content<=0;scan_good<=0;scan_pattern<=0;scan_odd<=0;
            hsync<=0;vsync<=0;data_enable<=0;physical_x<=0;physical_y<=0;
        end else begin
            done_sync0<={done_sync0[0],done0};done_sync1<={done_sync1[0],done1};
            valid_sync<={valid_sync[0],front_valid};pattern_sync<={pattern_sync[0],pattern_enable};mode_sync<={mode_sync[0],front_720p};
            hsync<=x<timing_hsync;vsync<=y<timing_vsync;data_enable<=active;
            physical_x<=px;physical_y<=py;
            scan_content<=active && canvas && (pattern_sync[1] || !mode_sync[1] || (px>=37 && px<442));scan_good<=line_good;
            scan_pattern<=pattern_sync[1];scan_odd<=source_py[0];
            if(x==H_TOTAL-1) begin x<=0; if(y==V_TOTAL-1)y<=0;else y<=y+1'b1;end
            else x<=x+1'b1;
            if(busy0 && done_sync0[1]==request0) begin
                busy0<=0;loaded0<=request_epoch0==frame_toggle;tag0<=request_line0;
            end
            if(busy1 && done_sync1[1]==request1) begin
                busy1<=0;loaded1<=request_epoch1==frame_toggle;tag1<=request_line1;
            end
            if(x==0 && y==0) begin
                frame_toggle<=~frame_toggle;loaded0<=0;loaded1<=0;line_good<=0;
            end
            if(x==H_START-1) begin
                line_good<=valid_sync[1] && (source_py[0] ? loaded1 && tag1==source_py : loaded0 && tag0==source_py);
            end
            if(x==H_START && y>=V_START && y<V_START+800 && canvas && valid_sync[1] && !pattern_sync[1] && !line_good) begin
                underrun_count<=underrun_count+1'b1;
                underrun_gray<=((underrun_count+1'b1)>>1)^(underrun_count+1'b1);
            end
            // Native, network-independent color bars inside the canvas.
            case (source_py/90)
                0:pattern_pixel<=16'hffff;1:pattern_pixel<=16'hffe0;2:pattern_pixel<=16'h07ff;3:pattern_pixel<=16'h07e0;
                4:pattern_pixel<=16'hf81f;5:pattern_pixel<=16'hf800;6:pattern_pixel<=16'h001f;default:pattern_pixel<=0;
            endcase
            // Start loading row k+2 only after row k is completely scanned.
            // Source rows -2/-1 prime0/1; source parity selects banks for odd margins too.
            if(x==H_START+480 && {1'b0,y}>=prefetch_first_y && {1'b0,y}<prefetch_limit_y && valid_sync[1] && !pattern_sync[1]) begin
                if(source_py[0]) begin
                    if(!busy1)begin request1<=~request1;request_line1<=source_py+10'd2;request_epoch1<=frame_toggle;busy1<=1;loaded1<=0;end
                end else begin
                    if(!busy0)begin request0<=~request0;request_line0<=source_py+10'd2;request_epoch0<=frame_toggle;busy0<=1;loaded0<=0;end
                end
            end
        end
    end

    (* ASYNC_REG="TRUE" *) reg [1:0] request_sync0=0,request_sync1=0,frame_sync=0;
    reg seen0=0,seen1=0,frame_seen=0;
    reg receiving=0,selected=0;
    // Capture the held payload before address arithmetic. Keeping this raw
    // register explicit prevents absorption into a pixel-clock DSP input and
    // makes the bundled-data timing boundary unambiguous after synthesis.
    (* DONT_TOUCH="TRUE" *) reg [9:0] captured_line=0;
    reg captured_buffer=0,address_pending=0;
    reg [8:0] fill=0;
    always @(posedge mem_clk) begin
        if(mem_reset)begin
            request_sync0<=0;request_sync1<=0;frame_sync<=0;seen0<=0;seen1<=0;frame_seen<=0;
            done0<=0;done1<=0;receiving<=0;selected<=0;fill<=0;
            captured_line<=0;captured_buffer<=0;address_pending<=0;
            line_req_valid<=0;line_req_address<=0;frame_boundary<=0;
            underrun_sync1<=0;underrun_sync2<=0;
        end else begin
            request_sync0<={request_sync0[0],request0};request_sync1<={request_sync1[0],request1};
            frame_sync<={frame_sync[0],frame_toggle};
            frame_boundary<=frame_sync[1]!=frame_seen;frame_seen<=frame_sync[1];
            underrun_sync1<=underrun_gray;underrun_sync2<=underrun_sync1;
            if(!receiving && !line_req_valid && !address_pending)begin
                if(request_sync0[1]!=seen0)begin
                    selected<=0;seen0<=request_sync0[1];address_pending<=1;
                    captured_line<=request_line0;captured_buffer<=front_buffer;
                end else if(request_sync1[1]!=seen1)begin
                    selected<=1;seen1<=request_sync1[1];address_pending<=1;
                    captured_line<=request_line1;captured_buffer<=front_buffer;
                end
            end
            if(address_pending)begin
                line_req_address<=(captured_buffer?24'h080000:24'h000000)+captured_line*24'd480;
                line_req_valid<=1;address_pending<=0;
            end
            if(line_req_valid && line_req_ready)begin line_req_valid<=0;receiving<=1;fill<=0;end
            if(receiving && line_data_valid)begin
                if(selected)bank1[fill]<=line_data;else bank0[fill]<=line_data;
                if(fill==479)begin
                    receiving<=0;
                    if(selected)done1<=seen1;else done0<=seen0;
                end else fill<=fill+1'b1;
            end
        end
    end
endmodule
`default_nettype wire
