#!/usr/bin/env python3
"""Compare actual admission RTL with clocked, explicitly prepared RAM cases."""
import datetime,gzip,hashlib,json,re,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv'
CAND=ROOT/'fpga/experiments/cu66-v102-memory/cs88_admission_v91i2a.sv'
AREA=ROOT/'experiments/python-gamebub-v102/memory'
CONTAINER='gamebub-cu66-v69-build'
sys.path.insert(0,str(ROOT/'scripts/cu66-v100'))
from run_rtl import resources

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,o):p.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')
def main():
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/stamp;out.mkdir(parents=True)
 build=Path('/home/lori/gamebub-build/cu66-v69')/('v102-memory-'+stamp);build.mkdir();mapped='/build/'+build.name
 rep={'schema':'v102-memory-clocked-probe-v1','status':'FAIL','baseline':'6b36a3228804953c50c10db61f620cad5412ecce','original':{'path':str(SRC.relative_to(ROOT)),'sha256':sha(SRC)},'candidate':{'path':str(CAND.relative_to(ROOT)),'sha256':sha(CAND)},'commands':[],'runs':[],'backend':'Verilator5.020 explicit historical two-state behavioral backend','limits':['Internal state and initial RAM are prepared explicitly; not a complete valid packet-admission test.','32 forced simultaneous RAM read/write cases per seed use verification-only force controls, not reachable interface transactions.','Full pipeline protocol regressions and native synthesis are separate root-owned lanes.','No mapped-netlist, physical latency, FPGA FPS, fit or routed-clock result.']}
 original_header=SRC.read_text().split(');',1)[0]+');';pp=[];inherited=None
 for item in original_header.split('(',1)[1].rsplit(');',1)[0].split(','):
  item=item.strip();m=re.fullmatch(r'(input|output)\s+logic\s+(signed\s+)?(\[\d+:\d+\]\s+)?(.+)',item,re.S)
  if m:
   direction,signed,packed,item=m.groups();inherited=(direction,signed or '',packed or '')
  assert inherited,item
  m=re.fullmatch(r'(\w+)\s*(\[\d+:\d+\])?',item);assert m,item
  pp.append({'name':m[1],'unpacked':m[2] or '', 'direction':inherited[0],'signed':inherited[1],'packed':inherited[2]})
 for path,name in [(SRC,'memory_original'),(CAND,'memory_candidate')]:
  (build/(name+'.sv')).write_text(path.read_text().replace('module cs88_admission_v91i2a (','module '+name+' (',1))
 lines=[original_header.replace('module cs88_admission_v91i2a (','module memory_probe (',1).replace(');',', input logic probe_force_collision, output logic probe_outputs_equal, probe_ram_equal);')]
 for p in pp:
  if p['direction']=='output':lines.append(f"logic {p['signed']}{p['packed']} old_{p['name']}{p['unpacked']};")
 for module,inst,old in [('memory_original','old_dut',True),('memory_candidate','new_dut',False)]:
  conns=['.'+p['name']+'('+('old_' if old and p['direction']=='output' else '')+p['name']+')' for p in pp];lines.append(module+' '+inst+'('+','.join(conns)+');')
 lines.append('assign probe_outputs_equal = '+' && '.join('(old_'+p['name']+' == '+p['name']+')' for p in pp if p['direction']=='output')+';')
 lines.append('assign probe_ram_equal = (old_dut.ram_data == new_dut.ram_data) && (old_dut.ram_addr == new_dut.ram_addr) && (old_dut.ram_epoch == new_dut.ram_epoch);')
 lines += ['// Verification-only forces: reach RAM read-first collision while normal FSM forbids it.','always @(probe_force_collision) begin','if(probe_force_collision) begin',"force old_dut.stage_write=1'b1; force new_dut.stage_write=1'b1;", "force old_dut.stage_read_req=1'b1; force new_dut.stage_read_req=1'b1;",'end else begin','release old_dut.stage_write; release new_dut.stage_write;','release old_dut.stage_read_req; release new_dut.stage_read_req;','end','end','endmodule']
 (build/'memory_probe.sv').write_text('\n'.join(lines)+'\n');write(build/'ports.json',pp)
 bench=ROOT/'fpga/experiments/cu66-v102-memory/tb_memory.cpp';shutil.copyfile(bench,build/bench.name);shutil.copyfile(Path(__file__),build/'memory.py')
 rep['source_sha256']={str(p.relative_to(ROOT)):sha(p) for p in [SRC,CAND,bench,Path(__file__)]};rep['port_names']=len(pp);rep['output_names']=sum(p['direction']=='output' for p in pp)
 def cmd(args,name,timeout):
  gate=resources();argv=['docker','exec','-e','OMP_NUM_THREADS=1','-w',mapped,CONTAINER,'timeout','--kill-after=5s',str(timeout)+'s']+args;start=time.monotonic()
  with (build/name).open('w') as log:r=subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT,timeout=timeout+15)
  rep['commands'].append({'argv':argv,'exit_code':r.returncode,'log':name,'wall_seconds':time.monotonic()-start,'resource_gate':gate});assert r.returncode==0,('command failure',name,r.returncode)
 try:
  cmd(['verilator','--version'],'tool.log',30)
  cmd(['verilator','--cc','--exe','--build','-j','2','--assert','-Wall','-Wno-DECLFILENAME','--public-flat-rw','--top-module','memory_probe','--Mdir',mapped+'/obj','-CFLAGS','-std=c++17 -O2 -Wall -Wextra -Werror',mapped+'/memory_original.sv',mapped+'/memory_candidate.sv',mapped+'/memory_probe.sv',mapped+'/tb_memory.cpp'],'compile.log',300)
  cmd(['sha256sum',mapped+'/obj/Vmemory_probe'],'binary.log',30)
  for seed in [102401,102402]:
   cmd([mapped+'/obj/Vmemory_probe',str(seed),mapped+'/seed-'+str(seed)+'.jsonl'],'seed-'+str(seed)+'.log',120)
   verdict=json.loads((build/('seed-'+str(seed)+'.log')).read_text());assert verdict['status']=='TEST_PASS' and verdict['cases']==9536 and verdict['same_address_read_first_collisions']==32
   rep['runs'].append(verdict)
  rep['status']='PASS_ACTUAL_CLOCKED_RAM_EQUIVALENCE';rep['total_cases']=sum(r['cases'] for r in rep['runs']);rep['total_clock_edges']=sum(r['clock_edges'] for r in rep['runs'])
 finally:
  artifacts={}
  for p in sorted(build.iterdir()):
   if not p.is_file():continue
   if p.suffix=='.jsonl':
    q=out/(p.name+'.gz')
    with q.open('wb') as dest:
     with gzip.GzipFile(fileobj=dest,filename='',mode='wb',mtime=0) as gz:gz.write(p.read_bytes())
    assert gzip.decompress(q.read_bytes())==p.read_bytes();artifacts[q.name]=sha(q)
   else:
    q=out/p.name;shutil.copyfile(p,q);artifacts[q.name]=sha(q)
  rep['artifacts_sha256']=artifacts;write(out/'receipt.json',rep);write(AREA/'probe-results.json',{'schema':'v102-memory-probe-selection-v1','status':rep['status'],'selected_receipt':str((out/'receipt.json').relative_to(ROOT)),'sha256':sha(out/'receipt.json')});print(rep['status'],out,flush=True)
  if rep['status']!='PASS_ACTUAL_CLOCKED_RAM_EQUIVALENCE':raise SystemExit(1)
if __name__=='__main__':main()
