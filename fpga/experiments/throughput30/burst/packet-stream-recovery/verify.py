#!/usr/bin/env python3
"""Check trace order, loss, abort, presentation accounting and packet timings."""
import re,sys
from pathlib import Path
lines=Path(sys.argv[1]).read_text().splitlines(); trace=Path(sys.argv[2]).read_text().splitlines()
assert 'TEST_PASS_PACKET_RECOVERY' in lines
result=[x for x in lines if x.startswith('PACKET_RECOVERY_RESULT ')];assert len(result)==1
nums=lambda x:{k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',x)}
r=nums(result[0]);assert r['events']==int(trace[0])==52 and r['aborts']==r['commits']==1 and r['presented']==2
assert r['forwarded_packets']==31 and r['prior_front_preserved']==1 and r['queue_high_bytes']<=5320
rows=[list(map(int,x.split())) for x in trace[1:]]
events=[x for x in lines if x.startswith('PACKET_EVENT ')];assert len(events)==len(rows)
for line,(fid,at,offset,size) in zip(events,rows,strict=True):
 e=nums(line);assert (e['id'],e['offset'],e['bytes'],e['arrival_cycle'])==(fid,offset,size,r['epoch']+at)
 action=re.search(r'action=(\w+)',line)[1]
 if fid==0 and offset==5120: assert action=='omitted'
 elif fid==0 and offset>6144: assert action=='discard_after_abort'
 else: assert action=='enqueue'
fwd=[nums(x) for x in lines if x.startswith('PACKET_FORWARD ')]
assert [(x['id'],x['offset'],x['bytes']) for x in fwd]==[(f,o,n) for f,t,o,n in rows if f==1 or (f==0 and o<5120)]
abort=[x for x in lines if x.startswith('FRAME_ABORT ')];commit=[x for x in lines if x.startswith('FRAME_COMMIT ')]
assert len(abort)==len(commit)==1 and nums(abort[0])['prior_front_intact']==1
assert nums(abort[0])['cycle']<nums(commit[0])['cycle']<r['finish_cycle']
print('PACKET_RECOVERY_CHECK_PASS: 52 arrivals, partial abort, prior front and valid recovery verified')
