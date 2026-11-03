#!/usr/bin/env python3
"""Validate and export two trace-timed ordered MSV1 frames for RTL stimulus."""
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5];sys.path.insert(0,str(ROOT/'host'))
from moonshine.protocol import packets,parse_packet,Reassembler
p=argparse.ArgumentParser();p.add_argument('--fixtures',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
trace=ROOT/'fpga/experiments/throughput30/burst/network-rtl-study/results-clean/packet-trace.jsonl'
rows=[x for x in map(json.loads,trace.read_text().splitlines()) if x['id'] in (0,1)]
r=Reassembler();maps={};jpegs={};completed=[]
for row in rows:
 fid=row['id']
 if fid not in maps:
  jpegs[fid]=(a.fixtures/f'{fid:04}.jpg').read_bytes()
  maps[fid]={parse_packet(x).offset:x for x in packets(jpegs[fid],fid,row['capture_cycle']//100)}
 raw=maps[fid][row['offset']]
 if hashlib.sha256(raw).hexdigest()!=row['datagram_sha256'] or len(parse_packet(raw).payload)!=row['payload_bytes']:raise ValueError('packet mismatch')
 done=r.accept(raw)
 if done is not None:
  if done[1]!=jpegs[fid]:raise ValueError('frame mismatch')
  completed.append(fid)
if completed!=[0,1] or len(rows)!=sum(len(x) for x in maps.values()):raise ValueError('incomplete trace')
a.output.write_text(str(len(rows))+'\n'+''.join(f"{e['id']} {e['arrival_cycle']} {e['offset']} {e['payload_bytes']}\n" for e in rows))
print('TWO_FRAME_TRACE_PASS',len(rows),'packets, CRC/reference correct before injected loss')
