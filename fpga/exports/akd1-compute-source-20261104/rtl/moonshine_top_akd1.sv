`timescale 1ns/1ps
`default_nettype none
// Decoder-exclusive local compute laboratory shell. No network/video admission.
module moonshine_top_akd1(
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
 wire fb,fbb,raw200,raw100,clk200,clk100,locked;
 PLLE2_BASE #(.CLKIN1_PERIOD(20.0),.CLKFBOUT_MULT(20),.DIVCLK_DIVIDE(1),.CLKOUT0_DIVIDE(5),.CLKOUT1_DIVIDE(10),.CLKOUT2_DIVIDE(10),.CLKOUT2_PHASE(279.0))
 service_pll(.CLKIN1(clk50),.CLKFBIN(fbb),.CLKFBOUT(fb),.CLKOUT0(raw200),.CLKOUT1(raw100),.CLKOUT2(),.LOCKED(locked),.PWRDWN(1'b0),.RST(1'b0));
 BUFG feedback(.I(fb),.O(fbb));BUFG spi_clock(.I(raw200),.O(clk200));BUFG memory_clock(.I(raw100),.O(clk100));
 wire pfb,pfbb,praw,pclk,plocked;
 MMCME2_BASE #(.CLKIN1_PERIOD(20.0),.CLKFBOUT_MULT_F(56.375),.DIVCLK_DIVIDE(3),.CLKOUT0_DIVIDE_F(32.0))
 panel_mmcm(.CLKIN1(clk50),.CLKFBIN(pfbb),.CLKFBOUT(pfb),.CLKOUT0(praw),.LOCKED(plocked),.PWRDWN(1'b0),.RST(1'b0));
 BUFG panel_feedback(.I(pfb),.O(pfbb));BUFG panel_clock(.I(praw),.O(pclk));
 (* ASYNC_REG="TRUE" *)reg[3:0]rst200=15,rst100=15,rstpixel=15;
 always @(posedge clk200 or negedge locked)if(!locked)rst200<=15;else rst200<={rst200[2:0],1'b0};
 always @(posedge clk100 or negedge locked)if(!locked)rst100<=15;else rst100<={rst100[2:0],1'b0};
 always @(posedge pclk or negedge plocked)if(!plocked)rstpixel<=15;else rstpixel<={rstpixel[2:0],1'b0};
 // One registered reset source in the always-running reference domain.
 // Synchronize each PLL status separately; never OR clocked-domain reset
 // outputs directly into another domain's asynchronous reset synchronizer.
 // Lock loss is observed within three50MHz cycles even if a PLL clock stops.
 (* ASYNC_REG="TRUE" *)reg[1:0]audio_service_lock_sync=0,audio_panel_lock_sync=0;
 reg audio_reset=1;
 always @(posedge clk50)begin
  audio_service_lock_sync<={audio_service_lock_sync[0],locked};
  audio_panel_lock_sync<={audio_panel_lock_sync[0],plocked};
  audio_reset<=!(audio_service_lock_sync[1] && audio_panel_lock_sync[1]);
 end
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
 wire[6:0]display_margin;wire lcd_frame_origin;wire[31:0]margin_rdata,timing_rdata,audio_rdata,diagnostic_rdata;
 wire[9:0]timing_hsync,timing_vsync,timing_hstart,timing_vstart,timing_htotal,timing_vtotal;
 wire diagnostic_address=core_address>=12'h400&&core_address<=12'h44c&&core_address[1:0]==0;
 assign core_rdata=core_address==12'h000 ? 32'h31444b41:
  core_address==12'h004 ? 32'h00010000:
  core_address==12'h008 ? 32'd0:
  core_address==12'h184 ? 32'h4d424b31:
  (core_address>=12'h300&&core_address<=12'h380)?audio_rdata:
  (core_address==12'h084||core_address==12'h088||core_address==12'h08c)?margin_rdata:
  (core_address>=12'h090&&core_address<=12'h0a8&&core_address[1:0]==0)?timing_rdata:
  diagnostic_address?diagnostic_rdata:32'd0;
 ar03_fixture_diagnostic diagnostic(.clk(clk100),.reset(rst100[3]),
  .bus_write(core_write&&diagnostic_address),.bus_address(core_address),
  .bus_wdata(core_wdata),.bus_rdata(diagnostic_rdata));
 moonshine_margin_control margin(.core_clk(clk100),.core_reset(rst100[3]),.pixel_clk(pclk),.pixel_reset(rstpixel[3]),.frame_origin(lcd_frame_origin),
  .bus_write(core_write),.bus_address(core_address),.bus_wdata(core_wdata),.bus_rdata(margin_rdata),.pixel_margin(display_margin));
 moonshine_timing_control timing(.core_clk(clk100),.core_reset(rst100[3]),.pixel_clk(pclk),.pixel_reset(rstpixel[3]),.frame_origin(lcd_frame_origin),
  .bus_write(core_write),.bus_address(core_address),.bus_wdata(core_wdata),.bus_rdata(timing_rdata),
  .pixel_hsync(timing_hsync),.pixel_vsync(timing_vsync),.pixel_hstart(timing_hstart),.pixel_vstart(timing_vstart),.pixel_htotal(timing_htotal),.pixel_vtotal(timing_vtotal));
 // Explicit inactive external memory. No initialization, capture or timing
 // qualification is claimed for these static pins; DQ is never driven/read.
 assign sdram_a=13'd0;assign sdram_bs=2'd0;assign sdram_dq=16'bz;
 assign sdram_clk=1'b0;assign sdram_we_n=1'b1;assign sdram_ldqm=1'b1;assign sdram_udqm=1'b1;
 assign sdram_cas_n=1'b1;assign sdram_ras_n=1'b1;assign sdram_cke=2'b00;assign sdram_cs_n=2'b11;
 moonshine_lcd_720p lcd(.pixel_clk(pclk),.reset_n(!rstpixel[3]),.mem_clk(clk100),.mem_reset(rst100[3]),
 .front_valid(1'b0),.front_buffer(1'b0),.pattern_enable(1'b1),.front_720p(1'b0),.display_margin(display_margin),.frame_origin(lcd_frame_origin),
 .timing_hsync(timing_hsync),.timing_vsync(timing_vsync),.timing_hstart(timing_hstart),.timing_vstart(timing_vstart),.timing_htotal(timing_htotal),.timing_vtotal(timing_vtotal),.line_req_valid(),.line_req_ready(1'b0),
 .line_req_address(),.line_data_valid(1'b0),.line_data(16'd0),.frame_boundary(),.underruns(),
 .hsync(hs),.vsync(vs),.data_enable(de),.red(red),.green(green),.blue(blue),.physical_x(px),.physical_y(py));
 esp32_overlay #(.TESTER_THEME(0)) overlay(.sys_clk(clk200),.sys_rst_n(!rst200[3]),
 .ov_wr(ov_wr),.ov_addr(ov_addr),.ov_data(ov_data),.pixel_clk(pclk),.pixel_rst_n(!rstpixel[3]),
 .in_x(px),.in_y(py),.in_hs(hs),.in_vs(vs),.in_de(de),.in_rgb({red,green,blue}),
 .out_hs(lcd_hsync),.out_vs(lcd_vsync),.out_de(lcd_data_en),.out_rgb({lcd_data_r,lcd_data_g,lcd_data_b}),.overlay_visible());
 ODDR #(.DDR_CLK_EDGE("SAME_EDGE")) dotclock(.C(pclk),.CE(1'b1),.D1(1'b1),.D2(1'b0),.R(1'b0),.S(1'b0),.Q(lcd_dotclk));
 reg[31:0]audio_transport_seen=0;
 always @(posedge clk100)if(rst100[3])audio_transport_seen<=0;else audio_transport_seen<=transport_lost_words;
 moonshine_audio audio(.core_clk(clk100),.pixel_clk(pclk),.arst(audio_reset),
 .bus_write(core_write),.bus_address(core_address),.bus_wdata(core_wdata),.bus_rdata(audio_rdata),
 .transport_fault(transport_lost_words!=audio_transport_seen),.dac_bclk(dac_bclk),.dac_wclk(dac_wclk),.dac_din(dac_din));
 ODDR #(.DDR_CLK_EDGE("SAME_EDGE")) audio_mclock(.C(pclk),.CE(1'b1),.D1(1'b1),.D2(1'b0),.R(1'b0),.S(1'b0),.Q(dac_mclk));
 assign vibrate_in1=0;assign vibrate_in2=0;
endmodule
`default_nettype wire
