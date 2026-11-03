#!/usr/bin/env python3
"""Conditional 30 Hz producer + bounded sink model. No ESP/RTL runs here."""
import argparse,collections,hashlib,heapq,json,struct,zlib
from pathlib import Path
HERE=Path(__file__).resolve().parent
CAPTURE=HERE.parent/'scheduled-live-replay/data'
PERIOD_NUM=10_000_000;PERIOD_DEN=3;CAPACITY=5*1039

def load_events():
 raw=(CAPTURE/'guest-events.bin').read_bytes();audit=[json.loads(x) for x in (CAPTURE/'adapter-events.jsonl').read_text().splitlines()]
 if hashlib.sha256(raw).hexdigest()!='7853a8233831ff6ceb6e44fe067ea32225a76df565647e56be45b72199fc8a0d':raise ValueError('capture hash')
 out=[];pos=0
 while pos<len(raw):
  if pos+4>len(raw):raise ValueError('truncated')
  n=struct.unpack_from('>I',raw,pos)[0];pos+=4
  if not 9<=n<=1039 or pos+n>len(raw):raise ValueError('length')
  b=raw[pos:pos+n];pos+=n;seq=len(out);a=audit[seq]
  if a['seq']!=seq or a['sha256']!=hashlib.sha256(b).hexdigest() or a['length']!=n:raise ValueError('audit')
  kind=chr(b[0]);fid=int.from_bytes(b[5:9],'big')
  if int.from_bytes(b[1:5],'big')!=seq or kind not in 'BDCA' or fid not in (0,1,2):raise ValueError('header')
  out.append(dict(seq=seq,id=fid,type=kind,body=b))
 if len(out)!=len(audit) or len(out)!=84:raise ValueError('count')
 return out

def assign(events):
 """Fresh independent source times, not captured execution/ACK timestamps."""
 last={};scheduled=[]
 for e0 in events:
  e=dict(e0);fid=e['id'];base=fid*PERIOD_NUM//PERIOD_DEN
  if e['type']=='B':t=base;last[fid]=base+100000
  elif e['type']=='D':t=last[fid];last[fid]+=120000
  else:t=last[fid]
  e['at']=t;scheduled.append(e)
 if any(scheduled[i]['at']>scheduled[i+1]['at'] for i in range(len(scheduled)-1)):
  raise ValueError('producer ordering would interleave recorded event sequence')
 return scheduled

