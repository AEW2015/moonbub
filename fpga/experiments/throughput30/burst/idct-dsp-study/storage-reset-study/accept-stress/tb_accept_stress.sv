`timescale 1ns/1ps
module tb_accept_stress;
reg clk=0; always #5 clk=~clk;
reg rst=1,start=0,valid=0,eob=0,ready=1; reg [15:0] data=0; reg [5:0] idx=0; reg [31:0] id=0;
wire accept,ov; wire [31:0] od,oid; wire [5:0] oi;
jpeg_idct dut(.clk_i(clk),.rst_i(rst),.img_start_i(start),.img_end_i(1'b0),.inport_valid_i(valid),.inport_data_i(data),.inport_idx_i(idx),.inport_eob_i(eob),.inport_id_i(id),.outport_accept_i(ready),.inport_accept_o(accept),.outport_valid_o(ov),.outport_data_o(od),.outport_idx_o(oi),.outport_id_o(oid));
integer accepted=0,rejected=0,cycles=0,excluded=0,blocks=0; reg [31:0] rng=32'h4321abcd; integer seed=0,mode=0,n,k,terms,gap;
function automatic [31:0] step(input [31:0] x); step=(x<<13)^x; step=(step>>17)^step; step=(step<<5)^step; endfunction
always @(posedge clk) begin
 cycles<=cycles+1;
 if(rst||start) excluded<=excluded+1;
 else if(dut.idct_x_valid_w) begin
  if(dut.idct_x_accept_w) accepted<=accepted+1;
  else begin rejected<=rejected+1;$display("REJECT cycle=%0d idx=%0d block=%0d",cycles,dut.idct_x_idx_w,blocks);$fatal(1,"X beat rejected");end
 end
end
always @(negedge clk) begin
 rng=step(rng);
 if(mode==0) ready=1;
 else ready=(rng[3:0]!=0 && rng[4]);
end
task beat(input bit v,input bit e,input [5:0] i,input [15:0] d);
 begin
  @(negedge clk); while(!accept) @(negedge clk);
  valid=v;eob=e;idx=i;data=d;
  @(negedge clk);valid=0;eob=0;
 end
endtask
initial begin
 if(!$value$plusargs("SEED=%d",seed))seed=1;
 if(!$value$plusargs("MODE=%d",mode))mode=0;
 rng=32'h9e3779b9 ^ seed;
 repeat(4) @(negedge clk);rst=0;start=1;@(negedge clk);start=0;
 for(n=0;n<256;n=n+1) begin
  id=n;terms=(n%8)+1;
  for(k=0;k<terms;k=k+1) begin
   gap=(n+k+seed)%4;repeat(gap) @(negedge clk);
   beat(1,0,k*8,16'(n*31+k+1));
  end
  beat(0,1,0,0);blocks=blocks+1;
 end
 repeat(3000) @(negedge clk);
 if(accepted!=256*64||rejected!=0)$fatal(1,"bad counts accepted=%0d rejected=%0d",accepted,rejected);
 $display("ACCEPT_STRESS_PASS seed=%0d mode=%0d blocks=%0d accepted=%0d rejected=%0d cycles=%0d excluded=%0d",seed,mode,blocks,accepted,rejected,cycles,excluded);$finish;
end
initial begin #20000000;$fatal(1,"simulation timeout");end
endmodule
