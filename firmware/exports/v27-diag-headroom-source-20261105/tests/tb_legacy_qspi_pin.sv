`timescale 1ns/1ps
module tb_legacy_qspi_pin;
 reg clk200=0,clk100=0;always #2.5 clk200=~clk200;always #5 clk100=~clk100;
 reg reset_n=0,cs=1,sck=0;reg[3:0]host_dq=0;wire[3:0]dq,oe;
 wire sw,sr,cw;wire[11:0]sa,ca;wire[31:0]sd,cd,read_spi,read_core;wire over;wire[31:0]gray;
 wire front,valid,pattern,pv;integer pixels=0,i;reg[31:0]value;
 moonshine_qspi_endpoint endpoint(.clk200(clk200),.rst_n(reset_n),.qspi_sck(sck),.qspi_cs_n(cs),
   .qspi_dq_i(host_dq),.dq_o(dq),.dq_oe(oe),.buttons_native(12'b0),.vblank(1'b0),
   .irq_request(),.control(),.force_buttons_native(),.display_external(),.color_correct_enable(),
   .overlay_xctrl(),.overlay_yctrl(),.ov_wr(),.ov_addr(),.ov_data(),
   .core_write(sw),.core_read(sr),.core_address(sa),.core_wdata(sd),.core_rdata(read_spi));
 moonshine_bus_cdc bridge(.spi_clk(clk200),.spi_reset(!reset_n),.spi_write(sw),.spi_read(sr),
   .spi_address(sa),.spi_wdata(sd),.spi_rdata(read_spi),.overflow(over),.overflow_gray(gray),
   .core_clk(clk100),.core_reset(!reset_n),.core_write(cw),.core_address(ca),.core_wdata(cd),.core_rdata(read_core));
 moonshine_core core(.clk(clk100),.reset(!reset_n),.bus_write(cw),.bus_address(ca),.bus_wdata(cd),.bus_rdata(read_core),
   .frame_boundary(1'b1),.memory_idle(1'b1),.front_buffer(front),.front_valid(valid),.pattern_enable(pattern),
   .pixel_valid(pv),.pixel_ready(1'b1),.pixel_address(),.pixel_rgb565(),.scanout_underruns(32'b0),.transport_overflows(32'b0));
 always @(posedge clk100)if(pv)pixels<=pixels+1;
 task begin_transaction;begin sck=0;host_dq=0;cs=0;#100;end endtask
 task end_transaction;begin sck=0;cs=1;#1;if(oe!==0)$fatal(1,"CS output enable");#99;end endtask
 task shift(input[31:0]v,input integer bits,input integer lanes,input realtime hp);
  integer n;begin for(n=bits-lanes;n>=0;n=n-lanes)begin host_dq=(v>>n)&((1<<lanes)-1);#(hp);sck=1;#(hp);sck=0;end end
 endtask
 task header(input[7:0]c,input[31:0]a,input realtime hp);begin begin_transaction();shift(c,8,1,hp);shift(a,32,4,hp);end endtask
 task write32(input[31:0]a,input[31:0]v);begin header(8'h54,a,12.5);shift(v,32,4,12.5);end_transaction();end endtask
 task read32(input[31:0]a,output[31:0]v);integer n;begin header(8'h55,a,31.25);shift(0,64,4,31.25);v=0;
   for(n=0;n<8;n=n+1)begin #31.25;sck=1;v=(v<<4)|dq;#31.25;sck=0;end end_transaction();end endtask
 initial begin
  #100;reset_n=1;#200;
  core.front_buffer=1;core.front_valid=1;core.pattern_enable=0;core.last_presented=77;core.presented_frames=1;
  read32(32'he0000008,value);if(value!==3)$fatal(1,"not legacy capability %h",value);
  write32(32'he0000014,1);write32(32'he0000018,4096);write32(32'he000001c,{16'd720,16'd480});write32(32'he0000020,32'h64f4eb7e);write32(32'he0000024,1);
  header(8'h40,32'he0000100,12.5);
  for(i=0;i<4096;i=i+1)shift(i==0 ? 8'hff : i==1 ? 8'hd8 : i==4094 ? 8'hff : i==4095 ? 8'hd9 : 8'h00,8,4,12.5);
  end_transaction();read32(32'he0000028,value);if(value!==4096)$fatal(1,"received count %h",value);
  write32(32'he0000024,4);write32(32'he0000024,2);
  read32(32'he000002c,value);if(value!==1)$fatal(1,"CRC gate not accepted %h",value);
  read32(32'he0000038,value);if(value!==0)$fatal(1,"fault %h",value);
  if(over||gray!==0||pixels!=0||!front||!valid||pattern||core.presented_frames!=1||core.last_presented!=77)$fatal(1,"overflow or frame disturbed");
  $display("LEGACY_PIN_PASS write40MHz read16MHz bytes=4096 crc=64f4eb7e abort_preserves_front=1 no_overflow=1");$finish;
 end
 initial begin #1000000;$fatal(1,"timeout");end
endmodule
