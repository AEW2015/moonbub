`timescale 1ns/1ps
`default_nettype none
module moonshine_top(
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
 PLLE2_BASE #(.CLKIN1_PERIOD(20.0),.CLKFBOUT_MULT(20),.DIVCLK_DIVIDE(1),.CLKOUT0_DIVIDE(5),.CLKOUT1_DIVIDE(10),.CLKOUT2_DIVIDE(10),.CLKOUT2_PHASE(279.0))
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
 wire front,front_valid,pattern,frame_boundary,mem_idle,pixel_valid,pixel_ready;
 wire[23:0]pixel_address;wire[15:0]pixel_data;wire[31:0]underruns;
 moonshine_core core(.clk(clk100),.reset(rst100[3]),.bus_write(core_write),.bus_address(core_address),
 .bus_wdata(core_wdata),.bus_rdata(core_rdata),.frame_boundary(frame_boundary),.memory_idle(mem_idle),
 .front_buffer(front),.front_valid(front_valid),.pattern_enable(pattern),
 .pixel_valid(pixel_valid),.pixel_ready(pixel_ready),.pixel_address(pixel_address),.pixel_rgb565(pixel_data),.scanout_underruns(underruns),.transport_overflows(transport_lost_words));
 wire line_request,line_ready,line_valid;wire[23:0]line_address;wire[15:0]line_data;
 moonshine_memory memory(.clk(clk100),.read_clk(read_clk100),.reset(rst100[3]),
 .pixel_valid(pixel_valid),.pixel_ready(pixel_ready),.pixel_address(pixel_address),.pixel_rgb565(pixel_data),
 .line_req_valid(line_request),.line_req_ready(line_ready),.line_req_address(line_address),.line_data_valid(line_valid),.line_data(line_data),.idle(mem_idle),
 .sdram_a(sdram_a),.sdram_bs(sdram_bs),.sdram_dq(sdram_dq),.sdram_clk(sdram_clk),.sdram_we_n(sdram_we_n),
 .sdram_ldqm(sdram_ldqm),.sdram_udqm(sdram_udqm),.sdram_cas_n(sdram_cas_n),.sdram_ras_n(sdram_ras_n),.sdram_cke(sdram_cke),.sdram_cs_n(sdram_cs_n));
 moonshine_lcd lcd(.pixel_clk(pclk),.reset_n(!rstpixel[3]),.mem_clk(clk100),.mem_reset(rst100[3]),
 .front_valid(front_valid),.front_buffer(front),.pattern_enable(pattern),.line_req_valid(line_request),.line_req_ready(line_ready),
 .line_req_address(line_address),.line_data_valid(line_valid),.line_data(line_data),.frame_boundary(frame_boundary),.underruns(underruns),
 .hsync(hs),.vsync(vs),.data_enable(de),.red(red),.green(green),.blue(blue),.physical_x(px),.physical_y(py));
 esp32_overlay #(.TESTER_THEME(0)) overlay(.sys_clk(clk200),.sys_rst_n(!rst200[3]),
 .ov_wr(ov_wr),.ov_addr(ov_addr),.ov_data(ov_data),.pixel_clk(pclk),.pixel_rst_n(!rstpixel[3]),
 .in_x(px),.in_y(py),.in_hs(hs),.in_vs(vs),.in_de(de),.in_rgb({red,green,blue}),
 .out_hs(lcd_hsync),.out_vs(lcd_vsync),.out_de(lcd_data_en),.out_rgb({lcd_data_r,lcd_data_g,lcd_data_b}),.overlay_visible());
 ODDR #(.DDR_CLK_EDGE("SAME_EDGE")) dotclock(.C(pclk),.CE(1'b1),.D1(1'b0),.D2(1'b1),.R(1'b0),.S(1'b0),.Q(lcd_dotclk));
 // No audio or motor activity in the video-only milestone.
 assign vibrate_in1=0;assign vibrate_in2=0;assign dac_mclk=0;assign dac_bclk=0;assign dac_wclk=0;assign dac_din=0;
endmodule
`default_nettype wire
