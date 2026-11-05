`timescale 1ns/1ps
`default_nettype none
module moonshine_top_cpl1(
 input wire clk_50mhz,
 input wire mcu_spi_clk,mcu_spi_cs_n,inout wire[3:0]mcu_spi_d,output wire mcu_irq_n,
 input wire btn_a,btn_b,btn_x,btn_y,btn_up,btn_down,btn_left,btn_right,btn_l,btn_r,btn_start,btn_select,
 output wire lcd_dotclk,lcd_hsync,lcd_vsync,lcd_data_en,
 output wire[7:0]lcd_data_r,lcd_data_g,lcd_data_b,
 output wire[12:0]sdram_a,output wire[1:0]sdram_bs,inout wire[15:0]sdram_dq,
 output wire sdram_clk,sdram_we_n,sdram_ldqm,sdram_udqm,sdram_cas_n,sdram_ras_n,
 output wire[1:0]sdram_cke,sdram_cs_n,
 output wire vibrate_in1,vibrate_in2,dac_mclk,dac_bclk,dac_wclk,dac_din
);
 wire clk50,inclk;IBUF input_buffer(.I(clk_50mhz),.O(inclk));BUFG base_clock(.I(inclk),.O(clk50));
 wire fb,fbb,raw200,raw100,raw_read100,clk200,clk100,read_clk100,locked;
 PLLE2_BASE #(.CLKIN1_PERIOD(20.0),.CLKFBOUT_MULT(20),.DIVCLK_DIVIDE(1),.CLKOUT0_DIVIDE(5),.CLKOUT1_DIVIDE(10),.CLKOUT2_DIVIDE(10),.CLKOUT2_PHASE(135.0))
 service_pll(.CLKIN1(clk50),.CLKFBIN(fbb),.CLKFBOUT(fb),.CLKOUT0(raw200),.CLKOUT1(raw100),.CLKOUT2(raw_read100),.LOCKED(locked),.PWRDWN(1'b0),.RST(1'b0));
 BUFG feedback(.I(fb),.O(fbb));BUFG spi_clock(.I(raw200),.O(clk200));BUFG memory_clock(.I(raw100),.O(clk100));
 BUFG read_clock(.I(raw_read100),.O(read_clk100));
 wire pfb,pfbb,praw,pclk,plocked;
 MMCME2_BASE #(.CLKIN1_PERIOD(20.0),.CLKFBOUT_MULT_F(56.375),.DIVCLK_DIVIDE(3),.CLKOUT0_DIVIDE_F(32.0))
 panel_mmcm(.CLKIN1(clk50),.CLKFBIN(pfbb),.CLKFBOUT(pfb),.CLKOUT0(praw),.LOCKED(plocked),.PWRDWN(1'b0),.RST(1'b0));
 BUFG panel_feedback(.I(pfb),.O(pfbb));BUFG panel_clock(.I(praw),.O(pclk));
 (* ASYNC_REG="TRUE" *)reg[3:0]rst200=15,rst100=15,rstpixel=15;
 always @(posedge clk200 or negedge locked)if(!locked)rst200<=15;else rst200<={rst200[2:0],1'b0};
 always @(posedge clk100 or negedge locked)if(!locked)rst100<=15;else rst100<={rst100[2:0],1'b0};
 always @(posedge pclk or negedge plocked)if(!plocked)rstpixel<=15;else rstpixel<={rstpixel[2:0],1'b0};
 wire[3:0]dq_i,dq_o,dq_oe,control;wire irq;
 genvar k;generate for(k=0;k<4;k=k+1)begin:mcu_io
 IOBUF lane(.IO(mcu_spi_d[k]),.I(dq_o[k]),.O(dq_i[k]),.T(!dq_oe[k]));end endgenerate
 OBUFT irq_driver(.O(mcu_irq_n),.I(1'b0),.T(!irq));
 wire[11:0]buttons=~{btn_select,btn_start,btn_r,btn_l,btn_right,btn_left,btn_down,btn_up,btn_y,btn_x,btn_b,btn_a};
 wire spi_write,spi_read,ov_wr;wire[11:0]spi_addr;wire[31:0]spi_wdata,spi_rdata;
 wire[17:0]ov_addr;wire[15:0]ov_data;
 wire hs,vs,de;wire[7:0]red,green,blue;wire[9:0]px,py;
 moonshine_qspi_endpoint endpoint(.clk200(clk200),.rst_n(!rst200[3]),
 .qspi_sck(mcu_spi_clk),.qspi_cs_n(mcu_spi_cs_n),.qspi_dq_i(dq_i),.dq_o(dq_o),.dq_oe(dq_oe),
 .buttons_native(buttons),.vblank(vs),.irq_request(irq),.control(control),.force_buttons_native(),
 .display_external(),.color_correct_enable(),.overlay_xctrl(),.overlay_yctrl(),
 .ov_wr(ov_wr),.ov_addr(ov_addr),.ov_data(ov_data),
 .core_write(spi_write),.core_read(spi_read),.core_address(spi_addr),.core_wdata(spi_wdata),.core_rdata(spi_rdata));
 wire core_write;wire[11:0]core_address;wire[31:0]core_wdata,core_rdata;wire transport_overflow;
 wire[31:0]transport_gray;
 (* ASYNC_REG="TRUE" *)reg[31:0]transport_gray_meta=0,transport_gray_sync=0;
 reg[31:0]transport_lost_words=0;
 function automatic[31:0]ungray_transport(input[31:0]value);
 integer i;begin for(i=0;i<32;i=i+1)ungray_transport[i]=^(value>>i);end
 endfunction
 always @(posedge clk100)begin
  if(rst100[3])begin transport_gray_meta<=0;transport_gray_sync<=0;transport_lost_words<=0;end
  else begin transport_gray_meta<=transport_gray;transport_gray_sync<=transport_gray_meta;
   transport_lost_words<=ungray_transport(transport_gray_sync);end
 end
 moonshine_bus_cdc bridge(.spi_clk(clk200),.spi_reset(rst200[3]),.spi_write(spi_write),.spi_read(spi_read),
 .spi_address(spi_addr),.spi_wdata(spi_wdata),.spi_rdata(spi_rdata),.overflow(transport_overflow),.overflow_gray(transport_gray),
 .core_clk(clk100),.core_reset(rst100[3]),.core_write(core_write),.core_address(core_address),.core_wdata(core_wdata),.core_rdata(core_rdata));

 // Keep paired service resets on the ordered bridge. The job has additional
 // reference-domain lock containment; no unilateral bridge token reset.
 (* ASYNC_REG="TRUE" *)reg[1:0]platform_service_lock_sync=0,platform_panel_lock_sync=0;
 reg platform_reset_ref=1;
 always @(posedge clk50)begin
  platform_service_lock_sync<={platform_service_lock_sync[0],locked};
  platform_panel_lock_sync<={platform_panel_lock_sync[0],plocked};
  platform_reset_ref<=!(platform_service_lock_sync[1]&&platform_panel_lock_sync[1]);
 end
 (* ASYNC_REG="TRUE" *)reg[3:0]job_reset_chain=15;
 always @(posedge clk100 or posedge platform_reset_ref)
  if(platform_reset_ref)job_reset_chain<=15;else job_reset_chain<={job_reset_chain[2:0],1'b0};
 wire job_reset=job_reset_chain[3];
 (* ASYNC_REG="TRUE" *)reg[1:0]status_service_lock_sync=0,status_panel_lock_sync=0;
 always @(posedge clk100)begin
  if(rst100[3])begin status_service_lock_sync<=0;status_panel_lock_sync<=0;end
  else begin status_service_lock_sync<={status_service_lock_sync[0],locked};status_panel_lock_sync<={status_panel_lock_sync[0],plocked};end
 end
 reg autostart_once=0,shell_quarantine=0;reg auto_pending=0,auto_start=0;
 wire loader_busy,start_accepted,start_rejected,load_complete,loader_cancelled,consumer_started_once,reconfigure_required;
 wire bootstrap_released,consumer_released,idle_certificate,base_qualified,front_valid,qualified,promoted,frame_boundary;
 wire[31:0]rejected_starts,bytes_sent,promotions,underruns;
 wire[767:0]observations;wire rgb_valid;wire[15:0]rgb_data;wire[9:0]rgb_x,rgb_y;
 wire quarantined=shell_quarantine||reconfigure_required;
 always @(posedge clk100)begin
  if(job_reset)begin auto_pending<=0;auto_start<=0;if(autostart_once)shell_quarantine<=1;end
  else begin
   auto_start<=0;
   if(bootstrap_released&&!autostart_once&&!quarantined)auto_pending<=1;
   if(auto_pending&&!autostart_once&&!quarantined)begin auto_start<=1;auto_pending<=0;autostart_once<=1;end
  end
 end
 cp23_rom_composite diagnostic(.clk(clk100),.read_clk(read_clk100),.pixel_clk(pclk),.reset(job_reset),.pixel_reset_n(!rstpixel[3]),
  .local_start(auto_start),.local_cancel(1'b0),.loader_busy(loader_busy),.local_start_accepted(start_accepted),.local_start_rejected(start_rejected),
  .rejected_starts(rejected_starts),.bytes_sent(bytes_sent),.load_complete(load_complete),.loader_cancelled(loader_cancelled),
  .consumer_started_once(consumer_started_once),.reconfigure_required(reconfigure_required),.bootstrap_released_pulse(bootstrap_released),
  .consumer_job_released_pulse(consumer_released),.idle_certificate(idle_certificate),.base_qualified(base_qualified),.front_valid(front_valid),
  .promotion_count(promotions),.lcd_underruns(underruns),.qualified_pulse(qualified),.promoted_pulse(promoted),.frame_boundary(frame_boundary),
  .observation(observations),.observed_rgb_valid(rgb_valid),.observed_rgb_data(rgb_data),.observed_rgb_x(rgb_x),.observed_rgb_y(rgb_y),
  .red(red),.green(green),.blue(blue),.hsync(hs),.vsync(vs),.data_enable(de),.physical_x(px),.physical_y(py),
  .sdram_a(sdram_a),.sdram_bs(sdram_bs),.sdram_dq(sdram_dq),.sdram_clk(sdram_clk),.sdram_cke(sdram_cke),.sdram_cs_n(sdram_cs_n),
  .sdram_ras_n(sdram_ras_n),.sdram_cas_n(sdram_cas_n),.sdram_we_n(sdram_we_n),.sdram_ldqm(sdram_ldqm),.sdram_udqm(sdram_udqm));
 assign lcd_hsync=hs;assign lcd_vsync=vs;assign lcd_data_en=de;
 assign lcd_data_r=red;assign lcd_data_g=green;assign lcd_data_b=blue;
 ODDR #(.DDR_CLK_EDGE("SAME_EDGE")) dotclock(.C(pclk),.CE(1'b1),.D1(1'b1),.D2(1'b0),.R(1'b0),.S(1'b0),.Q(lcd_dotclk));
 assign vibrate_in1=0;assign vibrate_in2=0;
 assign dac_mclk=0;assign dac_bclk=0;assign dac_wclk=0;assign dac_din=0;
 wire[31:0]canvas_sequence,canvas_crc,canvas_words,canvas_current,canvas_errors,canvas_flags;
 cpl_canvas_crc canvas(.clk(clk100),.reset(job_reset),.word_valid(rgb_valid),.word_data(rgb_data),.word_x(rgb_x),.word_y(rgb_y),
  .canvas_sequence(canvas_sequence),.last_crc(canvas_crc),.last_word_count(canvas_words),.current_word_count(canvas_current),.sequence_errors(canvas_errors),.flags(canvas_flags));
 reg[63:0]core_cycles=0;reg[31:0]boundaries=0,boot_releases=0,job_releases=0;
 always @(posedge clk100)begin
  if(job_reset)begin core_cycles<=0;boundaries<=0;boot_releases<=0;job_releases<=0;end
  else begin
   if(core_cycles!=64'hffffffffffffffff)core_cycles<=core_cycles+1'b1;
   if(frame_boundary&&boundaries!=32'hffffffff)boundaries<=boundaries+1'b1;
   if(bootstrap_released&&boot_releases!=32'hffffffff)boot_releases<=boot_releases+1'b1;
   if(consumer_released&&job_releases!=32'hffffffff)job_releases<=job_releases+1'b1;
  end
 end
 wire[31:0]ignored_writes;wire ignored_exhausted;wire[1279:0]live_snapshot;
 wire[31:0]obs_flags=observations[0+:32],obs_result_info=observations[6*32+:32];
 assign live_snapshot[0+:96]=0;
 assign live_snapshot[3*32+:32]={19'd0,ignored_exhausted,1'b0,job_releases!=0,obs_result_info[17]&&obs_result_info[16],front_valid,base_qualified,obs_flags[13],load_complete,loader_busy,quarantined,consumer_started_once,autostart_once,boot_releases!=0};
 assign live_snapshot[4*32+:64]=core_cycles;
 assign live_snapshot[6*32+:64]=observations[7*32+:64];
 assign live_snapshot[8*32+:96]=observations[9*32+:96];
 assign live_snapshot[11*32+:32]=bytes_sent;
 assign live_snapshot[12*32+:32]=observations[2*32+:32];
 assign live_snapshot[13*32+:32]=observations[3*32+:32];
 assign live_snapshot[14*32+:32]=observations[5*32+:32];
 assign live_snapshot[15*32+:32]=observations[4*32+:32];
 assign live_snapshot[16*32+:128]=observations[12*32+:128];
 assign live_snapshot[20*32+:128]=observations[16*32+:128];
 assign live_snapshot[24*32+:32]=obs_result_info;
 assign live_snapshot[25*32+:32]={25'd0,obs_flags[4:0],status_panel_lock_sync[1],status_service_lock_sync[1]};
 assign live_snapshot[26*32+:32]=underruns;
 assign live_snapshot[27*32+:32]=boundaries;
 assign live_snapshot[28*32+:32]=boot_releases;
 assign live_snapshot[29*32+:32]=job_releases;
 assign live_snapshot[30*32+:32]=transport_lost_words;
 assign live_snapshot[31*32+:32]=ignored_writes;
 assign live_snapshot[32*32+:32]=canvas_sequence;
 assign live_snapshot[33*32+:32]=canvas_crc;
 assign live_snapshot[34*32+:32]=canvas_words;
 assign live_snapshot[35*32+:32]=canvas_flags;
 assign live_snapshot[36*32+:32]=canvas_errors;
 assign live_snapshot[37*32+:32]=canvas_current;
 assign live_snapshot[38*32+:64]=0;
 cpl_snapshot_csr csr(.clk(clk100),.reset(job_reset),.bus_write(core_write),.bus_address(core_address),.bus_wdata(core_wdata),
  .live_words(live_snapshot),.bus_rdata(core_rdata),.ignored_writes(ignored_writes),.ignored_exhausted(ignored_exhausted));
endmodule
`default_nettype wire
