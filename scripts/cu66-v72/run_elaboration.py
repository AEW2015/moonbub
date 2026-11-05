#!/usr/bin/env python3
"""Direct native-Yosys preflight: report blocked leaves without changing RTL."""
import hashlib,json,os,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'fpga/experiments/cu66-v72/memory/elaboration'
MAP=ROOT/'fpga/experiments/cu66-v70/memory'
CONTAINER=os.environ.get('TASK_CONTAINER','gamebub-cu66-v69-build')
LEAVES=(('bridge','cu72_word_bridge','memory/cu72_word_bridge.sv'),('tiles','cu72_tile_memory','memory/cu72_tile_memory.sv'),('painter','cu72_painter_burst','display/cu72_painter_burst.sv'))
OLD=ROOT/'fpga/experiments/cu66-v70/display/cu70_painter_strip.sv'
SOURCES=[ROOT/'fpga/experiments/cu66-v72'/name for _,_,name in LEAVES]+[MAP/'cu70_memory_map.svh',OLD,Path(__file__).resolve()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
pins={str(p.relative_to(ROOT)):sha(p)for p in SOURCES};commands=[];rows=[]
def run(argv,path):
 with path.open('w')as f:p=subprocess.run(argv,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=120)
 commands.append(dict(argv=argv,log=str(path.relative_to(ROOT)),exit_code=p.returncode,sha256=sha(path)))
 return p.returncode,path.read_text()
OUT.mkdir(exist_ok=True)
code,version=run(['docker','exec',CONTAINER,'yosys','-V'],OUT/'tool-version.log')
if code:raise RuntimeError('Yosys version probe failed; inspect retained log')
for name,top,source in LEAVES:
 source=ROOT/'fpga/experiments/cu66-v72'/source
 script=OUT/(name+'.ys');stat=OUT/(name+'-stat.json');netlist=OUT/(name+'-netlist.json')
 script.write_text('\n'.join([f'read_verilog -sv -I{MAP} {source}',f'hierarchy -check -top {top}','proc','opt','memory_collect','check -assert',f'tee -o {stat} stat -json',f'write_json {netlist}'])+'\n')
 code,log=run(['docker','exec',CONTAINER,'yosys','-Q','-T','-s',str(script)],OUT/(name+'.log'))
 error=next((line for line in log.splitlines()if 'ERROR:'in line),'')
 if code:
  assert 'syntax error, unexpected TOK_INT'in error,'unexpected tool failure; investigate retained transcript'
  assert not stat.exists()and not netlist.exists(),'stale derived elaboration outputs'
  rows.append(dict(name=name,top=top,status='NOT_ELABORATED',exit_code=code,error=error,statistics=None,logical_memories=None,source=str(source.relative_to(ROOT)),files={str(script.relative_to(ROOT)):sha(script)}))
 else:
  raise RuntimeError('Frontend unexpectedly accepted leaf; qualify real reports before updating status')
 print(name,'NOT_ELABORATED',error,flush=True)
assert pins=={str(p.relative_to(ROOT)):sha(p)for p in SOURCES},'sources changed during preflight'
source=ROOT/'fpga/experiments/cu66-v72/display/cu72_painter_burst.sv'
text=source.read_text();strip=text.split('STRIP_DRAIN:begin',1)[1].split('WRITE_REQ:',1)[0]
old_text=OLD.read_text();old_strip=old_text.split('STRIP_DRAIN:begin',1)[1].split('WRITE_REQ:',1)[0]
reads=len(re.findall(r'rgb_strip\[',strip));old_reads=len(re.findall(r'rgb_strip\[',old_strip))
assert reads==8 and old_reads==1
lines=[n for n,line in enumerate(text.splitlines(),1)if 'rgb_strip['in line and 'drain_x'in line]
result=dict(schema='cu72-generic-leaf-preflight-v1',status='UNAVAILABLE_FRONTEND',tool=version.strip(),source_sha256=pins,commands=commands,runs=rows,strip_source_review=dict(source=str(source.relative_to(ROOT)),read_expression_lines=lines,declared_width=16,declared_words=5760,declared_bits=92160,declared_bytes=11520,v72_read_expressions_per_strip_drain=reads,v70_read_expressions_per_strip_drain=old_reads,addresses_share_drain_x=True,row_lanes=list(range(8)),inferred_memory_ports=None,inferred_fpga_resources=None,target_inference_qualified=False,finding='Eight source read expressions gather one eight-row group in a clocked strip-drain branch. Banking/packing or equivalent inferred-memory lowering remains an explicit target-implementation gate; no inferred port or BRAM count was obtained.'),research_sources=['https://yosyshq.readthedocs.io/projects/yosys/en/latest/using_yosys/more_scripting/load_design.html','https://github.com/YosysHQ/yosys/blob/main/docs/source/using_yosys/verilog.rst'],scope='Native read_verilog -sv rejected int casts before hierarchy; no process/memory elaboration completed. Source-level strip-access review only.',limitations=['No source conversion or RTL edits were used to bypass the native parser limitation','No generic cell/storage/memory-port statistics were produced','No synth_xilinx/techmap/BRAM mapping/placement/routing, FPGA LUT/FF/BRAM/DSP usage, Fmax, fit, electrical or CDC result','No fullsystem/frame30fps/sub10ms target proof'])
(OUT/'results.json').write_text(json.dumps(result,indent=2)+'\n')
print('ELABORATION_V72_UNAVAILABLE_FRONTEND leaves=3 source_read_sites=8 inferred_ports=unavailable sources_stable=true')
raise SystemExit(2)
