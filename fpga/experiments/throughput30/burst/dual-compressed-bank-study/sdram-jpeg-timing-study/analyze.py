#!/usr/bin/env python3
"""Convert one simulated stage-timing line to descriptive elapsed cycles."""
from pathlib import Path
import json,re,sys
lines=[s for s in Path(sys.argv[1]).read_text().splitlines() if s.startswith('STAGE_TIMING ')]
if len(lines)!=1:raise SystemExit('expected exactly one STAGE_TIMING line')
v={k:int(n) for k,n in re.findall(r'(\w+)=(\d+)',lines[0])}
keys=('begin','byte_first','byte_last','write_first','write_last','drained','reader_start','read_first','read_last','reader_done','pixel_first','pixel_last','present')
if set(v)!=set(keys) or any(v[k]<=0 for k in keys):raise SystemExit('incomplete event timestamps')
if not (v['begin']<=v['byte_first']<=v['byte_last']<=v['write_last']<v['drained']<v['reader_start']<=v['read_first']<=v['read_last']<=v['reader_done'] and v['pixel_first']<=v['pixel_last']<v['present']):raise SystemExit('invalid event order')
pairs={'writer_begin_to_drain':('begin','drained'),'byte_first_to_last':('byte_first','byte_last'),
 'write_first_to_last':('write_first','write_last'),'last_write_to_drain':('write_last','drained'),
 'drain_to_reader_start':('drained','reader_start'),'reader_start_to_last_input_word':('reader_start','reader_done'),
 'first_to_last_read_request':('read_first','read_last'),'first_to_last_pixel':('pixel_first','pixel_last'),
 'reader_start_to_last_pixel':('reader_start','pixel_last'),'last_pixel_to_present':('pixel_last','present'),
 'writer_begin_to_present':('begin','present')}
d={name:{'cycles':v[b]-v[a],'ms_at_100mhz':(v[b]-v[a])/100000} for name,(a,b) in pairs.items()}
print(json.dumps({'scope':'one bounded synthetic fixture and modeled phase; events overlap, no Wi-Fi/ESP32/physical latency or FPS claim',
                  'clock_hz':100000000,'event_cycles':v,'durations':d},indent=2,sort_keys=True))
