"""Minimal IO-only native synthesis, exact frozen DY71 pin XDC, private paths."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,time
r=Path(__file__).resolve().parents[3];p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--temp-style',choices=['native','forward'],required=True);p.add_argument('--without-xdc',action='store_true');a=p.parse_args()
o=a.output.resolve();o.mkdir(parents=True,exist_ok=False);tmp=o/'tmp';tmp.mkdir();sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
build=r/'dy71i03';selection=json.loads((build/'selection.json').read_text());top=next(n for n in selection['sources']if n.endswith('moonshine_top_dy71.sv'));source=build/'inputs'/top
text=source.read_text();header=text[:text.index(');')+2]
outputs='mcu_irq_n,lcd_dotclk,lcd_hsync,lcd_vsync,lcd_data_en,lcd_data_r,lcd_data_g,lcd_data_b,sdram_a,sdram_bs,sdram_clk,sdram_we_n,sdram_ldqm,sdram_udqm,sdram_cas_n,sdram_ras_n,sdram_cke,sdram_cs_n,vibrate_in1,vibrate_in2,dac_mclk,dac_bclk,dac_wclk,dac_din'
body='''
reg [7:0] count=0;
always @(posedge clk_50mhz) count<=count+{7'd0,(^mcu_spi_d)^(^sdram_dq)^mcu_spi_clk^mcu_spi_cs_n^btn_a^btn_b^btn_x^btn_y^btn_up^btn_down^btn_left^btn_right^btn_l^btn_r^btn_start^btn_select};
assign mcu_spi_d=4'bzzzz;assign sdram_dq=16'bz;
assign {OUTPUTS}={200{count[0]}};
endmodule
'''.replace('OUTPUTS',outputs)
(o/'minimal.sv').write_text(header+body,newline='\n');pins={top:sha(source)}
t='''set_param general.maxThreads 2
puts "OBSERVED_TEMP $::env(TEMP)"
puts "OBSERVED_TMP $::env(TMP)"
puts "OBSERVED_CWD [pwd]"
proc directory_observer {command operation} {if {[lindex $command 1] eq "mkdir"} {puts "OBSERVED_TCL_MKDIR [list $command]"}}
trace add execution ::file enter directory_observer
create_project -in_memory -part xc7a100tcsg324-1 minimal_io
read_verilog -sv {MINIMAL}
'''.replace('MINIMAL',(o/'minimal.sv').as_posix())
if not a.without_xdc:
 for name in selection['XDC_order']:
  n=str(Path(selection['constraint_entry']).parent/name).replace('\\','/');f=build/'inputs'/n;require=sha(f);assert require==selection['constraints_sha256'][n]
  dest=o/'inputs'/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dest);pins[n]=sha(f)
  t+='read_xdc {'+dest.as_posix()+'}\n'
t+='synth_design -top moonshine_top_dy71 -part xc7a100tcsg324-1\nputs MINIMAL_IO_SYNTH_COMPLETE_NO_IMPLEMENTATION_OR_HARDWARE\n'
(o/'executed.tcl').write_text(t,newline='\n');env=dict(os.environ,TEMP=tmp.as_posix()if a.temp_style=='forward'else str(tmp),TMP=tmp.as_posix()if a.temp_style=='forward'else str(tmp))
dump=lambda name,v:(o/name).write_text(json.dumps(v,indent=2)+'\n')
dump('binding.json',dict(source_header_parent_sha256=sha(source),minimal_source_sha256=sha(o/'minimal.sv'),frozen_XDC_sha256=pins,temp_style=a.temp_style,TEMP=env['TEMP'],TMP=env['TMP'],no_full_design=True,hardware=False))
cmd=['C:/Xilinx/2025.2/Vivado/bin/vivado.bat','-mode','batch','-source',str(o/'executed.tcl'),'-log',str(o/'vivado.log'),'-journal',str(o/'vivado.jou')]
start=time.monotonic()
with(o/'console.log').open('w')as log:q=subprocess.run(cmd,cwd=o,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=240)
text=(o/'console.log').read_text();errors=[x for x in text.splitlines()if x.startswith('ERROR:')]
result=dict(returncode=q.returncode,command=cmd,seconds=time.monotonic()-start,native_errors=errors,completion='MINIMAL_IO_SYNTH_COMPLETE_NO_IMPLEMENTATION_OR_HARDWARE'in text,binding_sha256=sha(o/'binding.json'),hardware=False)
dump('result.json',result);print(json.dumps(result,indent=2))
