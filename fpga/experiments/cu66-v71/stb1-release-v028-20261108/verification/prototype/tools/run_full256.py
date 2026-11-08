from pathlib import Path
import os,subprocess,json,hashlib
p=Path('C:/moon/dev/experiments/staging-burst-v1-20261108');e=p/'evidence/full256-unit02';e.mkdir(exist_ok=True);src=[p/'reference/cu71_packet_staging_safe.sv',p/'rtl/cu71_staging_burst_v1.sv',p/'tests/tb_staging_burst_full256_v1.sv'];env=dict(os.environ,PATH=str(Path('C:/msys64/ucrt64/bin'))+';'+os.environ['PATH'],TEMP=str(Path('C:/moon/tmp')),TMP=str(Path('C:/moon/tmp')));rows=[]
for name,cmd in [('compile',['C:/msys64/ucrt64/bin/iverilog.exe','-g2012','-s','tb_staging_burst_full256_v1','-o',(e/'unit.vvp').as_posix()]+[f.as_posix()for f in src]),('run',['C:/msys64/ucrt64/bin/vvp.exe',(e/'unit.vvp').as_posix()])]:
 r=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=60);(e/(name+'.log')).write_text(r.stdout+r.stderr);rows.append({'label':name,'argv':cmd,'returncode':r.returncode});(e/'execution.json').write_text(json.dumps(rows,indent=2));print(name,r.returncode,r.stdout+r.stderr)
 if r.returncode:raise SystemExit(1)
(e/'source-freeze.json').write_text(json.dumps({str(f):hashlib.sha256(f.read_bytes()).hexdigest()for f in src},indent=2))
