// Qualified-commit descriptor queue plus dedicated BL8 LCD prefetch.
// One aligned request is outstanding; the next request overlaps serialization.
// Each response is buffered before eight
// x16 words are serialized into the unchanged dual-clock line-buffer endpoint.
// No provisional descriptor is accepted here; the root owner decides commit.
`timescale 1ns/1ps
module cu71_scanout_prefetch #(
    parameter logic [23:0] RGB_BASE=24'hc00000
)(
    input logic mem_clk,mem_rst,pixel_clk,pixel_reset_n,
    input logic descriptor_valid,output logic descriptor_ready,
    input logic [63:0] descriptor_generation,
    input logic [31:0] descriptor_frame_id,
    input logic descriptor_slot,
    output logic presented,error,
    output logic front_valid,front_slot,
    output logic [63:0] front_generation,
    output logic [31:0] front_frame_id,
    output logic pending_valid,
    output logic [31:0] presented_count,
    output logic frame_boundary,scanout_drained,
    output logic lcd_req_valid,input logic lcd_req_ready,
    output logic [23:0] lcd_req_addr,
    input logic lcd_rsp_valid,output logic lcd_rsp_ready,
    input logic [127:0] lcd_rsp_data,input logic lcd_rsp_error,
    output logic lcd_abort_i,input logic lcd_busy,lcd_aborted,
    output logic [31:0] underruns,memory_errors,
    output logic hsync,vsync,data_enable,
    output logic [9:0] physical_x,physical_y,
    output logic [7:0] red,green,blue
);
    logic [63:0] pending_generation,latest_generation;
    logic [31:0] pending_frame_id;
    logic pending_slot;
    logic line_req_valid,line_req_ready,line_data_valid,requests_idle;
    logic [23:0] line_req_address;
    logic [15:0] line_data;
    logic reading,request_pending,buffer_valid,failed_response_pending;
    logic [23:0] read_address;
    logic [8:0] burst_word,request_word;
    logic [2:0] lane;
    logic [127:0] burst_data;
    assign descriptor_ready=!pending_valid&&!mem_rst;
    assign scanout_drained=requests_idle&&!reading&&!request_pending&&
        !buffer_valid&&!failed_response_pending&&!lcd_busy;
    assign line_req_ready=!reading&&!lcd_busy&&!mem_rst;
    assign lcd_req_valid=reading&&!request_pending&&!failed_response_pending&&request_word<480&&!mem_rst;
    assign lcd_req_addr=read_address+24'(request_word);
    assign lcd_rsp_ready=reading&&request_pending&&!buffer_valid&&!mem_rst;
    assign lcd_abort_i=mem_rst;
    assign line_data_valid=reading&&buffer_valid&&!mem_rst;
    assign line_data=burst_data[16*lane+:16];
    always_ff @(posedge mem_clk)begin
        if(mem_rst)begin
            front_valid<=0;front_slot<=0;front_generation<=0;front_frame_id<=32'hffffffff;
            pending_valid<=0;pending_slot<=0;pending_generation<=0;pending_frame_id<=0;
            latest_generation<=0;presented<=0;error<=0;presented_count<=0;
            reading<=0;request_pending<=0;buffer_valid<=0;read_address<=0;
            burst_word<=0;request_word<=0;lane<=0;burst_data<=0;memory_errors<=0;failed_response_pending<=0;
        end else begin
            presented<=0;error<=0;
            if(descriptor_valid&&descriptor_ready)begin
                if(descriptor_generation==0||descriptor_generation<=latest_generation||
                   descriptor_frame_id==32'hffffffff||
                   (front_valid&&descriptor_frame_id<=front_frame_id))error<=1;
                else begin
                    pending_valid<=1;pending_generation<=descriptor_generation;
                    pending_frame_id<=descriptor_frame_id;pending_slot<=descriptor_slot;
                    latest_generation<=descriptor_generation;
                end
            end
            if(frame_boundary&&scanout_drained&&pending_valid)begin
                front_valid<=1;front_slot<=pending_slot;front_generation<=pending_generation;
                front_frame_id<=pending_frame_id;pending_valid<=0;
                presented<=1;presented_count<=presented_count+1;
            end
            if(line_req_valid&&line_req_ready)begin
                reading<=1;read_address<=RGB_BASE+line_req_address;burst_word<=0;request_word<=0;
            end
            if(lcd_req_valid&&lcd_req_ready)begin
                request_pending<=1;request_word<=request_word+9'd8;
            end
            if(lcd_aborted&&reading&&request_pending)begin
                request_pending<=0;failed_response_pending<=1;
                memory_errors<=memory_errors+1;error<=1;
            end else if(lcd_rsp_valid&&lcd_rsp_ready)begin
                request_pending<=0;buffer_valid<=1;lane<=0;
                burst_data<=lcd_rsp_error?128'd0:lcd_rsp_data;
                if(lcd_rsp_error)memory_errors<=memory_errors+1;
            end
            // A prefetched operation can abort while the previous burst is
            // still being serialized. Retain its failed response until that
            // buffer is free; never lose the abort acknowledgment or a lease.
            if(failed_response_pending&&!buffer_valid)begin
                failed_response_pending<=0;buffer_valid<=1;lane<=0;burst_data<=0;
            end
            if(line_data_valid)begin
                if(lane==7)begin
                    buffer_valid<=0;lane<=0;
                    if(burst_word==472)reading<=0;
                    else burst_word<=burst_word+9'd8;
                end else lane<=lane+1'b1;
            end
        end
    end
    cu71_lcd_lines lcd(
        .pixel_clk,.reset_n(pixel_reset_n),.mem_clk,.mem_reset(mem_rst),
        .front_valid,.front_buffer(front_slot),.pattern_enable(1'b0),
        .line_req_valid,.line_req_ready,.line_req_address,.line_data_valid,.line_data,
        .frame_boundary,.underruns,.requests_idle,
        .hsync,.vsync,.data_enable,.physical_x,.physical_y,.red,.green,.blue);
endmodule
