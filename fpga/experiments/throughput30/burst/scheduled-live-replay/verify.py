#!/usr/bin/env python3
"""Check all scheduled arrival times, event IDs and finite-case outcomes."""
import re,struct,sys
from pathlib import Path
lines=Path(sys.argv[1]).read_text().splitlines();raw=Path(sys.argv[2]).read_bytes();mode=sys.argv[3]
assert mode in ('no-stall','stall') and 'TEST_PASS_SCHEDULED_GUEST' in lines
nums=lambda line:{k:int(v) for k,v in re.findall(r'(\w+)=(-?\d+)',line)}
rline=[x for x in lines if x.startswith('SCHEDULE_RESULT ')];assert len(rline)==1;r=nums(rline[0])
assert r['events']==84 and r['queue_high']<=5195 and r['stall']==(0 if mode=='no-stall' else 1000000)
arr=[];p=0
while p<len(raw):
 t,n=struct.unpack_from('>II',raw,p);p+=8;b=raw[p:p+n];p+=n;arr.append((t,b))
assert len(arr)==84 and p==len(raw)
entries=[x for x in lines if x.startswith('ARRIVE ')];assert len(entries)==84
for line,(t,b) in zip(entries,arr,strict=True):
 v=nums(line);assert v['cycle']==r['epoch']+t and v['seq']==int.from_bytes(b[1:5],'big') and v['id']==int.from_bytes(b[5:9],'big')
 assert 0<=v['slots']<=5 and 0<=v['queue_bytes']<=5195
presents=[nums(x)['id'] for x in lines if x.startswith('PRESENT ')];drops=[nums(x)['id'] for x in lines if x.startswith('DROP ')]
assert presents==([0,2] if mode=='no-stall' else [2]);assert drops==([1] if mode=='no-stall' else [0,1])
assert r['published']==len(presents) and r['dropped']==len(drops)
overflows=[x for x in entries if 'action=overflow' in x]
assert len(overflows)==(0 if mode=='no-stall' else 1)
if overflows:assert nums(overflows[0])['id']==0 and nums(overflows[0])['slots']==5
if mode=='stall':
 overflow_drop=next(x for x in lines if x.startswith('DROP id=0 '))
 assert nums(overflow_drop)['forwarded_bytes']==1024
print(f'SCHEDULE_CHECK_PASS {mode}: 84 exact arrivals, presented {presents}, dropped {drops}, max queue {r["queue_high"]}')
