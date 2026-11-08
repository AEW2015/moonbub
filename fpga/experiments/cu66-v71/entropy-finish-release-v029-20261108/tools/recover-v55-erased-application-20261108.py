"""Explicit completion after observed ERASE timeout. Never issues another ERASE."""
from pathlib import Path
import sys,json,hashlib
sys.path.insert(0,'C:/moon/publish/host/lab-selftest-v1')
import dfu_vendor as d
r=Path('C:/moon/dev/evidence/v55-v029-hardware-20261108-run01')
plan_path=Path('C:/moon/dev/evidence/dfu-v48-offline-update-plans-20261108-v001/v55-plan.json')
image_path=Path('C:/moon/publish/firmware/experiments/v55-dy71-stb1-performance-20261108/release-stb1-performance-v001/moonshine-rev4.bin')
plan=json.loads(plan_path.read_text());old,regions=d.checked_backup(plan['backup_path'])
assert plan==d.make_plan(plan['backup_path'],image_path,plan['new_bin_sha256'])
events=[json.loads(s) for s in (r/'apply-v55.json.events.jsonl').read_text().splitlines()]
headers=[e for e in events if e['event']=='before_header' and e['command'] in (d.ERASE,d.WRITE)]
assert len(headers)==1 and headers[0]['command']==d.ERASE
erase=headers[0];assert erase['length']==plan['erase_bytes'] and erase['flash_offset']==d.FACTORY
assert events[-1]['event']=='operation_failed' and events[-1]['mutation_started']
j=d.Journal(r/'recovery-v55.events.jsonl');b=None
try:
 b=d.UsbBackend(Path('C:/msys64/ucrt64/bin/libusb-1.0.dll'));c=d.Client(b,journal=j)
 assert c.info()==plan['identity']
 assert c.status()==(erase['token'],0,d.ERASE,False),'Original erase must be complete and healthy'
 # The timed-out client never consumed the successful erase IN acknowledgement.
 assert b.read(d.PACKET)==b'','Expected original ERASE completion ZLP'
 factory=c.read(d.FACTORY,d.FACTORY_SIZE)
 assert factory[:plan['erase_bytes']]==b'\xff'*plan['erase_bytes'],'Erased span not completely erased'
 assert factory[plan['erase_bytes']:]==regions['factory'][plan['erase_bytes']:],'Untouched factory tail changed'
 assert c.read(d.DFU,d.DFU_SIZE)==regions['dfu'] and c.read(d.PARTITION_TABLE,d.PARTITION_SIZE)==regions['partition']
 c.event('recovery_validated',sync=True,original_erase_token=erase['token'],erase_repeated=False,plan_sha256=d.sha(plan_path.read_bytes()))
 c.mutation_started=True
 image=d.image(image_path,plan['new_bin_sha256']);c.write(d.FACTORY,image+b'\xff'*(plan['write_bytes']-len(image)))
 observed=c.read(d.FACTORY,d.FACTORY_SIZE)
 assert observed[:len(image)]==image and d.sha(observed)==plan['expected_factory_sha256']
 assert c.read(d.DFU,d.DFU_SIZE)==regions['dfu'] and c.read(d.PARTITION_TABLE,d.PARTITION_SIZE)==regions['partition']
 result={'schema':'moonbub-explicit-erase-completion-v1','result':'VERIFIED_NO_REBOOT','plan_sha256':d.sha(plan_path.read_bytes()),'new_bin_sha256':d.sha(image),'factory_sha256':d.sha(observed),'dfu_preserved':True,'partition_table_preserved':True,'original_erase_completed':True,'erase_repeated':False,'writes_repeated':False,'automatic_retry':False}
 c.event('recovery_verified',sync=True,**result)
 with (r/'recovery-v55.json').open('x') as f:json.dump(result,f,indent=2)
 print(json.dumps(result),flush=True)
finally:
 if b is not None:b.close()
 j.close()
