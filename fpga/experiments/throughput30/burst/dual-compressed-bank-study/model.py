#!/usr/bin/env python3
"""Synthetic dual compressed-bank ownership model; no FPGA or target execution."""
import argparse,collections,hashlib,heapq,importlib.util,json,zlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;SOURCE=HERE.parent/'scheduled-30hz-model/model.py'
spec=importlib.util.spec_from_file_location('onebank30',SOURCE);source=importlib.util.module_from_spec(spec);spec.loader.exec_module(source)

def two_bank(events,release_cycles=3397969,service_us_per_kib=200,bank_bytes=32768,record_details=False):
 if release_cycles<0 or service_us_per_kib<1 or bank_bytes<1:raise ValueError('bad parameter')
 banks=[{'state':'FREE'},{'state':'FREE'}];q=collections.deque();occ=0;high=0;highslots=0;inflight=None
 receiving=None;decoder=None;completed=[];drops=[];drop_ids=set();actions=[];bank_events=[];overlap_receives=[];events_heap=[];serial=0;now=0;ready_order=[]
 def put(t,kind,item):
  nonlocal serial
  serial+=1;heapq.heappush(events_heap,(t,serial,kind,item))
 for e in events:put(e['at'],'arrival',e)
 def drop(fid,reason):
  nonlocal q,occ,receiving
  if fid in drop_ids:return
  drop_ids.add(fid);drops.append({'id':fid,'reason':reason,'cycle':now})
  kept=collections.deque()
  while q:
   e=q.popleft()
   if e['id']==fid:occ-=len(e['body'])
   else:kept.append(e)
  q=kept
  if receiving is not None and banks[receiving].get('id')==fid:
   bank_events.append({'event':'receive_abort','id':fid,'bank':receiving,'cycle':now,'reason':reason});banks[receiving]={'state':'FREE'};receiving=None
 def service():
  nonlocal inflight
  if inflight is not None or not q:return
  e=q.popleft();inflight=e;payload=len(e['body'])-15 if e['type']=='D' else 0
  duration=max(1,(payload*service_us_per_kib*100+1023)//1024) if payload else 2000
  put(now+duration,'served',e)
 def start_decode():
  nonlocal decoder
  if decoder is None and ready_order:
   slot=ready_order.pop(0)
   if banks[slot]['state']!='READY':raise ValueError('bank state')
   banks[slot]['state']='PRESENTING';decoder=slot;bank_events.append({'event':'decode_start','id':banks[slot]['id'],'bank':slot,'cycle':now});put(now+release_cycles,'present',slot)
 while events_heap:
  now,_,kind,e=heapq.heappop(events_heap)
  if kind=='arrival':
   fid=e['id'];typ=e['type'];body=e['body']
   if fid in drop_ids:actions.append({'seq':e['seq'],'id':fid,'cycle':now,'action':'discard_dropped'});continue
   if typ=='B' and (receiving is not None or not any(x['state']=='FREE' for x in banks)):
    drop(fid,'no_free_bank');actions.append({'seq':e['seq'],'id':fid,'cycle':now,'action':'drop_busy'});continue
   if len(q)+(inflight is not None)>=5 or occ+len(body)>5*1039:
    drop(fid,'queue_full');actions.append({'seq':e['seq'],'id':fid,'cycle':now,'action':'drop_full'});continue
   occ+=len(body);high=max(high,occ);q.append(e);highslots=max(highslots,len(q)+(inflight is not None));actions.append({'seq':e['seq'],'id':fid,'cycle':now,'action':'enqueue','queue_bytes':occ});service()
  elif kind=='served':
   if inflight is not e:raise AssertionError('service')
   inflight=None;occ-=len(e['body']);fid=e['id'];typ=e['type'];b=e['body']
   if fid in drop_ids:service();continue
   if typ=='B':
    if len(b)!=17:raise ValueError('B length')
    if receiving is not None:drop(fid,'begin_while_receiving')
    else:
     free=[i for i,x in enumerate(banks) if x['state']=='FREE']
     length=int.from_bytes(b[9:13],'big')
     if not free:drop(fid,'no_free_bank_at_service')
     elif length<1 or length>bank_bytes:drop(fid,'oversized_frame')
     else:
      receiving=free[0];banks[receiving]={'state':'RECEIVING','id':fid,'length':length,'expected_crc':int.from_bytes(b[13:17],'big'),'bytes':0,'crc':0};bank_events.append({'event':'receive_begin','id':fid,'bank':receiving,'cycle':now});
      if decoder is not None:overlap_receives.append({'receiving_id':fid,'receiving_bank':receiving,'presenting_id':banks[decoder]['id'],'presenting_bank':decoder,'cycle':now})
   elif typ=='D':
    if receiving is None or banks[receiving].get('id')!=fid:drop(fid,'data_without_begin')
    else:
     bank=banks[receiving];off=int.from_bytes(b[9:13],'big');n=int.from_bytes(b[13:15],'big');payload=b[15:]
     if n!=len(payload) or off!=bank['bytes'] or bank['bytes']+n>bank['length']:raise ValueError('bad payload ordering')
     bank['bytes']+=n;bank['crc']=zlib.crc32(payload,bank['crc'])
   elif typ=='C':
    if receiving is None or banks[receiving].get('id')!=fid:drop(fid,'commit_without_begin')
    else:
     bank=banks[receiving]
     if bank['bytes']!=bank['length'] or bank['crc']!=bank['expected_crc']:raise ValueError('commit CRC/length')
     bank['state']='READY';bank_events.append({'event':'receive_commit','id':fid,'bank':receiving,'cycle':now});ready_order.append(receiving);receiving=None;start_decode()
   else:
    if receiving is None or banks[receiving].get('id')!=fid:drop(fid,'abort_without_begin')
    else:drop(fid,'recorded_guest_abort')
   service()
  else:
   slot=e
   if decoder!=slot or banks[slot]['state']!='PRESENTING':raise ValueError('present ownership')
   fid=banks[slot]['id'];capture=fid*source.PERIOD_NUM//source.PERIOD_DEN
   completed.append({'id':fid,'present_cycle':now,'synthetic_capture_cycle':capture,'model_age_ms':(now-capture)/100000,'crc32':f"{banks[slot]['crc']:08x}"})
   bank_events.append({'event':'present_and_free','id':fid,'bank':slot,'cycle':now});banks[slot]={'state':'FREE'};decoder=None;start_decode();service()
 if q or inflight is not None or receiving is not None or decoder is not None or ready_order or occ!=0 or any(x['state']!='FREE' for x in banks):raise ValueError('unfinished')
 if {x['id'] for x in completed}|drop_ids!={0,1,2}:raise ValueError('accounting')
 result={'bank_count':2,'bank_capacity_bytes':bank_bytes,'release_cycles':release_cycles,'event_fifo_highwater_bytes':high,'event_fifo_highwater_slots':highslots,'presented':completed,'dropped':drops,'actions':actions}
 if record_details:result.update(bank_events=bank_events,overlap_receives=overlap_receives)
 return result

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path);a=p.parse_args();events=source.assign(source.load_events())
 one=source.simulate(events,3397969);two=two_bank(events)
 output={'scope':'synthetic finite Python ownership simulation; no FPGA, firmware, or hardware','cases':{'one_bank':one,'two_bank_32KiB':two}}
 a.output.write_text(json.dumps(output,indent=2)+'\n')
 for name,c in output['cases'].items():print(name,'presented',[x['id'] for x in c['presented']],'dropped',[(x['id'],x['reason']) for x in c['dropped']])
if __name__=='__main__':main()
