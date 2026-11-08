`timescale 1ns/1ps
module cu66_tables_unit_v107 (
 input wire clk,reset,start,abort_packet,
 input wire a_write,input wire[10:0]a_addr,input wire[1:0]a_data,
 input wire b_write,b_read,input wire[10:0]b_addr,input wire[1:0]b_data,output wire[1:0]b_q,
 input wire mode_write,mode_read,input wire[12:0]mode_address,mode_read_address,
 input wire[1:0]mode_data,output wire[1:0]mode_q
);
 wire live=!reset&&!start&&!abort_packet;
 cu66_scale_tdp_v107 scales(.clk(clk),.a_write(a_write&&live),.a_addr(a_addr),.a_data(a_data),
 .b_write(b_write&&live),.b_read(b_read&&live),.b_addr(b_addr),.b_data(b_data),.b_q(b_q));
 cu66_mode_store_v107 modes(.clk(clk),.write_enable(mode_write&&live),.write_address(mode_address),
 .write_data(mode_data),.read_enable(mode_read&&live),.read_address(mode_read_address),.q(mode_q));
endmodule
