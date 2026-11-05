`timescale 1ns/1ps
`default_nettype none
module tb_audio_top_reset;
 reg clk50=0;always #10 clk50=~clk50;
 reg sck=0,csn=1,drive=0,manual_origin=0;reg[3:0]host_dq=0;
 wire dot,hs,vs,de;wire[7:0]r,g,b;tri[3:0]qspi;tri[15:0]sdram;
 assign qspi=drive?host_dq:4'bz;
 moonshine_top_akd1 dut(.clk_50mhz(clk50),.mcu_spi_clk(sck),.mcu_spi_cs_n(csn),.mcu_spi_d(qspi),.mcu_irq_n(),
 .btn_a(1'b1),.btn_b(1'b1),.btn_x(1'b1),.btn_y(1'b1),.btn_up(1'b1),.btn_down(1'b1),.btn_left(1'b1),.btn_right(1'b1),.btn_l(1'b1),.btn_r(1'b1),.btn_start(1'b1),.btn_select(1'b1),
 .lcd_dotclk(dot),.lcd_hsync(hs),.lcd_vsync(vs),.lcd_data_en(de),.lcd_data_r(r),.lcd_data_g(g),.lcd_data_b(b),
 .sdram_a(),.sdram_bs(),.sdram_dq(sdram),.sdram_clk(),.sdram_we_n(),.sdram_ldqm(),.sdram_udqm(),.sdram_cas_n(),.sdram_ras_n(),.sdram_cke(),.sdram_cs_n(),
 .vibrate_in1(),.vibrate_in2(),.dac_mclk(),.dac_bclk(),.dac_wclk(),.dac_din());

 // Protocol-only test uses actual TOP/QSPI/CDC/mux/controllers but synthetic
 // origin pulses. Natural raster/atomic image timing is checked elsewhere.
 initial force dut.lcd_frame_origin=manual_origin;
 integer checks=0;reg[31:0]v;reg[31:0]audio_words[0:1023];integer ai,ab;
 initial $readmemh("pcm.hex",audio_words);
 task begin_transaction;begin sck=0;host_dq=0;drive=1;csn=0;#100;end endtask
 task end_transaction;begin sck=0;csn=1;drive=0;#100;end endtask
 task shift(input[31:0]value,input integer bits,input integer lanes,input realtime hp);
 integer z;begin for(z=bits-lanes;z>=0;z=z-lanes)begin host_dq=(value>>z)&((1<<lanes)-1);#(hp);sck=1;#(hp);sck=0;end end endtask
 task header(input[7:0]command,input[31:0]address,input realtime hp);begin begin_transaction();shift(command,8,1,hp);shift(address,32,4,hp);end endtask
 task write_reg(input[11:0]a,input[31:0]value);begin header(8'h54,32'he0000000|a,12.5);shift(value,32,4,12.5);end_transaction();end endtask
 task read_reg(input[11:0]a,output[31:0]value);integer z;begin header(8'h55,32'he0000000|a,31.25);shift(0,64,4,31.25);drive=0;value=0;for(z=0;z<8;z=z+1)begin #31.25;sck=1;value=(value<<4)|qspi;#31.25;sck=0;end end_transaction();end endtask
 task check(input[11:0]a,input[31:0]mask,input[31:0]expected);reg[31:0]x;begin read_reg(a,x);if((x&mask)!==expected)$fatal(1,"QSPI_CSR_CONTRACT a%h got%h expected%h",a,x,expected);checks=checks+1;end endtask
 task pulse;begin @(negedge dut.pclk);manual_origin=1;@(negedge dut.pclk);manual_origin=0;end endtask
 task ready;integer i;reg[31:0]x,y;begin i=0;x=0;y=0;while((!x[10] || !y[10])&&i<20)begin read_reg('h088,x);read_reg('h0a8,y);i=i+1;end if(i==20)$fatal(1,"QSPI_READY_TIMEOUT");end endtask

 task packet(input[31:0]seq_id,input[31:0]word_value,input[31:0]crc_value);begin
  write_reg('h310,1);write_reg('h314,seq_id);write_reg('h318,crc_value);write_reg('h308,2);write_reg('h380,word_value);write_reg('h308,3);
 end endtask
 task audio_ready;integer n;reg[31:0]t;begin n=0;t=0;while(!t[0] && n<30)begin read_reg('h30c,t);n=n+1;end if(n==30)$fatal(1,"TOP_AUDIO_RECOVERY_TIMEOUT");end endtask
 task nonzero_sample(output[31:0]sample);integer bitsn,tries;begin
  sample=0;tries=0;
  while(sample==0 && tries<5)begin
   @(negedge dut.dac_bclk);while(!dut.dac_wclk)@(negedge dut.dac_bclk);
   sample=0;for(bitsn=0;bitsn<32;bitsn=bitsn+1)begin sample={sample[30:0],dut.dac_din};if(bitsn!=31)@(negedge dut.dac_bclk);end
   tries=tries+1;
  end
  if(sample==0)$fatal(1,"TOP_AUDIO_NEVER_RESUMED");
 end endtask
 realtime last_base_edge=0;
 always @(posedge dut.clk50)last_base_edge=$realtime;
 always @(dut.audio_reset)if($time>10)begin #0.001;if(($realtime-last_base_edge)>0.01)$fatal(1,"COMMON_RESET_NOT_REFERENCE_REGISTERED");end
 integer trial,k;realtime start_reset;reg[31:0]heard;
 initial begin
  wait(!dut.rst100[3] && !dut.rstpixel[3] && !dut.rst200[3]);audio_ready();
  for(trial=0;trial<16;trial=trial+1)begin
   write_reg('h308,0);audio_ready();write_reg('h31c,100+trial);
   packet(0,32'h7fff8000,32'h93ef5543);packet(1,32'h7fff8000,32'h93ef5543);
   // Unpublished partial slot must not survive lock loss alongside queued PCM.
   write_reg('h310,2);write_reg('h314,2);write_reg('h308,2);write_reg('h380,32'h12345678);write_reg('h308,1);
   wait(dut.audio.played==1);#(1+(trial%8)*3);start_reset=$realtime;
   if(trial<8)begin force dut.locked=0;force dut.clk100=0;force dut.clk200=0;end
   else begin force dut.plocked=0;force dut.pclk=0;end
   k=0;while(!dut.audio_reset && k<65)begin #1;k=k+1;end
   if(!dut.audio_reset || ($realtime-start_reset)>61)$fatal(1,"COMMON_RESET_NOT_BOUNDED clkcase%0d delay%f",trial,$realtime-start_reset);
   #0.001;if(dut.audio.crst!==3'b111 || dut.audio.prst!==3'b111)$fatal(1,"PRIVATE_RESET_NOT_ASSERTED_WITH_ABSENT_CLOCK");
   #500;if(!dut.audio_reset)$fatal(1,"RESET_NOT_HELD_THROUGH_UNLOCK");
   if(trial<8)begin release dut.clk100;release dut.clk200;#140;release dut.locked;end
   else begin release dut.pclk;#140;release dut.plocked;end
   wait(!dut.rst100[3] && !dut.rstpixel[3] && !dut.rst200[3]);audio_ready();
   check('h324,-1,0);check('h334,-1,0);check('h348,-1,0);check('h320,32'h03ff0f0f,8);check('h30c,7,1);
   write_reg('h31c,200+trial);packet(0,32'h00020001,32'habcedafb);packet(1,32'h00020001,32'habcedafb);write_reg('h308,1);
   nonzero_sample(heard);if(heard!==32'h00010002)$fatal(1,"OLD_OR_PARTIAL_PCM_AFTER_CLOCK_RECOVERY %h",heard);
   checks=checks+1;write_reg('h308,0);audio_ready();
  end
  $display("AUDIO_ACTUAL_TOP_PLL_RESET_PASS cases16 checks%0d clock_absence_both_types1 common_assert_le3basecycles1 partial_and_committed_flush1 DACpin_newsession_no_oldreplay1",checks);$finish;
 end
 initial begin #5000000;$fatal(1,"TOP_RESET_TIMEOUT");end
endmodule
