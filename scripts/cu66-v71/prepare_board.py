"""Prepare isolated Rev4.1 CU71 lab shell; no synthesis/image/hardware by itself."""
from pathlib import Path
import argparse,hashlib,json,re,shutil
r=Path(__file__).resolve().parents[2]
a=argparse.ArgumentParser();a.add_argument('--output',required=True);a.add_argument('--system-module',default='cu71_system_bram');args=a.parse_args()
o=(r/args.output).resolve();o.mkdir(parents=True,exist_ok=False)
prior=Path('C:/Users/lavat/codex/moonbub/fpga/candidates/cp23-sdr2-balancedtag-20261105-v001/inputs')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=(prior/'rtl/moonshine_top_cpl1.sv').read_text()
header=old.split(' wire clk50',1)[0].replace('module moonshine_top_cpl1(', 'module moonshine_top_cu71(')
clocks=' wire clk50'+old.split(' wire clk50',1)[1].split(' wire[3:0]dq_i',1)[0]
def ports(path):
 s=path.read_text();m=re.search(r'module\s+\w+(?:\s*#\(.*?\))?\s*\((.*?)\n\);',s,re.S);assert m,path
 out={};direction=None;width=''
 for token in m[1].split(','):
  t=re.fullmatch(r'\s*(?:(input|output|inout)\s+(?:wire|logic|reg)\s*)?(\[[^\]]+\])?\s*(\w+)\s*',token);assert t,token
  if t[1]:direction=t[1];width=t[2] or ''
  elif t[2]:width=t[2]
  out[t[3]]=(direction,width)
 return out
sysports=ports(r/'fpga/experiments/cu66-v71/system/cu71_system.sv')
ctrlports=ports(r/'fpga/experiments/cu66-v71/system/cu71_local_control.sv')
physical=set(re.findall(r'\b(sdram_\w+)\b',header))
explicit=physical|{'clk','rst','read_clk','pixel_clk','pixel_reset_n','bus_write','bus_address','bus_wdata','bus_rdata','transport_fault'}
allports=dict(sysports)
for name,spec in ctrlports.items():
 if name in allports:assert allports[name][1]==spec[1],name
 allports[name]=spec
