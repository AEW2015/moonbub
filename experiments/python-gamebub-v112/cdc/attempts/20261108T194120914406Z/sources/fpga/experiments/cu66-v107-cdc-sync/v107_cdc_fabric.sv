`timescale 1ns/1ps
`default_nettype none
// NEW synchronous-BRAM-control prototype; no production parent connection.
// Four explicit clock inputs have NO board-frequency assumption.
// Any reset/abort request flushes ALL channel owners and pending work.
module v107_cdc_fabric (
    input wire transport_clk,decoder_clk,memory_clk,display_clk,
    input wire [3:0] reset_request,
    output wire [3:0] local_reset,
    input wire command_valid,output wire command_ready,input wire [43:0] command_data,
    output wire decoder_command_valid,input wire decoder_command_ready,output wire [43:0] decoder_command_data,
    input wire write_valid,output wire write_ready,input wire [93:0] write_data,
    output wire memory_write_valid,input wire memory_write_ready,output wire [93:0] memory_write_data,
    input wire ack_valid,output wire ack_ready,input wire [86:0] ack_data,
    output wire decoder_ack_valid,input wire decoder_ack_ready,output wire [86:0] decoder_ack_data,
    input wire line_valid,output wire line_ready,input wire [23:0] line_data,
    output wire memory_line_valid,input wire memory_line_ready,output wire [23:0] memory_line_data,
    input wire pixel_valid,output wire pixel_ready,input wire [15:0] pixel_data,
    output wire display_pixel_valid,input wire display_pixel_ready,output wire [15:0] display_pixel_data
);
    wire coordinated_reset=|reset_request;
    v107_reset_release transport_reset(.clk(transport_clk),.async_reset(coordinated_reset),.reset(local_reset[0]));
    v107_reset_release decoder_reset(.clk(decoder_clk),.async_reset(coordinated_reset),.reset(local_reset[1]));
    v107_reset_release memory_reset(.clk(memory_clk),.async_reset(coordinated_reset),.reset(local_reset[2]));
    v107_reset_release display_reset(.clk(display_clk),.async_reset(coordinated_reset),.reset(local_reset[3]));
    v107_async_fifo #(.WIDTH(44)) commands(.async_reset(coordinated_reset),.wclk(transport_clk),.wrst(local_reset[0]),.wvalid(command_valid),.wready(command_ready),.wdata(command_data),.rclk(decoder_clk),.rrst(local_reset[1]),.rvalid(decoder_command_valid),.rready(decoder_command_ready),.rdata(decoder_command_data));
    v107_async_fifo #(.WIDTH(94)) writes(.async_reset(coordinated_reset),.wclk(decoder_clk),.wrst(local_reset[1]),.wvalid(write_valid),.wready(write_ready),.wdata(write_data),.rclk(memory_clk),.rrst(local_reset[2]),.rvalid(memory_write_valid),.rready(memory_write_ready),.rdata(memory_write_data));
    v107_async_fifo #(.WIDTH(87)) acks(.async_reset(coordinated_reset),.wclk(memory_clk),.wrst(local_reset[2]),.wvalid(ack_valid),.wready(ack_ready),.wdata(ack_data),.rclk(decoder_clk),.rrst(local_reset[1]),.rvalid(decoder_ack_valid),.rready(decoder_ack_ready),.rdata(decoder_ack_data));
    v107_async_fifo #(.WIDTH(24)) lines(.async_reset(coordinated_reset),.wclk(display_clk),.wrst(local_reset[3]),.wvalid(line_valid),.wready(line_ready),.wdata(line_data),.rclk(memory_clk),.rrst(local_reset[2]),.rvalid(memory_line_valid),.rready(memory_line_ready),.rdata(memory_line_data));
    v107_async_fifo #(.WIDTH(16)) pixels(.async_reset(coordinated_reset),.wclk(memory_clk),.wrst(local_reset[2]),.wvalid(pixel_valid),.wready(pixel_ready),.wdata(pixel_data),.rclk(display_clk),.rrst(local_reset[3]),.rvalid(display_pixel_valid),.rready(display_pixel_ready),.rdata(display_pixel_data));
endmodule
`default_nettype wire
