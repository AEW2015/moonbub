#!/usr/bin/env python3
"""Independently replay retained RAM traces; no FPGA tools or producer imports."""
import gzip,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
AREA=ROOT/'experiments/python-gamebub-v102/memory'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
selection=json.loads((AREA/'probe-results.json').read_text());receipt=ROOT/selection['selected_receipt'];assert sha(receipt)==selection['sha256']
r=json.loads(receipt.read_text());assert r['status']=='PASS_ACTUAL_CLOCKED_RAM_EQUIVALENCE'
rows=[]
for result in r['runs']:
 seed=result['seed'];p=receipt.parent/('seed-'+str(seed)+'.jsonl.gz');assert sha(p)==r['artifacts_sha256'][p.name]
 memory=[((i*131)^(i>>5)^seed)&255 for i in range(49152)]
 data,address,epoch=0xA5,0x87654321,0x12345678;count=collisions=reads=writes=forced=0
 with gzip.open(p,'rt') as stream:
  for line in stream:
   row=json.loads(line);assert row['case']==count and row['equal'] is True
   if not row['forced_collision']:
    if row['guards']!=0:assert row['read']==0 and row['write']==0
    if row['state']!=1:assert row['write']==0
    if row['state'] not in (26,28):assert row['read']==0
   else:
    assert row['state']==0 and row['guards']==0 and row['read']==1 and row['write']==1;forced+=1
   if row['read']:
    index=row['read_addr']&65535;assert index<len(memory)
    data=memory[index];address=row['read_addr'];epoch=row['prepared_epoch'];reads+=1
   if row['write']:
    index=row['write_addr'];assert index<len(memory)
    if row['read'] and index==(row['read_addr']&65535):collisions+=1
    memory[index]=row['write_data'];writes+=1
   assert (row['data'],row['latched_addr'],row['latched_epoch'])==(data,address,epoch)
   count+=1
 assert count==result['cases']==9536 and collisions==result['same_address_read_first_collisions']==32
 assert (reads,writes,forced)==(result['reads'],result['writes'],result['verification_forced_collision_cases'])
 rows.append({'seed':seed,'cases_replayed':count,'reads':reads,'writes':writes,'same_address_read_first_collisions':collisions,'forced_collision_cases':forced,'trace':str(p.relative_to(ROOT)),'trace_sha256':sha(p)})
o={'schema':'v102-independent-memory-trace-audit-v1','status':'PASS_INDEPENDENT_RAM_TRACE_REPLAY','source':str(Path(__file__).relative_to(ROOT)),'source_sha256':sha(Path(__file__)),'selected_receipt':str(receipt.relative_to(ROOT)),'selected_receipt_sha256':sha(receipt),'runs':rows,'total_cases_replayed':sum(x['cases_replayed'] for x in rows),'scope':'Independent old-data byte model, address/epoch latch-and-hold, reset/start/abort guard suppression and explicitly forced collisions only; no hardware or reachability proof.'}
(AREA/'trace-audit.json').write_text(json.dumps(o,indent=2,sort_keys=True)+'\n');print(o['status'],o['total_cases_replayed'])
