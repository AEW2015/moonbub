#!/usr/bin/env python3
"""V77 direct cache/render frontend, exact converted replay and bounded XC7 map."""
import hashlib,json,os,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];AREA=ROOT/'fpga/experiments/cu66-v77';OUT=AREA/'elaboration-bounded';TOP='cu77_render_bounded_sim';NATIVE=ROOT/'experiments/cu66-native-v69'
CONTAINER='gamebub-cu66-v69-build';FRONT=os.environ.get('SV2V_PATH','/build/v72-tools/sv2v');FRONT_SHA='b80a8ac6212aa72a196d9d6129cda35f16dbfa799ec61848c46321f845b6b635'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 sources=[AREA/'cache/cu77_direct_cache_bounded.sv',AREA/'render/cu77_yuv_rgb.sv',AREA/'render/cu77_render_bounded_sim.sv'];files=sources+[AREA/'render/tb_render.cpp',AREA/'render/bounded/results.json',Path(__file__).resolve(),*NATIVE.glob('*.hpp'),NATIVE/'index.tsv',*sorted((NATIVE/'fixtures').glob('*.cu66'))]
 pins={str(p.relative_to(ROOT)):sha(p)for p in files};commands=[];OUT.mkdir(exist_ok=True)
 def run(argv,name,timeout=600):
  path=OUT/name
  try:
   with path.open('w')as f:r=subprocess.run(argv,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
  except subprocess.TimeoutExpired:
   if 'yosys'in argv:
    pattern='^yosys -Q -T -s '+re.escape(argv[argv.index('-s')+1])+'$';subprocess.run(['docker','exec',CONTAINER,'pkill','-f',pattern],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False)
   commands.append(dict(argv=argv,log=str(path.relative_to(ROOT)),exit_code=None,status='TIMEOUT',sha256=sha(path)));raise TimeoutError(name)
  commands.append(dict(argv=argv,log=str(path.relative_to(ROOT)),exit_code=r.returncode,sha256=sha(path)));assert r.returncode==0,(name,r.returncode);return path.read_text()
 ver=run(['docker','exec',CONTAINER,FRONT,'--version'],'sv2v-version.log').strip();digest=run(['docker','exec',CONTAINER,'sha256sum',FRONT],'sv2v-sha256.log').split()[0];assert ver=='sv2v v0.0.13'and digest==FRONT_SHA
 yver=run(['docker','exec',CONTAINER,'yosys','-V'],'yosys-version.log').strip();converted=OUT/(TOP+'.v')
 run(['docker','exec',CONTAINER,FRONT,'--top='+TOP,'--write='+str(converted),*map(str,sources)],'sv2v.log')
 stat=OUT/'stat.json';net=OUT/'netlist.json';ys=OUT/'generic.ys';ys.write_text('\n'.join([f'read_verilog {converted}',f'hierarchy -check -top {TOP}','proc','opt','memory_dff','memory_share','opt','memory_collect','check -assert',f'tee -o {stat} stat -json',f'write_json {net}'])+'\n')
 log=run(['docker','exec',CONTAINER,'yosys','-Q','-T','-s',str(ys)],'yosys.log');assert 'Found and reported 0 problems.'in log
 modules=json.loads(net.read_text())['modules'];mem=[]
 for module,m in modules.items():
  for name,c in m['cells'].items():
   if c['type']=='$mem_v2':
    p=c['parameters'];n=lambda k:int(p[k],2);mem.append(dict(module=module,name=name,width=n('WIDTH'),size=n('SIZE'),read_ports=n('RD_PORTS'),write_ports=n('WR_PORTS'),read_clock_enable=n('RD_CLK_ENABLE'),logical_bits=n('WIDTH')*n('SIZE')))
 data=[m for m in mem if m['name']in['ymemory','hmemory',*['cbmem'+str(i)for i in range(4)],*['crmem'+str(i)for i in range(4)]]]
 assert len(data)==10 and sum(m['logical_bits']for m in data)==29184*8
 assert all(m['width']==16 and m['read_ports']==1 and m['write_ports']==1 and m['read_clock_enable']==1 for m in data),data
 run(['docker','exec',CONTAINER,'verilator','--cc','--exe','--build','-j','1','--Wall','-Wno-WIDTHEXPAND','-Wno-WIDTHTRUNC','-Wno-EOFNEWLINE','-Wno-DECLFILENAME','--top-module',TOP,'--prefix','Vcu77_render_sim','--Mdir','/build/v77-render-bounded-converted','-CFLAGS','-O2 -std=c++17',str(converted),str(AREA/'render/tb_render.cpp')],'converted-build.log')
 native=json.loads((AREA/'render/bounded/results.json').read_text());runs=[]
 for seed in(0,7701,7702):
  log=run(['docker','exec',CONTAINER,'/build/v77-render-bounded-converted/Vcu77_render_sim',str(NATIVE/'index.tsv'),str(seed)],f'converted-run-{seed}.log')
  assert f'RENDER_PASS actual_frames=8 patterns=4 recovery=1 full_frames=13 RGB_words=4492800 fault_probes={2 if seed else 0} seed={seed}'in log and 'FAIL'not in log
  cases=[{k:int(v)for k,v in re.findall(r'(\w+)=(\d+)',l)}for l in log.splitlines()if l.startswith('RENDER_CASE_PASS')];nr=next(x for x in native['runs']if x['seed']==seed);assert cases==nr['per_case'],'converted case counts/cycles differ';runs.append(dict(seed=seed,per_case=cases))
 fs=OUT/'family-xc7-stat.json';fn=OUT/'family-xc7-netlist.json';fy=OUT/'family-xc7.ys';fy.write_text('\n'.join([f'read_verilog {converted}',f'synth_xilinx -family xc7 -top {TOP} -noiopad -noclkbuf','check -assert',f'tee -o {fs} stat -json',f'write_json {fn}'])+'\n')
 try:
  log=run(['docker','exec',CONTAINER,'yosys','-Q','-T','-s',str(fy)],'family-xc7.log',120);assert 'Found and reported 0 problems.'in log;family=dict(status='PASS_UNPLACED_FAMILY_MAPPING',statistics=json.loads(fs.read_text()),files={str(p.relative_to(ROOT)):sha(p)for p in(fy,fs,fn)})
 except TimeoutError:family=dict(status='BOUNDED_TIMEOUT',timeout_seconds=120,scope='partial log only, no primitive/fit claim')
 assert pins=={str(p.relative_to(ROOT)):sha(p)for p in files},'qualified sources changed'
 result=dict(schema='cu77-bounded-cache-render-elaboration-v1',status='PASS_GENERIC_AND_CONVERTED_SIMULATION',source_sha256=pins,commands=commands,frontend=dict(path=FRONT,version=ver,sha256=digest),yosys=yver,converted_only_lint_exceptions=['WIDTHEXPAND','WIDTHTRUNC','EOFNEWLINE','DECLFILENAME (sv2v concatenated modules only)'],statistics=json.loads(stat.read_text()),memories=mem,data_memories=data,logical_data_bytes=29184,converted_simulation=runs,converted_native_case_counters_identical=True,derived_files_sha256={str(p.relative_to(ROOT)):sha(p)for p in(converted,ys,stat,net)},family_map=family,limitations=['Unplacedgenericfamilymapping, not exact-device fit/route/Fmax/CDC proof','ConvertedRTLsimulation is not mapped-netlist/timing simulation','No fullreceiver/front/referencelease/pixelclock/liveESP32 or physical30fps/sub10ms proof'])
 (OUT/'results.json').write_text(json.dumps(result,indent=2)+'\n');print('V77_BOUNDED_ELABORATION_PASS data_memories=10 bytes=29184 converted_frames=39 family='+family['status'])
if __name__=='__main__':main()
