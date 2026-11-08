#!/usr/bin/env python3
"""Independent evidence replay for the full-production ingress cache probe."""
import gzip,hashlib,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];AREA=ROOT/'experiments/python-gamebub-v106/ingress'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 selection=read(AREA/'probe-results.json');receipt=ROOT/selection['selected_receipt'];assert sha(receipt)==selection['sha256'];r=read(receipt);assert r['status']=='PASS_ACTUAL_INGRESS_CACHE_EQUIVALENCE'
 for path,h in r['source_sha256'].items():assert sha(ROOT/path)==h,('live source drift',path)
 for path,h in r['artifacts_sha256'].items():assert sha(receipt.parent/path)==h,('retained artifact drift',path)
 spec=importlib.util.spec_from_file_location('v106_ingress_runner',ROOT/'scripts/cu66-v106/ingress.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);recipe=m.verify_sources();assert m.model()==read(AREA/'model.json')
 assert len(recipe['edits'])==7
 ports=read(ROOT/'fpga/experiments/cu66-v106-ingress/ports.json');wrapper=(ROOT/'fpga/experiments/cu66-v106-ingress/ingress_probe.sv').read_text()
 outputs=[n for d,n in ports if d=='output'];assert len(ports)==62 and len(outputs)==47
 for n in outputs:assert wrapper.count('(old_dut.packet_decoder.synchronous.ingress.'+n+'==new_dut.packet_decoder.synchronous.ingress.'+n+')')>=1
 original=(ROOT/recipe['original_path']).read_text();candidate=(ROOT/recipe['candidate_path']).read_text()
 # All functional state transitions and original guards survive unchanged;
 # the exact recipe reconstructs the only seven changes.
 original_header=original.split(');',1)[0];assert candidate.split(');',1)[0]==original_header
 for guard in ('if(ctx_valid && ctx_ready)','else if(!word_valid && replay_bits<sizes[band])','ctx_valid=state==CONTEXT_RUN && word_valid && replay_bits<sizes[band] && !cancelled && !context_failure;','if(context_active && ctx_error!=0) fail_packet(ctx_error);','else if(context_active && ctx_done) begin'):
  assert original.count(guard)==candidate.count(guard)==1
 child=(ROOT/'fpga/experiments/cu66-v106-context/br88_context.sv').read_text();rice=(ROOT/'fpga/experiments/cu66-v106-suffix/br88_rice_elastic.sv').read_text()
 ready=rice.split('        in_ready=',1)[1].split(';',1)[0];assert 'in_bits' not in ready and 'in_last' not in ready
 assert 'assign in_ready=parser_in_ready && active && !start && !abort_context && !reset;' in child
 runs=[];mask=(1<<32)-1
 for run in r['runs']:
  path=receipt.parent/('seed-'+str(run['seed'])+'.jsonl.gz');prepared=events=historical=init=update=0;coverage=set();in_historical=False
  for raw in gzip.open(path,'rt'):
   e=json.loads(raw)
   if 'model_start' in e:in_historical=True;continue
   if 'prepare' in e:
    prepared+=1;coverage.add((e['size'],e['band'],e['mode'],e['guards'],e['action']));assert ((e['size']-e['replay'])&mask)==e['remaining'];continue
   cache,replay=e['before_cache'],e['before_replay']
   if e['cancel']:cache=replay=0
   elif e['initialize']:cache=e['selected_size'];replay=0
   elif e['update']:cache=(cache-e['bits'])&mask;replay=(replay+e['bits'])&mask
   assert cache==e['cache'] and replay==e['replay']
   if e['live'] and not e['cancel']:assert e['cache']==((e['size']-e['replay'])&mask)
   assert e['equal'] and e['parser_available']<=64
   if in_historical:historical+=1
   else:events+=1;init+=e['initialize'] and not e['cancel'];update+=e['update'] and not e['cancel']
  assert prepared==run['prepared_cases']==5760 and len(coverage)==5760 and events==run['prepared_edges'] and historical==run['historical_trace_rows']
  assert init==run['prepared_initializations'] and update==run['prepared_updates']
  runs.append(dict(seed=run['seed'],prepared_cases=prepared,prepared_edges=events,historical_checkpoints=historical,prepared_initializations=init,prepared_updates=update,historical_edges=run['historical_edges'],complete_trace_sha256=sha(path)))
 result=dict(schema='v106-ingress-evidence-audit-v1',status='PASS_INGRESS_MODEL_ADAPTERS_AND_CHECKPOINTS',receipt=str(receipt.relative_to(ROOT)),receipt_sha256=sha(receipt),auditor=dict(path=str(Path(__file__).resolve().relative_to(ROOT)),sha256=sha(Path(__file__))),checks=['Every source and retained artifact pinned and rehashed','Exact seven-edit source recipe and complete module/type-rename adapters','Original public header, bounds, valid, cancellation/error/done priority retained','Full32 cache/last algebra independently rerun','Actual old/new production pipelines with all synchronous-ingress public outputs compared each clock','Every prepared clock replayed independently; historical checkpoints individually checked but not a complete offline historical trace','Unchanged child in_ready independent of private inactive in_bits/in_last'],model=read(AREA/'model.json'),runs=runs,total_clock_edges=r['total_clock_edges'],scope='Native timing, hardware30fps and validated under10ms remain separate open gates.')
 (AREA/'trace-audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(result['status'])
if __name__=='__main__':main()
