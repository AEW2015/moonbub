`timescale 1ns/1ps
module tb_tile_full_trace;
 reg clk=0,reset=1,abort=0,in_valid=0,out_ready=0;
 reg [23:0] in_address=0;reg [15:0] in_data=0;
 wire in_ready,out_valid,first,last,fault;wire [23:0] out_address;wire [15:0] out_data;
 reg [23:0] addresses[0:63];reg [15:0] values[0:63];
 reg [31:0] random_state=32'h48b25b41;
 integer fd,rc,index,pixel,i,j,b,srcidx,total=0,x,y;
 reg[2047:0] trace_name;
 always #5 clk=~clk;
 moonbub_tile_transpose dut(clk,reset,abort,in_valid,in_ready,in_address,in_data,
  out_valid,out_ready,out_address,out_data,first,last,fault);
 initial begin
  if(!$value$plusargs("TRACE_FILE=%s",trace_name))trace_name="/ross-work/tile-study/decoded-rgb565.txt";
  fd=$fopen(trace_name,"r");
  if(!fd)$fatal(1,"missing trace");
  repeat(4)@(negedge clk);reset=0;
  for(b=0;b<5400;b=b+1)begin
   for(i=0;i<64;i=i+1)begin
    rc=$fscanf(fd,"%d %h\n",index,pixel);
    if(rc!=2)$fatal(1,"trace ended at block %0d pixel %0d",b,i);
    x=index%720;y=index/720;
    addresses[i]=24'h080000+(x+40)*480+y;values[i]=pixel;
   end
   for(i=0;i<64;i=i+1)begin
    @(negedge clk);if(!in_ready)$fatal(1,"unexpected input backpressure");
    in_valid=1;in_address=addresses[i];in_data=values[i];
   end
   @(negedge clk);in_valid=0;
   j=0;
   while(j<64)begin
    random_state={random_state[30:0],random_state[31]^random_state[21]^random_state[1]^random_state[0]};
    out_ready=random_state[0] | random_state[3];
    @(posedge clk);
    if(out_valid && out_ready)begin
     srcidx=(j%8)*8+(j/8);
     if(out_address!==addresses[srcidx] || out_data!==values[srcidx])
      $fatal(1,"trace mismatch block=%0d output=%0d",b,j);
     if(first!==((j%8)==0) || last!==((j%8)==7))$fatal(1,"burst mismatch");
     total=total+1;j=j+1;
    end
    @(negedge clk);
   end
   out_ready=0;
   if(fault)$fatal(1,"unexpected fault");
  end
  if(total!=345600)$fatal(1,"wrong output count");
  rc=$fscanf(fd,"%d %h",index,pixel);if(rc==2)$fatal(1,"unexpected extra pixels");
  $fclose(fd);$display("TEST_PASS_FULL_TRACE blocks=%0d pixels=%0d",b,total);$finish;
 end
 initial begin #20000000;$fatal(1,"full trace watchdog");end
endmodule
