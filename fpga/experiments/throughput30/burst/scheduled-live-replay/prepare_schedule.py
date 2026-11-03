#!/usr/bin/env python3
"""Verify recorded emulator bodies and assign explicit synthetic event times."""
import hashlib,json,struct,sys
from pathlib import Path
here=Path(__file__).resolve().parent
raw=(here/'data/guest-events.bin').read_bytes();audit=[json.loads(x) for x in (here/'data/adapter-events.jsonl').read_text().splitlines()]
if hashlib.sha256(raw).hexdigest()!='7853a8233831ff6ceb6e44fe067ea32225a76df565647e56be45b72199fc8a0d':raise SystemExit('guest capture hash mismatch')
p=0;out=[];seq=0;frame_start=0;next_data=0
while p<len(raw):
 if p+4>len(raw):raise ValueError('truncated record')
 n=struct.unpack_from('>I',raw,p)[0];p+=4
 if not 9<=n<=1039 or p+n>len(raw):raise ValueError('record bounds')
 b=raw[p:p+n];p+=n;a=audit[seq]
 if a['seq']!=seq or a['length']!=n or a['sha256']!=hashlib.sha256(b).hexdigest() or int.from_bytes(b[1:5],'big')!=seq:raise ValueError('guest audit mismatch')
 typ=chr(b[0]);fid=int.from_bytes(b[5:9],'big')
 if typ=='B':
  frame_start=100000+fid*9000000;next_data=frame_start+100000;at=frame_start
 elif typ=='D':at=next_data;next_data+=120000
 elif typ in ('A','C'):at=next_data
 else:raise ValueError('unknown event')
 if out and at<out[-1][0]:raise ValueError('nonmonotonic synthetic schedule')
 out.append((at,b));seq+=1
if seq!=84 or seq!=len(audit):raise ValueError('unexpected event count')
Path(sys.argv[1]).write_bytes(b''.join(struct.pack('>II',at,len(b))+b for at,b in out))
print('SCHEDULE_PASS',seq,'guest-captured events, 90ms frame spacing, 1.2ms DATA spacing')
