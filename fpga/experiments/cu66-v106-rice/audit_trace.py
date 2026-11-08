#!/usr/bin/env python3
"""Check complete adapters, exact cache recipe, modular algebra, trace checkpoints."""
import gzip,hashlib,json,random
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
AREA=ROOT/'experiments/python-gamebub-v106/rice'
MOD=1<<32
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def normal(coeff):return {k:v%MOD for k,v in coeff.items() if v%MOD}
def plus(a,b):return normal({k:a.get(k,0)+b.get(k,0) for k in a.keys()|b.keys()})
def neg(a):return normal({k:-v for k,v in a.items()})
def subtract(a,b):return plus(a,neg(b))
def algebra():
 s={'size':1};c={'count':1};delta={'delta':1};stream={'stream_bits':1};cache=subtract(s,c)
 lhs=subtract(cache,delta);rhs=subtract(s,plus(c,delta));assert lhs==rhs
 reset_left=stream;reset_right=subtract(stream,{});assert reset_left==reset_right
 old_zero=subtract(plus(c,delta),s);new_zero=subtract(subtract(s,c),delta);assert old_zero==neg(new_zero)
 count=0;wraps=0;edge=[0,1,15,16,17,31,32,33,0x7fffffff,0x80000000,0xffffffe0,0xfffffff0,0xffffffff]
 def check(size,used,d):
  nonlocal count,wraps
  cached=(size-used)&0xffffffff;next_used=(used+d)&0xffffffff;next_cached=(cached-d)&0xffffffff
  assert next_cached==((size-next_used)&0xffffffff)
  assert (((used+d)&0xffffffff)==size)==(cached==(d&0xffffffff))
  wraps+=used+d>=MOD;count+=1
 for a in edge:
  for b in edge:
   for d in edge:check(a,b,d)
 rng=random.Random(106402)
 for _ in range(100000):check(rng.getrandbits(32),rng.getrandbits(32),rng.getrandbits(32))
 return {'status':'PASS_EXACT_AFFINE_RING_IDENTITIES','domain':'All size/count/delta/stream_bits in Z/(2^32); affine coefficient normalization proves identities, not enumeration.','update_lhs_normal_form':lhs,'update_rhs_normal_form':rhs,'reset_normal_form':reset_right,'old_zero_normal_form':old_zero,'negative_new_zero_normal_form':neg(new_zero),'lastword_reason':'Old and new predicates test additive inverses for zero; negation is a bijection, so equivalence holds including modular wrap.','supplementary_numeric_cases':count,'numeric_wrap_cases':wraps,'proof_scope':'Mathematical cache-maintenance and lastword identities; not a complete parser formal state-space proof.'}
