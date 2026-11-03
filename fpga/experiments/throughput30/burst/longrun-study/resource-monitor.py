#!/usr/bin/env python3
"""Record host memory availability, PSI and combined memory/swap pressure."""
import argparse
import json
import os
from pathlib import Path
import time

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--pid',type=int,required=True)
p.add_argument('--output',type=Path,required=True)
p.add_argument('--interval',type=int,default=30)
a=p.parse_args()
if a.pid<=0 or a.interval<1:p.error('invalid pid or interval')
if a.output.exists():p.error('output must not already exist')
a.output.parent.mkdir(parents=True,exist_ok=True)
def start_time():
 try:
  return Path(f'/proc/{a.pid}/stat').read_text().rsplit(')',1)[1].split()[19]
 except (FileNotFoundError,IndexError):return None
initial_start=start_time()
if initial_start is None:raise SystemExit('process is not running')
with a.output.open('x',buffering=1) as out:
 while start_time()==initial_start:
  mem={}
  for line in Path('/proc/meminfo').read_text().splitlines():
   key,vals=line.split(':',1); parts=vals.split()
   if key in ('MemTotal','MemAvailable','SwapTotal','SwapFree'): mem[key]=int(parts[0])*1024
  psi={}
  for line in Path('/proc/pressure/memory').read_text().splitlines():
   fields=line.split();psi[fields[0]]={k:float(v) for k,v in (p.split('=') for p in fields[1:])}
  swap_used=mem['SwapTotal']-mem['SwapFree']; denominator=mem['MemTotal']+mem['SwapTotal']
  entry={'unix_time':time.time(),'mem_available_bytes':mem['MemAvailable'],'mem_total_bytes':mem['MemTotal'],
         'swap_used_bytes':swap_used,'swap_total_bytes':mem['SwapTotal'],
         'combined_util_using_available':(mem['MemTotal']-mem['MemAvailable']+swap_used)/denominator,
         'memory_psi':psi}
  out.write(json.dumps(entry,sort_keys=True)+'\n');out.flush();time.sleep(a.interval)
