from pathlib import Path
import json,re,statistics,hashlib
root=Path('C:/moon/maintenance/v49-canonical-huffman')
def read(p):
 b=p.read_bytes();return b.decode('utf-16'if b.startswith(b'\xff\xfe')else'utf-8')
a=[s.split('\t')[:2]for s in read(root/'control-deep.log').splitlines()];b=[s.split('\t')[:2]for s in read(root/'candidate-deep.log').splitlines()];assert a==b
runs=json.loads((root/'benchmark01/runs.json').read_text())
summary=json.loads((root/'qualification.json').read_text());summary['deep_mutation_cases']=len(a);summary['total_differential_cases']=summary['cases']+len(a);summary['microbench']={}
for v in ('control','candidate'):
 rows=[x for x in runs if x['variant']==v and x['benchmark']=='microbench'];fields=[dict(re.findall(r'(\w+)=(\d+)',x['stdout']))for x in rows]
 summary['microbench'][v]={'median_internal_us':statistics.median(int(x['elapsed_us'])for x in fields),'peak':int(fields[0]['peak']),'allocations':int(fields[0]['allocations']),'decodes':100}
summary['corpus_allocations']={'control':84765,'candidate':14829};summary['host_huffman_frame']={'control':352,'candidate':896,'delta':544};summary['target_stack_proof']=False
(root/'RESULT.json').write_text(json.dumps(summary,indent=2)+'\n')
(root/'source-bindings-final.json').write_text(json.dumps({str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest()for d in ['control/native','candidate/native','harness']for f in(root/d).rglob('*')if f.is_file()},indent=2)+'\n')
print(json.dumps(summary,indent=2))
