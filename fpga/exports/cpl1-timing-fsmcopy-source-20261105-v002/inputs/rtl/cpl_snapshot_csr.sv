`timescale 1ns/1ps
// Private observation only: no data-plane/reset/start controls.
module cpl_snapshot_csr(
 input wire clk,reset,bus_write,input wire[11:0]bus_address,input wire[31:0]bus_wdata,
 input wire[1279:0]live_words,output wire[31:0]bus_rdata,
 output reg[31:0]ignored_writes,output reg ignored_exhausted
);
 reg[1279:0]snapshot;reg[31:0]generation;
 wire in_snapshot=bus_address>=12'h500&&bus_address<=12'h59c&&bus_address[1:0]==0;
 wire capture=bus_write&&bus_address==12'h500&&bus_wdata!=0;
 assign bus_rdata=bus_address==12'h000 ? 32'h314c5043:
  bus_address==12'h004 ? 32'h00010000:bus_address==12'h008 ? 32'd0:
  bus_address==12'h184 ? 32'h43505231:in_snapshot ? snapshot[((bus_address-12'h500)>>2)*32+:32]:32'd0;
 always @(posedge clk)begin
  if(reset)begin snapshot<=0;generation<=0;ignored_writes<=0;ignored_exhausted<=0;end
  else begin
   if(capture)begin
    if(generation>=32'hfffffffe)begin
     generation<=32'hffffffff;snapshot[0+:32]<=0;snapshot[32+:32]<=32'hffffffff;snapshot[3*32+11]<=1;
    end else begin
     snapshot<=live_words;snapshot[0+:32]<=bus_wdata;snapshot[32+:32]<=generation+1'b1;snapshot[64+:32]<=32'h00010000;
     generation<=generation+1'b1;
    end
   end else if(bus_write)begin
    if(ignored_writes>=32'hfffffffe)begin ignored_writes<=32'hffffffff;ignored_exhausted<=1;end
    else ignored_writes<=ignored_writes+1'b1;
   end
  end
 end
endmodule
