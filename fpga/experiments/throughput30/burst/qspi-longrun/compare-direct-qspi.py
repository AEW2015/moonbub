#!/usr/bin/env python3
"""Compare matched QSPI/direct 60s simulation records, not hardware behavior."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('direct',type=Path);p.add_argument('qspi',type=Path)
p.add_argument('--output',type=Path,required=True);a=p.parse_args()
def read(path):return [json.loads(x) for x in path.read_text().splitlines()]
direct,qspi=read(a.direct),read(a.qspi)
if len(direct)!=1800 or len(qspi)!=1800:raise ValueError('require 1800 verified frames per run')
deltas=[];out_match=0
for i,(d,q) in enumerate(zip(direct,qspi),1):
 if d['frame_id']!=i or q['frame_id']!=i or d['jpeg_sha256']!=q['jpeg_sha256'] or d['arrival_cycle']!=q['arrival_cycle']:
  raise ValueError(f'inputs or timestamps differ at frame {i}')
 if d['rtl_dump_sha256']!=q['rtl_dump_sha256']:raise ValueError(f'decoded output differs at frame {i}')
 if d['cmodel_exact_pixels']!=345600 or q['cmodel_exact_pixels']!=345600:raise ValueError('incomplete oracle comparison')
 out_match+=1;deltas.append(q['present_cycle']-d['present_cycle'])
result={'frames':len(direct),'matching_input_hashes':len(direct),'matching_output_hashes':out_match,
        'qspi_minus_direct_presentation_cycles':dict(sorted(Counter(deltas).items())),
        'input_fps':30,'core_clock_hz':100000000,
        'direct_jsonl_sha256':hashlib.sha256(a.direct.read_bytes()).hexdigest(),
        'qspi_jsonl_sha256':hashlib.sha256(a.qspi.read_bytes()).hexdigest(),
        'caveat':'Behavioral comparisons with synthetic inputs and different experimental parsers. QSPI timings are ideal digital pin model; no ESP32, radio or physical timing.'}
a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
