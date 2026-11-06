#!/usr/bin/env python3
"""Pinned sv2v conversion, exact converted simulation, bounded generic XC7 map."""
import hashlib,json,os,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'fpga/experiments/cu66-v75/memory/elaboration'
CONTAINER=os.environ.get('TASK_CONTAINER','gamebub-cu66-v69-build')
FRONT=os.environ.get('SV2V_PATH','/build/v72-tools/sv2v')
FRONT_SHA='b80a8ac6212aa72a196d9d6129cda35f16dbfa799ec61848c46321f845b6b635'
NATIVE=ROOT/'experiments/cu66-native-v69'
AREA=ROOT/'fpga/experiments/cu66-v75/display'
TOP='cu75_painter_burst'
SOURCES=[AREA/(TOP+'.sv'),AREA/'tb_painter_burst.cpp',AREA/'results.json',Path(__file__).resolve(),NATIVE/'index.tsv',*NATIVE.glob('*.hpp'),*sorted((NATIVE/'fixtures').glob('*.cu66')),ROOT/'fpga/experiments/cu66-v74/memory/elaboration/results.json']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 OUT.mkdir(parents=True,exist_ok=True);pins={str(p.relative_to(ROOT)):sha(p)for p in SOURCES};commands=[]
 def run(argv,name,timeout=120):
  path=OUT/name
  try:
   with path.open('w')as f:r=subprocess.run(argv,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
  except subprocess.TimeoutExpired:
   if 'yosys'in argv and '-s'in argv:
    pattern='^yosys -Q -T -s '+re.escape(argv[argv.index('-s')+1])+'$'
    subprocess.run(['docker','exec',CONTAINER,'pkill','-f',pattern],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False)
   commands.append(dict(argv=argv,log=str(path.relative_to(ROOT)),exit_code=None,status='TIMEOUT',sha256=sha(path)))
   raise TimeoutError(name)
  commands.append(dict(argv=argv,log=str(path.relative_to(ROOT)),exit_code=r.returncode,sha256=sha(path)))
  if r.returncode:raise RuntimeError(f'{name} exit{r.returncode}; retained log')
  return path.read_text()
 version=run(['docker','exec',CONTAINER,FRONT,'--version'],'sv2v-version.log').strip()
 digest=run(['docker','exec',CONTAINER,'sha256sum',FRONT],'sv2v-sha256.log').split()[0]
 assert version=='sv2v v0.0.13' and digest==FRONT_SHA
 yosys=run(['docker','exec',CONTAINER,'yosys','-V'],'yosys-version.log').strip()
 converted=OUT/(TOP+'.v')
 run(['docker','exec',CONTAINER,FRONT,'--top='+TOP,'--write='+str(converted),str(SOURCES[0])],'sv2v.log')
 stat=OUT/'stat.json';net=OUT/'netlist.json';ys=OUT/'generic.ys'
 ys.write_text('\n'.join([f'read_verilog {converted}',f'hierarchy -check -top {TOP}','proc','opt','memory_dff','memory_share','opt','memory_collect','check -assert',f'tee -o {stat} stat -json',f'write_json {net}'])+'\n')
 log=run(['docker','exec',CONTAINER,'yosys','-Q','-T','-s',str(ys)],'yosys.log')
 assert 'Found and reported 0 problems.'in log
 module=json.loads(net.read_text())['modules'][TOP];memories=[]
 for name,cell in module['cells'].items():
  if cell['type']in('$mem','$mem_v2'):
   param=cell['parameters'];number=lambda n:int(param[n],2)
   memories.append(dict(name=name,width=number('WIDTH'),size=number('SIZE'),read_ports=number('RD_PORTS'),write_ports=number('WR_PORTS'),read_clock_enable=number('RD_CLK_ENABLE'),logical_bits=number('WIDTH')*number('SIZE')))
 data_memories=[m for m in memories if m['name']!='quad_tag']
 assert len(data_memories)==33 and sum(m['logical_bits']for m in data_memories)==184448
 input_memories=[m for m in data_memories if m['name'].startswith(('yw','cb','cr'))]
 assert len(input_memories)==24 and all(m['width']==16 and m['read_ports']==1 and m['read_clock_enable']==1 and m['write_ports']==1 for m in input_memories),'input cache must have one clocked full-word read and one write port'
 waiver=OUT/'converted-only.vlt'
 waiver.write_text('`verilator_config\nlint_off -rule UNUSEDSIGNAL -file "*cu75_painter_burst.v" -match "*aux_rsp_data*"\n')
 run(['docker','exec',CONTAINER,'verilator','--cc','--exe','--build','-j','1','--Wall',str(waiver),'-Wno-WIDTHEXPAND','-Wno-WIDTHTRUNC','-Wno-EOFNEWLINE','--top-module',TOP,'--Mdir','/build/v75-painter-converted','-CFLAGS','-O2 -std=c++17',str(converted),str(SOURCES[1])],'converted-build.log',600)
 converted_runs=[]
 for seed in (0,7201,7202):
  log=run(['docker','exec',CONTAINER,'/build/v75-painter-converted/V'+TOP,str(NATIVE/'index.tsv'),str(seed)],f'converted-run-{seed}.log',600)
  assert f'PASS actual_frames=8 patterns=4 recovery=1 fault_probes={10 if seed else 0} seed={seed}'in log and 'FAIL'not in log
  assert log.count('START_REJECT_PASS ')==10
  cases=[{k:int(v)for k,v in re.findall(r'(\w+)=(\d+)',line)}for line in log.splitlines()if line.startswith('CASE_PASS')]
  good=[c for c in cases if c['mode']==0]
  assert len(good)==13 and all(c['write_words']==384000 and c['write_commands']==48000 and c['read_words']==280320 and c['read_commands']==35040 for c in good)
  converted_runs.append(dict(seed=seed,per_case=cases))
 native=json.loads((AREA/'results.json').read_text())
 for row in converted_runs:
  same=next(x for x in native['runs']if x['seed']==row['seed'])
  assert same['per_case']==row['per_case'],'lowering changed exact case counters/timing'
 ys=OUT/'family-xc7.ys';stat=OUT/'family-xc7-stat.json';net=OUT/'family-xc7-netlist.json'
 ys.write_text('\n'.join([f'read_verilog {converted}',f'synth_xilinx -family xc7 -top {TOP} -noiopad -noclkbuf','check -assert',f'tee -o {stat} stat -json',f'write_json {net}'])+'\n')
 try:
  log=run(['docker','exec',CONTAINER,'yosys','-Q','-T','-s',str(ys)],'family-xc7.log',120)
  assert 'Found and reported 0 problems.'in log
  family=dict(status='PASS_UNPLACED_FAMILY_MAPPING',statistics=json.loads(stat.read_text())['modules']['\\'+TOP],files={str(p.relative_to(ROOT)):sha(p)for p in(ys,stat,net)})
 except TimeoutError:
  family=dict(status='BOUNDED_TIMEOUT',timeout_seconds=120,scope='partial mapping log retained; no primitive or fit claim')
 assert pins=={str(p.relative_to(ROOT)):sha(p)for p in SOURCES},'qualified sources changed'
 result=dict(schema='cu75-frontend-memory-inspection-v1',status='PASS_GENERIC_AND_CONVERTED_SIMULATION',source_sha256=pins,commands=commands,frontend=dict(path=FRONT,version=version,sha256=digest,official_release='https://github.com/zachjs/sv2v/releases/tag/v0.0.13',archive_sha256='552799a1d76cd177b9b4cc63a3e77823a3d2a6eb4ec006569288abeff28e1ff8'),yosys=yosys,converted_only_lint_exceptions=['WIDTHEXPAND','WIDTHTRUNC','EOFNEWLINE','UNUSEDSIGNAL only aux_rsp_data in generated file'],lint_exception_reason='sv2v cast helpers and terminal newline; precise converted-only.vlt restores the narrow unused scalar compatibility-port annotation stripped by sv2v; native SV retains full Wall',statistics=json.loads((OUT/'stat.json').read_text())['modules']['\\'+TOP],memories=memories,logical_memory_bytes=23056,input_cache_contract=dict(banks=24,word_bits=16,read_ports_per_bank=1,clocked_reads=True,write_ports_per_bank=1),derived_files_sha256={str(p.relative_to(ROOT)):sha(p)for p in(OUT/'cu75_painter_burst.v',OUT/'generic.ys',OUT/'stat.json',OUT/'netlist.json',OUT/'converted-only.vlt')},converted_simulation=converted_runs,converted_native_case_counters_identical=True,family_map=family,limitations=['not exact-device fit/placement/routing/Fmax/CDC proof','behavioral converted simulation is not mapped-netlist simulation','functional cycle counts are not physical30fps or sub10ms proof'])
 (OUT/'results.json').write_text(json.dumps(result,indent=2)+'\n')
 print('V75_FRONTEND_GENERIC_PASS data_memories=33 bytes=23056 converted_rasters=39 converted_faults=20 converted_start_rejects=30 family='+family['status'])
if __name__=='__main__':main()
