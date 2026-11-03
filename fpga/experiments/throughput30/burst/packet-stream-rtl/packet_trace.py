#!/usr/bin/env python3
"""Verify actual MSV1 datagrams and emit frame 0's incremental RTL arrivals."""
import argparse, hashlib, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT/'host'))
from moonshine.protocol import packets,parse_packet,Reassembler

def main():
 p=argparse.ArgumentParser();p.add_argument('--fixtures',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
 path=ROOT/'fpga/experiments/throughput30/burst/network-rtl-study/results-clean/packet-trace.jsonl'
 rows=[json.loads(x) for x in path.read_text().splitlines() if json.loads(x)['id']==0]
 jpeg=(a.fixtures/'0000.jpg').read_bytes();tx=list(packets(jpeg,0,0)); mapping={parse_packet(x).offset:x for x in tx}; r=Reassembler()
 if len(rows)!=len(tx):raise ValueError('missing packet')
 out=[];done=None
 for row in rows:
  raw=mapping[row['offset']];h=parse_packet(raw)
  if hashlib.sha256(raw).hexdigest()!=row['datagram_sha256'] or len(h.payload)!=row['payload_bytes']:raise ValueError('wire mismatch')
  result=r.accept(raw)
  if result is not None:done=result[1]
  out.append(f"{row['arrival_cycle']} {row['offset']} {row['payload_bytes']}")
 if done!=jpeg:raise ValueError('CRC or reassembly failed')
 a.output.write_text(str(len(out))+'\n'+'\n'.join(out)+'\n')
 print('PACKET_TRACE_PASS',len(out),'packets',len(jpeg),'bytes',hashlib.sha256(jpeg).hexdigest())
if __name__=='__main__':main()
