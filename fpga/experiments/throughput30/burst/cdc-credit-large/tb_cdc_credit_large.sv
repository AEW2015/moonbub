`timescale 1ns/1ps
module tb_cdc_credit_large;
 reg sc=0,cc=0,reset=1,wr=0;integer core_half_ps=5000;always #2.5 sc=~sc;always #(core_half_ps/1000.0) cc=~cc;
 reg[31:0]data=0;wire[31:0]rdata,gray,cdata;wire[11:0]caddr;wire lost,cwrite;wire[11:0]free_count;
 integer sent=0,received=0,blocked=0,check_count=0,actual_used;integer i;
 moonshine_bus_cdc_credit_large dut(.spi_clk(sc),.spi_reset(reset),.spi_write(wr),.spi_read(1'b0),
 .spi_address(12'h100),.spi_wdata(data),.spi_rdata(rdata),.overflow(lost),.overflow_gray(gray),.spi_free(free_count),
 .core_clk(cc),.core_reset(reset),.core_write(cwrite),.core_address(caddr),.core_wdata(cdata),.core_rdata(32'd0));
 always @(posedge cc)if(!reset && cwrite)begin
  if(caddr!==12'h100 || cdata!==received)$fatal(1,"incorrect delivered word got=%0d want=%0d",cdata,received);
  received<=received+1;
 end
 // Compare against true pointer occupancy only as a testbench oracle. RTL does
 // not use the asynchronous pointer; status must never overstate free slots.
 always @(negedge sc)if(!reset)begin
  actual_used=(integer'(dut.wp)-integer'(dut.rp))&4095;
  if(actual_used>2047)$fatal(1,"invalid actual occupancy %0d",actual_used);
  if(free_count>2047-actual_used)$fatal(1,"credit overstated free=%0d actual=%0d",free_count,63-actual_used);
  check_count=check_count+1;
 end
 initial begin
  if($value$plusargs("CORE_HALF_PS=%d",core_half_ps))begin end
  if(core_half_ps<5000 || core_half_ps>20000)$fatal(1,"invalid core clock");
  repeat(10)@(negedge sc);reset=0;repeat(10)@(negedge sc);
  for(i=0;i<3000;)begin
   @(negedge sc);
   if(free_count>0)begin wr=1;data=i;i=i+1;sent=sent+1;end
   else begin wr=0;blocked=blocked+1;end
  end
  @(negedge sc);wr=0;
  while(received<sent)@(negedge cc);
  repeat(20)@(negedge sc);
  if(sent!=3000 || received!=3000 || lost || gray!=0 || blocked==0 || free_count!=2047)
   $fatal(1,"bad completion sent=%0d received=%0d lost=%0d blocked=%0d free=%0d",sent,received,lost,blocked,free_count);
  $display("CDC_LARGE_CREDIT_PASS sent=%0d received=%0d credit_blocked_cycles=%0d checks=%0d free_final=%0d lost=%0d core_half_ps=%0d",sent,received,blocked,check_count,free_count,lost,core_half_ps);$finish;
 end
 initial begin #1000000;$fatal(1,"credit test watchdog");end
endmodule
