#!/usr/bin/env python3
"""Full production Rice parser comparison with historical vectors and full32 cache oracle."""
import datetime,gzip,hashlib,json,re,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'fpga/experiments/cu66-v91/br88_rice_elastic.sv'
CAND=ROOT/'fpga/experiments/cu66-v106-rice/br88_rice_elastic.sv'
BENCH=ROOT/'fpga/experiments/cu66-v106-rice/tb_rice_cache.cpp'
HIST=ROOT/'fpga/experiments/cu66-v91/tb_rice.cpp'
VECTORS=ROOT/'experiments/python-gamebub-v91/rtl-vectors/cases.jsonl.gz'
AREA=ROOT/'experiments/python-gamebub-v106/rice'
sys.path.insert(0,str(ROOT/'scripts/cu66-v100'))
from run_rtl import resources

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,o):p.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')
def main():
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/stamp;out.mkdir(parents=True)
 build=Path('/home/lori/gamebub-build/cu66-v69')/('v106-rice-'+stamp);build.mkdir();mapped='/build/'+build.name
 rep={'schema':'v106-rice-clocked-probe-v1','status':'FAIL','baseline':'eececf35da97c9b14230d464ecde7576cb7840db','original':{'path':str(SRC.relative_to(ROOT)),'sha256':sha(SRC)},'candidate':{'path':str(CAND.relative_to(ROOT)),'sha256':sha(CAND)},'commands':[],'runs':[],'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [SRC,CAND,BENCH,HIST,VECTORS,Path(__file__)]},'limits':['Two-state behavioral actual whole-module clocked comparison; no four-state, mapped-netlist or FPGA frequency proof.','Prepared full32 cache-consistent internal states are verification-only and not valid-stream reachability proof.','Independent loaded/consumed/reservoir/cache/counter oracle runs every clock. Historical trace checkpoints are sampled every256clocks and every reset/start; prepared clocks are all logged.']}
 header=SRC.read_text().split(');',1)[0]+');';ports=[];inherited=None
 for item in header.split('(',1)[1].rsplit(');',1)[0].split(','):
  item=item.strip();m=re.fullmatch(r'(input|output)\s+logic\s+(signed\s+)?(\[\d+:\d+\]\s+)?(.+)',item,re.S)
  if m:direction,signed,packed,item=m.groups();inherited=(direction,signed or '',packed or '')
  assert inherited and re.fullmatch(r'\w+',item),item
  ports.append({'name':item,'direction':inherited[0],'signed':inherited[1],'packed':inherited[2]})
 for path,name in [(SRC,'rice_original'),(CAND,'rice_candidate')]:
  (build/(name+'.sv')).write_text(path.read_text().replace('module br88_rice_elastic (','module '+name+' (',1))
 extra=', output logic probe_outputs_equal, probe_internal_equal, probe_word_bad, output logic [31:0] probe_size, probe_loaded, probe_consumed, probe_cache_remaining, probe_cache_load, output logic [63:0] probe_reservoir, output logic [1:0] probe_state, output logic [3:0] probe_failed, output logic [4:0] probe_suffix_left);'
 lines=[header.replace('module br88_rice_elastic (','module rice_probe (',1).replace(');',extra)]
 for p in ports:
  if p['direction']=='output':lines.append(f"logic {p['signed']}{p['packed']}old_{p['name']};")
 for mod,inst,old in [('rice_original','old_dut',True),('rice_candidate','new_dut',False)]:
  lines.append(mod+' '+inst+'('+','.join('.'+p['name']+'('+('old_' if old and p['direction']=='output' else '')+p['name']+')' for p in ports)+');')
 lines.append('assign probe_outputs_equal = '+' && '.join('(old_'+p['name']+'=='+p['name']+')' for p in ports if p['direction']=='output')+';')
 internals=['state','active','use16','serial','failed','size_bits','loaded','consumed','reservoir','available','k','escape_width','quotient','suffix_left','suffix_acc','remaining','load_remaining','word_bad']
 lines.append('assign probe_internal_equal = '+' && '.join('(old_dut.'+n+'==new_dut.'+n+')' for n in internals)+';')
 for outname,n in [('word_bad','word_bad'),('size','size_bits'),('loaded','loaded'),('consumed','consumed'),('cache_remaining','cached_remaining'),('cache_load','cached_load_remaining'),('reservoir','reservoir'),('state','state'),('failed','failed'),('suffix_left','suffix_left')]:lines.append('assign probe_'+outname+'=new_dut.'+n+';')
 lines.append('endmodule');(build/'rice_probe.sv').write_text('\n'.join(lines)+'\n');save(build/'ports.json',ports)
 h=HIST.read_text().replace('Vbr88_rice_elastic','Vrice_probe').replace('int main(int argc,char** argv)','int historical_rice_main(int argc,char** argv)')
 anchor='d.clk=1; d.eval(); d.clk=0; d.eval();';assert h.count(anchor)==1
 h=h.replace(anchor,'rice_pre(d); d.clk=1; d.eval(); rice_post(d); d.clk=0; d.eval();');(build/'historical_rice.cpp').write_text(h)
 shutil.copyfile(BENCH,build/BENCH.name);shutil.copyfile(Path(__file__),build/'rice.py');shutil.copyfile(VECTORS,build/'cases.jsonl.gz')
 cases=requests=0
 with gzip.open(VECTORS,'rt') as src,(build/'vectors.txt').open('w') as dst:
  for line in src:
   c=json.loads(line);dst.write(f"{c['id']} {c['bit_size']} {c['data_hex'] or '-'} {len(c['requests'])}\n")
   for req in c['requests']:dst.write(' '.join(map(str,req))+'\n')
   cases+=1;requests+=len(c['requests'])
 rep.update(port_names=len(ports),output_names=sum(p['direction']=='output' for p in ports),historical_vector_cases=cases,historical_requests_per_configuration=requests,text_vectors_sha256=sha(build/'vectors.txt'))
 def command(args,name,timeout):
  gate=resources();argv=['docker','exec','-e','OMP_NUM_THREADS=1','-w',mapped,'gamebub-cu66-v69-build','timeout','--kill-after=5s',str(timeout)+'s']+args;start=time.monotonic()
  with (build/name).open('w') as log:r=subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT,timeout=timeout+15)
  rep['commands'].append({'argv':argv,'exit_code':r.returncode,'log':name,'wall_seconds':time.monotonic()-start,'resource_gate':gate});assert r.returncode==0,(name,r.returncode)
 try:
  command(['verilator','--version'],'tool.log',30)
  command(['verilator','--cc','--exe','--build','-j','2','--assert','-Wall','-Wno-DECLFILENAME','--public-flat-rw','--top-module','rice_probe','--Mdir',mapped+'/obj','-CFLAGS','-std=c++17 -O2 -Wall -Wextra -Werror',mapped+'/rice_original.sv',mapped+'/rice_candidate.sv',mapped+'/rice_probe.sv',mapped+'/tb_rice_cache.cpp'],'compile.log',300)
  command(['sha256sum',mapped+'/obj/Vrice_probe'],'binary.log',30)
  for seed in [106401,106402]:
   command([mapped+'/obj/Vrice_probe',str(seed),mapped+'/seed-'+str(seed)+'.jsonl',mapped+'/vectors.txt'],'seed-'+str(seed)+'.log',120)
   rows=[json.loads(x) for x in (build/('seed-'+str(seed)+'.log')).read_text().splitlines()];v=rows[-1];historical=next(x for x in rows if x.get('type')=='verdict');assert v['status']=='TEST_PASS' and v['prepared_clocks']>65000 and historical['cases']==cases and historical['requests_per_configuration']==requests and historical['configurations']==8 and historical['directed_checks']>90
   v['historical_verdict']=historical;rep['runs'].append(v)
  rep['status']='PASS_ACTUAL_RICE_CACHE_EQUIVALENCE';rep['total_clock_edges']=sum(v['prepared_clocks']+v['historical_clocks'] for v in rep['runs'])
 finally:
  artifacts={}
  for p in sorted(build.iterdir()):
   if not p.is_file():continue
   if p.suffix=='.jsonl':
    q=out/(p.name+'.gz')
    with p.open('rb') as src,q.open('wb') as dst:
     with gzip.GzipFile(filename='',mode='wb',fileobj=dst,mtime=0) as gz:shutil.copyfileobj(src,gz)
   else:q=out/p.name;shutil.copyfile(p,q)
   artifacts[q.name]=sha(q)
  rep['artifacts_sha256']=artifacts;save(out/'receipt.json',rep);save(AREA/'probe-results.json',{'schema':'v106-rice-probe-selection-v1','status':rep['status'],'selected_receipt':str((out/'receipt.json').relative_to(ROOT)),'sha256':sha(out/'receipt.json')});print(rep['status'],out,flush=True)
  if rep['status']!='PASS_ACTUAL_RICE_CACHE_EQUIVALENCE':raise SystemExit(1)
if __name__=='__main__':main()
