from pathlib import Path
import argparse,hashlib,json,os,shlex,shutil,subprocess,time
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/direct-display';native=r/'experiments/cu66-native-v69'
a=argparse.ArgumentParser();a.add_argument('--output',required=True);a.add_argument('--corner',choices=['fast','slow'],default='fast');a.add_argument('--last-line',type=int,default=799);a.add_argument('--variant',choices=['base','pipe'],default='base');a.add_argument('--background',action='store_true');a.add_argument('--front-bank',type=int,default=0);a.add_argument('--write-bank',type=int,default=1);a.add_argument('--write-hud-bank',type=int);args=a.parse_args();o=(r/args.output).resolve();o.mkdir(parents=True,exist_ok=False)
m=r/'fpga/experiments/cu66-v71/memory/evidence/direct-fast01';freeze=json.loads((m/'source-freeze.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
names=['cu71_memory_system_direct.sv','cu71_word_bridge_direct.sv','cu71_tile_memory_direct.sv','moonshine_sdram_burst.sv','cu70_memory_map.svh','model.sv','primitives.sv']
for n in names:assert sha(m/n)==freeze[n];shutil.copyfile(m/n,o/n)
top='cu71_direct_scanout_pipe'if args.variant=='pipe'else'cu71_direct_scanout'
dnames=[top+'.sv','cu71_cache_dma.sv','cu71_direct_cache.sv','cu71_yuv_pixel_pipe.sv','cu71_lcd_lines_direct.sv','tb_direct_reference.sv','export_pin_fixture.cpp']
for n in dnames:shutil.copyfile(d/n,o/n)
if args.variant=='pipe':
 p=o/'tb_direct_reference.sv';p.write_text(p.read_text().replace('cu71_direct_scanout scanout','cu71_direct_scanout_pipe scanout'),newline='\n')
if args.corner=='slow':
 p=o/'tb_direct_reference.sv';p.write_text(p.read_text().replace('.T_AC_NS(2.223),.CLOCK_FLIGHT_NS(0.757),.T_OH_NS(2.223)','.T_AC_NS(8.489),.CLOCK_FLIGHT_NS(3.768),.T_OH_NS(2.223)'),newline='\n')
sources={n:sha(o/n)for n in names+dnames};(o/'source-freeze.json').write_text(json.dumps(sources,indent=2)+'\n');shutil.copyfile(Path(__file__),o/'executed-runner.py')
steps=[];env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env.get('PATH','')
def run(label,cmd,timeout=1200):
 t=time.monotonic()
 with(o/(label+'.log')).open('wb')as f:q=subprocess.run(cmd,cwd=o,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
 steps.append(dict(label=label,command=cmd,returncode=q.returncode,seconds=time.monotonic()-t));(o/'execution.json').write_text(json.dumps(steps,indent=2)+'\n');print(label,q.returncode,flush=True);assert q.returncode==0,(label,o)
unix=lambda p:'/mnt/'+p.drive[0].lower()+str(p)[2:].replace('\\','/')
# Compile original fixture exporter, retaining its source and native codec identity.
files=[d/'export_pin_fixture.cpp',*native.glob('*.hpp'),native/'index.tsv',*sorted((native/'fixtures').glob('*.cu66'))]
for p in files:
 f=o/'source-snapshot'/p.relative_to(r);f.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,f)
(o/'fixture-source-hashes.json').write_text(json.dumps({str(p.relative_to(r)):sha(p)for p in files},indent=2)+'\n')
exe='/tmp/cu71-direct-export-'+str(time.time_ns());run('export-build',['wsl','-d','MRS-HDL-Research','--','g++','-std=c++17','-O2',unix(d/'export_pin_fixture.cpp'),'-o',exe]);run('fixture-export',['wsl','-d','MRS-HDL-Research','--',exe,unix(native/'index.tsv'),unix(o)])
rtl=[n for n in names if n.endswith('.sv')]+[n for n in dnames if n.endswith('.sv')]
run('compile',['C:/msys64/ucrt64/bin/iverilog.exe','-g2012','-s','tb_direct_reference','-Ptb_direct_reference.LAST_LINE='+str(args.last_line),'-Ptb_direct_reference.BACKGROUND='+str(int(args.background)),'-Ptb_direct_reference.FRONT_BANK='+str(args.front_bank),'-Ptb_direct_reference.WRITE_BANK='+str(args.write_bank),'-Ptb_direct_reference.WRITE_HUD_BANK='+str(args.write_hud_bank if args.write_hud_bank is not None else args.write_bank),'-I',str(o),'-o',str(o/'test.vvp'),*[str(o/n)for n in rtl]])
run('simulation',['C:/msys64/ucrt64/bin/vvp.exe','-i',str(o/'test.vvp')])
log=(o/'simulation.log').read_text();assert 'CU71_DIRECT_PIN_FUNCTIONAL_PASS'in log;assert sources=={n:sha(o/n)for n in sources}
(o/'result.json').write_text(json.dumps(dict(status='PASS_PIN_NATIVE_RASTER'if'CU71_DIRECT_PIN_CADENCE_PASS'in log else'FAIL_CADENCE_EXACT_OR_WHOLE_BLACK_LINES',sources=sources,corner=args.corner,last_line=args.last_line,front_bank=args.front_bank,reference_bank=args.front_bank,candidate_bank=args.write_bank,hud_candidate_bank=args.write_hud_bank if args.write_hud_bank is not None else args.write_bank,owner_variant=args.variant,background_reference_copy=args.background,hardware=False,SIMULATION_define=False,limits=['Canonical/HUD actual native key fixture preloaded by testbench; no decoder/write-path qualification',('Actual FRONT canonical reference reads + candidate canonical/HUD writes + refresh; complete decoder/root integration pending'if args.background else'LCD-only actual selected pin-model with refresh; concurrent decode and owner integration pending'),'Lumped selected timing corners are not independent board/PVT signoff']),indent=2)+'\n')
