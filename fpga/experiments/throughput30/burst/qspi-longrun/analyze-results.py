#!/usr/bin/env python3
"""Summarize checked QSPI run; don't treat an incomplete/failed run as PASS."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('run_dir',type=Path)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
root=a.run_dir;checked=root/'checked'
text=(checked/'simulation.log').read_text()
rows=[json.loads(x) for x in (checked/'verified.jsonl').read_text().splitlines()]
if not rows: raise SystemExit('no verified frames')
if [x['frame_id'] for x in rows]!=list(range(1,len(rows)+1)):raise ValueError('noncontiguous checked frames')
required={'arrival_cycle','commit_cycle','present_cycle','arrival_to_present_cycles','writes','bursts','underruns','rtl_dump_sha256','jpeg_sha256','cmodel_exact_pixels'}
for row in rows:
 if not required.issubset(row):raise ValueError('incomplete frame record')
 if row['writes']!=345600 or row['cmodel_exact_pixels']!=345600 or row['underruns']!=0:raise ValueError('incorrect frame counters')
 if row['present_cycle']-row['arrival_cycle'] != row['arrival_to_present_cycles']:raise ValueError('incorrect frame age')
if len({x['jpeg_sha256'] for x in rows})!=len(rows):raise ValueError('repeated input JPEG hash')
summary_path=checked/'summary.json';summary=json.loads(summary_path.read_text()) if summary_path.is_file() else None
marker=bool(re.search(r'^TEST_PASS_JPEG720_60S frames=1800\b',text,re.M))
fatal=bool(re.search(r'%Fatal|^FATAL:',text,re.M))
epoch=rows[0]['arrival_cycle'];end=epoch+6000000000
w=summary.get('window',{}) if summary else {}
pass_strict=bool(summary and summary.get('pass_marker') and summary.get('frames')==1800 and w.get('strict')==1 and w.get('elapsed_cycles')==6000000000 and w.get('epoch')==epoch and w.get('end')==end and marker and not fatal and len(rows)==1800 and rows[-1]['present_cycle']<=end)
ages=sorted(x['arrival_to_present_cycles'] for x in rows)
def percentile(q):return ages[math.ceil(q*len(ages))-1]/100000
intervals=[b['present_cycle']-a['present_cycle'] for a,b in zip(rows,rows[1:])]
within=sum(epoch<x['present_cycle']<=end for x in rows)
persec=[sum(epoch+i*100000000<x['present_cycle']<=epoch+(i+1)*100000000 for x in rows) for i in range(60)]
wrap=next((x['frame_id'] for x in rows if x['present_cycle']>=2**32),None)
result={'status':'PASS_STRICT' if pass_strict else ('FAIL_STRICT' if fatal else 'INCOMPLETE'),
        'input':'1800 distinct synthetic 720x480 JPEGs, QSPI RTL, abstract instant-availability one-slot queue; no ESP32, Wi-Fi, host capture, or physical timings',
        'scope':'verilator behavioral; related C decoder pixel comparison, SDRAM readback, LCD swap/underrun; LCD output pixels not individually checked',
        'verified_frames':len(rows),'distinct_jpeg_hashes':len({x['jpeg_sha256'] for x in rows}),'verified_pixels':sum(x['cmodel_exact_pixels'] for x in rows),
        'pass_marker':marker,'fatal_seen':fatal,'summary_present':summary is not None,'capture_epoch_cycle':epoch,'strict_window_end_cycle':end,
        'within_strict_window':within,'final_present_cycle':rows[-1]['present_cycle'],'final_window_offset_ms':(rows[-1]['present_cycle']-end)/100000 if len(rows)==1800 else None,
        'presentation_fps_first_to_last':((len(rows)-1)*1e8/(rows[-1]['present_cycle']-rows[0]['present_cycle'])) if len(rows)>1 else None,
        'fps_60s_capture_window':within/60 if len(rows)==1800 else None,'age_ms_p50':percentile(.5),'age_ms_p95':percentile(.95),'age_ms_p99':percentile(.99),'age_ms_max':ages[-1]/100000,
        'frames_above_nominal_33_333ms_age':sum(x['arrival_to_present_cycles']>10000000//3 for x in rows),
        'max_upload_ms':max(x['upload_cycles'] for x in rows)/100000,
        'interval_cycle_histogram':dict(sorted(Counter(intervals).items())),
        'frames_per_second_capture_aligned_histogram':dict(sorted(Counter(persec).items())) if len(rows)==1800 else None,
        'first_frame_above_u32_cycle':wrap,'verified_jsonl_sha256':hashlib.sha256((checked/'verified.jsonl').read_bytes()).hexdigest(),
        'simulation_log_sha256':hashlib.sha256((checked/'simulation.log').read_bytes()).hexdigest()}
a.output.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
if not pass_strict:raise SystemExit(1)
