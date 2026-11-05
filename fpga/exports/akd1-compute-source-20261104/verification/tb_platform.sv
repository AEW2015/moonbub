`timescale 1ns/1ps
`default_nettype none
module tb_platform;
 reg clk50=0;always #10 clk50=~clk50;
 reg sck=0,csn=1,drive=0,manual_origin=0;reg[3:0]host_dq=0;
 reg[11:0]buttons_n=12'hfff;
 wire irq_n;tri1 irq_pull=irq_n;
 wire dot,hs,vs,de;wire[7:0]r,g,b;tri[3:0]qspi;tri[15:0]sdram;
 assign qspi=drive?host_dq:4'bz;
 moonshine_top_akd1 dut(.clk_50mhz(clk50),.mcu_spi_clk(sck),.mcu_spi_cs_n(csn),.mcu_spi_d(qspi),.mcu_irq_n(irq_n),
 .btn_a(buttons_n[0]),.btn_b(buttons_n[1]),.btn_x(buttons_n[2]),.btn_y(buttons_n[3]),.btn_up(buttons_n[4]),.btn_down(buttons_n[5]),.btn_left(buttons_n[6]),.btn_right(buttons_n[7]),.btn_l(buttons_n[8]),.btn_r(buttons_n[9]),.btn_start(buttons_n[10]),.btn_select(buttons_n[11]),
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
 task read_mode(input[31:0]address,input integer lanes,input integer bits,input integer swap,output[31:0]value);
 integer z;reg[7:0]cmd;begin
 cmd=((lanes==4?2:lanes==2?1:0)<<5)|((bits==32?2:bits==16?1:0)<<1)|(swap<<3)|1;
 begin_transaction();shift(cmd,8,1,31.25);shift(address,32,lanes,31.25);shift(0,64,lanes,31.25);drive=0;value=0;
 for(z=0;z<bits/lanes;z=z+1)begin #31.25;sck=1;value=(value<<lanes)|(lanes==1?qspi[1]:lanes==2?qspi[1:0]:qspi);#31.25;sck=0;end
 end_transaction();end endtask
 task write_mode(input[31:0]address,input integer lanes,input integer bits,input integer swap,input[31:0]value);
 reg[7:0]cmd;begin
 cmd=((lanes==4?2:lanes==2?1:0)<<5)|((bits==32?2:bits==16?1:0)<<1)|(swap<<3);
 begin_transaction();shift(cmd,8,1,12.5);shift(address,32,lanes,12.5);shift(value,bits,lanes,12.5);end_transaction();end endtask
 task mode_tests;
 integer lanes,bits,swap,z,n,incr;reg[31:0]got,want;begin
 for(lanes=1;lanes<=4;lanes=lanes*2)for(bits=8;bits<=32;bits=bits*2)for(swap=0;swap<2;swap=swap+1)begin
  read_mode(32'he0000000,lanes,bits,swap,got);
  want=bits==8?32'h41:bits==16?(swap?32'h414b:32'h4b41):(swap?32'h414b4431:32'h31444b41);
  if(got!==want)$fatal(1,"mode read lanes%0d bits%0d swap%0d got%h",lanes,bits,swap,got);
  write_mode(32'he000031c,lanes,bits,swap,32'h11223344);
  want=bits==8?32'h44:bits==16?(swap?32'h4433:32'h3344):(swap?32'h44332211:32'h11223344);
  check('h31c,-1,want);checks=checks+1;
 end
 // Three complete words, both fixed and incrementing read snapshots.
 for(incr=0;incr<2;incr=incr+1)begin
  header(incr?8'h55:8'h45,32'he0000000,31.25);shift(0,64,4,31.25);drive=0;
  for(n=0;n<3;n=n+1)begin got=0;for(z=0;z<8;z=z+1)begin #31.25;sck=1;got=(got<<4)|qspi;#31.25;sck=0;end
   want=!incr||n==0?32'h31444b41:n==1?32'h00010000:0;
   if(got!==want)$fatal(1,"fixed/increment read word%0d got%h",n,got);checks=checks+1;
  end end_transaction();
 end
 // Multiword incrementing writes must retain each pre-increment address.
 header(8'h54,32'he0000310,12.5);
 shift(32'd2,32,4,12.5);shift(32'h12345678,32,4,12.5);
 shift(32'hdeadbeef,32,4,12.5);shift(32'ha5a55a5a,32,4,12.5);end_transaction();
 check('h310,-1,2);check('h314,-1,32'h12345678);check('h318,-1,32'hdeadbeef);check('h31c,-1,32'ha5a55a5a);
 header(8'h45,32'he0000000,31.25);shift(0,64,4,31.25);drive=0;#50;
 if(dut.dq_oe==0)$fatal(1,"read never acquired DQ");csn=1;#0.01;if(dut.dq_oe!==0)$fatal(1,"raw CS did not release DQ immediately");#100;
 end endtask
 task queued_reset_tests;
 begin
 // Actual common service reset with a queued write and unanswered read. A
 // stopped core cannot drain them before both bridge domains are reset.
 force dut.clk100=0;write_reg('h31c,32'hdeadbeef);read_reg('h31c,v);
 if(dut.bridge.wp==dut.bridge.rp)$fatal(1,"queued-reset setup did not queue a write");
 force dut.locked=0;#100;
 if(dut.dq_oe!==0)$fatal(1,"reset did not release QSPI");
 release dut.clk100;#100;release dut.locked;
 wait(!dut.rst100[3]&&!dut.rst200[3]);
 wait(dut.margin.pixel_pending&&dut.timing.pixel_pending);pulse();ready();
 check('h31c,-1,0);check('h000,-1,32'h31444b41);check('h008,-1,0);check('h184,-1,32'h4d424b31);
 end endtask
 task framework_tests;
 integer j;reg[31:0]got;begin
 read_mode(32'h01000200,4,32,0,got);if(got!=={16'd800,16'd480})$fatal(1,"framework dimensions");
 for(j=0;j<12;j=j+1)begin
  buttons_n=~(12'd1<<j);#100;read_mode(32'h0100001c,4,32,0,got);
  if(got!==(32'd1<<(11-j)))$fatal(1,"physical button mapping%0d got%h",j,got);
  if(irq_pull!==0)$fatal(1,"button IRQ was not asserted");checks=checks+1;
  buttons_n=12'hfff;#100;write_mode(32'h01000010,4,32,0,2);
 end
 write_mode(32'h03000000,4,16,0,32'hfc00);#100;
 if(dut.overlay.overlay_bank[0].mem[0]!==16'hfc00)$fatal(1,"overlay address/ARGB1555 write");
 write_reg('h024,1);write_reg('h100,32'hdeadbeef);
 check('h010,-1,0);check('h00c,-1,0);check('h04c,-1,0);check('h074,-1,0);check('h078,-1,0);check('h07c,-1,0);check('h034,-1,0);check('h008,-1,0);
 end endtask
 always @(posedge clk50)begin
  if({dut.sdram_a,dut.sdram_bs,dut.sdram_clk,dut.sdram_we_n,dut.sdram_ldqm,dut.sdram_udqm,dut.sdram_cas_n,dut.sdram_ras_n,dut.sdram_cke,dut.sdram_cs_n}!=={13'd0,2'd0,1'b0,5'b11111,2'b00,2'b11}||sdram!==16'bz)
   $fatal(1,"inactive SDRAM pins changed");
 end
 initial begin
  wait(!dut.rst100[3] && !dut.rstpixel[3] && !dut.rst200[3]);
  wait(dut.margin.pixel_pending && dut.timing.pixel_pending);pulse();ready();
  check('h000,-1,32'h31444b41);check('h004,-1,32'h00010000);check('h008,-1,0);check('h184,-1,32'h4d424b31);
  check('h400,-1,32'h31444b41);check('h404,-1,32'h00010000);
  mode_tests();queued_reset_tests();
  check('h08c,-1,32'h4d524731);check('h090,-1,32'h54494d31);check('h09c,-1,32'h00010003);
  check('h084,-1,20);check('h094,-1,32'h02f02804);check('h098,-1,32'h00a05004);
  check('h088,32'h000007ff,32'h00000714);check('h0a8,32'h000007ff,32'h00000700);
  write_reg('h084,80);check('h088,32'h000f0480,32'h00010080);
  write_reg('h084,1);check('h084,-1,80);check('h088,32'h000f0080,32'h00040080);
  write_reg('h084,81);check('h084,-1,80);check('h088,32'h000f0080,32'h00030080);
  write_reg('h09c,1);write_reg('h094,32'h00200001);check('h094,-1,32'h0021dc04);check('h0a8,32'h000f0080,32'h00040080);
  // No actual boundary yet: applied fields remain prior/default, independently.
  check('h088,127,20);check('h0a0,-1,32'h02f02804);check('h0a4,-1,32'h00a05004);
  write_reg('h024,2);check('h084,-1,80);check('h088,32'hff000080,32'h01000080);check('h0a8,32'hff000080,32'h01000080);
  pulse();ready();check('h088,32'hff0f07ff,32'h02020750);check('h0a8,32'hff0f07ff,32'h02020701);
  check('h0a0,-1,32'h0021dc04);check('h0a4,-1,32'h00300804);
  if(dut.display_margin!=80 || dut.timing_htotal!=605 || dut.timing_vtotal!=809 || dut.timing_hstart!=123 || dut.timing_vstart!=6)$fatal(1,"TOP_CONTROLLER_LCD_WIRING");
  write_reg('h024,2);check('h088,32'hff0f07ff,32'h02020750);check('h0a8,32'hff0f07ff,32'h02020701);check('h0a0,-1,32'h0021dc04);check('h0a4,-1,32'h00300804);
  write_reg('h094,32'h40000004);check('h094,-1,32'h0021dc04);check('h0a8,32'h000f0000,32'h00030000);
  write_reg('h09c,3);check('h0a8,32'h000f0000,32'h00030000);
  write_reg('h094,32'h00200001);write_reg('h098,32'h00100401);check('h0a8,32'h000f0080,32'h00060000);check('h0a0,-1,32'h0021dc04);
  write_reg('h09c,2);write_reg('h098,32'h0dd00401);check('h098,-1,32'h00100401);check('h0a8,32'h000f0080,32'h00040080);
  check('h09c,-1,32'h00010003);pulse();ready();check('h0a0,-1,32'h00200001);check('h0a4,-1,32'h00100401);check('h0a8,32'hff0f07ff,32'h03020702);
  write_reg('h084,1);write_reg('h09c,0);wait(dut.margin.pixel_pending && dut.timing.pixel_pending);pulse();ready();check('h088,127,1);check('h0a0,-1,32'h02f02804);check('h0a4,-1,32'h00a05004);
  check('h02c,-1,0);check('h030,-1,0);check('h034,-1,0);check('h038,-1,0);check('h03c,-1,0);check('h050,-1,0);
  check('h089,-1,0);check('h091,-1,0);

  check('h300,-1,32'h41504331);check('h304,-1,32'h00010001);check('h30c,1,1);check('h33c,-1,4096);
  check('h340,-1,176171875);check('h344,-1,3648);check('h348,-1,0);
  write_reg('h31c,77);write_reg('h310,505);
  write_reg('h314,0);write_reg('h318,32'he7c0e3c1);write_reg('h308,2);
  // Bits32 byte_swap=true and little-endian buffer bytes; fixed FIFO address.
  header(8'h4c,32'he0000380,12.5);
  for(ai=0;ai<505;ai=ai+1)shift({audio_words[ai][7:0],audio_words[ai][15:8],audio_words[ai][23:16],audio_words[ai][31:24]},32,4,12.5);
  end_transaction();write_reg('h308,3);check('h324,-1,1);check('h328,-1,0);check('h32c,-1,77);
  write_reg('h314,1);write_reg('h318,32'he196c2c1);write_reg('h308,2);
  // Bits32 byte_swap=true and little-endian buffer bytes; fixed FIFO address.
  header(8'h4c,32'he0000380,12.5);
  for(ai=512;ai<1017;ai=ai+1)shift({audio_words[ai][7:0],audio_words[ai][15:8],audio_words[ai][23:16],audio_words[ai][31:24]},32,4,12.5);
  end_transaction();write_reg('h308,3);check('h324,-1,2);check('h328,-1,1);check('h32c,-1,77);

  check('h348,-1,1010);check('h334,-1,0);check('h320,32'h00000f0f,32'h00000206);
  for(ab=0;ab<2;ab=ab+1)for(ai=0;ai<505;ai=ai+1)begin
   if(dut.audio.samples[ab*512+ai]!=={ai==504,audio_words[ab*512+ai]})$fatal(1,"QSPI PCM byte packing or LAST wrong");
  end
  write_reg('h308,1);#65000;read_reg('h334,v);if(v<1)$fatal(1,"QSPI ARM not playing");checks=checks+1;
  write_reg('h308,0);#2000;check('h30c,7,1);check('h348,-1,0);check('h324,-1,2);check('h320,32'h00000f0f,8);
  check('h02c,-1,0);check('h030,-1,0);check('h034,-1,0);check('h038,-1,0);check('h050,-1,0);
  framework_tests();
`ifdef AKD1_PLATFORM_STUB
  $display("AKD1_PLATFORM_QSPI_PASS checks=%0d stub=1 actual_endpoint_CDC=1 lanes124=1 swap_sizes=1 fixed_increment=1 synthetic_origin_only=1",checks);
`else
  $display("AKD1_PLATFORM_QSPI_PASS checks=%0d stub=0 actual_endpoint_CDC=1 lanes124=1 swap_sizes=1 fixed_increment=1 synthetic_origin_only=1",checks);
`endif
  $finish;
 end
 initial begin #2000000;$fatal(1,"timeout");end
endmodule
`default_nettype wire

