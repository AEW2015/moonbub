#!/usr/bin/env python3
"""Replay storage traces and prove focused adapters preserve full production bodies."""
import gzip,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
AREA=ROOT/'experiments/python-gamebub-v106/locality'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 selection=json.loads((AREA/'probe-results.json').read_text());rp=ROOT/selection['selected_receipt'];r=json.loads(rp.read_text());assert sha(rp)==selection['sha256'];assert r['status']=='PASS_ACTUAL_INVERSE_STORAGE_EQUIVALENCE'
 report={'schema':'v106-storage-independent-replay-v1','status':'FAIL','receipt':str(rp.relative_to(ROOT)),'receipt_sha256':sha(rp),'auditor':{'path':str(Path(__file__).resolve().relative_to(ROOT)),'sha256':sha(Path(__file__))},'checks':[],'runs':[]}
 for k,module in [('original','locality_original'),('candidate','locality_candidate')]:
  p=ROOT/r[k]['path'];assert sha(p)==r[k]['sha256'];assert (rp.parent/(module+'.sv')).read_text().replace('module '+module+' (','module cu66_inverse_stream_v91j (',1)==p.read_text();report['checks'].append({'name':k+' whole production adapter body','sha256':sha(p),'status':'PASS'})
 proofp=ROOT/'fpga/experiments/cu66-v106-locality/edit-proof.json';proof=json.loads(proofp.read_text());before=(ROOT/proof['original_path']).read_text();s=before
 for e in proof['edits']:assert s.count(e['before'])==e['expected_occurrences']==1;s=s.replace(e['before'],e['after'],1)
 after=(ROOT/proof['candidate_path']).read_text();assert s==after and len(proof['edits'])==2
 assert before.split(');',1)[0]==after.split(');',1)[0]
 assert before.split('function automatic logic [10:0] quant_cell',1)[1].split('endfunction',1)[0]==after.split('function automatic logic [10:0] quant_cell',1)[1].split('endfunction',1)[0]
 report['checks'].append({'name':'two-edit exact recipe, byte-exact module header and quant_cell','path':str(proofp.relative_to(ROOT)),'sha256':sha(proofp),'status':'PASS'})
 historical=ROOT/'fpga/experiments/cu66-v91j/tb_inverse.cpp';h=historical.read_text().replace('Vcu66_inverse_stream_v91j','Vlocality_probe').replace('int main(int argc,char **argv)','int historical_inverse_main(int argc,char **argv)');h=h.replace('d.clk=1;d.eval();++cycle;','locality_pre(d);d.clk=1;d.eval();locality_post(d);++cycle;');assert (rp.parent/'historical_inverse.cpp').read_text()==h
 report['checks'].append({'name':'historical real-interface bench only class/main rename and pre/post hooks','path':str(historical.relative_to(ROOT)),'sha256':sha(historical),'status':'PASS'})
 for run in r['runs']:
  p=rp.parent/f"seed-{run['seed']}.jsonl.gz";assert sha(p)==r['artifacts_sha256'][p.name];store=[[0]*64 for _ in range(2)];counts={};writes={};guards=0;addresses=set();records=0;phase='prepared'
  with gzip.open(p,'rt') as f:
   for line in f:
    e=json.loads(line)
    if 'model_start' in e:assert e['model_start']=='historical-real-interface';store=[[0]*64 for _ in range(2)];phase='historical';continue
    assert e['equal'] and e['phase']==phase and e['clock']==counts.get(phase,0);assert 0<=e['bank']<2 and 0<=e['fill_index']<64 and 0<=e['value']<65536
    write=bool(e['in_valid'] and e['in_ready'] and e['fault']==0);assert write==bool(e['write']);assert not(e['guards'] and write)
    if write:store[e['bank']][e['fill_index']]=e['value'];writes[phase]=writes.get(phase,0)+1;addresses.add((e['bank'],e['fill_index']))
    value=1469598103934665603
    for bank in store:
     for word in bank:value=((value^word)*1099511628211)&0xffffffffffffffff
    assert value==e['store_digest'];counts[phase]=counts.get(phase,0)+1;records+=1
    if phase=='prepared':guards+=bool(e['guards'])
  assert counts['prepared']==run['prepared_clocks'] and counts['historical']==run['historical_clocks'];assert writes['prepared']==run['prepared_writes'] and writes['historical']==run['historical_writes'];assert guards==run['guarded_clocks'] and len(addresses)==128
  logs=[json.loads(line) for line in (rp.parent/f"seed-{run['seed']}.log").read_text().splitlines()];historical_verdict=next(x for x in logs if x.get('type')=='verdict');assert historical_verdict['boundary_cases']==48 and historical_verdict['directed_checks']==15 and historical_verdict['status']=='TEST_PASS';assert logs[-1]==run
  report['runs'].append({'seed':run['seed'],'records':records,'phase_clock_counts':counts,'phase_write_counts':writes,'guarded_prepared_clocks':guards,'unique_written_words':len(addresses),'coefficient_words_checked_per_clock':128,'historical_boundary_cases':48,'historical_directed_checks':15,'trace_sha256':sha(p),'status':'PASS'})
 report['status']='PASS_STORAGE_TRACE_AND_ADAPTER_AUDIT';(AREA/'trace-audit.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
