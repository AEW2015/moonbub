#!/usr/bin/env python3
"""Pinned sv2v frontend plus generic Yosys memory/structure inspection."""
import hashlib,json,os,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'fpga/experiments/cu66-v73/memory/elaboration'
CONTAINER=os.environ.get('TASK_CONTAINER','gamebub-cu66-v69-build')
FRONT=os.environ.get('SV2V_PATH','/build/v72-tools/sv2v')
FRONT_SHA='b80a8ac6212aa72a196d9d6129cda35f16dbfa799ec61848c46321f845b6b635'
NATIVE=ROOT/'experiments/cu66-native-v69'
SOURCES=[ROOT/'fpga/experiments/cu66-v72/display/cu72_painter_burst.sv',ROOT/'fpga/experiments/cu66-v73/display/cu73_painter_burst.sv',ROOT/'fpga/experiments/cu66-v73/display/tb_painter_burst.cpp',Path(__file__).resolve(),NATIVE/'index.tsv',*NATIVE.glob('*.hpp'),*sorted((NATIVE/'fixtures').glob('*.cu66')),ROOT/'fpga/experiments/cu66-v72/display/results.json',ROOT/'fpga/experiments/cu66-v73/display/results.json']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 OUT.mkdir(parents=True,exist_ok=True);pins={str(p.relative_to(ROOT)):sha(p)for p in SOURCES};commands=[]
 def run(argv,name,timeout=120,expected=0):
  path=OUT/name
  try:
   with path.open('w')as f:r=subprocess.run(argv,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
  except subprocess.TimeoutExpired:
   # Killing the docker client alone does not stop a container process.
   if 'yosys'in argv and '-s'in argv:
    pattern='^yosys -Q -T -s '+re.escape(argv[argv.index('-s')+1])+'$'
    subprocess.run(['docker','exec',CONTAINER,'pkill','-f',pattern],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False)
   raise RuntimeError(f'{name}: timeout; retained log and stopped matching Yosys job')
  commands.append(dict(argv=argv,log=str(path.relative_to(ROOT)),exit_code=r.returncode,sha256=sha(path)))
  if r.returncode!=expected:raise RuntimeError(f'{name} exit{r.returncode}; retained log')
  return path.read_text()
 version=run(['docker','exec',CONTAINER,FRONT,'--version'],'sv2v-version.log').strip()
 digest=run(['docker','exec',CONTAINER,'sha256sum',FRONT],'sv2v-sha256.log').split()[0]
 assert version=='sv2v v0.0.13' and digest==FRONT_SHA
 yosys=run(['docker','exec',CONTAINER,'yosys','-V'],'yosys-version.log').strip()
 rows=[]
 for variant,source in zip(('v72','v73'),SOURCES[:2]):
  top='cu'+variant[1:]+'_painter_burst';converted=OUT/variant/(top+'.v');converted.parent.mkdir(exist_ok=True)
  run(['docker','exec',CONTAINER,FRONT,'--top='+top,'--write='+str(converted),str(source)],variant+'-sv2v.log')
  assert converted.is_file() and converted.stat().st_size>0
  stat=OUT/(variant+'-stat.json');net=OUT/(variant+'-netlist.json');ys=OUT/(variant+'.ys')
  ys.write_text('\n'.join([f'read_verilog {converted}',f'hierarchy -check -top {top}','proc','opt','memory_dff','memory_share','opt','memory_collect','check -assert',f'tee -o {stat} stat -json',f'write_json {net}'])+'\n')
  log=run(['docker','exec',CONTAINER,'yosys','-Q','-T','-s',str(ys)],variant+'-yosys.log')
  assert 'Found and reported 0 problems.'in log
  module=json.loads(net.read_text())['modules'][top]
  memories=[]
  for name,cell in module['cells'].items():
   if cell['type']in('$mem','$mem_v2'):
    param=cell['parameters'];number=lambda n:int(param[n],2)
    memories.append(dict(name=name,width=number('WIDTH'),size=number('SIZE'),read_ports=number('RD_PORTS'),write_ports=number('WR_PORTS'),read_clock_enable=number('RD_CLK_ENABLE'),logical_bits=number('WIDTH')*number('SIZE')))
  rows.append(dict(variant=variant,top=top,status='PASS_GENERIC_STRUCTURE',statistics=json.loads(stat.read_text())['modules']['\\'+top],memories=memories,files={str(p.relative_to(ROOT)):sha(p)for p in(converted,ys,stat,net)}))
 # Validate the translated current design through the same native oracle bench.
 top='cu73_painter_burst';converted=OUT/'v73'/(top+'.v')
 run(['docker','exec',CONTAINER,'verilator','--cc','--exe','--build','-j','1','--Wall','-Wno-WIDTHEXPAND','-Wno-WIDTHTRUNC','-Wno-EOFNEWLINE','--top-module',top,'--Mdir','/build/v73-painter-converted','-CFLAGS','-O2 -std=c++17',str(converted),str(SOURCES[2])],'converted-build.log',600)
 converted_runs=[]
 for seed in (0,7201,7202):
  log=run(['docker','exec',CONTAINER,'/build/v73-painter-converted/V'+top,str(NATIVE/'index.tsv'),str(seed)],f'converted-run-{seed}.log',600)
  assert f'PASS actual_frames=8 patterns=4 recovery=1 fault_probes={5 if seed else 0} seed={seed}'in log and 'FAIL'not in log
  assert log.count('START_REJECT_PASS ')==10
  cases=[{k:int(v)for k,v in re.findall(r'(\w+)=(\d+)',line)}for line in log.splitlines()if line.startswith('CASE_PASS')]
  good=[c for c in cases if c['mode']==0]
  assert len(good)==13 and all(c['write_words']==384000 and c['write_commands']==48000 and c['read_words']==280320 for c in good)
  converted_runs.append(dict(seed=seed,full_rasters=13,fault_probes=5 if seed else 0,start_rejects=10,per_case=cases))
 native=json.loads((ROOT/'fpga/experiments/cu66-v73/display/results.json').read_text())
 old_native=json.loads((ROOT/'fpga/experiments/cu66-v72/display/results.json').read_text())
 assert native['status']==old_native['status']=='PASS' and native['runs']==old_native['runs'],'banking changed native case counters/timing'
 for row in converted_runs:
  same=next(x for x in native['runs']if x['seed']==row['seed'])
  assert same['per_case']==row['per_case'],'lowering changed exact case counters/timing'
 family=[]
 for variant in ('v72','v73'):
  top='cu'+variant[1:]+'_painter_burst';converted=OUT/variant/(top+'.v');ys=OUT/(variant+'-family-xc7.ys');stat=OUT/(variant+'-family-xc7-stat.json');net=OUT/(variant+'-family-xc7-netlist.json')
  ys.write_text('\n'.join([f'read_verilog {converted}',f'synth_xilinx -family xc7 -top {top} -noiopad -noclkbuf','check -assert',f'tee -o {stat} stat -json',f'write_json {net}'])+'\n')
  log=run(['docker','exec',CONTAINER,'yosys','-Q','-T','-s',str(ys)],variant+'-family-xc7.log',120)
  assert 'Found and reported 0 problems.'in log
  module=json.loads(net.read_text())['modules'][top]
  strip_cells={name:cell['type']for name,cell in module['cells'].items()if cell['type']in('RAMB18E1','RAMB36E1')and(name.startswith('rgb_strip.')or re.match(r'strip[0-7]\.',name))}
  counts={kind:sum(t==kind for t in strip_cells.values())for kind in('RAMB18E1','RAMB36E1')}
  family.append(dict(variant=variant,status='PASS_UNPLACED_FAMILY_MAPPING',statistics=json.loads(stat.read_text())['modules']['\\'+top],strip_cells=strip_cells,strip_primitives=counts,strip_18k_equivalents=counts['RAMB18E1']+2*counts['RAMB36E1'],files={str(p.relative_to(ROOT)):sha(p)for p in(ys,stat,net)}))
 assert family[0]['strip_primitives']==dict(RAMB18E1=0,RAMB36E1=24)
 assert family[1]['strip_primitives']==dict(RAMB18E1=8,RAMB36E1=0)
 assert pins=={str(p.relative_to(ROOT)):sha(p)for p in SOURCES},'qualified sources changed'
 result=dict(schema='cu73-frontend-memory-inspection-v1',status='PASS_GENERIC_AND_CONVERTED_SIMULATION',source_sha256=pins,commands=commands,frontend=dict(path=FRONT,version=version,sha256=digest,official_release='https://github.com/zachjs/sv2v/releases/tag/v0.0.13',archive_sha256='552799a1d76cd177b9b4cc63a3e77823a3d2a6eb4ec006569288abeff28e1ff8'),yosys=yosys,converted_only_lint_exceptions=['WIDTHEXPAND','WIDTHTRUNC','EOFNEWLINE'],lint_exception_reason='sv2v emits sized cast helper function arguments and no terminal newline; native SV build retains full Wall',runs=rows,converted_simulation=converted_runs,native_v72_v73_case_counters_identical=True,converted_native_case_counters_identical=True,family_maps=family,strip_18k_equivalent_reduction_percent=100*(family[0]['strip_18k_equivalents']-family[1]['strip_18k_equivalents'])/family[0]['strip_18k_equivalents'],scope='sv2v-generated Verilog generic Yosys memories/structure plus exact translated current painter simulation; native SV separately authoritative',limitations=['no exact-device place/route/Fmax/CDC or electrical signoff','generic memory ports are before mapping; family primitive counts are unplaced and exclude board I/O/clock constraints','finite converted simulation does not constitute formal equivalence or target30fps/sub10ms proof'])
 (OUT/'results.json').write_text(json.dumps(result,indent=2)+'\n')
 print('V73_FRONTEND_GENERIC_PASS variants=2 converted_rasters=39 converted_faults=10 converted_start_rejects=30')
if __name__=='__main__':main()
