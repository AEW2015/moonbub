from pathlib import Path
import subprocess,json,time,hashlib
p=Path(__file__).resolve().parent;cmd=json.loads((p/'compile-command.json').read_text());start=time.monotonic()
with(p/'compile.log').open('x')as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=1200)
(p/'compile-result.json').write_text(json.dumps({'returncode':r.returncode,'seconds':time.monotonic()-start,'command':cmd},indent=2));print('compile',r.returncode,flush=True);raise SystemExit(r.returncode)
