"""One bounded, source-pinned physical read-only updater probe; no reset or mutation."""
from pathlib import Path
import hashlib, json, subprocess, sys, time

p=Path(__file__).resolve().parent
client=Path('C:/moon/publish/host/lab-selftest-v1/dfu_vendor.py')
current=Path('C:/moon/publish/firmware/experiments/v48-dy71-selftest-control-20261107/release-selftest-control-v001/moonshine-rev4.bin')
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert sha(client)=='51c5d10579f369fb236e4341492bb81feae3cc02e43d98afd0afd95cc22275e6'
assert sha(current)=='852bfca679a72ef1cdf20e55df22c3bc9cd22d7c184cfaa4c951591df37b1217'
cmd=[sys.executable,str(client),'--libusb-dll','C:/msys64/ucrt64/bin/libusb-1.0.dll','probe','--current-bin',str(current),'--current-sha256',sha(current),'--output',str(p/'probe.json')]
with (p/'launch.json').open('x') as f:
    json.dump({'command':cmd,'client_sha256':sha(client),'current_bin_sha256':sha(current),'timeout_s':90,'flash_writes':False,'reset':False,'retry':False},f,indent=2)
t=time.monotonic()
record={}
try:
    with (p/'stdout.log').open('x') as out,(p/'stderr.log').open('x') as err:
        result=subprocess.run(cmd,stdout=out,stderr=err,timeout=90)
    record={'returncode':result.returncode,'timeout':False}
except subprocess.TimeoutExpired:
    record={'returncode':None,'timeout':True}
finally:
    record.update(seconds=time.monotonic()-t,client_unchanged=sha(client)=='51c5d10579f369fb236e4341492bb81feae3cc02e43d98afd0afd95cc22275e6',flash_writes=False,reset=False,retry=False)
    with (p/'execution.json').open('x') as f:json.dump(record,f,indent=2)
print(json.dumps(record),flush=True)
assert record['returncode']==0 and not record['timeout'] and record['client_unchanged']
