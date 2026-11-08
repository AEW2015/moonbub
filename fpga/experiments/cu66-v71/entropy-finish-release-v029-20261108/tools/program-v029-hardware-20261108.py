from pathlib import Path
import json,hashlib,re,subprocess,os,time
r=Path('C:/moon/dev/evidence/v55-v029-hardware-20261108-run01');image=Path('C:/moon/builds/entropy-finish-image-v029')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
execution=json.loads((image/'execution.json').read_text());binding=json.loads((image/'binding.json').read_text())
assert execution['returncode']==0 and execution['marker'] and not execution['errors'] and execution['input_unchanged'] and execution['sources_unchanged']
assert binding['USERCODE']=='44593741' and binding['routed_slack_ns']=={'setup':0.,'hold':.008,'pulse':2.}
bit=image/'moonbub-v029-entropyfinish-rev4.1.bit';digest=sha(bit);assert execution['artifacts'][bit.name]==digest
identity=(image/'identity.tsv').read_text();assert "32'h44593741" in identity and '0x44593741' in identity and 'xc7a100tcsg324-1' in identity
raw=(r/'usb01/serial.raw').read_text(errors='replace')
assert 'sdk_elf_sha256=ef005e82d795b3ea1bdb6248901b821a7b5e78ad753de5fe0b6d2766a663976b' in raw
assert 'USB_CU66_HUD12 complete=true result=Ok(' in raw and 'hardware_access=false network_capability=false' in raw
assert 'USB_LCD_PREP enabled=false applied=true FPGA_write=false' in raw
assert 'DY71_NET ready=true' not in raw and 'USB_CU71_LOCAL requested_profile=' not in raw and 'Guru Meditation' not in raw
memory=re.findall(r'p=memory free=(\d+) largest=(\d+)',raw);assert memory and int(memory[-1][0])>=170000 and int(memory[-1][1])>=24576
old=Path('C:/moon/dev/evidence/v45-v027-network-20261107-run02/program-v027.tcl').read_text()
tcl=old.replace('C:/moon/dev/dy71-v027-20261107-v001/image01/moonbub-v027-lab.bit',bit.as_posix()).replace('4459373f','44593741').replace('V027','V029').replace('C:/moon/dev/evidence/v45-v027-network-20261107-run02',r.as_posix())
script=r/'program-v029.tcl';assert not script.exists();script.write_text(tcl)
out=r/'program01';out.mkdir();tmp=Path('C:/moon/tmp/v029-program-20261108');tmp.mkdir()
(out/'preconditions.json').write_text(json.dumps({'BIT_sha256':digest,'source_freeze_sha256':binding['source_freeze_sha256'],'user_accepted_zero_setup':True,'firmware':'ef005e82d795b3ea1bdb6248901b821a7b5e78ad753de5fe0b6d2766a663976b','raw_serial_sha256_before':sha(r/'usb01/serial.raw')},indent=2))
cmd=['C:/Xilinx/2025.2/Vivado/bin/vivado.bat','-mode','batch','-source',str(script),'-log',str(out/'vivado.log'),'-journal',str(out/'vivado.jou')]
start=time.monotonic()
with (out/'console.log').open('x') as f:p=subprocess.run(cmd,cwd=out,env=dict(os.environ,TEMP=str(tmp),TMP=str(tmp)),stdout=f,stderr=subprocess.STDOUT,timeout=180)
log=(out/'console.log').read_text(errors='replace');result={'returncode':p.returncode,'seconds':time.monotonic()-start,'errors':re.findall(r'^ERROR:.*',log,re.M),'completion_marker':any(s.strip()=='V029_PROGRAM_COMPLETE_NO_FLASH_OR_SD_WRITES' for s in log.splitlines()),'bit_unchanged':sha(bit)==digest,'BIT_sha256':digest,'volatile_only':True}
(out/'execution.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
assert p.returncode==0 and not result['errors'] and result['completion_marker'] and result['bit_unchanged']
