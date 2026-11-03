#!/usr/bin/env python3
"""Check every trace event plus loss handling and recovery accounting."""
import re,sys
from pathlib import Path
lines=Path(sys.argv[1]).read_text().splitlines();trace=Path(sys.argv[2]).read_text().splitlines()
start=int(sys.argv[3]);count=int(sys.argv[4]);assert 'TEST_PASS_PACKET_RECOVERY' in lines
result=[x for x in lines if x.startswith('PACKET_RECOVERY_RESULT ')];assert len(result)==1
nums=lambda x:{k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',x)}
r=nums(result[0]);assert r['events']==int(trace[0])==52 and r['commits']==1 and r['presented']==2
assert r['aborts']==(0 if start==0 else 1) and r['no_sof']==(1 if start==0 else 0)
assert r['forwarded_packets']==26+start and r['prior_front_preserved']==1 and r['queue_high_bytes']<=5320
rows=[list(map(int,x.split())) for x in trace[1:]];frame0=[row for row in rows if row[0]==0];assert 0<=start<26 and 1<=count<=26-start
omitted_offsets={row[2] for row in frame0[start:start+count]}
events=[x for x in lines if x.startswith('PACKET_EVENT ')];assert len(events)==len(rows)
actions=[]
for line,(fid,at,offset,size) in zip(events,rows,strict=True):
 e=nums(line);assert (e['id'],e['offset'],e['bytes'],e['arrival_cycle'])==(fid,offset,size,r['epoch']+at)
 action=re.search(r'action=(\w+)',line)[1];actions.append(action)
 if fid==0 and offset in omitted_offsets:assert action=='omitted'
 if fid==1:assert action=='enqueue'
fwd=[nums(x) for x in lines if x.startswith('PACKET_FORWARD ')]
assert [(x['id'],x['offset'],x['bytes']) for x in fwd]==[(f,o,n) for f,t,o,n in rows if f==1 or (f==0 and o<frame0[start][2])]
abort=[x for x in lines if x.startswith('FRAME_ABORT ')];no_sof=[x for x in lines if x.startswith('FRAME_NO_SOF ')];commit=[x for x in lines if x.startswith('FRAME_COMMIT ')];assert len(commit)==1
if start==0:
 assert not abort and len(no_sof)==1
 bad=nums(no_sof[0]);assert bad['first_offset']==frame0[count][2] and bad['prior_front_intact']==1
 assert bad['cycle']<nums(commit[0])['cycle']
 assert not any(x.startswith('FRAME_BEGIN id=0 ') for x in lines)
else:
 assert len(abort)==1 and not no_sof
 ab=nums(abort[0]);assert ab['prior_front_intact']==1 and ab['forwarded_bytes']==frame0[start][2]
 assert ab['reason'] in (0,1) and ab['trigger_cycle']<=ab['cycle']<nums(commit[0])['cycle']
 if ab['reason']==1:assert 200000<=ab['trigger_cycle']-ab['last_forward_cycle']<=200001
 else:assert start+count<26 and ab['trigger_cycle']>=r['epoch']+frame0[start+count][1]
assert nums(commit[0])['cycle']<r['finish_cycle']
print(f'RECOVERY_CHECK_PASS loss_start={start} count={count}, events=52, prior front and recovery verified')
