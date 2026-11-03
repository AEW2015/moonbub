#!/usr/bin/env python3
"""Generate timed complete-frame events via actual MSV1 packet/reference state.

Input contains ten synthetic JPEGs. This models store-and-forward full-frame
availability, not the current ESP32 streaming receiver or real Wi-Fi/QSPI.
"""
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT/'fpga/experiments/throughput30/burst/transport-followup/recovery-study'))
from study import fixture_data,simulate_link,strict_receiver,rust_compare
from moonshine.protocol import Reassembler,parse_packet,packets

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--fixtures',type=Path,required=True);p.add_argument('--rust-replay',type=Path,required=True)
 p.add_argument('--output',type=Path,required=True);p.add_argument('--seed',type=int,default=73)
 p.add_argument('--rate-bps',type=int,default=8_000_000);p.add_argument('--jitter-us',type=int,default=300)
 p.add_argument('--captures',type=int,default=10);p.add_argument('--channel',choices=('none','iid','bursty'),default='iid')
 p.add_argument('--deadline-ms',type=int,default=100)
 a=p.parse_args()
 if not 1<=a.captures<=10 or a.rate_bps<=0 or a.jitter_us<0 or a.deadline_ms<=0:p.error('invalid configuration')
 frames=fixture_data(a.fixtures)
 events,net=simulate_link(frames,a.captures,a.rate_bps,a.seed,a.channel,False,a.jitter_us)
 summary,outcomes,packet_events=strict_receiver(events,a.captures,a.deadline_ms)
 interop=rust_compare(a.rust_replay,outcomes,packet_events)
 if interop['mismatch_count']:raise RuntimeError('actual Rust Receiver disagrees with Python state')
 sink=Reassembler();complete=[];packet_rows=[];arrived_offsets=set()
 for e in events:
  if e['kind']!='data':continue
  h0=parse_packet(e['payload']);key=(h0.frame_id,h0.offset)
  if key in arrived_offsets:raise ValueError('duplicate datagram in source trace')
  arrived_offsets.add(key)
  row={'id':h0.frame_id,'offset':h0.offset,'payload_bytes':len(h0.payload),
       'capture_cycle':e['capture'],'arrival_cycle':e['at'],
       'datagram_sha256':hashlib.sha256(e['payload']).hexdigest()}
  if e['at']-e['capture']>a.deadline_ms*100_000:
   row['reference_outcome']='deadline_ignored';packet_rows.append(row);continue
  try:result=sink.accept(e['payload'])
  except ValueError:
   row['reference_outcome']='error';packet_rows.append(row);continue
  row['reference_outcome']='done' if result else 'partial';packet_rows.append(row)
  if result:
   h,jpeg=result;fid=h.frame_id
   if fid>=a.captures or jpeg!=frames[fid%10]:raise ValueError('bad reassembly')
   complete.append({'id':fid,'fixture_index':fid%10,'capture_cycle':e['capture'],
                    'complete_cycle':e['at'],'jpeg_bytes':len(jpeg),'jpeg_sha256':hashlib.sha256(jpeg).hexdigest()})
 if len(complete)!=summary['complete'] or not complete:raise RuntimeError('inconsistent or empty trace')
 if len({x['id'] for x in complete})!=len(complete):raise RuntimeError('duplicate completed ID')
 if any(a['complete_cycle']>b['complete_cycle'] for a,b in zip(complete,complete[1:])):raise RuntimeError('nonmonotonic completion')
 missing=sorted(set(range(a.captures))-{r['id'] for r in complete})
 if net['sender_replaced'] or net['sender_expired'] or net['started']!=a.captures:
  raise ValueError('packet-loss attribution requires all captured frames to be sent')
 missing_packets=[]
 for fid in range(a.captures):
  for pkt in packets(frames[fid%10],fid,(fid*10_000_000//3)//100):
   h=parse_packet(pkt)
   if (fid,h.offset) not in arrived_offsets:missing_packets.append({'id':fid,'offset':h.offset})
 if len(missing_packets)!=net['lost_data']:raise ValueError('lost packet accounting mismatch')
 a.output.mkdir(parents=True,exist_ok=True)
 packet_trace=''.join(json.dumps(r,sort_keys=True)+'\n' for r in packet_rows)
 (a.output/'packet-trace.jsonl').write_text(packet_trace)
 trace=str(len(complete))+'\n'+''.join(f"{r['id']} {r['fixture_index']} {r['capture_cycle']} {r['complete_cycle']}\n" for r in complete)
 (a.output/'frame-trace.txt').write_text(trace)
 result={'scope':'synthetic packet timing -> full-frame Python and Rust protocol reference; no ESP32 execution',
         'captures':a.captures,'frame_trace_count':len(complete),'trace_sha256':hashlib.sha256(trace.encode()).hexdigest(),
         'packet_trace_sha256':hashlib.sha256(packet_trace.encode()).hexdigest(),
         'inferred_lost_packets':missing_packets,
         'capture_hz':30,'cycle_hz':100000000,'rate_bps_l3_assumed':a.rate_bps,'seed':a.seed,
         'channel':a.channel,'jitter_us_uniform_max':a.jitter_us,'deadline_ms':a.deadline_ms,
         'network_counters':net,'reference_result':summary,'rust_comparison':interop,
         'not_reassembled_ids':missing,'complete':complete,
         'caveat':'complete-frame staging is hypothetical; CRC/CPU/OS/WiFi MAC+PHY/QSPI delivery not measured'}
 (a.output/'trace-manifest.json').write_text(json.dumps(result,indent=2)+'\n')
 print(f"TRACE_READY captures={a.captures} reassembled={len(complete)} missing={missing} rust_events={interop['packet_events']}")
if __name__=='__main__':main()
