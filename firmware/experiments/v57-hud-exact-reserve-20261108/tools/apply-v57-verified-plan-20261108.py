"""One explicit app-only installation; 60-second bounded commands, no retry/reboot."""
from pathlib import Path
import sys,json,hashlib
sys.path.insert(0,'C:/moon/publish/host/lab-selftest-v1')
import dfu_vendor as d
r=Path('C:/moon/dev/evidence/v57-v029-hardware-20261108-run01')
candidate=Path('C:/moon/dev/experiments/v57-hud-exact-reserve-20261108')
release=candidate/'release-exact-reserve-v001'
binfile=release/'moonshine-rev4.bin';assert d.sha(binfile.read_bytes())=='38aff3d8dba66393e07df5efdf6d22536c33e0a1d9b3d50bb95717255ffdf013'
build=json.loads(Path('C:/moon/builds/v57-target-run01/result.json').read_text());assert build['returncode']==0 and not build['source_changes'] and not build['native_changes']
assert json.loads(Path('C:/moon/builds/v57-host01/source-check.json').read_text())['unchanged']
steps=json.loads(Path('C:/moon/builds/v57-host01/execution.json').read_text());assert len(steps)==28 and all(s['returncode']==0 for s in steps)
pack=json.loads((release/'verification/commands.json').read_text());assert len(pack)==6 and all(s['returncode']==0 for s in pack)
plan=r/'v57-plan.json';assert plan.is_file()
assert json.loads(plan.read_text())==d.make_plan('C:/moon/backups/DFU-V56-READONLY-20261108-v001/backup.json',binfile,'38aff3d8dba66393e07df5efdf6d22536c33e0a1d9b3d50bb95717255ffdf013')
j=d.Journal(r/'apply-v57.json.events.jsonl');b=None
try:
 j({'event':'operation_start','action':'apply','sync':True,'command_timeout_seconds':60})
 b=d.UsbBackend(Path('C:/msys64/ucrt64/bin/libusb-1.0.dll'));c=d.Client(b,timeout=60,journal=j)
 result=d.apply(c,plan,binfile,execute=True)
 with (r/'apply-v57.json').open('x') as f:json.dump(result,f,indent=2)
 print(json.dumps(result),flush=True)
finally:
 if b is not None:b.close()
 j.close()
