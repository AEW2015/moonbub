#!/usr/bin/env python3
"""Bridge guest-accepted events to RTL using loopback TCP, one event in flight."""
import hashlib,json,socket,struct,subprocess,sys,time
from pathlib import Path
if len(sys.argv)!=3:raise SystemExit('usage: adapter.py WORK_DIR ESP_EMU')
w=Path(sys.argv[1]).resolve();emu=sys.argv[2]
trace=(w/'fixture.trace').read_bytes()
if hashlib.sha256(trace).hexdigest()!='bef1ac9f645d0378849d4e3b0d6b4d7c935e309338a41c6a067891596405d372':raise SystemExit('fixture trace hash mismatch')
packets=[];pos=0
while pos<len(trace):
 if pos+2>len(trace):raise SystemExit('truncated trace length')
 n=int.from_bytes(trace[pos:pos+2],'big');pos+=2
 if not 40<=n<=1064 or pos+n>len(trace):raise SystemExit('invalid trace packet')
 packets.append(trace[pos:pos+n]);pos+=n
if len(packets)!=79:raise SystemExit('unexpected packet count')
def exact(sock,n):
 chunks=[]
 while n:
  b=sock.recv(n)
  if not b:raise ConnectionError('RTL disconnected')
  chunks.append(b);n-=len(b)
 return b''.join(chunks)
def as_event(kind,seq,frame,body=b''):return kind+struct.pack('>II',seq,frame)+body
cmd=[emu,'--chip','esp32s3','--firmware',str(w/'guest-flash.bin'),'--elf',str(w/'guest.elf'),'--timeout','300s','--net','user,restrict=yes,hostfwd=udp:127.0.0.1:15533-:5533','--wifi-ssid','emu-test','--wifi-auth','open','--wifi-password','','--psram-size','0']
with (w/'adapter-events.jsonl').open('x') as events,(w/'guest.log').open('x') as log, socket.socket() as server:
 server.bind(('127.0.0.1',15536));server.listen(1);server.settimeout(120)
 print('BRIDGE_LISTENING 127.0.0.1:15536',flush=True)
 rtl,addr=server.accept()
 if addr[0]!='127.0.0.1':raise RuntimeError('non-loopback RTL peer')
 with rtl, socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as udp:
  rtl.settimeout(240);udp.settimeout(240)
  p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
  try:
   deadline=time.monotonic()+30
   while time.monotonic()<deadline:
    if 'MULTI_GUEST_READY' in (w/'guest.log').read_text(errors='replace'):break
    if p.poll() is not None:raise RuntimeError('guest exited before ready')
    time.sleep(.1)
   else:raise TimeoutError('guest did not become ready')
   seq=0;offset=0
   def relay(expected):
    nonlocal_placeholder=None
    event,peer=udp.recvfrom(1200)
    if peer[0]!='127.0.0.1' or event!=expected:raise RuntimeError('unexpected guest event')
    if not 9<=len(event)<=1039:raise RuntimeError('invalid event length')
    this_seq=int.from_bytes(event[1:5],'big')
    rtl.sendall(struct.pack('>I',len(event))+event)
    reply=exact(rtl,5)
    if reply!=(b'\x05' if this_seq==83 else b'\x00')+this_seq.to_bytes(4,'big'):raise RuntimeError('RTL rejection or ACK mismatch')
    events.write(json.dumps({'seq':this_seq,'type':chr(event[0]),'length':len(event),'sha256':hashlib.sha256(event).hexdigest()})+'\n');events.flush()
    if this_seq!=83:udp.sendto(b'K'+this_seq.to_bytes(4,'big'),peer)
    else:print('EXPECTED_NEGATIVE_ACK seq=83 status=5 guest_commit_ack_withheld=1',flush=True)
   for i,original in enumerate(packets):
    packet=bytearray(original);frame=int.from_bytes(packet[8:12],'big');off=int.from_bytes(packet[20:24],'big');size=int.from_bytes(packet[16:20],'big');crc=int.from_bytes(packet[28:32],'big');last=bool(packet[7]&2)
    if frame not in (0,1,2) or off!=offset:raise RuntimeError('unexpected source order')
    if frame==1 and last:packet[-1]^=1
    udp.sendto(packet,('127.0.0.1',15533))
    if off==0:relay(as_event(b'B',seq,frame,struct.pack('>II',size,crc)));seq+=1
    if frame==1 and last:
     relay(as_event(b'A',seq,frame));seq+=1;offset=0;continue
    payload=packet[40:];relay(as_event(b'D',seq,frame,struct.pack('>IH',offset,len(payload))+payload));seq+=1;offset+=len(payload)
    if last:
     if offset!=size:raise RuntimeError('bad completion length')
     relay(as_event(b'C',seq,frame));seq+=1;offset=0
   if seq!=84 or offset!=0:raise RuntimeError('multi bridge totals mismatch')
   if 'MULTI_GUEST_PASS' in (w/'guest.log').read_text(errors='replace'):raise RuntimeError('guest should not receive commit success')
   print('NEGATIVE_ADAPTER_PASS events=84 negative_status=5',flush=True)
  finally:
   if p.poll() is None:p.terminate();p.wait(timeout=10)
