#!/usr/bin/env python3
"""Run a fresh localhost-only live guest/RTL proof with exact pixel checking."""
import hashlib,json,shutil,signal,subprocess,sys,time
from pathlib import Path
if len(sys.argv)!=8:raise SystemExit('usage: run.py NEW_WORK_DIR EMULATOR GUEST_ELF GUEST_FLASH FIXTURE_TRACE RTL_BINARY FIXTURE_DIR')
w,emu,elf,flash,trace,rtl,fixtures=map(lambda s:Path(s).resolve(),sys.argv[1:]);here=Path(__file__).resolve().parent
root=here.parents[5];burst=root/'fpga/experiments/throughput30/burst';cmodel=fixtures.parent/'cmodel';jpeg=fixtures/'0000.jpg'
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
for path,want in [(elf,'9018eec674635439907d9ef0b46bb739c04702afcd8cb014f5e2d8bef208cff4'),(flash,'873b9c86536dcf19e1bf0a6dad3f182014675b9e232606a6d9bb3b84ee2ec2bd'),(trace,'a8ff3d87e165247637d97fd2b56414f54943337ff7cb11102aa73cba26f26e05'),(jpeg,'8cc99ea7d50d1d20255e41ff7247b0770b3349e705c27152a41817418ce5c9de')]:
 if digest(path)!=want:raise SystemExit(f'hash mismatch: {path}')
w.mkdir(parents=True,exist_ok=False);(w/'dumps').mkdir()
for src,name in [(elf,'guest.elf'),(flash,'guest-flash.bin'),(trace,'fixture.trace')]:shutil.copyfile(src,w/name)
with (w/'adapter.log').open('x') as log:
 p=subprocess.Popen([sys.executable,'-u',str(here/'adapter.py'),str(w),str(emu)],stdout=log,stderr=subprocess.STDOUT)
 try:
  deadline=time.monotonic()+30
  while time.monotonic()<deadline:
   if 'BRIDGE_LISTENING' in (w/'adapter.log').read_text():break
   if p.poll() is not None:raise RuntimeError('adapter exited before listen')
   time.sleep(.1)
  else:raise TimeoutError('adapter did not listen')
  with (w/'rtl.log').open('x') as f:
   r=subprocess.run([str(rtl),f'+DUMP_DIR={w}/dumps'],stdout=f,stderr=subprocess.STDOUT,timeout=400)
  if r.returncode!=0 or 'TEST_PASS_LIVE_QSPI' not in (w/'rtl.log').read_text():raise RuntimeError('RTL did not pass')
  if p.wait(timeout=30)!=0 or 'ADAPTER_PASS' not in (w/'adapter.log').read_text():raise RuntimeError('adapter did not pass')
  with (w/'event-audit.log').open('x') as f:
   subprocess.run([sys.executable,str(here/'check-events.py'),str(w/'fixture.trace'),str(w)],stdout=f,stderr=subprocess.STDOUT,check=True,timeout=30)
  with (w/'cmodel.log').open('x') as f:
   subprocess.run([str(cmodel),str(jpeg),str(w/'cmodel.ppm')],stdout=f,stderr=subprocess.STDOUT,check=True,timeout=60)
  with (w/'comparison.json').open('x') as f:
   subprocess.run([sys.executable,str(burst/'compare-frame.py'),str(w/'cmodel.ppm'),str(w/'dumps/live-rgb565.txt'),'--exact'],stdout=f,stderr=subprocess.PIPE,check=True,timeout=60)
  result=json.loads((w/'comparison.json').read_text())
  if result.get('pixels')!=345600 or result.get('exact_rgb565_pixels')!=345600:raise RuntimeError('pixel count mismatch')
  manifest={name:digest(w/name) for name in ('guest.elf','guest-flash.bin','fixture.trace','guest.log','adapter.log','adapter-events.jsonl','rtl.log','comparison.json','dumps/live-rgb565.txt')}
  manifest.update({'rtl_binary_sha256':digest(rtl),'cmodel_sha256':digest(cmodel),'jpeg_sha256':digest(jpeg)})
  (w/'sha256.json').write_text(json.dumps(manifest,indent=2)+'\n')
  print('LIVE_BRIDGE_WRAPPER_PASS packets=26 bytes=26159 exact_pixels=345600')
 finally:
  if p.poll() is None:
   p.send_signal(signal.SIGINT)
   try:p.wait(timeout=10)
   except subprocess.TimeoutExpired:p.kill();p.wait()
