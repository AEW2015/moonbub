from pathlib import Path
import subprocess,os,time,json
p=Path('C:/moon/dev/experiments/stb1-v55-video12-real-rust-system-20261108');env=dict(os.environ,PATH='C:/msys64/ucrt64/bin;'+str(p)+';'+os.environ['PATH'],TEMP='C:/moon/tmp',TMP='C:/moon/tmp');t=time.monotonic()
with(p/'native-run.log').open('x')as f:r=subprocess.run([str(p/'actual-rust.exe')],stdout=f,stderr=subprocess.STDOUT,env=env,timeout=5400)
(p/'rust-run-result.json').write_text(json.dumps({'returncode':r.returncode,'wall_seconds':time.monotonic()-t},indent=2));print(r.returncode)
