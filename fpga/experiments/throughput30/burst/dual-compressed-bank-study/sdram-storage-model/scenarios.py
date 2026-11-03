#!/usr/bin/env python3
"""Arithmetic comparisons using isolated row-hit controller spacing."""
import json
from model import calculate

cases={}
for size in (29337,33324,262144):
 for kind in ('baseline_single','experimental_bl8'):
  for access in ('all_hit','all_switch'):
   read_cycles=15 if access=='all_hit' else 23
   if kind=='baseline_single':
    write_cycles=6 if access=='all_hit' else 14
    result=calculate(jpeg_bytes=size,scan_cycles=read_cycles,pixel_cycles=write_cycles,
                     jpeg_read_cycles=read_cycles,jpeg_write_cycles=write_cycles,
                     pixel_burst=False,jpeg_write_burst=False)
   else:
    write_cycles=13 if access=='all_hit' else 21
    result=calculate(jpeg_bytes=size,scan_cycles=read_cycles,pixel_cycles=write_cycles,
                     jpeg_read_cycles=read_cycles,jpeg_write_cycles=write_cycles)
   cases[f'{kind}_{access}_{size}']=result
print(json.dumps(cases,indent=2,sort_keys=True))
