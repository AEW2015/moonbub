#!/usr/bin/env python3
"""Synthetic timed MSV1 recovery study; no real networking or target execution."""
import argparse,hashlib,heapq,json,math,random,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[6]
sys.path.insert(0,str(ROOT/'host'))
from moonshine.protocol import Reassembler,packets,parse_packet,MAX_PAYLOAD,VIDEO,SOF
CLOCK=100_000_000
PERIOD_NUM=10_000_000
PERIOD_DEN=3
IP_UDP=28
FEC_META=24
FEC_GROUP=8

def fixture_data(path):
 m=json.loads((path/'manifest.json').read_text());out=[]
 for row in m['frames']:
  b=(path/f"{row['id']:04d}.jpg").read_bytes()
  if hashlib.sha256(b).hexdigest()!=row['jpeg_sha256']:raise ValueError('fixture hash mismatch')
  out.append(b)
 if len(out)!=10:raise ValueError('requires ten fixture JPEGs')
 return out

def xor_packets(ps):
 if not ps:raise ValueError('empty group')
 n=max(map(len,ps));v=0
 for p in ps:v^=int.from_bytes(p.ljust(n,b'\0'),'big')
 return v.to_bytes(n,'big')

def simulate_link(frames,count,rate,seed,channel,fec,jitter_us=1200):
 if count<1 or rate<1 or jitter_us<0:raise ValueError('invalid configuration')
 rng=random.Random(seed); bad=False;queued=None;busy=False; serial=0; events=[]; arrivals=[]
 stats={'captures':0,'started':0,'sender_replaced':0,'sender_expired':0,'sent_data':0,'sent_parity':0,
        'lost_data':0,'lost_parity':0,'wire_bytes':0,'data_bytes':0,'parity_bytes':0,
        'sender_wait_highwater_bytes':0,'sender_max_wait_ms':0.}
 def put(at,kind,val):
  nonlocal serial
  serial+=1;heapq.heappush(events,(at,serial,kind,val))
 def lost():
  nonlocal bad
  if channel=='none':return False
  if channel=='iid':return rng.randrange(1_000_000)<5000
  if channel=='bursty':
   # packet-time Gilbert-Elliott, defined probabilities not measured Wi-Fi
   if bad:
    if rng.random()<0.25:bad=False
   elif rng.random()<0.002:bad=True
   return rng.random()<(0.5 if bad else 0.0005)
  raise ValueError('channel must be none, iid or bursty')
 def capture(i):return i*PERIOD_NUM//PERIOD_DEN
 def transmit(i,start):
  nonlocal busy
  busy=True;stats['started']+=1
  seq=list(packets(frames[i%10],i,capture(i)//100));pending=[]
  for first in range(0,len(seq),FEC_GROUP):
   group=seq[first:first+FEC_GROUP]
   pending.extend(('data',first+j,p) for j,p in enumerate(group))
   if fec:pending.append(('parity',first//FEC_GROUP,xor_packets(group)))
  now=start
  for kind,index,payload in pending:
   wire=len(payload)+IP_UDP+(FEC_META if kind=='parity' else 0)
   now+=(wire*8*CLOCK+rate-1)//rate
   if kind=='data':stats['sent_data']+=1;stats['data_bytes']+=wire
   else:stats['sent_parity']+=1;stats['parity_bytes']+=wire
   stats['wire_bytes']+=wire
   if lost():
    stats['lost_'+kind]+=1
   else:
    delay=rng.randrange(jitter_us+1)*100 if jitter_us else 0
    arrivals.append({'at':now+delay,'fid':i,'kind':kind,'index':index,
                     'payload':payload,'capture':capture(i),'count':len(seq),
                     'length':len(frames[i%10]),'jpeg':frames[i%10]})
  put(now,'finished',i)
 for i in range(count):put(capture(i),'capture',i)
 while events:
  now,_,kind,val=heapq.heappop(events)
  if kind=='capture':
   stats['captures']+=1
   if not busy:transmit(val,now)
   else:
    if queued is not None:stats['sender_replaced']+=1
    queued=val;stats['sender_wait_highwater_bytes']=max(stats['sender_wait_highwater_bytes'],len(frames[val%10]))
  else:
   busy=False
   if queued is not None:
    nxt=queued;queued=None;age=now-capture(nxt)
    if age>100*100_000:stats['sender_expired']+=1
    else:
     stats['sender_max_wait_ms']=max(stats['sender_max_wait_ms'],age/100_000)
     transmit(nxt,now)
 arrivals.sort(key=lambda e:(e['at'],e['fid'],e['kind'],e['index']))
 return arrivals,stats


def stats_times(done,count):
 ages=sorted((at-capture)/100_000 for _,at,capture in done)
 d={'complete':len(done),'received_fps_over_capture_duration':len(done)*30/count,
    'p50_complete_age_ms':None,'p95_complete_age_ms':None,'p99_complete_age_ms':None,
    'max_complete_age_ms':None}
 if ages:
  for p in (50,95,99):d[f'p{p}_complete_age_ms']=ages[max(0,math.ceil(len(ages)*p/100)-1)]
  d['max_complete_age_ms']=ages[-1]
 return d


def feed_sink(sink,packet,outcomes,events):
 try:
  result=sink.accept(packet);outcomes.append('done' if result is not None else 'partial')
 except ValueError:result=None;outcomes.append('error')
 events.append(packet)
 return result


def strict_receiver(arrivals,count,deadline_ms):
 sink=Reassembler();done=[];outcomes=[]; events=[]; late=0; rejected=0
 for e in arrivals:
  if e['kind']!='data':continue
  if e['at']-e['capture']>deadline_ms*100_000:late+=1;continue
  result=feed_sink(sink,e['payload'],outcomes,events)
  if outcomes[-1]=='error':rejected+=1
  if result:
   h,b=result
   if b!=e['jpeg']:raise AssertionError('payload mismatch')
   done.append((h.frame_id,e['at'],e['capture']))
 result=stats_times(done,count);result.update({'rejected_datagrams':rejected,'late_datagrams':late})
 return result,outcomes,events


def window_receiver(arrivals,count,deadline_ms,slots=4,gap_ms=2):
 """Experimental fixed reorder window feeding strict receiver as contiguous packets.

 Delay starts when a gap is first observed; per-gap timeout is checked before
 the next event. Lost SOF cannot be repaired. Explicit abort is forwarded to
 the actual Rust receiver in the host replay. No target memory or timing claim.
 """
 if slots<1 or gap_ms<=0:raise ValueError('positive reorder slots and gap timeout required')
 sink=Reassembler();done=[];outcomes=[];events=[];pending={};gap_since=None
 peak=0;timeouts=0;overflow=0;late=0;bad=0; no_active_fids=set()
 def abort():
  sink.reset(False);pending.clear();outcomes.append('abort');events.append(b'')
 def deliver(packet,at,capture,jpeg):
  nonlocal bad
  result=feed_sink(sink,packet,outcomes,events)
  if outcomes[-1]=='error':bad+=1
  if result:
   h,b=result
   if b!=jpeg:raise AssertionError('window payload mismatch')
   done.append((h.frame_id,at,capture))
 for e in arrivals:
  if e['kind']!='data':continue
  now=e['at']
  if gap_since is not None and now-gap_since>=gap_ms*100_000:
   abort();gap_since=None;timeouts+=1
  if now-e['capture']>deadline_ms*100_000:late+=1;continue
  packet=e['payload']
  try:p=parse_packet(packet)
  except ValueError:
   abort();gap_since=None;bad+=1;continue
  if p.flags&SOF:
   pending.clear();gap_since=None;deliver(packet,now,e['capture'],e['jpeg']);continue
  a=sink.active
  if a is None or (p.frame_id,p.frame_len,p.crc32,p.capture_us)!=(a.frame_id,a.frame_len,a.crc32,a.capture_us):
   if a is None:no_active_fids.add(p.frame_id)
   pending.clear();gap_since=None;deliver(packet,now,e['capture'],e['jpeg']);continue
  want=len(sink.data)
  if p.offset>want:
   if p.offset-want>slots*MAX_PAYLOAD or len(pending)>=slots or p.offset in pending:
    abort();gap_since=None;overflow+=1;continue
   pending[p.offset]=(packet,now,e['capture'],e['jpeg'])
   peak=max(peak,sum(len(v[0]) for v in pending.values()))
   if gap_since is None:gap_since=now
   continue
  if p.offset<want:
   pending.clear();gap_since=None;deliver(packet,now,e['capture'],e['jpeg']);continue
  deliver(packet,now,e['capture'],e['jpeg'])
  while sink.active is not None and len(sink.data) in pending:
   packet,_,capture,jpeg=pending.pop(len(sink.data))
   deliver(packet,now,capture,jpeg)
  gap_since=min((v[1] for v in pending.values()),default=None)
 result=stats_times(done,count);result.update({'window_slots':slots,'gap_ms':gap_ms,
   'max_buffered_datagram_bytes':peak,'gap_timeouts':timeouts,'window_overflows':overflow,
   'late_datagrams':late,'rejected_datagrams':bad,
   'frame_ids_seen_without_active_receiver':len(no_active_fids)})
 return result,outcomes,events

def window_presof_receiver(arrivals,count,deadline_ms,slots=4,gap_ms=2):
 """Four-slot post-SOF window plus one expiring pre-SOF datagram.

 Hypothetical; all packets, including pre-SOF, are checked by strict parser.
 Stored data is released only after a matching validated SOF. This models one
 extra packet, not packet security, DMA cost or the actual firmware.
 """
 if slots<1 or gap_ms<=0:raise ValueError('positive reorder slots and gap timeout required')
 sink=Reassembler();done=[];outcomes=[];events=[];pending={};gap_since=None;pre=None
 peak=0;timeouts=0;overflow=0;late=0;bad=0;pre_expired=0;pre_accepted=0;pre_rejected=0
 def identity(p):return (p.frame_id,p.frame_len,p.crc32,p.capture_us)
 def held():return sum(len(v[0]) for v in pending.values())+(len(pre[0]) if pre else 0)
 def abort():
  sink.reset(False);pending.clear();outcomes.append('abort');events.append(b'')
 def deliver(packet,at,capture,jpeg):
  nonlocal bad
  result=feed_sink(sink,packet,outcomes,events)
  if outcomes[-1]=='error':bad+=1
  if result:
   h,b=result
   if b!=jpeg:raise AssertionError('presof window payload mismatch')
   done.append((h.frame_id,at,capture))
 def stage(packet,now,capture,jpeg):
  nonlocal gap_since,peak,overflow
  p=parse_packet(packet);want=len(sink.data)
  if p.offset>want:
   if p.offset-want>slots*MAX_PAYLOAD or len(pending)>=slots or p.offset in pending:
    abort();gap_since=None;overflow+=1;return
   pending[p.offset]=(packet,now,capture,jpeg)
   peak=max(peak,held())
   if gap_since is None:gap_since=now
   return
  if p.offset<want:
   pending.clear();gap_since=None;deliver(packet,now,capture,jpeg);return
  deliver(packet,now,capture,jpeg)
  while sink.active is not None and len(sink.data) in pending:
   data,_,capture2,jpeg2=pending.pop(len(sink.data))
   deliver(data,now,capture2,jpeg2)
  gap_since=min((v[1] for v in pending.values()),default=None)
 for e in arrivals:
  if e['kind']!='data':continue
  now=e['at']
  if pre and now-pre[1]>=gap_ms*100_000:pre=None;pre_expired+=1
  if gap_since is not None and now-gap_since>=gap_ms*100_000:
   abort();gap_since=None;timeouts+=1
  if now-e['capture']>deadline_ms*100_000:late+=1;continue
  packet=e['payload']
  try:p=parse_packet(packet)
  except ValueError:
   abort();gap_since=None;bad+=1;continue
  if p.flags&SOF:
   candidate=pre;pre=None;pending.clear();gap_since=None
   deliver(packet,now,e['capture'],e['jpeg'])
   if candidate and sink.active is not None:
    cp=parse_packet(candidate[0])
    if identity(cp)==identity(p):
     pre_accepted+=1;stage(candidate[0],now,candidate[2],candidate[3])
    else:pre_rejected+=1
   continue
  a=sink.active
  if a is None or identity(p)!=identity(a):
   # Stage only a plausible next frame and an early bounded offset. A duplicate,
   # old or same-ID fragment does not create a new untrusted frame state.
   last=sink.last_frame_id
   delta=(p.frame_id-last)&0xffffffff if last is not None else 1
   plausible=(0<delta<0x80000000 and 0<p.offset<=slots*MAX_PAYLOAD)
   if plausible and pre is None:
    pre=(packet,now,e['capture'],e['jpeg']);peak=max(peak,held())
   else:pre_rejected+=1
   continue
  stage(packet,now,e['capture'],e['jpeg'])
 result=stats_times(done,count);result.update({'window_slots':slots,'pre_sof_slots':1,'gap_ms':gap_ms,
   'max_buffered_datagram_bytes':peak,'gap_timeouts':timeouts,'window_overflows':overflow,
   'pre_sof_expired':pre_expired,'pre_sof_accepted':pre_accepted,'pre_sof_rejected':pre_rejected,
   'late_datagrams':late,'rejected_datagrams':bad})
 return result,outcomes,events

def staged_receiver(arrivals,count,deadline_ms,use_fec):
 """One-frame buffer; accept any fragment of newest frame; release sorted.

 This is a non-deployable hypothetical wire extension for parity, not the
 actual ESP32 streaming receiver. Reordering-only uses original MSV1 datagrams.
 """
 sink=Reassembler();done=[]; outcomes=[];events=[];state=None;last_fid=-1
 evictions=0;late=0;peak=0;repairs=0;parity_count=0
 for e in arrivals:
  fid=e['fid'];now=e['at']
  if now-e['capture']>deadline_ms*100_000:late+=1;continue
  if fid<last_fid:continue
  if fid>last_fid:
   if state is not None and not state['complete']:evictions+=1
   state={'fid':fid,'capture':e['capture'],'count':e['count'],'length':e['length'],
          'items':{},'parities':{},'bytes':0,'complete':False}
   last_fid=fid
  if state is None or state['complete']:continue
  if e['kind']=='parity':
   if not use_fec:continue
   if e['index'] in state['parities']:raise ValueError('duplicate parity')
   state['parities'][e['index']]=e['payload'];state['bytes']+=len(e['payload'])+FEC_META;parity_count+=1
  else:
   p=parse_packet(e['payload'])
   if p.frame_id!=fid or p.frame_len!=state['length'] or p.offset!=e['index']*MAX_PAYLOAD:raise ValueError('packet identity mismatch')
   if e['index'] not in state['items']:
    state['items'][e['index']]=e['payload'];state['bytes']+=len(e['payload'])
  peak=max(peak,state['bytes'])
  if use_fec:
   for group,par in list(state['parities'].items()):
    start=group*FEC_GROUP;indices=list(range(start,min(start+FEC_GROUP,state['count'])))
    missing=[x for x in indices if x not in state['items']]
    if len(missing)==1:
     recovered=xor_packets([par]+[state['items'][x] for x in indices if x in state['items']])
     # Packet's own offset+payload count restore padding unambiguously.
     if len(recovered)<VIDEO.size:raise ValueError('truncated reconstructed header')
     payload_len=struct.unpack('!H',recovered[24:26])[0];recovered=recovered[:VIDEO.size+payload_len]
     p=parse_packet(recovered)
     if p.frame_id!=fid or p.offset!=missing[0]*MAX_PAYLOAD:raise ValueError('wrong recovered packet')
     state['items'][missing[0]]=recovered;state['bytes']+=len(recovered);repairs+=1
     peak=max(peak,state['bytes'])
     del state['parities'][group];state['bytes']-=len(par)+FEC_META
  if len(state['items'])==state['count']:
   result=None
   for i in range(state['count']):result=feed_sink(sink,state['items'][i],outcomes,events)
   if result is None or result[1]!=e['jpeg']:raise AssertionError('sorted datagrams failed checksum')
   done.append((fid,now,state['capture']));state['complete']=True
  if state['bytes']>262144+VIDEO.size*256+FEC_META*32+32*1100:
   raise ValueError('bounded full-frame staging storage exceeded')
 result=stats_times(done,count);result.update({'incomplete_evictions':evictions,'late_datagrams':late,
                                               'max_buffered_bytes':peak,'parity_received':parity_count,'packets_reconstructed':repairs})
 return result,outcomes,events


def rust_compare(executable,outcomes,events):
 data=b''.join(struct.pack('!H',len(x))+x for x in events)
 p=subprocess.run([str(executable)],input=data,capture_output=True,check=True)
 lines=p.stdout.decode().splitlines()
 if len(lines)!=len(outcomes):raise AssertionError('Rust emitted wrong event count')
 mismatches=[i for i,(a,b) in enumerate(zip(lines,outcomes)) if a!=b]
 return {'packet_events':len(lines),'mismatch_count':len(mismatches),'first_mismatches':mismatches[:10]}


def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--fixtures',type=Path,required=True);ap.add_argument('--rust-replay',type=Path,required=True)
 ap.add_argument('--frames',type=int,default=600);ap.add_argument('--seeds',type=int,default=5)
 ap.add_argument('--deadline-ms',type=int,default=100);ap.add_argument('--wire-mbps',type=float,default=10.)
 ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 if a.frames<1 or a.seeds<1 or a.deadline_ms<1 or a.wire_mbps<=0:ap.error('positive values required')
 frames=fixture_data(a.fixtures);rows=[]
 for scenario in ('clean','jitter','iid','bursty'):
  for fec in (False,True):
   for seed in range(a.seeds):
    channel='none' if scenario in ('clean','jitter') else scenario
    jitter=0 if scenario=='clean' else 1200
    stream,net=simulate_link(frames,a.frames,round(a.wire_mbps*1e6),seed+71,channel,fec,jitter)
    # Strict comparison only meaningful on ordinary MSV1 stream without parity.
    policies=('strict','window4','window4p1','reorder') if not fec else ('fec8',)
    for policy in policies:
     if policy=='strict':result,out,ev=strict_receiver(stream,a.frames,a.deadline_ms)
     elif policy=='window4':result,out,ev=window_receiver(stream,a.frames,a.deadline_ms)
     elif policy=='window4p1':result,out,ev=window_presof_receiver(stream,a.frames,a.deadline_ms)
     else:result,out,ev=staged_receiver(stream,a.frames,a.deadline_ms,fec)
     compare=rust_compare(a.rust_replay,out,ev)
     if compare['mismatch_count']:raise RuntimeError('Python/Rust receiver disagreement')
     rows.append({'scenario':scenario,'policy':policy,'seed':seed+71,'network':net,'result':result,'rust_reference_comparison':compare})
     print(f"{scenario} {policy} seed={seed+71}: complete={result['complete']}/{a.frames} sender_replaced={net['sender_replaced']} loss={net['lost_data']+net['lost_parity']}",flush=True)
 summary=[]
 for scenario in ('clean','jitter','iid','bursty'):
  for policy in ('strict','window4','window4p1','reorder','fec8'):
   q=[r for r in rows if r['scenario']==scenario and r['policy']==policy]
   summary.append({'scenario':scenario,'policy':policy,'seeds':len(q),'frames':sum(a.frames for _ in q),
    'complete':sum(r['result']['complete'] for r in q),'mean_complete':sum(r['result']['complete'] for r in q)/len(q),
    'mean_sender_replaced':sum(r['network']['sender_replaced'] for r in q)/len(q),
    'mean_wire_mbps':sum(r['network']['wire_bytes'] for r in q)/len(q)*8/(a.frames/30)/1e6,
    'worst_p95_complete_age_ms':max((r['result']['p95_complete_age_ms'] or 0) for r in q),
    'peak_reorder_bytes':max(r['result'].get('max_buffered_bytes',r['result'].get('max_buffered_datagram_bytes',0)) for r in q),
    'rust_mismatches':sum(r['rust_reference_comparison']['mismatch_count'] for r in q)})
 result={'scope':'host-only actual Rust MSV1 receiver + ideal synthetic network, candidate single-frame reorder/XOR repair; not hardware',
         'python_version':sys.version.split()[0],
         'frames_per_seed':a.frames,'seed_count':a.seeds,'wire_service_mbps':a.wire_mbps,'deadline_ms':a.deadline_ms,
         'fixture_sha256':[hashlib.sha256(x).hexdigest() for x in frames],
         'rust_receiver_source_sha256':hashlib.sha256((ROOT/'firmware/handheld/src/streaming/protocol.rs').read_bytes()).hexdigest(),
         'python_reference_source_sha256':hashlib.sha256((ROOT/'host/moonshine/protocol.py').read_bytes()).hexdigest(),
         'conditions':{'jitter':'independent uniform 0-1200 us per packet',
          'iid':'0.5% independent packet loss','bursty':'packet-step GE: good->bad 0.002, bad->good 0.25; per-state losses good 0.0005, bad 0.5',
          'rate':'constant L3 byte service shared by data and parity; no Wi-Fi MAC/PHY, audio or host/device timing',
          'parity':'one parity datagram per eight complete MSV1 datagrams, +24 assumed metadata bytes and IPv4/UDP; no negotiated implementation, auth, or ESP32 RAM timing',
          'source':'10 repeated synthetic frames, not gameplay'},'summary':summary,'runs':rows}
 a.out.write_text(json.dumps(result,indent=2)+'\n')
 for r in summary:print(r)
if __name__=='__main__':main()