wires='\n'.join(' wire '+width+' '+name+';' for name,(_,width) in sorted(allports.items()) if name not in explicit)
body=r'''
 // Both domains and transport are jointly flushed; later clock loss quarantines
 // this diagnostic configuration until full reconfiguration, never a soft reset.
 (* ASYNC_REG="TRUE" *)reg[1:0]platform_service_lock_sync=0,platform_panel_lock_sync=0;
 reg platform_reset_ref=1;
 always @(posedge clk50)begin
  platform_service_lock_sync<={platform_service_lock_sync[0],locked};
  platform_panel_lock_sync<={platform_panel_lock_sync[0],plocked};
  platform_reset_ref<=!(platform_service_lock_sync[1]&&platform_panel_lock_sync[1]);
 end
 (* ASYNC_REG="TRUE" *)reg[3:0]joint_core_reset=15,joint_spi_reset=15,joint_pixel_reset=15;
 always @(posedge clk100 or posedge platform_reset_ref)if(platform_reset_ref)joint_core_reset<=15;else joint_core_reset<={joint_core_reset[2:0],1'b0};
 always @(posedge clk200 or posedge platform_reset_ref)if(platform_reset_ref)joint_spi_reset<=15;else joint_spi_reset<={joint_spi_reset[2:0],1'b0};
 always @(posedge pclk or posedge platform_reset_ref)if(platform_reset_ref)joint_pixel_reset<=15;else joint_pixel_reset<={joint_pixel_reset[2:0],1'b0};
 reg configuration_started=0,reconfigure_required=0;
 always @(posedge clk50)begin
  if(!platform_reset_ref)configuration_started<=1;
  if(configuration_started&&platform_reset_ref)reconfigure_required<=1;
 end
 (* ASYNC_REG="TRUE" *)reg[1:0]quarantine_sync=0;
 always @(posedge clk100)quarantine_sync<={quarantine_sync[0],reconfigure_required};
 wire clk=clk100,rst=joint_core_reset[3],read_clk=read_clk100,pixel_clk=pclk,pixel_reset_n=!joint_pixel_reset[3];
 wire[3:0]dq_i,dq_o,dq_oe,endpoint_control;wire irq;
 genvar k;generate for(k=0;k<4;k=k+1)begin:mcu_io
 IOBUF lane(.IO(mcu_spi_d[k]),.I(dq_o[k]),.O(dq_i[k]),.T(!dq_oe[k]));end endgenerate
 OBUFT irq_driver(.O(mcu_irq_n),.I(1'b0),.T(!irq));
 wire[11:0]buttons=~{btn_select,btn_start,btn_r,btn_l,btn_right,btn_left,btn_down,btn_up,btn_y,btn_x,btn_b,btn_a};
 wire spi_write,spi_read;wire[11:0]spi_addr;wire[31:0]spi_wdata,spi_rdata;
 moonshine_qspi_endpoint endpoint(.clk200(clk200),.rst_n(!joint_spi_reset[3]),
 .qspi_sck(mcu_spi_clk),.qspi_cs_n(mcu_spi_cs_n),.qspi_dq_i(dq_i),.dq_o(dq_o),.dq_oe(dq_oe),
 .buttons_native(buttons),.vblank(vsync),.irq_request(irq),.control(endpoint_control),.force_buttons_native(),
 .display_external(),.color_correct_enable(),.overlay_xctrl(),.overlay_yctrl(),.ov_wr(),.ov_addr(),.ov_data(),
 .core_write(spi_write),.core_read(spi_read),.core_address(spi_addr),.core_wdata(spi_wdata),.core_rdata(spi_rdata));
 wire bus_write;wire[11:0]bus_address;wire[31:0]bus_wdata,bus_rdata;
 wire transport_overflow;wire[31:0]transport_gray;
 (* ASYNC_REG="TRUE" *)reg[31:0]transport_gray_meta=0,transport_gray_sync=0;
 reg[31:0]transport_lost_words=0;
 function automatic[31:0]ungray_transport(input[31:0]value);
 integer i;begin for(i=0;i<32;i=i+1)ungray_transport[i]=^(value>>i);end endfunction
 always @(posedge clk100)begin
  if(rst)begin transport_gray_meta<=0;transport_gray_sync<=0;transport_lost_words<=0;end
  else begin transport_gray_meta<=transport_gray;transport_gray_sync<=transport_gray_meta;transport_lost_words<=ungray_transport(transport_gray_sync);end
 end
 wire transport_fault=quarantine_sync[1]||transport_lost_words!=0;
 moonshine_bus_cdc bridge(.spi_clk(clk200),.spi_reset(joint_spi_reset[3]),.spi_write(spi_write),.spi_read(spi_read),
 .spi_address(spi_addr),.spi_wdata(spi_wdata),.spi_rdata(spi_rdata),.overflow(transport_overflow),.overflow_gray(transport_gray),
 .core_clk(clk100),.core_reset(rst),.core_write(bus_write),.core_address(bus_address),.core_wdata(bus_wdata),.core_rdata(bus_rdata));
'''
instances=' cu71_local_control control_plane('+','.join('.'+n+'('+n+')' for n in ctrlports)+');\n'
instances+=' '+args.system_module+' #(.USE_STRIP(1),.WATCHDOG_CYCLES(32\'d3000000000)) system_core('+','.join('.'+n+'('+n+')' for n in sysports)+');\n'
tail=r'''
 assign lcd_hsync=hsync;assign lcd_vsync=vsync;assign lcd_data_en=data_enable;
 assign lcd_data_r=red;assign lcd_data_g=green;assign lcd_data_b=blue;
 ODDR #(.DDR_CLK_EDGE("SAME_EDGE")) dotclock(.C(pclk),.CE(1'b1),.D1(1'b1),.D2(1'b0),.R(1'b0),.S(1'b0),.Q(lcd_dotclk));
 assign vibrate_in1=0;assign vibrate_in2=0;assign dac_mclk=0;assign dac_bclk=0;assign dac_wclk=0;assign dac_din=0;
endmodule
`default_nettype wire
'''
top=o/'moonshine_top_cu71.sv';top.write_text(header+clocks+body+wires+'\n'+instances+tail,newline='\n')
for name in ['moonshine_qspi_endpoint.sv','moonshine_bus_cdc.sv']:shutil.copyfile(prior/'rtl'/name,o/name)
(o/'constraints').mkdir()
for name in ['lcd_pins_rev4.xdc','sdram_pins_rev4.xdc','buttons.xdc','platform.xdc']:shutil.copyfile(prior/'constraints'/name,o/'constraints'/name)
platform=o/'constraints/platform.xdc';text=platform.read_text()
assert text.count('0xC2310001')==1 and text.count('0x43505231')==1
platform.write_text(text.replace('0xC2310001','0x43553731').replace('0x43505231','0x43553731'),newline='\n')
(o/'provenance.json').write_text(json.dumps(dict(scope='LAB30SECOND_WATCHDOG_LOCAL_CU66_NO_NETWORK_OR_RATE_CLAIM',system_module=args.system_module,
 parent_top_sha256=sha(prior/'rtl/moonshine_top_cpl1.sv'),files={str(f.relative_to(o)).replace('\\','/'):sha(f) for f in o.rglob('*') if f.is_file()},
 qualification='Pending exact sources, functional shell tests, resource, clocks, CDC/reset, routed timing and hardware'),indent=2)+'\n')
print(o)
