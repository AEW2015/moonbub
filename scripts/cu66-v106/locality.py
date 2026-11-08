#!/usr/bin/env python3
"""Compare actual admission RTL with clocked, explicitly prepared RAM cases."""
import datetime,gzip,hashlib,json,re,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'fpga/experiments/cu66-v91j/cu66_inverse_stream_v91j.sv'
CAND=ROOT/'fpga/experiments/cu66-v106-locality/cu66_inverse_stream_v91j.sv'
AREA=ROOT/'experiments/python-gamebub-v106/locality'
CONTAINER='gamebub-cu66-v69-build'
sys.path.insert(0,str(ROOT/'scripts/cu66-v100'))
from run_rtl import resources

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,o):p.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')
def main():
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/stamp;out.mkdir(parents=True)
 build=Path('/home/lori/gamebub-build/cu66-v69')/('v106-locality-'+stamp);build.mkdir();mapped='/build/'+build.name
 rep={'schema':'v106-locality-clocked-probe-v1','status':'FAIL','baseline':'eececf35da97c9b14230d464ecde7576cb7840db','original':{'path':str(SRC.relative_to(ROOT)),'sha256':sha(SRC)},'candidate':{'path':str(CAND.relative_to(ROOT)),'sha256':sha(CAND)},'commands':[],'runs':[],'backend':'Verilator5.020 explicit historical two-state behavioral backend','limits':['Prepared internal states supplement actual historical inverse boundary/interface tests; prepared cases are not full packet reachability proof.','Two-state power-on zeros are test initialization, not FPGA power-on memory qualification. Coefficient data is not reset by the candidate.','All 128 coefficient words are checked every clock against an independent store oracle, including inactive and held contents.','No native mapping, routed improvement, board FPS or latency is established by this focused behavioral lane.']}
 original_header=SRC.read_text().split(');',1)[0]+');';pp=[];inherited=None
 for item in original_header.split('(',1)[1].rsplit(');',1)[0].split(','):
  item=item.strip();m=re.fullmatch(r'(input|output)\s+logic\s+(signed\s+)?(\[\d+:\d+\]\s+)?(.+)',item,re.S)
  if m:
   direction,signed,packed,item=m.groups();inherited=(direction,signed or '',packed or '')
  assert inherited,item
  m=re.fullmatch(r'(\w+)\s*(\[\d+:\d+\])?',item);assert m,item
  pp.append({'name':m[1],'unpacked':m[2] or '', 'direction':inherited[0],'signed':inherited[1],'packed':inherited[2]})
 for path,name in [(SRC,'locality_original'),(CAND,'locality_candidate')]:
  (build/(name+'.sv')).write_text(path.read_text().replace('module cu66_inverse_stream_v91j (','module '+name+' (',1))
 lines=[original_header.replace('module cu66_inverse_stream_v91j (','module locality_probe (',1).replace(');',', output logic probe_outputs_equal, probe_stores_equal, output logic [1023:0] probe_store0, probe_store1, output logic [5:0] probe_fill_index, output logic [31:0] probe_next_token, output logic [7:0] probe_fault);')]
 for p in pp:
  if p['direction']=='output':lines.append(f"logic {p['signed']}{p['packed']} old_{p['name']}{p['unpacked']};")
 for module,inst,old in [('locality_original','old_dut',True),('locality_candidate','new_dut',False)]:
  conns=['.'+p['name']+'('+('old_' if old and p['direction']=='output' else '')+p['name']+')' for p in pp];lines.append(module+' '+inst+'('+','.join(conns)+');')
 lines.append('assign probe_outputs_equal = '+' && '.join('(old_'+p['name']+' == '+p['name']+')' for p in pp if p['direction']=='output')+';')
 lines += ['assign probe_store0=new_dut.coefficients[0]; assign probe_store1=new_dut.coefficients[1];', 'assign probe_stores_equal=(old_dut.coefficients[0]==new_dut.coefficients[0])&&(old_dut.coefficients[1]==new_dut.coefficients[1]);','assign probe_fill_index=new_dut.fill_index; assign probe_next_token=new_dut.next_token; assign probe_fault=new_dut.input_fault;', 'endmodule']
 (build/'locality_probe.sv').write_text('\n'.join(lines)+'\n');write(build/'ports.json',pp)
 bench=ROOT/'fpga/experiments/cu66-v106-locality/tb_locality.cpp';shutil.copyfile(bench,build/bench.name);shutil.copyfile(Path(__file__),build/'locality.py')
 historical=ROOT/'fpga/experiments/cu66-v91j/tb_inverse.cpp'
 h=historical.read_text().replace('Vcu66_inverse_stream_v91j','Vlocality_probe').replace('int main(int argc,char **argv)','int historical_inverse_main(int argc,char **argv)')
 before='d.clk=1;d.eval();++cycle;'
 assert h.count(before)==1
 h=h.replace(before,'locality_pre(d);d.clk=1;d.eval();locality_post(d);++cycle;')
 (build/'historical_inverse.cpp').write_text(h)
 boundary=ROOT/'experiments/python-gamebub-v91j/vectors/boundary.tsv';shutil.copyfile(boundary,build/'boundary.tsv')
 math=[ROOT/'fpga/experiments/cu66-v69/inverse'/n for n in ['cu66_dequant.sv','cu66_idct8x8.sv','cu66_quant_rom.svh']]
 for p in math:shutil.copyfile(p,build/p.name)
 rep['source_sha256']={str(p.relative_to(ROOT)):sha(p) for p in [SRC,CAND,bench,Path(__file__),historical,boundary,*math]};rep['port_names']=len(pp);rep['output_names']=sum(p['direction']=='output' for p in pp)
 def cmd(args,name,timeout):
  gate=resources();argv=['docker','exec','-e','OMP_NUM_THREADS=1','-w',mapped,CONTAINER,'timeout','--kill-after=5s',str(timeout)+'s']+args;start=time.monotonic()
  with (build/name).open('w') as log:r=subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT,timeout=timeout+15)
  rep['commands'].append({'argv':argv,'exit_code':r.returncode,'log':name,'wall_seconds':time.monotonic()-start,'resource_gate':gate});assert r.returncode==0,('command failure',name,r.returncode)
 try:
  cmd(['verilator','--version'],'tool.log',30)
  cmd(['verilator','--cc','--exe','--build','-j','2','--assert','-Wall','-Wno-DECLFILENAME','--public-flat-rw','--top-module','locality_probe','--Mdir',mapped+'/obj','-CFLAGS','-std=c++17 -O2 -Wall -Wextra -Werror',mapped+'/locality_original.sv',mapped+'/locality_candidate.sv',mapped+'/locality_probe.sv',mapped+'/cu66_dequant.sv',mapped+'/cu66_idct8x8.sv','-I'+mapped,mapped+'/tb_locality.cpp'],'compile.log',300)
  cmd(['sha256sum',mapped+'/obj/Vlocality_probe'],'binary.log',30)
  for seed in [106401,106402]:
   cmd([mapped+'/obj/Vlocality_probe',str(seed),mapped+'/seed-'+str(seed)+'.jsonl',mapped+'/boundary.tsv'],'seed-'+str(seed)+'.log',120)
   verdict=json.loads((build/('seed-'+str(seed)+'.log')).read_text().splitlines()[-1]);assert verdict['status']=='TEST_PASS' and verdict['prepared_clocks']>9000 and verdict['word_count']==128 and verdict['late_same_edge_write_fail_cases']==2
   rep['runs'].append(verdict)
  rep['status']='PASS_ACTUAL_INVERSE_STORAGE_EQUIVALENCE';rep['total_clock_edges']=sum(r['prepared_clocks']+r['historical_clocks'] for r in rep['runs'])
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
  rep['artifacts_sha256']=artifacts;write(out/'receipt.json',rep);write(AREA/'probe-results.json',{'schema':'v106-locality-probe-selection-v1','status':rep['status'],'selected_receipt':str((out/'receipt.json').relative_to(ROOT)),'sha256':sha(out/'receipt.json')});print(rep['status'],out,flush=True)
  if rep['status']!='PASS_ACTUAL_INVERSE_STORAGE_EQUIVALENCE':raise SystemExit(1)
if __name__=='__main__':main()
