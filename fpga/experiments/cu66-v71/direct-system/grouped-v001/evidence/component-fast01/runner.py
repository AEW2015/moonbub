"""Actual pin-model regression of isolated grouped scheduler, all accepted-beat aborts."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,time
p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--slow',action='store_true');p.add_argument('--seed',type=int,default=7001);a=p.parse_args();r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/direct-system/grouped-v001';base=r/'fpga/experiments/cu66-v71/memory/evidence/direct-fast01';o=Path(a.output).resolve();o.mkdir(parents=True,exist_ok=False);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=['cu71_memory_system_direct.sv','cu71_word_bridge_direct.sv','cu71_tile_memory_direct.sv','moonshine_sdram_burst.sv','model.sv','primitives.sv','cu70_memory_map.svh']
for n in files:shutil.copy2(d/'source'/n,o/n)
tb=(base/'tb.sv').read_text();tb=tb.replace(' integer checks=0,',''' integer observed_LCD=0,observed_BG=0;
 always @(posedge clk)if(!rst&&dut.mem_req_valid&&dut.mem_req_ready)begin
  if(dut.bridge.owner==2)observed_LCD=observed_LCD+1;else observed_BG=observed_BG+1;
 end
 integer checks=0,''')
if a.slow:tb=tb.replace('.T_AC_NS(2.223),.CLOCK_FLIGHT_NS(0.757)', '.T_AC_NS(8.489),.CLOCK_FLIGHT_NS(3.768)')
needle='  $display("CU71_DIRECT_MEMORY_PASS';assert tb.count(needle)==1
tb=tb.replace(needle,'''  if(observed_LCD!=dut.bridge.group_lcd_accepted||observed_BG!=dut.bridge.group_bg_accepted)$fatal(1,"quota chargednonphysical/localoperation");
  $display("CU71_GROUPED_ACCOUNTING_PASS LCD=%0d BG=%0d uncharged=%0d idle=%0d LCD_idle=%0d BG_idle=%0d LCD_expiry=%0d BG_expiry=%0d max_LCD_wait=%0d max_BG_wait=%0d",observed_LCD,observed_BG,dut.bridge.group_uncharged,dut.bridge.group_reserved_idle,dut.bridge.group_lcd_reserved_idle,dut.bridge.group_bg_reserved_idle,dut.bridge.group_lcd_expiry,dut.bridge.group_bg_expiry,lcd_max_wait,dut.bridge.group_bg_max_wait);
'''+needle)
(o/'tb.sv').write_text(tb,newline='\n');(o/'runner.py').write_bytes(Path(__file__).read_bytes());(o/'source-freeze.json').write_text(json.dumps({n:sha(o/n)for n in files+['tb.sv','runner.py']},indent=2)+'\n')
sources=[n for n in files if n.endswith('.sv')]+['tb.sv'];env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env.get('PATH','');steps=[]
for label,cmd in [('compile',['C:/msys64/ucrt64/bin/iverilog.exe','-g2012','-s','tb_memory','-I',str(o),'-o',str(o/'test.vvp'),*[str(o/n)for n in sources]]),('simulation',['C:/msys64/ucrt64/bin/vvp.exe','-i',str(o/'test.vvp'),'+SEED='+str(a.seed)])]:
 t=time.monotonic()
 with(o/(label+'.log')).open('wb')as f:q=subprocess.run(cmd,cwd=o,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=600)
 steps.append({'label':label,'command':cmd,'returncode':q.returncode,'seconds':time.monotonic()-t});(o/'execution.json').write_text(json.dumps(steps,indent=2)+'\n');print(label,q.returncode,flush=True);assert q.returncode==0,(label,o)
log=(o/'simulation.log').read_text();assert all(s in log for s in ['CU71_DIRECT_MEMORY_PASS','CU71_DIRECT_TILE_COMMAND_PASS','CU71_DIRECT_ABORT_ALL_PASS','CU71_GROUPED_ACCOUNTING_PASS'])
(o/'result.json').write_text(json.dumps({'status':'PASS_GROUPED_ACTUAL_CONTROLLER_COMPONENT_AND_ABORTS','slow':a.slow,'seed':a.seed,'policy':'8LCD:4BGphysicalcommands+18LCD/4BGboundedgrace','hardware':False,'routed_timing':False,'scope':'Originaldirectallplanes/banks/bounds/masks/physicaloracle/94abortprobes plusphysical-onlyquotaaccounting. Dedicatedcontendedfairness/responseisolationproofrequiredseparatelybeforefullsystemuse.'},indent=2)+'\n')
