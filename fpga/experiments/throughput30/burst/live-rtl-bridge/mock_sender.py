#!/usr/bin/env python3
"""Independent host fixture/protocol sender; smoke test, not an ESP emulator."""
import argparse,socket,struct,zlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('jpeg',type=Path);p.add_argument('--port',type=int,default=15535);p.add_argument('--mode',choices=('normal','abort','badseq','disconnect','oversize','truncate'),default='normal');a=p.parse_args()
data=a.jpeg.read_bytes();crc=zlib.crc32(data);seq=0
with socket.socket() as server:
 server.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);server.settimeout(120);server.bind(('127.0.0.1',a.port));server.listen(1);print('MOCK_LISTENING',flush=True)
 conn,_=server.accept()
 with conn:
  conn.settimeout(120)
  def send(body,seq,status=0):
   conn.sendall(struct.pack('!I',len(body))+body);reply=b''
   while len(reply)<5:
    part=conn.recv(5-len(reply))
    if not part:raise RuntimeError('peer disconnected')
    reply+=part
   if reply!=struct.pack('!BI',status,seq):raise RuntimeError(f'bad ack {seq} {reply.hex()}')
  if a.mode=='badseq':send(struct.pack('!cIIII',b'B',1,0,len(data),crc),1,2)
  elif a.mode=='oversize':conn.sendall(struct.pack('!I',1040))
  elif a.mode=='truncate':conn.sendall(struct.pack('!I',17)+b'B\0')
  elif a.mode in ('normal','abort'):
   send(struct.pack('!cIIII',b'B',seq,0,len(data),crc),seq);seq+=1
   for offset in range(0,len(data),1024):
    if a.mode=='abort' and offset+1024>=len(data):break
    payload=data[offset:offset+1024];send(struct.pack('!cIIIH',b'D',seq,0,offset,len(payload))+payload,seq);seq+=1
   send(struct.pack('!cII',b'A' if a.mode=='abort' else b'C',seq,0),seq)
print('MOCK_SENDER_PASS mode='+a.mode,flush=True)
