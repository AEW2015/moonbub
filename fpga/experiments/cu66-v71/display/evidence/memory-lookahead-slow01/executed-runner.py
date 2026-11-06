"""Conditional pin-model + exact selected backend + asynchronous LCD integration."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,time
r=Path(__file__).resolve().parents[3]
a=argparse.ArgumentParser();a.add_argument('--output',required=True);a.add_argument('--corner',choices=['fast','slow'],required=True)
a.add_argument('--memory-proof',default='fpga/experiments/cu66-v71/memory/evidence/rowburst-line01')
a.add_argument('--background',choices=['contended','idle'],default='contended');args=a.parse_args()
o=(r/args.output).resolve();o.mkdir(parents=True,exist_ok=False)
memory=(r/args.memory_proof).resolve()
display=r/'fpga/experiments/cu66-v71/display'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
freeze=json.loads((memory/'source-freeze.json').read_text())
names=['cu71_memory_system.sv','cu71_word_bridge.sv','cu71_tile_memory.sv','moonshine_sdram_burst.sv','cu70_memory_map.svh','model.sv','primitives.sv']
for name in names:
 assert sha(memory/name)==freeze[name],name
 shutil.copyfile(memory/name,o/name)
for name in ['cu71_scanout_prefetch.sv','cu71_lcd_lines.sv','tb_scanout_memory.sv']:shutil.copyfile(display/name,o/name)
if args.corner=='slow':
 p=o/'tb_scanout_memory.sv';s=p.read_text().replace('.T_AC_NS(2.223),.CLOCK_FLIGHT_NS(0.757),.T_OH_NS(2.223)','.T_AC_NS(8.489),.CLOCK_FLIGHT_NS(3.768),.T_OH_NS(2.223)');p.write_text(s,newline='\n')
files=names[:-3]+['model.sv','primitives.sv','cu71_scanout_prefetch.sv','cu71_lcd_lines.sv','tb_scanout_memory.sv']
sources={n:sha(o/n) for n in names+['cu71_scanout_prefetch.sv','cu71_lcd_lines.sv','tb_scanout_memory.sv']}
(o/'source-freeze.json').write_text(json.dumps(sources,indent=2)+'\n')
shutil.copyfile(Path(__file__),o/'executed-runner.py')
env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env.get('PATH','')
steps=[]
for label,cmd in [('compile',['C:/msys64/ucrt64/bin/iverilog.exe','-g2012','-s','tb_scanout_memory','-Ptb_scanout_memory.BACKGROUND='+str(int(args.background=='contended')),'-I',str(o),'-o',str(o/'test.vvp'),*[str(o/n)for n in files]]),('simulation',['C:/msys64/ucrt64/bin/vvp.exe','-i',str(o/'test.vvp')])]:
 started=time.monotonic()
 with(o/(label+'.log')).open('wb')as f:p=subprocess.run(cmd,cwd=o,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=600)
 steps.append(dict(label=label,command=cmd,returncode=p.returncode,seconds=time.monotonic()-started))
 (o/'execution.json').write_text(json.dumps(steps,indent=2)+'\n')
 print(label,p.returncode,flush=True);assert p.returncode==0,(label,o)
log=(o/'simulation.log').read_text()
assert 'CU71_MEMORY_SCANOUT_FUNCTIONAL_PASS' in log
cadence='CU71_MEMORY_SCANOUT_CADENCE_PASS' in log
assert sources=={n:sha(o/n)for n in sources}
(o/'result.json').write_text(json.dumps(dict(status='PASS_SELECTED_LINE_INTEGRATION' if cadence else 'FAIL_SELECTED_LINE_CADENCE_FUNCTIONAL_DATA_PASS',corner=args.corner,
 sources=sources,memory_origin=str(memory),background=args.background,SIMULATION_define=False,hardware=False,routed_timing=False,normal_load_underrun_gate=cadence,
 limits=['8 selected canvas lines, not full raster or30fps qualification','Fixture memory is initialized by testbench; this is not decode or write-path qualification','Concurrent actual canonical tile/HUD writes and refresh','Selected lumped routed timing model terms, not independent board/PVT signoff']),indent=2)+'\n')
print('CU71_SELECTED_LINES_COMPLETE cadence=',cadence,o,flush=True)
