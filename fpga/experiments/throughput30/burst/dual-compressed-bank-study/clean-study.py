#!/usr/bin/env python3
"""New clean synthetic three-frame workload; not the captured guest events."""
import argparse,hashlib,json,struct,zlib
from pathlib import Path
import model
source=model.source
ROOT=Path(__file__).resolve().parents[5]
import sys
sys.path.insert(0,str(ROOT/'host'))
from moonshine.protocol import packets,parse_packet

def make(fixtures):
 manifest=json.loads((HERE.parent/'network-rtl-study/results-clean/trace-manifest.json').read_text())
 expected={x['id']:x for x in manifest['complete']};out=[];seq=0;fixture_info=[]
 for fid in range(3):
  data=(fixtures/f'{fid:04}.jpg').read_bytes();sha=hashlib.sha256(data).hexdigest()
  if sha!=expected[fid]['jpeg_sha256'] or len(data)!=expected[fid]['jpeg_bytes']:raise ValueError('fixture hash/length mismatch')
  crc=zlib.crc32(data);fixture_info.append({'id':fid,'bytes':len(data),'sha256':sha,'crc32':f'{crc:08x}'})
  def add(kind,body):
   nonlocal seq
   raw=kind.encode()+struct.pack('>II',seq,fid)+body;out.append({'seq':seq,'id':fid,'type':kind,'body':raw});seq+=1
  add('B',struct.pack('>II',len(data),crc))
  for packet in packets(data,fid,(fid*source.PERIOD_NUM//source.PERIOD_DEN)//100):
   h=parse_packet(packet)
   if h.frame_id!=fid or h.frame_len!=len(data) or h.crc32!=crc:raise ValueError('packetizer metadata')
   add('D',struct.pack('>IH',h.offset,len(h.payload))+h.payload)
  add('C',b'')
 if len(out)!=85:raise ValueError('unexpected workload count')
 return out,fixture_info

HERE=Path(__file__).resolve().parent

def run(fixtures):
 raw,info=make(fixtures);events=source.assign(raw)
 scenarios=[('zero_release',0,200),('20ms_release',2000000,200),('sampled_max_release',3397969,200),('50ms_release',5000000,200),('slow_service_stress',3397969,2000)]
 cases={}
 for name,release,service in scenarios:
  cases[name]={'release_cycles':release,'service_us_per_kib_assumed':service,
   'one_bank':source.simulate(events,release,service_us_per_kib=service),
   'two_bank_32KiB':model.two_bank(events,release_cycles=release,service_us_per_kib=service,record_details=True)}
 return {'scope':'new fixture-generated clean synthetic workload; no guest, FPGA, firmware or hardware execution',
  'fixture_info':info,'events':len(events),'producer_events_sha256':hashlib.sha256(b''.join(struct.pack('>I',len(x['body']))+x['body'] for x in raw)).hexdigest(),'data_spacing_ms':1.2,'first_data_delay_ms':1.0,'nominal_capture_hz':30,
  'last_captured_event_cycle':events[-1]['at'],'next_fourth_frame_cycle':3*source.PERIOD_NUM//source.PERIOD_DEN,'cases':cases}

def main():
 p=argparse.ArgumentParser();p.add_argument('--fixtures',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 r=run(a.fixtures);a.output.write_text(json.dumps(r,indent=2)+'\n')
 for name,c in r['cases'].items():
  print(name,*[label+' present='+str([x['id'] for x in c[label]['presented']])+' drop='+str([(x['id'],x['reason']) for x in c[label]['dropped']]) for label in ('one_bank','two_bank_32KiB')])
if __name__=='__main__':main()
