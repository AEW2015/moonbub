"""Independent original V105 full mode-store event and hold oracle."""
import json

def hidden(p,t):
 if p:return 1046<=t<=1064
 return any(a<=t<=b for a,b in ((633,651),(723,741),(993,1011),(1083,1101),(4071,4110),(4161,4200),(4251,4290),(4431,4460),(4521,4550)))
def mode_replay(path,seed):
 memory=[((i*131+(i>>3))^seed)&3 for i in range(8100)];held=3;cases=reads=writes=guarded=finals=0;branches=[0]*5;domains=[set() for _ in range(5)];read_addresses=set()
 for line in path.open():
  e=json.loads(line)
  if 'final_addr' in e:assert e['final_addr']==finals and e['value']==memory[finals];finals+=1;continue
  assert e['case']==cases and e['equal'];state,p,t=e['state'],e['plane'],e['tile'];base=(0,5400,6750)[p];branch=-1;addr=data=0
  if not e['guard']:
   if state==31 and e['index']!=8100:branch=0;addr=e['index']&8191;data=1
   elif state==6 and t!=(5400 if p==0 else 1350):branch=1;addr=(base+t)&8191;data=1 if hidden(p,t) else 2
   elif state==8 and e['bits'] and e['mixed']:branch=2;addr=(base+t)&8191;data=2 if e['bit'] else 0
   elif state==10 and t!=e['end']:
    if hidden(p,t) or e['tag']==0:branch=3;addr=(base+t)&8191;data=1 if hidden(p,t) else 0
    elif e['tag']==1:branch=4;addr=(base+t)&8191;data=2
  read=bool(e['lookup'] and state==26 and not e['guard'])
  assert (e['branch'],e['write_addr'],e['write_data'],bool(e['read']))==(branch,addr,data,read)
  assert not(read and branch>=0)
  if read:held=memory[e['addr']];reads+=1;read_addresses.add(e['addr'])
  if branch>=0:assert addr<8100;memory[addr]=data;writes+=1;branches[branch]+=1;domains[branch].add(addr)
  assert held==e['held'];cases+=1;guarded+=bool(e['guard'])
 assert cases==158228 and finals==8100 and len(read_addresses)==8100
 assert all(len(domains[i])==8100 for i in range(4))
 return dict(status='PASS_INDEPENDENT_MODE_PORT_ORACLE',events=cases,read_events=reads,write_events=writes,guarded=guarded,branches=branches,unique_addresses_per_branch=list(map(len,domains)),valid_read_addresses=len(read_addresses),final_store_words=finals,scope='Prepared full production states plus arbitrary initialized 2-bit memory, high32 ACTIVE_CLEAR indices; not arbitrary unreachable coordinate-state proof.')
