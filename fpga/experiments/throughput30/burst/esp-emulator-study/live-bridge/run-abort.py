#!/usr/bin/env python3
"""Run a fresh bounded localhost bridge test with corrupt-final abort."""
import hashlib,json,shutil,signal,subprocess,sys,time
from pathlib import Path
if len(sys.argv)!=7:raise SystemExit('usage: run-abort.py NEW_WORK_DIR EMULATOR GUEST_ELF GUEST_FLASH FIXTURE_TRACE RTL_BINARY')
w,emu,elf,flash,trace,rtl=map(lambda s:Path(s).resolve(),sys.argv[1:]);here=Path(__file__).resolve().parent
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for path,want in [(elf,'9b336a4068935c8356c1e6fd18e047825ac9c5a9b51bb88025e07eeee30a4411'),(flash,'bd60742d8f5fab47d32435728193fe877a52d2637f1b725651d92daca3d0f2c2'),(trace,'a8ff3d87e165247637d97fd2b56414f54943337ff7cb11102aa73cba26f26e05')]:
 if digest(path)!=want:raise SystemExit(f'hash mismatch: {path}')
w.mkdir(parents=True,exist_ok=False);(w/'dumps').mkdir()
for src,name in [(elf,'guest.elf'),(flash,'guest-flash.bin'),(trace,'fixture.trace')]:shutil.copyfile(src,w/name)
with (w/'adapter.log').open('x') as log:
 p=subprocess.Popen([sys.executable,'-u',str(here/'adapter-abort.py'),str(w),str(emu)],stdout=log,stderr=subprocess.STDOUT)
 try:
  deadline=time.monotonic()+30
  while time.monotonic()<deadline:
   if 'BRIDGE_LISTENING' in (w/'adapter.log').read_text():break
   if p.poll() is not None:raise RuntimeError('adapter exited before listen')
   time.sleep(.1)
  else:raise TimeoutError('adapter did not listen')
  with (w/'rtl.log').open('x') as f:
   r=subprocess.run([str(rtl),f'+DUMP_DIR={w}/dumps','+FINISH_AFTER_ABORT=1'],stdout=f,stderr=subprocess.STDOUT,timeout=400)
  if r.returncode!=0 or 'TEST_PASS_LIVE_ABORT' not in (w/'rtl.log').read_text():raise RuntimeError('RTL did not pass abort')
  if p.wait(timeout=30)!=0 or 'ADAPTER_ABORT_PASS' not in (w/'adapter.log').read_text():raise RuntimeError('adapter did not pass')
  with (w/'event-audit.log').open('x') as f:subprocess.run([sys.executable,str(here/'check-abort.py'),str(w/'fixture.trace'),str(w)],stdout=f,stderr=subprocess.STDOUT,check=True,timeout=30)
  manifest={name:digest(w/name) for name in ('guest.elf','guest-flash.bin','fixture.trace','guest.log','adapter.log','adapter-events.jsonl','rtl.log','event-audit.log')}
  manifest['rtl_binary_sha256']=digest(rtl);(w/'sha256.json').write_text(json.dumps(manifest,indent=2)+'\n')
  print('LIVE_BRIDGE_ABORT_WRAPPER_PASS accepted_packets=25 bytes=25600 no_publication')
 finally:
  if p.poll() is None:
   p.send_signal(signal.SIGINT)
   try:p.wait(timeout=10)
   except subprocess.TimeoutExpired:p.kill();p.wait()
