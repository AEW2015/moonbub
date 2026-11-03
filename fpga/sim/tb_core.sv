`timescale 1ns/1ps
module tb_core;
 reg clk=0;always #5 clk=!clk;
 reg reset=1,wr=0;reg[11:0]addr=0;reg[31:0]data=0;wire[31:0]rd;
 reg boundary=0,ready=1;wire front,valid,pattern,pv;wire[23:0]pa;wire[15:0]rgb;
 integer fd,n,i,cycles=0,accepted=0,dump;reg[7:0]jpeg[0:262143];reg[31:0]crc=32'hffffffff;
 reg[31:0]seen[0:10799];integer index;reg[31:0]small_crc;
 moonshine_core #(.WATCHDOG_CYCLES(4000000)) dut(.clk(clk),.reset(reset),
 .bus_write(wr),.bus_address(addr),.bus_wdata(data),.bus_rdata(rd),
 .frame_boundary(boundary),.memory_idle(1'b1),.front_buffer(front),.front_valid(valid),.pattern_enable(pattern),
 .pixel_valid(pv),.pixel_ready(ready),.pixel_address(pa),.pixel_rgb565(rgb),.scanout_underruns(32'd0),.transport_overflows(32'd0));
 task write_reg(input[11:0]a,input[31:0]d);begin @(negedge clk);addr=a;data=d;wr=1;@(negedge clk);wr=0;end endtask
 task check_reg(input[11:0]a,input[31:0]v);begin @(negedge clk);addr=a;#1;if(rd!==v)$fatal(1,"reg %x actual %x expected %x",a,rd,v);end endtask
 task metadata(input[31:0] c);begin
 write_reg('h14,7);write_reg('h18,n);write_reg('h1c,{16'd720,16'd480});write_reg('h20,c);
 write_reg('h24,1);end endtask
 always @(negedge clk)begin cycles<=cycles+1;ready<=cycles%29>8;end
 reg stalled=0;reg[39:0]held;
 always @(posedge clk)if(!reset)begin
  if(stalled && (!pv || {pa,rgb}!==held))$fatal(1,"pixel changed under backpressure");
  stalled<=pv&&!ready;held<={pa,rgb};
  if(pv&&ready)begin
   if(valid)$fatal(1,"front buffer changed before display boundary");
   if(pa<24'h080000 || pa>=24'h0ddc00)$fatal(1,"bad backbuffer address %x",pa);
   index=(pa-24'h080000)/480-40+((pa-24'h080000)%480)*720;
   if(index<0||index>=345600)$fatal(1,"invalid coordinate index");
   if(seen[index/32][index%32])$fatal(1,"duplicate decoded pixel %d",index);
   seen[index/32][index%32]<=1;
   $fwrite(dump,"%d %04x\n",index,rgb);accepted<=accepted+1;
  end
 end
 initial begin
  for(i=0;i<10800;i=i+1)seen[i]=0;
  fd=$fopen("../../host/fixtures/pattern-720x480-420-q65.jpg","rb");if(fd==0)$fatal(1,"fixture missing");
  n=$fread(jpeg,fd);$fclose(fd);
  for(i=0;i<n;i=i+1)crc=dut.crc_byte(crc,jpeg[i]);crc=~crc;
  dump=$fopen("decoded-rgb565.txt","w");
  repeat(8)@(negedge clk);reset=0;
  check_reg(0,32'h4d425631);check_reg('h4c,262144);
  metadata(crc);for(i=0;i<20;i=i+1)write_reg('h100,jpeg[i]);write_reg('h24,4);
  check_reg('h38,1);if(valid)$fatal(1,"truncated frame published");write_reg('h24,2);
  metadata(crc^1);for(i=0;i<n;i=i+1)write_reg('h100,jpeg[i]);write_reg('h24,4);
  check_reg('h38,2);if(valid)$fatal(1,"CRC damaged frame published");write_reg('h24,2);
  // An extra byte poisons the transaction even if all declared bytes and CRC
  // were otherwise correct. A later COMMIT cannot publish an overflowed frame.
  small_crc=32'hffffffff;small_crc=dut.crc_byte(small_crc,'hff);small_crc=dut.crc_byte(small_crc,'hd8);
  small_crc=dut.crc_byte(small_crc,'hff);small_crc=~dut.crc_byte(small_crc,'hd9);
  write_reg('h18,4);write_reg('h20,small_crc);write_reg('h24,1);
  write_reg('h100,'hff);write_reg('h100,'hd8);write_reg('h100,'hff);write_reg('h100,'hd9);write_reg('h100,0);
  write_reg('h24,4);check_reg('h38,3);check_reg('h40,1);write_reg('h24,2);
  metadata(crc);for(i=0;i<n;i=i+1)write_reg('h100,jpeg[i]);write_reg('h24,4);
  while(!dut.pending && cycles<4200000)@(negedge clk);
  if(!dut.pending)$fatal(1,"decode did not complete count=%d faults=%d",accepted,dut.faults);
  if(accepted!=345600)$fatal(1,"pixel count %d",accepted);
  if(valid)$fatal(1,"published outside boundary");
  repeat(100)@(negedge clk);boundary=1;@(negedge clk);boundary=0;
  check_reg('h48,7);check_reg('h34,1);check_reg('h30,1);
  if(!front||!valid||pattern)$fatal(1,"bad frame ownership");
  $fclose(dump);$display("CORE_PASS pixels=%0d cycles=%0d truncated_crc_recovery=1 backpressure=1 ownership=1",accepted,cycles);$finish;
 end
 initial begin #50000000;$fatal(1,"timeout");end
endmodule
