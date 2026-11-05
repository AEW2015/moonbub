// Descriptor queue and scalar reader around existing dual-clock LCD line RTL.
// Descriptor input is ALREADY globally committed; never queues provisional data.
`timescale 1ns/1ps
module cu70_scanout #(
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
    output logic aux_req_valid,input logic aux_req_ready,
    output logic aux_req_write,
    output logic [23:0] aux_req_addr,
    output logic [15:0] aux_req_data,
    input logic aux_rsp_valid,output logic aux_rsp_ready,
    input logic [15:0] aux_rsp_data,input logic aux_rsp_error,
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
    logic reading,request_pending;
    logic [23:0] read_address;
    logic [8:0] word_index;
    assign descriptor_ready=!pending_valid&&!mem_rst;
    assign scanout_drained=requests_idle&&!reading&&!request_pending;
    assign line_req_ready=!reading&&!mem_rst;
    assign aux_req_valid=reading&&!request_pending&&!mem_rst;
    assign aux_req_write=0;
    assign aux_req_data=0;
    assign aux_req_addr=read_address+24'(word_index);
    assign aux_rsp_ready=reading&&request_pending&&!mem_rst;
    assign line_data_valid=aux_rsp_valid&&aux_rsp_ready;
    // A failed read is consumed as black while preserving line framing.
    assign line_data=aux_rsp_error?16'd0:aux_rsp_data;
    always_ff @(posedge mem_clk)begin
        if(mem_rst)begin
            front_valid<=0;front_slot<=0;front_generation<=0;front_frame_id<=32'hffffffff;
            pending_valid<=0;pending_slot<=0;pending_generation<=0;pending_frame_id<=0;
            latest_generation<=0;presented<=0;error<=0;presented_count<=0;
            reading<=0;request_pending<=0;read_address<=0;word_index<=0;memory_errors<=0;
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
                reading<=1;read_address<=RGB_BASE+line_req_address;word_index<=0;
            end
            if(aux_req_valid&&aux_req_ready)request_pending<=1;
            if(aux_rsp_valid&&aux_rsp_ready)begin
                request_pending<=0;
                if(aux_rsp_error)memory_errors<=memory_errors+1;
                if(word_index==479)reading<=0;else word_index<=word_index+1;
            end
        end
    end
    cu70_lcd_lines lcd(
        .pixel_clk,.reset_n(pixel_reset_n),.mem_clk,.mem_reset(mem_rst),
        .front_valid,.front_buffer(front_slot),.pattern_enable(1'b0),
        .line_req_valid,.line_req_ready,.line_req_address,.line_data_valid,.line_data,
        .frame_boundary,.underruns,.requests_idle,
        .hsync,.vsync,.data_enable,.physical_x,.physical_y,.red,.green,.blue);
endmodule
