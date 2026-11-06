`timescale 1ns/1ps
`default_nettype none
module sdr1_top(
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
 PLLE2_BASE #(.CLKIN1_PERIOD(20.0),.CLKFBOUT_MULT(20),.DIVCLK_DIVIDE(1),.CLKOUT0_DIVIDE(5),.CLKOUT1_DIVIDE(10),.CLKOUT2_DIVIDE(10),.CLKOUT2_PHASE(274.5))
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
 wire hs,vs,de;assign vs=v;wire[7:0]red,green,blue;wire[9:0]px,py;
 moonshine_qspi_endpoint endpoint(.clk200(clk200),.rst_n(!rst200[3]),
 .qspi_sck(mcu_spi_clk),.qspi_cs_n(mcu_spi_cs_n),.qspi_dq_i(dq_i),.dq_o(dq_o),.dq_oe(dq_oe),
 .buttons_native(buttons),.vblank(vs),.irq_request(irq),.control(control),.force_buttons_native(),
 .display_external(),.color_correct_enable(),.overlay_xctrl(),.overlay_yctrl(),
 .ov_wr(ov_wr),.ov_addr(ov_addr),.ov_data(ov_data),
 .core_write(spi_write),.core_read(spi_read),.core_address(spi_addr),.core_wdata(spi_wdata),.core_rdata(spi_rdata));

 assign spi_rdata = (spi_addr == 0) ? 32'h53445231 : (spi_addr == 4) ? 32'h00010000 : (spi_addr == 32'h00000184) ? 32'h53445231 : 32'd0;
 wire go,req,ready,wr,rv,mem_idle,wb,ri;wire[23:0]addr;wire[127:0]data;wire[15:0]rd,raw;
 wire[31:0]status,counts,first_values,run_id;wire[23:0]first_address;
 wire[255:0]raw_trace;wire[127:0]first_response;wire[15:0]response_mask;
 sdr1_engine engine(.clk(clk100),.reset(rst100[3]),.go(go),.request_valid(req),.request_ready(ready),
  .request_write(wr),.request_address(addr),.request_data(data),.response_valid(rv),.response_data(rd),
  .observe_write_beat(wb),.observe_read_issue(ri),.raw_read(raw),.status(status),.counts(counts),
  .first_address(first_address),.first_values(first_values),.raw_trace(raw_trace),
  .first_response(first_response),.response_mask(response_mask),.run_id(run_id));
 moonshine_sdram_burst controller(.clk(clk100),.read_clk(read_clk100),.reset(rst100[3]),
  .request_valid(req),.request_ready(ready),.request_write(wr),.request_address(addr),
  .request_burst_data(data),.request_burst_mask(16'd0),.response_valid(rv),.response_data(rd),.idle(mem_idle),
  .observe_write_beat(wb),.observe_read_issue(ri),.observe_raw_read(raw),
  .sdram_a(sdram_a),.sdram_bs(sdram_bs),.sdram_dq(sdram_dq),.sdram_clk(sdram_clk),
  .sdram_cke(sdram_cke),.sdram_cs_n(sdram_cs_n),.sdram_ras_n(sdram_ras_n),.sdram_cas_n(sdram_cas_n),
  .sdram_we_n(sdram_we_n),.sdram_ldqm(sdram_ldqm),.sdram_udqm(sdram_udqm));
 sdr1_vio monitor(.clk(clk100),.probe_out0(go),.probe_in0(status),.probe_in1({8'd0,first_address}),
  .probe_in2(first_values),.probe_in3(raw_trace[127:0]),.probe_in4(raw_trace[255:128]),
  .probe_in5(first_response),.probe_in6({response_mask,counts[15:0]}),.probe_in7(run_id),.probe_in8(counts));
 reg panel_error=0;
 always @(posedge clk100)begin
  if(rst100[3])panel_error<=0;else panel_error<=|status[23:16]|counts[3];
 end
 (* ASYNC_REG="TRUE" *)reg[1:0]panel_done=0,panel_bad=0;
 reg[9:0]lcd_x=0,lcd_y=0;reg h=0,v=0,active=0;reg[7:0]r=0,g=0,b=0;
 always @(posedge pclk)begin
  if(rstpixel[3])begin panel_done<=0;panel_bad<=0;lcd_x<=0;lcd_y<=0;h<=0;v<=0;active<=0;r<=0;g<=0;b<=0;end
  else begin
   panel_done<={panel_done[0],status[1]};panel_bad<={panel_bad[0],panel_error};
   if(lcd_x==540)begin lcd_x<=0;if(lcd_y==833)lcd_y<=0;else lcd_y<=lcd_y+1'b1;end else lcd_x<=lcd_x+1'b1;
   h<=lcd_x<4;v<=lcd_y<4;active<=lcd_x>=14&&lcd_x<494&&lcd_y>=24&&lcd_y<824;
   r<=panel_done[1]&&panel_bad[1]?8'hd0:8'h10;
   g<=panel_done[1]&&!panel_bad[1]?8'hb0:8'h20;
   b<=panel_done[1]?8'h10:8'h50;
  end
 end
 assign lcd_hsync=h;assign lcd_vsync=v;assign lcd_data_en=active;
 assign lcd_data_r=active?r:0;assign lcd_data_g=active?g:0;assign lcd_data_b=active?b:0;
 ODDR #(.DDR_CLK_EDGE("SAME_EDGE"))dotclock(.C(pclk),.CE(1'b1),.D1(1'b1),.D2(1'b0),.R(1'b0),.S(1'b0),.Q(lcd_dotclk));
 assign vibrate_in1=0;assign vibrate_in2=0;assign dac_mclk=0;assign dac_bclk=0;assign dac_wclk=0;assign dac_din=0;
endmodule