def simulate(events,release_cycles,service_us_per_kib=200,capacity=CAPACITY):
 if release_cycles<0 or capacity<1039 or service_us_per_kib<1:raise ValueError('invalid parameter')
 timeline=[];serial=0
 def put(t,kind,body):
  nonlocal serial
  serial+=1;heapq.heappush(timeline,(t,serial,kind,body))
 for e in events:put(e['at'],'arrival',e)
 q=collections.deque();occupied=0;high=0;high_slots=0;inflight=None;active=None;pending=None;front=None
 completed=[];drops=[];drop_ids=set();last_crc={};busy_until=0;now=0;actions=[]
 def drop(fid,reason):
  nonlocal q,occupied,active
  if fid in drop_ids:return
  drop_ids.add(fid);drops.append({'id':fid,'reason':reason,'cycle':now})
  kept=collections.deque()
  while q:
   x=q.popleft()
   if x['id']==fid:occupied-=len(x['body'])
   else:kept.append(x)
  q=kept
  if active is not None and active['id']==fid:active=None
 def service():
  nonlocal inflight
  if inflight is not None or not q:return
  e=q.popleft();inflight=e
  body=e['body'];payload=(len(body)-15) if e['type']=='D' else 0
  duration=max(1,(payload*service_us_per_kib*100+1023)//1024) if payload else 2000
  put(now+duration,'served',e)
 while timeline:
  now,_,kind,e=heapq.heappop(timeline)
  if kind=='arrival':
   fid=e['id'];typ=e['type'];b=e['body']
   if fid in drop_ids:actions.append({'seq':e['seq'],'id':fid,'cycle':now,'action':'discard_dropped'});continue
   if typ=='B' and (active is not None or pending is not None or (inflight is not None and inflight['id']!=fid)):
    drop(fid,'busy_begin');actions.append({'seq':e['seq'],'id':fid,'cycle':now,'action':'drop_busy'});continue
   if len(q)+(inflight is not None)>=5 or occupied+len(b)>capacity:
    drop(fid,'queue_full');actions.append({'seq':e['seq'],'id':fid,'cycle':now,'action':'drop_full'});continue
   occupied+=len(b);high=max(high,occupied);q.append(e);high_slots=max(high_slots,len(q)+(inflight is not None));actions.append({'seq':e['seq'],'id':fid,'cycle':now,'action':'enqueue','queue_bytes':occupied});service()
  elif kind=='served':
   if inflight is not e:raise AssertionError('unexpected service')
   inflight=None;occupied-=len(e['body']);fid=e['id'];typ=e['type'];b=e['body']
   if fid in drop_ids:service();continue
   if typ=='B':
    if active is not None or pending is not None:drop(fid,'busy_begin_at_service')
    else:
     if len(b)!=17:raise ValueError('begin length')
     active={'id':fid,'length':int.from_bytes(b[9:13],'big'),'expected_crc':int.from_bytes(b[13:17],'big'),'bytes':0,'crc':0}
   elif typ=='D':
    if active is None or active['id']!=fid:drop(fid,'data_without_begin')
    else:
     off=int.from_bytes(b[9:13],'big');n=int.from_bytes(b[13:15],'big');payload=b[15:]
     if n!=len(payload) or off!=active['bytes'] or active['bytes']+n>active['length']:raise ValueError('bad data order/length')
     active['bytes']+=n;active['crc']=zlib.crc32(payload,active['crc'])
   elif typ=='C':
    if active is None or active['id']!=fid:drop(fid,'commit_without_begin')
    else:
     if active['bytes']!=active['length'] or active['crc']!=active['expected_crc']:raise ValueError('commit CRC/length')
     last_crc[fid]=active['crc'];active=None;pending=fid;busy_until=now+release_cycles;put(busy_until,'present',fid)
   else:
    if active is None or active['id']!=fid:drop(fid,'abort_without_begin')
    else:drop(fid,'recorded_guest_abort')
   service()
  else:
   if pending!=e:raise ValueError('presentation mismatch')
   fid=e;pending=None;front=fid
   capture=fid*PERIOD_NUM//PERIOD_DEN
   completed.append({'id':fid,'present_cycle':now,'synthetic_capture_cycle':capture,'model_age_ms':(now-capture)/100000,'crc32':f'{last_crc[fid]:08x}'})
   service()
 if q or inflight is not None or active is not None or pending is not None or occupied!=0:raise ValueError('unfinished')
 if {x['id'] for x in completed}|drop_ids!={0,1,2}:raise ValueError('frame accounting')
 return {'release_cycles':release_cycles,'service_us_per_kib_assumed':service_us_per_kib,'event_fifo_capacity_bytes':capacity,'event_fifo_highwater_bytes':high,'event_fifo_highwater_slots':high_slots,'presented':completed,'dropped':drops,'actions':actions}

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path);a=p.parse_args();events=assign(load_events())
 result={'scope':'offline synthetic producer and Python sink model; not live guest, RTL or hardware','cycles_hz':100000000,'nominal_capture_hz':30,'data_spacing_ms':1.2,'first_data_delay_ms':1.0,'queue':'five 1039-byte event slots, in-flight included; file/producer storage excluded',
 'next_fourth_frame_cycle':3*PERIOD_NUM//PERIOD_DEN,'last_captured_event_cycle':events[-1]['at'],
 'cases':{'sampled_max_release':simulate(events,3397969),'zero_release_control':simulate(events,0)}}
 a.output.write_text(json.dumps(result,indent=2)+'\n')
 for name,c in result['cases'].items():print('MODEL_CASE',name,'presented',[x['id'] for x in c['presented']],'dropped',[(x['id'],x['reason']) for x in c['dropped']],'fifo',c['event_fifo_highwater_bytes'])
if __name__=='__main__':main()
