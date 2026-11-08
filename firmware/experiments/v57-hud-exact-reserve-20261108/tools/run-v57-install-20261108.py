from pathlib import Path
import subprocess,time,json
r=Path('C:/moon/dev/evidence/v57-v029-hardware-20261108-run01')
cmd=['python','C:/moon/maintenance/apply-v57-verified-plan-20261108.py'];started=time.monotonic()
with (r/'install-console.log').open('x') as f:
 p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT)
 (r/'install-launch.json').write_text(json.dumps({'pid':p.pid,'command':cmd,'started_unix_us':time.time_ns()//1000,'overall_timeout_seconds':300},indent=2))
 try:code=p.wait(timeout=300)
 except subprocess.TimeoutExpired:p.terminate();code=p.wait(timeout=10)
result={'returncode':code,'seconds':time.monotonic()-started,'automatic_retry':False,'automatic_reboot':False}
(r/'install-execution.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
assert code==0
