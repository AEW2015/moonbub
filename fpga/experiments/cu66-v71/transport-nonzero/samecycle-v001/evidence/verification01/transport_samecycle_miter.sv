`timescale 1ns/1ps
module transport_samecycle_old(input wire clk100,rst,reconfigure_required,input wire[31:0]transport_gray,output wire fault,output wire[97:0]history,output wire nonzero);
 (* ASYNC_REG="TRUE" *)reg[1:0]quarantine_sync=0;
 always @(posedge clk100)quarantine_sync<={quarantine_sync[0],reconfigure_required};
 (* ASYNC_REG="TRUE" *)reg[31:0]transport_gray_meta=0,transport_gray_sync=0;
 reg[31:0]transport_lost_words=0;
 function automatic[31:0]ungray_transport(input[31:0]value);
 integer i;begin for(i=0;i<32;i=i+1)ungray_transport[i]=^(value>>i);end endfunction
 always @(posedge clk100)begin
  if(rst)begin transport_gray_meta<=0;transport_gray_sync<=0;transport_lost_words<=0;end
  else begin transport_gray_meta<=transport_gray;transport_gray_sync<=transport_gray_meta;transport_lost_words<=ungray_transport(transport_gray_sync);end
 end
 wire transport_fault=quarantine_sync[1]||transport_lost_words!=0;
assign fault=transport_fault;assign history={quarantine_sync,transport_gray_meta,transport_gray_sync,transport_lost_words};assign nonzero=transport_lost_words!=0;
endmodule
module transport_samecycle_new(input wire clk100,rst,reconfigure_required,input wire[31:0]transport_gray,output wire fault,output wire[97:0]history,output wire nonzero);
 (* ASYNC_REG="TRUE" *)reg[1:0]quarantine_sync=0;
 always @(posedge clk100)quarantine_sync<={quarantine_sync[0],reconfigure_required};
 (* ASYNC_REG="TRUE" *)reg[31:0]transport_gray_meta=0,transport_gray_sync=0;
 reg[31:0]transport_lost_words=0;
 (* MAX_FANOUT=64 *)reg transport_lost_nonzero=0;
 function automatic[31:0]ungray_transport(input[31:0]value);
 integer i;begin for(i=0;i<32;i=i+1)ungray_transport[i]=^(value>>i);end endfunction
 always @(posedge clk100)begin
  if(rst)begin transport_gray_meta<=0;transport_gray_sync<=0;transport_lost_words<=0;transport_lost_nonzero<=0;end
  else begin transport_gray_meta<=transport_gray;transport_gray_sync<=transport_gray_meta;transport_lost_words<=ungray_transport(transport_gray_sync);transport_lost_nonzero<=|transport_gray_sync;end
 end
 wire transport_fault=quarantine_sync[1]||transport_lost_nonzero;
assign fault=transport_fault;assign history={quarantine_sync,transport_gray_meta,transport_gray_sync,transport_lost_words};assign nonzero=transport_lost_nonzero;
endmodule
module transport_samecycle_miter(input wire clk100,rst,reconfigure_required,input wire[31:0]transport_gray,output wire mismatch,output wire old_fault,new_fault,old_nonzero,new_nonzero,output wire[97:0]old_history,new_history);
transport_samecycle_old old_dut(.clk100,.rst,.reconfigure_required,.transport_gray,.fault(old_fault),.history(old_history),.nonzero(old_nonzero));
transport_samecycle_new new_dut(.clk100,.rst,.reconfigure_required,.transport_gray,.fault(new_fault),.history(new_history),.nonzero(new_nonzero));
assign mismatch=(old_history!=new_history)||(old_nonzero!=new_nonzero)||(old_fault!=new_fault);
endmodule
