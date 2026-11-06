`timescale 1ns/1ps
module tb;
 parameter LOSS=0,SMOKE=0;
 `include "units.svh"
 reg clk50=0;always #10 clk50=~clk50;
 reg sck=0,csn=1,drive=0;reg[3:0]host_dq=0;wire[3:0]qspi;assign qspi=drive?host_dq:4'bz;
 wire irq;tri1 irq_pull=irq;wire dot,hs,vs,de;wire[7:0]r,g,b;wire[12:0]a;wire[1:0]ba,cke,cs;tri[15:0]dq;wire sk,ras,cas,we,lm,um;wire vm0,vm1,dm,db,dw,dd;
 moonshine_top_cpl1 dut(.clk_50mhz(clk50),.mcu_spi_clk(sck),.mcu_spi_cs_n(csn),.mcu_spi_d(qspi),.mcu_irq_n(irq),
 .btn_a(1'b1),.btn_b(1'b1),.btn_x(1'b1),.btn_y(1'b1),.btn_up(1'b1),.btn_down(1'b1),.btn_left(1'b1),.btn_right(1'b1),.btn_l(1'b1),.btn_r(1'b1),.btn_start(1'b1),.btn_select(1'b1),
 .lcd_dotclk(dot),.lcd_hsync(hs),.lcd_vsync(vs),.lcd_data_en(de),.lcd_data_r(r),.lcd_data_g(g),.lcd_data_b(b),
 .sdram_a(a),.sdram_bs(ba),.sdram_dq(dq),.sdram_clk(sk),.sdram_we_n(we),.sdram_ldqm(lm),.sdram_udqm(um),.sdram_cas_n(cas),.sdram_ras_n(ras),.sdram_cke(cke),.sdram_cs_n(cs),
 .vibrate_in1(vm0),.vibrate_in2(vm1),.dac_mclk(dm),.dac_bclk(db),.dac_wclk(dw),.dac_din(dd));
 sdram_model_burst #(.MEM_WORDS(1572865),.CLOCK_FLIGHT_NS(3.768),.T_AC_NS(8.489),.T_OH_NS(2.223))model(.clk(sk),.a(a),.ba(ba),.cke(cke),.cs(cs),.ras(ras),.cas(cas),.we(we),.ldqm(lm),.udqm(um),.dq(dq));
 integer checks=0,starts=0,boots=0,releases=0,cycle=0;reg issued_loss=0;reg[31:0]v,cookie0,generation0,bytes0;integer i;
 realtime last100=0,last200=0,lastpixel=0;integer n100=0,n200=0,npixel=0,nread=0;
 always @(posedge dut.clk100)begin
  cycle=cycle+1;if(n100>4&&($realtime-last100<9.999||$realtime-last100>10.001))$fatal(1,"core clock changed");last100=$realtime;n100=n100+1;
  if(dut.start_accepted)starts=starts+1;if(dut.bootstrap_released)boots=boots+1;if(dut.consumer_released)releases=releases+1;
  if(starts>1)$fatal(1,"autostart repeated");
  if(issued_loss&&dut.auto_start)$fatal(1,"autostart after lock loss");
  if(cycle>12000000)$fatal(1,"bounded platform timeout");
 end
 always @(posedge dut.clk200)begin if(n200>4&&($realtime-last200<4.999||$realtime-last200>5.001))$fatal(1,"SPI clock changed");last200=$realtime;n200=n200+1;end
 always @(posedge dut.pclk)begin if(npixel>4&&($realtime-lastpixel<34.055||$realtime-lastpixel>34.060))$fatal(1,"panel clock changed");lastpixel=$realtime;npixel=npixel+1;end
 always @(posedge dut.read_clk100)begin if(n100>4&&($realtime-last100<7.624||$realtime-last100>7.626))$fatal(1,"read phase changed");nread=nread+1;end
 always @(negedge dut.clk100)begin
  #4.001;
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

 localparam BASE=24'h100000,WORDS=259200;
 reg[15:0]gold_pixels[0:345599],gold_column[0:WORDS-1];reg[31:0]captured[0:39];
 integer canvas=0,margins=0,blank=0,latches=0,misses=0,mismatches=0,origins=0,background=0;
 integer line_words=0,line_column=0,accepted_lines=0,completed_lines=0,physical_checked=0,writes_seen=0,write_address=0;
 integer shadow_x=0,shadow_y=0,page_file,line_file,p,j;reg watching=0,coverage_done=0;
 reg[11:0]page_offset;reg[31:0]old_gen,query_gen;localparam[31:0]QUERY_COOKIE=32'h0c231001;
 wire[15:0]panel_rgb={r[7:3],g[7:2],b[7:3]};
 task guard;
  begin check(0,32'h314c5043);check(4,32'h10000);check(8,0);check('h184,32'h43505231);check('h500,QUERY_COOKIE);check('h504,query_gen);end
 endtask
 always @(posedge dut.clk100)if(!dut.job_reset)begin
  if(dut.promoted)begin if(watching||!dut.front_valid||!dut.base_qualified||releases!=1)$fatal(1,"first publication not positively retired");watching=1;origins=0;end
  if(dut.diagnostic.core.line_req_valid&&dut.diagnostic.core.line_req_ready)begin
   line_column=dut.diagnostic.core.line_req_address/480;line_words=0;accepted_lines=accepted_lines+1;
  end
  if(dut.diagnostic.core.line_data_valid)begin
   if(line_words>=480||dut.diagnostic.core.line_data!==gold_pixels[line_words*720+line_column])$fatal(1,"actual board final line mismatch col%0d row%0d",line_column,line_words);
   line_words=line_words+1;if(line_words==480)begin completed_lines=completed_lines+1;$fdisplay(line_file,"COMPLETE column=%0d time_ns=%0.3f",line_column,$realtime);end
  end
  if(watching&&dut.frame_boundary&&!dut.promoted&&!coverage_done)begin
   origins=origins+1;
   if(origins==2)begin
    if(canvas!=691200||margins!=76800||latches!=1440||misses||mismatches||dut.underruns||physical_checked!=259200||accepted_lines!=1440||completed_lines!=1440)$fatal(1,"two native board refreshes incomplete canvas%0d margins%0d latches%0d misses%0d physical%0d",canvas,margins,latches,misses,physical_checked);
    coverage_done=1;$display("CPL1_BOARD_NATIVE_TWO_CANVASES_PASS canvas=%0d margins=%0d blank=%0d latches=%0d misses=%0d mismatches=%0d physical=%0d",canvas,margins,blank,latches,misses,mismatches,physical_checked);
   end
  end
 end
 always @(posedge dut.pclk)begin
  if(dut.rstpixel[3])begin shadow_x=0;shadow_y=0;end
  else begin
   if(dut.diagnostic.core.lcd.x!==shadow_x||dut.diagnostic.core.lcd.y!==shadow_y)$fatal(1,"native board raster totals changed");
   if(shadow_x==540)begin shadow_x=0;if(shadow_y==833)shadow_y=0;else shadow_y=shadow_y+1;end else shadow_x=shadow_x+1;
   if(watching&&dut.diagnostic.core.lcd.x==13&&dut.diagnostic.core.lcd.y>=37&&dut.diagnostic.core.lcd.y<757)begin
    #0.001;latches=latches+1;if(!dut.diagnostic.core.lcd.line_good)misses=misses+1;
    $fdisplay(line_file,"NEED column=%0d latch_ns=%0.3f good=%b",dut.diagnostic.core.lcd.y-37,$realtime,dut.diagnostic.core.lcd.line_good);
   end
  end
 end
 always @(negedge dut.pclk)if(!dut.rstpixel[3])begin
  if(!watching)begin if({r,g,b}!==0)$fatal(1,"prepublication board privacy");background=background+1;end
  else if(de)begin
   if(dut.py>=13&&dut.py<733)begin
    canvas=canvas+1;if(panel_rgb!==gold_pixels[dut.px*720+dut.py-13])begin mismatches=mismatches+1;if(mismatches<=5)$display("BOARD_PIXEL_MISMATCH x%0d y%0d got%h expected%h",dut.py-13,dut.px,panel_rgb,gold_pixels[dut.px*720+dut.py-13]);end
   end else begin margins=margins+1;if({r,g,b}!==0)$fatal(1,"nonblack board margin");end
  end else begin blank=blank+1;if({r,g,b}!==0)$fatal(1,"nonblack board blanking");end
 end
 always @(posedge model.device_clock)begin
  #0.001;
  if(model.writes!=writes_seen)begin
   write_address=model.writeaddr-1;
   if(model.writes!=writes_seen+1||write_address<BASE||write_address>=BASE+WORDS||model.mem[write_address]!==gold_column[write_address-BASE]||lm||um)$fatal(1,"actual board physical write/address/data mismatch");
   physical_checked=physical_checked+1;writes_seen=model.writes;
  end
 end
 initial begin
  page_file=$fopen("pages.log","w");line_file=$fopen("panel-line-timing.log","w");
  $readmemh("composite.hex",gold_pixels);$readmemh("column.hex",gold_column);
  wait(dut.consumer_started_once);if(starts!=1||boots!=1||dut.quarantined)$fatal(1,"board autoSTART/bootstrap");
  check(0,32'h314c5043);check(4,32'h10000);check(8,0);check('h184,32'h43505231);
  if(SMOKE)begin wait(model.writes>=8);repeat(100)@(posedge dut.clk100);$display("CPL1_BOARD_PRODUCTION_IO_SMOKE_PASS actual_ODDR_IOBUF=1 physical=%0d pad_launches=%0d",physical_checked,dut.observations[5*32+:32]);$finish;end
  wait(coverage_done);
  check('h500,0);rd('h504,old_gen);wr('h500,QUERY_COOKIE);query_gen=old_gen+1;guard();
  for(p=0;p<10;p=p+1)begin
   guard();for(j=0;j<4;j=j+1)rd('h500+(p*4+j)*4,captured[p*4+j]);guard();
  end
  if(captured[0]!==QUERY_COOKIE||captured[1]!==query_gen||captured[2]!=32'h10000||captured[3][3]||!captured[3][7]||!captured[3][8]||!captured[3][9]||!captured[3][10]||captured[25][1:0]!=3)$fatal(1,"captured identity/status/locks");
  if({captured[7],captured[6]}!==64'h123456789abcdef0||captured[8]!=1||captured[9]!=0||captured[10]!=1||captured[11]!=17412||captured[12]!=518400||captured[13]!=21120||captured[14]!=259200||captured[15]!=259200)$fatal(1,"captured actual identity/counts");
  if({captured[19],captured[18],captured[17],captured[16]}!==128'hb74b12e10009cfccbcb5363d13edc4ee||{captured[23],captured[22],captured[21],captured[20]}!==128'h1026aab8b7df606614f560a966806641)$fatal(1,"captured actual computed tags");
  if(captured[26]||captured[28]!=1||captured[29]!=1||captured[30]||captured[31]||captured[32]<2||captured[33]!==NATIVE_CRC||captured[34]!=345600||!captured[35][0]||captured[35][4:2]||captured[36]||captured[38]||captured[39])$fatal(1,"captured postread CRC/counters");
  check('h510,captured[4]);check('h514,captured[5]);guard();
  for(p=0;p<10;p=p+1)begin
   page_offset='h500+p*16;
   $fdisplay(page_file,"USB_TRACE cpl1 v=1 page=%0d cookie=%08h gen=%0d off=%03h words=%08h,%08h,%08h,%08h",p,captured[0],captured[1],page_offset,captured[p*4],captured[p*4+1],captured[p*4+2],captured[p*4+3]);
   $display("USB_TRACE cpl1 v=1 page=%0d cookie=%08h gen=%0d off=%03h words=%08h,%08h,%08h,%08h",p,captured[0],captured[1],page_offset,captured[p*4],captured[p*4+1],captured[p*4+2],captured[p*4+3]);
  end
  if(misses||mismatches||dut.underruns||starts!=1||boots!=1||releases!=1||dut.canvas_errors)$fatal(1,"board final counters");
  $display("CPL1_BOARD_NATIVE_QSPI_OBSERVER_PASS guarded_reads=40 checks=%0d actual_crc=%08h same_image_canvases=%0d actual_pad_launches=%0d profile_caps=0 source_product_unchanged=1",checks,captured[33],captured[32],captured[14]);
  $fclose(page_file);$fclose(line_file);$finish;
 end
endmodule
