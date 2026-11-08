from pathlib import Path
import subprocess,hashlib,json
r=Path('C:/moon/dev/evidence/v57-v029-hardware-20261108-run01')
image=Path('C:/moon/dev/experiments/v57-hud-exact-reserve-20261108/release-exact-reserve-v001/moonshine-rev4.bin')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
receipt=r/'apply-v57.json';plan=r/'v57-plan.json';journal=r/'apply-v57.json.events.jsonl'
assert json.loads(receipt.read_text())['result']=='VERIFIED_NO_REBOOT'
cmd=['python','C:/moon/publish/host/lab-selftest-v1/normal-reboot-v1/normal_reboot.py','--receipt',str(receipt),'--receipt-sha256',sha(receipt),'--plan',str(plan),'--plan-sha256',sha(plan),'--new-bin',str(image),'--new-sha256',sha(image),'--apply-journal',str(journal),'--apply-journal-sha256',sha(journal),'--expected-sdk-elf','c2f4fbef591d85409aed7908e90ab132f1b4348c72379881fd1067dc66fc8ae0','--output',str(r/'normal-reboot.json'),'--send-once']
(r/'normal-reboot-command.json').write_text(json.dumps(cmd,indent=2))
with (r/'normal-reboot-console.log').open('x') as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=120)
print(json.dumps({'returncode':p.returncode,'automatic_retry':False}));assert p.returncode==0
