"""Independently replay actual run/fill edges against original packet bytes."""
import json

def quant_replay(path,vectors):
 packets={v[0]:bytes.fromhex(v[2]) for v in map(str.split,vectors.read_text().splitlines())}
 case=None;cursor=0;remaining=0;value=0;run_edges=fill_edges=bad_runs=terminal=0;cases=set()
 for line in path.open():
  r=json.loads(line)
  if 'begin' in r:case=r['begin'];cursor=remaining=value=0;continue
  if not r.get('quant') or r['kill']:continue
  packet=packets[case];qstart=128+int.from_bytes(packet[36:40],'big');qsize=int.from_bytes(packet[40:44],'big')
  assert r['runs']==cursor,(case,r,cursor)
  if r['state']==17:
   run_edges+=1;cases.add(case)
   if r['index']==qsize-4:terminal+=1;continue
   b=packet[qstart+r['index']]
   assert r['selected']==r['cached']==b,(case,r,b)
   remaining=(b&63)+1;value=b>>6
   if value>2 or cursor+remaining>1350:bad_runs+=1;remaining=0
  else:
   fill_edges+=1
   assert remaining>0 and r['remaining']==remaining and r['value']==value,(case,r,remaining,value)
   cursor+=1;remaining-=1
 assert run_edges>1000 and fill_edges>100000 and bad_runs>0 and terminal>0
 return {'status':'PASS_INDEPENDENT_PACKET_RUN_FILL_ORACLE','run_edges':run_edges,'fill_edges':fill_edges,'rejected_run_edges':bad_runs,'terminal_edges':terminal,'packet_ids_checked':len(cases),'oracle':'Original packet bytes, integer run grammar, complete fill-address/value/remaining sequence; cache equality checked only on consumed Q_RUN branch.'}
