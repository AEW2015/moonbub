"""Observe this one already-running finite replay and finalize once; never rerun it."""
from pathlib import Path
import time,json,subprocess,re,sys
p=Path(__file__).resolve().parent
assert not (p/'result.json').exists()
started=time.monotonic();next_report=0
while not (p/'rust-run-result.json').exists():
    elapsed=time.monotonic()-started
    if elapsed>4500:raise SystemExit('WATCH_TIMEOUT_NO_RETRY')
    if elapsed>=next_report:
        text=(p/'native-run.log').read_text(errors='replace') if (p/'native-run.log').exists() else ''
        presented=re.findall(r'ACTUAL_FRAME_PRESENTED frame=(\d+) bank=(\d+)',text)
        print(json.dumps({'watch_seconds':round(elapsed,1),'observed_presentations':len(presented),'latest':presented[-1]if presented else None}),flush=True)
        next_report=elapsed+60
    time.sleep(5)
run=json.loads((p/'rust-run-result.json').read_text())
if run['returncode']!=0:raise SystemExit('REPLAY_FAILED_PRESERVED_NO_RETRY')
with(p/'final-check.log').open('x')as out:
    r=subprocess.run([sys.executable,str(p/'finalize.py')],stdout=out,stderr=subprocess.STDOUT,timeout=90)
print('ONE_SHOT_FINAL_CHECK_RETURN',r.returncode,flush=True)
if r.returncode:raise SystemExit(r.returncode)
print((p/'result.json').read_text(),flush=True)
