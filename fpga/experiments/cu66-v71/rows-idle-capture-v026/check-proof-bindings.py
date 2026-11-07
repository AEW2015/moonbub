"""Validate executed proof/test receipts against the actual candidate bytes."""
from pathlib import Path
import hashlib,json
p=Path(__file__).resolve().parent;sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
r=json.loads((p/'proof02/result.json').read_text());assert r['status']=='PASS_EXACT_CONTROL_PROJECTION_AND_OWNED_PAYLOAD_INDUCTION'
assert all(sha(p/n)==h for n,h in r['source_sha256'].items())
rows=json.loads((p/'proof02/execution.json').read_text());assert [(x['mode'],x['banks'])for x in rows]==[('induction',1),('induction',2),('negative',2),('nonvacuity',2)]
for row in rows:
 d=p/'proof02'/(row['mode']+'-banks'+str(row['banks']))
 assert row['passed'] and sha(d/'executed.ys')==row['script_sha256'] and sha(d/'yosys.log')==row['log_sha256']
 assert all(sha(p/'proof02'/n)==h for n,h in row['sources_sha256'].items())
 text=(d/'yosys.log').read_text()
 assert ('model found: FAIL!'in text and row['returncode']!=0)if row['expected_counterexample']else('Induction step proven: SUCCESS!'in text and row['returncode']==0)
pair=p/'pair01';v=json.loads((pair/'result.json').read_text());assert v['status']=='PASS_OBSERVED_OLD_NEW_ROWS_AND_AUTHORITATIVE_PAYLOAD' and sha(pair/'source-freeze.json')==v['source_freeze_sha256']
assert all(sha(p/n)==h for n,h in json.loads((pair/'source-freeze.json').read_text()).items())
assert all(x['returncode']==0 for x in json.loads((pair/'execution.json').read_text()))
for banks in [1,2]:assert 'ROW_IDLE_CAPTURE_PAIR_PASS banks'+str(banks)+' frames2 qualified_bytes1036816'in(pair/('banks'+str(banks)+'-run.log')).read_text()
print('V026_EXECUTED_PROOF_AND_PAIR_SOURCE_BINDINGS_PASS')
