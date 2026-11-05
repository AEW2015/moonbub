
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
 initial if(!$test$plusargs("natural"))force dut.lcd_frame_origin=manual_origin;
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
