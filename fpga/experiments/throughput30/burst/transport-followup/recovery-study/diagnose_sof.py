#!/usr/bin/env python3
"""Explain jitter-only four-slot failures; source data and seeds are synthetic."""
import argparse,json
from pathlib import Path
from study import fixture_data,simulate_link,window_receiver,parse_packet
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--fixtures',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
a=ap.parse_args();frames=fixture_data(a.fixtures);results=[]
for rate in (8_000_000,10_000_000):
 for seed in range(71,76):
  events,net=simulate_link(frames,600,rate,seed,'none',False,1200)
  if net['sender_replaced'] or net['sender_expired'] or net['lost_data']:raise RuntimeError('not a clean jitter-only delivery')
  outcome,states,forwarded=window_receiver(events,600,100)
  complete={parse_packet(packet).frame_id for packet,status in zip(forwarded,states) if status=='done'}
  failed=set(range(600))-complete;first={}
  for packet in events:first.setdefault(packet['fid'],packet['index'])
  results.append({'rate_bps':rate,'seed':seed,'failed_frame_count':len(failed),
                  'failed_with_first_packet_not_sof':sum(first.get(fid)!=0 for fid in failed),
                  'all_frames_with_first_packet_not_sof':sum(first.get(fid)!=0 for fid in range(600)),
                  'gap_timeouts':outcome['gap_timeouts'],'window_overflows':outcome['window_overflows']})
a.out.write_text(json.dumps({'scope':'jitter-only synthetic four-slot receiver; no RF/ESP32',
                             'frames_per_seed':600,'results':results},indent=2)+'\n')
for row in results:print(row)
