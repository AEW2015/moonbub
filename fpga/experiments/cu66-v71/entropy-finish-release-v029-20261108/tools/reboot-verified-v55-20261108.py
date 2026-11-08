from pathlib import Path
import sys,hashlib,json,time,importlib.util
r=Path('C:/moon/dev/evidence/v55-v029-hardware-20261108-run01')
receipt=json.loads((r/'recovery-v55.json').read_text())
assert receipt['result']=='VERIFIED_NO_REBOOT' and receipt['dfu_preserved'] and receipt['partition_table_preserved']
spec=importlib.util.spec_from_file_location('normal_reboot','C:/moon/publish/host/lab-selftest-v1/normal-reboot-v1/normal_reboot.py');n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)
d=n.library();plan=json.loads(Path('C:/moon/dev/evidence/dfu-v48-offline-update-plans-20261108-v001/v55-plan.json').read_text());old,regions=d.checked_backup(plan['backup_path'])
assert receipt['factory_sha256']==plan['expected_factory_sha256'] and receipt['new_bin_sha256']==plan['new_bin_sha256']
j=d.Journal(r/'normal-reboot.events.jsonl');b=None
try:
 b=d.UsbBackend(Path('C:/msys64/ucrt64/bin/libusb-1.0.dll'));io=n.ReadOnlyTransport(b,time.monotonic,time.monotonic()+60);c=d.Client(io,journal=j)
 assert c.info()==plan['identity'] and c.status()[1]==0 and not c.status()[3]
 assert d.sha(c.read(d.FACTORY,d.FACTORY_SIZE))==plan['expected_factory_sha256']
 assert c.read(d.DFU,d.DFU_SIZE)==regions['dfu'] and c.read(d.PARTITION_TABLE,d.PARTITION_SIZE)==regions['partition']
 c.event('normal_reboot_intent',sync=True,recovery_receipt_sha256=d.sha((r/'recovery-v55.json').read_bytes()),request=1,value=1,index=0)
 io.armed=True
 answer=io.control(1,1,0,out=True)
 result={'request_sent_once':True,'transport_return':int(answer),'reset_verified':False,'post_reboot_ELF_verified':False,'flash_writes':False}
 with (r/'normal-reboot.json').open('x') as f:json.dump(result,f,indent=2)
 print(json.dumps(result),flush=True)
finally:
 if b is not None:b.close()
 j.close()
