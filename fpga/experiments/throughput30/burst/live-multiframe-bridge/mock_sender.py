#!/usr/bin/env python3
"""Independent synthetic three-frame mock; not emulated firmware."""
import argparse,socket,struct,zlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('fixtures',type=Path);p.add_argument('--port',type=int,default=15537);a=p.parse_args()
seq=0
with socket.socket() as server:
 server.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);server.settimeout(120);server.bind(('127.0.0.1',a.port));server.listen(1);print('MOCK_LISTENING',flush=True)
 conn,_=server.accept()
 with conn:
  conn.settimeout(120)
  def send(body,seq):
   conn.sendall(struct.pack('!I',len(body))+body);ack=b''
   while len(ack)<5:
    part=conn.recv(5-len(ack))
    if not part:raise RuntimeError('peer disconnected')
    ack+=part
   if ack!=struct.pack('!BI',0,seq):raise RuntimeError(f'bad ack seq={seq} {ack.hex()}')
  for fid in (0,1,2):
   data=(a.fixtures/f'{fid:04}.jpg').read_bytes();crc=zlib.crc32(data)
   send(struct.pack('!cIIII',b'B',seq,fid,len(data),crc),seq);seq+=1
   for offset in range(0,len(data),1024):
    if fid==1 and offset+1024>=len(data):break
    payload=data[offset:offset+1024];send(struct.pack('!cIIIH',b'D',seq,fid,offset,len(payload))+payload,seq);seq+=1
   send(struct.pack('!cII',b'A' if fid==1 else b'C',seq,fid),seq);seq+=1
print('MOCK_MULTIFRAME_PASS',seq,'events')
