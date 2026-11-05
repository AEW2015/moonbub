`timescale 1ns/1ps
module tb;
 parameter LOSS=0;
 reg clk50=0;always #10 clk50=~clk50;
 reg sck=0,csn=1,drive=0;reg[3:0]host_dq=0;wire[3:0]qspi;assign qspi=drive?host_dq:4'bz;
 wire irq;tri1 irq_pull=irq;wire dot,hs,vs,de;wire[7:0]r,g,b;wire[12:0]a;wire[1:0]ba,cke,cs;tri[15:0]dq;wire sk,ras,cas,we,lm,um;wire vm0,vm1,dm,db,dw,dd;
 moonshine_top_cpl1 dut(.clk_50mhz(clk50),.mcu_spi_clk(sck),.mcu_spi_cs_n(csn),.mcu_spi_d(qspi),.mcu_irq_n(irq),
 .btn_a(1'b1),.btn_b(1'b1),.btn_x(1'b1),.btn_y(1'b1),.btn_up(1'b1),.btn_down(1'b1),.btn_left(1'b1),.btn_right(1'b1),.btn_l(1'b1),.btn_r(1'b1),.btn_start(1'b1),.btn_select(1'b1),
 .lcd_dotclk(dot),.lcd_hsync(hs),.lcd_vsync(vs),.lcd_data_en(de),.lcd_data_r(r),.lcd_data_g(g),.lcd_data_b(b),
 .sdram_a(a),.sdram_bs(ba),.sdram_dq(dq),.sdram_clk(sk),.sdram_we_n(we),.sdram_ldqm(lm),.sdram_udqm(um),.sdram_cas_n(cas),.sdram_ras_n(ras),.sdram_cke(cke),.sdram_cs_n(cs),
 .vibrate_in1(vm0),.vibrate_in2(vm1),.dac_mclk(dm),.dac_bclk(db),.dac_wclk(dw),.dac_din(dd));
 sdram_model_burst #(.MEM_WORDS(1572865),.CLOCK_FLIGHT_NS(0.0))model(.clk(sk),.a(a),.ba(ba),.cke(cke),.cs(cs),.ras(ras),.cas(cas),.we(we),.ldqm(lm),.udqm(um),.dq(dq));
 integer checks=0,starts=0,boots=0,releases=0,cycle=0;reg issued_loss=0;reg[31:0]v,cookie0,generation0,bytes0;integer i;
 realtime last100=0,last200=0,lastpixel=0;integer n100=0,n200=0,npixel=0,nread=0;
 always @(posedge dut.clk100)begin
  cycle=cycle+1;if(n100>4&&($realtime-last100<9.999||$realtime-last100>10.001))$fatal(1,"core clock changed");last100=$realtime;n100=n100+1;
  if(dut.start_accepted)starts=starts+1;if(dut.bootstrap_released)boots=boots+1;if(dut.consumer_released)releases=releases+1;
  if(starts>1)$fatal(1,"autostart repeated");
  if(issued_loss&&dut.auto_start)$fatal(1,"autostart after lock loss");
  if(cycle>1000000)$fatal(1,"bounded platform timeout");
 end
 always @(posedge dut.clk200)begin if(n200>4&&($realtime-last200<4.999||$realtime-last200>5.001))$fatal(1,"SPI clock changed");last200=$realtime;n200=n200+1;end
 always @(posedge dut.pclk)begin if(npixel>4&&($realtime-lastpixel<34.055||$realtime-lastpixel>34.060))$fatal(1,"panel clock changed");lastpixel=$realtime;npixel=npixel+1;end
 always @(posedge dut.read_clk100)begin if(n100>4&&($realtime-last100<3.749||$realtime-last100>3.751))$fatal(1,"read phase changed");nread=nread+1;end
 always @(negedge dut.clk100)begin
  #0.001;
  if(!dut.job_reset&&!issued_loss&&dut.observations[5*32+:32]!==model.writes)$fatal(1,"pad-launch observer/model count disagree observer=%0d physical=%0d",dut.observations[5*32+:32],model.writes);
 end
 always @(negedge dut.pclk)if(!dut.rstpixel[3]&&{vm0,vm1,dm,db,dw,dd}!==0)$fatal(1,"disabled outputs active");
 task begin_tx;begin sck=0;host_dq=0;drive=1;csn=0;#100;end endtask
 task end_tx;begin sck=0;csn=1;drive=0;#100;end endtask
 task shift(input[31:0]value,input integer bits,lanes);integer z;begin for(z=bits-lanes;z>=0;z=z-lanes)begin host_dq=(value>>z)&((1<<lanes)-1);#31.25;sck=1;#31.25;sck=0;end end endtask
 task header(input[7:0]cmd,input[31:0]addr);begin begin_tx();shift(cmd,8,1);shift(addr,32,4);end endtask
 task wr(input[11:0]addr,input[31:0]data);begin header(8'h54,32'he0000000|addr);shift(data,32,4);end_tx();end endtask
 task rd(input[11:0]addr,output[31:0]data);integer z;begin header(8'h55,32'he0000000|addr);shift(0,64,4);drive=0;data=0;for(z=0;z<8;z=z+1)begin #31.25;sck=1;data=(data<<4)|qspi;#31.25;sck=0;end end_tx();end endtask
 task check(input[11:0]addr,input[31:0]want);reg[31:0]got;begin rd(addr,got);if(got!==want)$fatal(1,"QSPI addr%h got%h want%h",addr,got,want);checks=checks+1;end endtask
 initial begin
  wait(dut.consumer_started_once);if(starts!=1||boots!=1||dut.quarantined)$fatal(1,"positive bootstrap/automatic start");checks=checks+1;
  check(0,32'h314c5043);check(4,32'h10000);check(8,0);check('h184,32'h43505231);
  wr('h500,32'h76543210);check('h500,32'h76543210);check('h504,1);check('h508,32'h10000);
  rd('h50c,v);if(v[3]||v[2:0]!=7)$fatal(1,"snapshot auto flags %h",v);checks=checks+1;
  rd('h564,v);if(v[1:0]!=3)$fatal(1,"captured PLL flags");checks=checks+1;
  rd('h52c,bytes0);repeat(500)@(posedge dut.clk100);check('h52c,bytes0);
  wr('h084,32'hffff);wr('h090,32'hffff);wr('h100,32'hffff);check('h084,0);check('h090,0);check('h100,0);
  wr('h500,32'h76543211);check('h504,2);check('h57c,3);
  if(LOSS)begin
   wait(dut.bytes_sent>=1000);issued_loss=1;
   if(LOSS==1)force dut.plocked=0;else force dut.locked=0;
   repeat(100)@(posedge clk50);
   if(!dut.quarantined||!dut.job_reset)$fatal(1,"loss did not quarantine/hold job reset");
   if(LOSS==1)release dut.plocked;else release dut.locked;
   repeat(1000)@(posedge clk50);
   if(!dut.quarantined||!dut.autostart_once||starts!=1||boots!=1||releases)$fatal(1,"loss fabricated fresh job/release");
   wr('h500,32'h76543212);check('h500,32'h76543212);rd('h50c,v);if(!v[3]||v[8]||v[7])$fatal(1,"fresh snapshot lost quarantine %h",v);checks=checks+1;
   $display("CPL1_PLATFORM_LOCK_QUARANTINE_PASS loss=%0d checks=%0d starts=%0d boot=%0d releases=%0d",LOSS,checks,starts,boots,releases);$finish;
  end else begin
   wait(model.writes>=8);repeat(100)@(posedge dut.clk100);
   if(!nread||n100<100||n200<100||npixel<100||cke!=1||cs!=2)$fatal(1,"live clocks/pins");
   $display("CPL1_PLATFORM_SOURCE_SMOKE_PASS checks=%0d starts=%0d bootstrap=%0d physical_writes=%0d read_phase279=1 spi16MHz_dummy8bytes=1",checks,starts,boots,model.writes);$finish;
  end
 end
endmodule
