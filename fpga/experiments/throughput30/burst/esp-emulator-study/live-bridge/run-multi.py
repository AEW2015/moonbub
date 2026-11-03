#!/usr/bin/env python3
"""Fresh live 0/abort-1/2 run with exact comparisons of both presentations."""
import hashlib,json,os,shutil,signal,subprocess,sys,time
from pathlib import Path
if len(sys.argv)!=8:raise SystemExit('usage: run-multi.py NEW_WORK_DIR EMULATOR GUEST_ELF GUEST_FLASH FIXTURE_TRACE RTL_BINARY FIXTURE_DIR')
w,emu,elf,flash,trace,rtl,fixtures=map(lambda s:Path(s).resolve(),sys.argv[1:]);here=Path(__file__).resolve().parent
root=here.parents[5];burst=root/'fpga/experiments/throughput30/burst';cmodel=fixtures.parent/'cmodel'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
inputs=[(elf,'c8f625536e14db3d4a1a3f870f87c364aba171ae3a6b9b310c86b035cf8a5748'),(flash,'fbc2405e19dcf2ff7b1963a377e9b5541532d1f1b4aef360507ab5264714285c'),(trace,'bef1ac9f645d0378849d4e3b0d6b4d7c935e309338a41c6a067891596405d372'),(fixtures/'0000.jpg','8cc99ea7d50d1d20255e41ff7247b0770b3349e705c27152a41817418ce5c9de'),(fixtures/'0001.jpg','c7db8fa330fca9bf715ad2e915dd84051b43de0e70009a8b93f181046a805fb0'),(fixtures/'0002.jpg','a76055f8d43e1b0affe2810697f0f2f795302751ab2e592c43eb83cd19cfa13e')]
for path,want in inputs:
 if digest(path)!=want:raise SystemExit(f'hash mismatch: {path}')
w.mkdir(parents=True,exist_ok=False);(w/'dumps').mkdir()
for src,name in [(elf,'guest.elf'),(flash,'guest-flash.bin'),(trace,'fixture.trace')]:shutil.copyfile(src,w/name)
with (w/'adapter.log').open('x') as log:
 p=subprocess.Popen([sys.executable,'-u',str(here/'multi-adapter.py'),str(w),str(emu)],stdout=log,stderr=subprocess.STDOUT)
 try:
  deadline=time.monotonic()+30
  while time.monotonic()<deadline:
   if 'BRIDGE_LISTENING' in (w/'adapter.log').read_text():break
   if p.poll() is not None:raise RuntimeError('adapter exited before listen')
   time.sleep(.1)
  else:raise TimeoutError('adapter did not listen')
  env=os.environ.copy();env['BRIDGE_PORT']='15536'
  with (w/'rtl.log').open('x') as f:r=subprocess.run([str(rtl),f'+DUMP_DIR={w}/dumps'],stdout=f,stderr=subprocess.STDOUT,timeout=400,env=env)
  if r.returncode!=0 or 'TEST_PASS_LIVE_MULTIFRAME' not in (w/'rtl.log').read_text():raise RuntimeError('RTL did not pass')
  if p.wait(timeout=30)!=0 or 'MULTI_ADAPTER_PASS' not in (w/'adapter.log').read_text():raise RuntimeError('adapter did not pass')
  with (w/'event-audit.log').open('x') as f:subprocess.run([sys.executable,str(here/'check-multi-events.py'),str(w/'fixture.trace'),str(w)],stdout=f,stderr=subprocess.STDOUT,check=True,timeout=30)
  for frame in (0,2):
   with (w/f'cmodel-{frame}.log').open('x') as f:subprocess.run([str(cmodel),str(fixtures/f'{frame:04}.jpg'),str(w/f'cmodel-{frame}.ppm')],stdout=f,stderr=subprocess.STDOUT,check=True,timeout=60)
   with (w/f'comparison-{frame}.json').open('x') as f:subprocess.run([sys.executable,str(burst/'compare-frame.py'),str(w/f'cmodel-{frame}.ppm'),str(w/f'dumps/frame-{frame}-rgb565.txt'),'--exact'],stdout=f,stderr=subprocess.PIPE,check=True,timeout=60)
   result=json.loads((w/f'comparison-{frame}.json').read_text())
   if result.get('pixels')!=345600 or result.get('exact_rgb565_pixels')!=345600:raise RuntimeError('pixel mismatch')
  names=('guest.elf','guest-flash.bin','fixture.trace','guest.log','adapter.log','adapter-events.jsonl','rtl.log','event-audit.log','comparison-0.json','comparison-2.json','dumps/frame-0-rgb565.txt','dumps/frame-2-rgb565.txt')
  hashes={name:digest(w/name) for name in names};hashes.update({'rtl_binary_sha256':digest(rtl),'cmodel_sha256':digest(cmodel)})
  (w/'sha256.json').write_text(json.dumps(hashes,indent=2)+'\n');print('LIVE_MULTIFRAME_WRAPPER_PASS events=84 commits=2 aborts=1 exact_pixels=691200')
 finally:
  if p.poll() is None:
   p.send_signal(signal.SIGINT)
   try:p.wait(timeout=10)
   except subprocess.TimeoutExpired:p.kill();p.wait()
