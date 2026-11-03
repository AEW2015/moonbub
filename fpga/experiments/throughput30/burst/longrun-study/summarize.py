#!/usr/bin/env python3
"""Summarize actual FRAME_RESULT records; never infer PASS from partial data."""
import argparse
import json
import math
from pathlib import Path
import re

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('log',type=Path)
p.add_argument('--expected',type=int,default=60)
a=p.parse_args()
s=a.log.read_text()
frames=[]
for line in s.splitlines():
    if line.startswith('FRAME_RESULT '):
        fields={k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',line)}
        required={'id','arrival_cycle','commit_cycle','present_cycle','arrival_to_present_cycles','writes','bursts','underruns'}
        if not required.issubset(fields): raise ValueError('incomplete FRAME_RESULT')
        frames.append(fields)
if not frames: raise SystemExit('no complete frames')
ids=[f['id'] for f in frames]
if ids!=list(range(1,len(frames)+1)): raise ValueError('frame IDs out of order or missing')
last=frames[-1]['present_cycle']; first=frames[0]['present_cycle']
interval=[b['present_cycle']-a['present_cycle'] for a,b in zip(frames,frames[1:])]
ages=sorted(f['arrival_to_present_cycles']/100000 for f in frames)
def percentile(q): return ages[max(0,math.ceil(q*len(ages))-1)]
fatal_seen=bool(re.search(r'%Fatal|^FATAL:|^Error:',s,re.M))
passed=bool(re.search(r'^TEST_PASS_JPEG720_LONGRUN ',s,re.M))
result={'expected_frames':a.expected,'observed_frames':len(frames),'pass_marker_present':passed,'fatal_seen':fatal_seen,
        'complete':len(frames)==a.expected and passed and not fatal_seen,
        'first_present_cycle':first,'last_present_cycle':last,
        'displayed_fps_first_to_last':(len(frames)-1)*100000000/(last-first) if len(frames)>1 else None,
        'age_ms_p50_nearest_rank':percentile(.50),'age_ms_p95_nearest_rank':percentile(.95),
        'age_ms_max':ages[-1], 'display_interval_ms_min': min(interval)/100000 if interval else None,
        'display_interval_ms_max': max(interval)/100000 if interval else None,
        'verified_pixel_writes':sum(f['writes'] for f in frames),'observed_underruns_max':max(f['underruns'] for f in frames),
        'model_scope':'synthetic JPEGs, functional SDRAM, hypothetical instant compressed arrivals and one-frame queue; not hardware or sustained 60-second result'}
print(json.dumps(result,indent=2))
if not result['complete']: raise SystemExit(1)