def main():
 sel=json.loads((AREA/'probe-results.json').read_text());rp=ROOT/sel['selected_receipt'];r=json.loads(rp.read_text());assert sha(rp)==sel['sha256'] and r['status']=='PASS_ACTUAL_RICE_CACHE_EQUIVALENCE'
 out={'schema':'v106-rice-cache-evidence-audit-v1','status':'FAIL','receipt':str(rp.relative_to(ROOT)),'receipt_sha256':sha(rp),'auditor':{'path':str(Path(__file__).resolve().relative_to(ROOT)),'sha256':sha(Path(__file__))},'checks':[],'algebra':algebra(),'runs':[]}
 for k,mod in [('original','rice_original'),('candidate','rice_candidate')]:
  src=ROOT/r[k]['path'];assert sha(src)==r[k]['sha256'];assert (rp.parent/(mod+'.sv')).read_text().replace('module '+mod+' (','module br88_rice_elastic (',1)==src.read_text();out['checks'].append({'name':k+' complete production body after module rename reversal','sha256':sha(src),'status':'PASS'})
 proofp=ROOT/'fpga/experiments/cu66-v106-rice/edit-proof.json';proof=json.loads(proofp.read_text());before=(ROOT/proof['original_path']).read_text();s=before
 for e in proof['edits']:assert s.count(e['before'])==e['expected_occurrences']==1;s=s.replace(e['before'],e['after'],1)
 after=(ROOT/proof['candidate_path']).read_text();assert s==after and len(proof['edits'])==8 and before.split(');',1)[0]==after.split(');',1)[0]
 assert sum(line.strip()=="loaded<=loaded+32'(in_bits);" for line in after.splitlines())==1 and sum(line.strip()=="consumed<=consumed+32'(take_bits);" for line in after.splitlines())==2
 assert after.count("cached_load_remaining<=cached_load_remaining-32'(in_bits);")==1 and after.count("cached_remaining<=cached_remaining-32'(take_bits);")==2
 assert 'cached_remaining<=stream_bits; cached_load_remaining<=stream_bits;' in after
 assert 'always_ff @(posedge clk) if (!reset && !stream_start) begin' in after
 out['checks'].append({'name':'eight exact edits, header unchanged, full32 mirrors and reset/start cache identities','path':str(proofp.relative_to(ROOT)),'sha256':sha(proofp),'status':'PASS'})
 hist=ROOT/'fpga/experiments/cu66-v91/tb_rice.cpp';h=hist.read_text().replace('Vbr88_rice_elastic','Vrice_probe').replace('int main(int argc,char** argv)','int historical_rice_main(int argc,char** argv)').replace('d.clk=1; d.eval(); d.clk=0; d.eval();','rice_pre(d); d.clk=1; d.eval(); rice_post(d); d.clk=0; d.eval();');assert (rp.parent/'historical_rice.cpp').read_text()==h
 out['checks'].append({'name':'historical generic bench only class/main rename and oracle clock hooks','sha256':sha(hist),'status':'PASS'})
 for run in r['runs']:
  seed=run['seed'];p=rp.parent/f'seed-{seed}.jsonl.gz';assert sha(p)==r['artifacts_sha256'][p.name];phase='prepared';counts={'prepared':0,'historical':0};previous={'prepared':-1,'historical':-1}
  with gzip.open(p,'rt') as f:
   for line in f:
    e=json.loads(line)
    if 'model_start' in e:assert e['model_start']=='historical-generic-rice';phase='historical';continue
    assert e['equal'] and e['phase']==phase and e['clock']>previous[phase]
    if phase=='prepared':assert e['clock']==counts[phase]
    assert 0<=e['size']<MOD and 0<=e['loaded']<MOD and 0<=e['consumed']<MOD
    assert e['remaining']==(e['size']-e['consumed'])%MOD and e['load_remaining']==(e['size']-e['loaded'])%MOD
    assert 0<=e['available']<=64 and 0<=e['reservoir']<(1<<e['available'])
    previous[phase]=e['clock'];counts[phase]+=1
  assert counts['prepared']==run['prepared_clocks']==run['prepared_trace_records'] and counts['historical']==run['historical_trace_records']
  logs=[json.loads(x) for x in (rp.parent/f'seed-{seed}.log').read_text().splitlines()];v=next(x for x in logs if x.get('type')=='verdict');assert v==run['historical_verdict'] and v['cases']==1520 and v['configurations']==8 and v['requests_per_configuration']==173061 and v['directed_checks']==104
  assert len([x for x in logs if x.get('type')=='case'])==1520*8
  final={k:v for k,v in run.items() if k!='historical_verdict'};assert logs[-1]==final
  out['runs'].append({'seed':seed,'prepared_complete_trace_records':counts['prepared'],'historical_sampled_checkpoint_records':counts['historical'],'actual_every_clock_oracle_edges':run['prepared_clocks']+run['historical_clocks'],'historical_cases':1520,'configurations':8,'directed_checks':104,'trace_sha256':sha(p),'status':'PASS','offline_scope':'All recorded cache/reservoir checkpoints verified. Historical traces are sampled; actual C++ oracle/comparator checks every edge.'})
 out['status']='PASS_RICE_CACHE_ALGEBRA_ADAPTERS_AND_CHECKPOINTS';(AREA/'trace-audit.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
