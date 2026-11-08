from pathlib import Path
import json,time,re,os
r=Path('C:/moon/dev/evidence/v57-v029-hardware-20261108-run01');raw=r/'usb01/serial.raw';command=r/'usb-command.txt';steps=[]
def send(value,needle,seconds=15):
 assert not command.exists();start=len(raw.read_bytes());tmp=r/'command.pending';assert not tmp.exists();tmp.write_text(value,encoding='ascii');os.replace(tmp,command)
 deadline=time.monotonic()+seconds
 while time.monotonic()<deadline:
  data=raw.read_bytes()[start:].decode(errors='replace')
  if needle in data:
   steps.append({'command':value,'observed':data});return data
  time.sleep(.1)
 raise RuntimeError('No matching completion for '+value+'; never retry automatically')
send('?','sdk_elf_sha256=c2f4fbef591d85409aed7908e90ab132f1b4348c72379881fd1067dc66fc8ae0')
send('I','USB_CU66_HUD12 complete=true result=Ok(',30)
send('v','Screen enter: Game')
send('(','USB_LCD_PREP enabled=false applied=true FPGA_write=false')
memory=send('?','sdk_elf_sha256=c2f4fbef591d85409aed7908e90ab132f1b4348c72379881fd1067dc66fc8ae0')
m=re.search(r'p=memory free=(\d+) largest=(\d+)',memory);assert m and int(m[1])>=170000 and int(m[2])>=24576
send('!MBLAB1 57aa000000000001 HOST33','MBLAB1 nonce=57aa000000000001 action=HOST33 result=OK')
(r/'runtime-preconditions.json').write_text(json.dumps({'firmware_identity_verified':True,'CPU12_pass':True,'steps':steps,'free':int(m[1]),'largest':int(m[2]),'HOST33_confirmed':True,'LCD_sleep':True},indent=2))
print(json.dumps({'status':'RUNTIME_PRECONDITIONS_PASS','free':int(m[1]),'largest':int(m[2])}),flush=True)
