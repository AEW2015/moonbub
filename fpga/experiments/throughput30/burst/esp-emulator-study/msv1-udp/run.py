import hashlib, socket, subprocess, sys, time
from pathlib import Path
if len(sys.argv)!=3: raise SystemExit('usage: run.py WORK_DIRECTORY ESP_EMU')
root=Path(__file__).resolve().parents[6];sys.path.insert(0,str(root/'host'))
from moonshine.protocol import packets
w=Path(sys.argv[1]).resolve();emu=sys.argv[2]
cmd=[emu,'--chip','esp32s3','--firmware',str(w/'msv1-udp-flash.bin'),'--elf',str(w/'msv1-udp.elf'),'--timeout','35s','--net','user,restrict=yes,hostfwd=udp:127.0.0.1:15533-:5533','--wifi-ssid','emu-test','--wifi-auth','open','--wifi-password','','--psram-size','0']
with (w/'msv1-udp-boot.log').open('x') as f:
 p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT)
 try:
  end=time.monotonic()+25
  while time.monotonic()<end and p.poll() is None:
   if 'UDP_HARNESS_READY' in (w/'msv1-udp-boot.log').read_text(errors='replace'):break
   time.sleep(.1)
  else: raise RuntimeError('guest not ready within bound')
  sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);sock.settimeout(4)
  data=bytes([42])*2048
  for i,packet in enumerate(packets(data,42,0)):
   print('send',i,'bytes',len(packet),'sha256',hashlib.sha256(packet).hexdigest(),flush=True)
   sock.sendto(packet,('127.0.0.1',15533));resp,_=sock.recvfrom(64)
   if resp!=b'ok':raise ValueError('bad ack')
   print('ack',i,flush=True)
  end=time.monotonic()+5
  while time.monotonic()<end:
   log=(w/'msv1-udp-boot.log').read_text(errors='replace')
   if 'UDP_RECEIVER_PASS packets=2 bytes=2048 crc32=50db49b7' in log: break
   if p.poll() is not None: raise RuntimeError('emulator exited before pass marker')
   time.sleep(.1)
  else: raise RuntimeError('guest pass marker missing')
  print('host PASS',flush=True)
 finally:
  if p.poll() is None:p.terminate();p.wait(timeout=5)
