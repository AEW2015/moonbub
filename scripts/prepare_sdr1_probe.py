"""Prepare a distinct SDR1 JTAG/VIO probe; no image or hardware operation."""
from pathlib import Path
import hashlib,json,shutil
r=Path(__file__).resolve().parents[1]
p=r/'fpga/candidates/cp23-sdram-capture274p5-20261105-v001/inputs'
c=r/'fpga/diagnostics/sdr1-20261105';o=c/'source-v005';o.mkdir(exist_ok=False)
shutil.copyfile(c/'engine.sv',o/'engine.sv')
s=(p/'core/parents/moonshine_sdram_burst.sv').read_text()
assert s.count('/*CPL_OBS_BEGIN*/output wire observe_write_beat,')==1
s=s.replace('/*CPL_OBS_BEGIN*/output wire observe_write_beat,','/*CPL_OBS_BEGIN*/output wire observe_read_issue,output wire[15:0]observe_raw_read,output wire observe_write_beat,')
s=s.replace(' assign observe_write_beat=', ' assign observe_read_issue=!reset&&state==RW_CMD&&!is_write;assign observe_raw_read=dq_retime;\n assign observe_write_beat=')
(o/'controller.sv').write_text(s,newline='\n')
shutil.copyfile(p/'rtl/moonshine_qspi_endpoint.sv',o/'endpoint.sv')
shutil.copytree(p/'constraints',o/'constraints')
f=o/'constraints/platform.xdc';f.write_text(f.read_text().replace('0xC2310001','0x53445231').replace('0x43505231','0x53445231'),newline='\n')
top=(p/'rtl/moonshine_top_cpl1.sv').read_text()
top=top[:top.index(' wire core_write;')].replace('moonshine_top_cpl1','sdr1_top')
top+='''
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
'''
# Endpoint's retained vblank connection uses this status raster.
top=top.replace(' wire hs,vs,de;',' wire hs,vs,de;assign vs=v;')
(o/'top.sv').write_text(top,newline='\n')
(o/'source-freeze.json').write_text(json.dumps({str(f.relative_to(o)).replace('\\','/'):hashlib.sha256(f.read_bytes()).hexdigest()for f in o.rglob('*')if f.is_file()},indent=2)+'\n')
print('SDR1_SOURCE_PREPARED',o)
