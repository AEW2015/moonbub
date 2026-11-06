"""Bounded native elaboration for isolated DY71 hardware hierarchy."""
from pathlib import Path
import hashlib,json,shlex,subprocess,time
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/direct-system';o=d/'evidence/lint01';o.mkdir(parents=True,exist_ok=False);m=json.loads((d/'sources.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();lin=lambda p:'/mnt/'+p.drive[0].lower()+p.as_posix()[2:]
sources=[r/n for n in m['sources']]+[r/'fpga/experiments/cu66-v71/memory/verification/primitives.sv'];pins={str(f.relative_to(r)):sha(f)for f in sources}
args=['verilator','--lint-only','--timing','--Wall','-Wno-fatal','-Wno-BLKSEQ','-Wno-PINCONNECTEMPTY','--top-module',m['top']]+['-I'+lin(r/n)for n in m['include_dirs']]+[lin(f)for f in sources]
cmd=['wsl','-d','MRS-HDL-Research','--','bash','-lc','source /opt/gamebub-openxc7-20261021/oss-cad-suite/environment; '+shlex.join(args)];start=time.monotonic();q=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);(o/'executed.log').write_text(q.stdout)
for n,h in pins.items():assert sha(r/n)==h
(o/'execution.json').write_text(json.dumps({'command':cmd,'returncode':q.returncode,'seconds':time.monotonic()-start,'source_pins':pins,'scope':'Nativehierarchyelaborationonly;notfunctional/timing/HWproof'},indent=2)+'\n');print(q.stdout[-4000:]);raise SystemExit(q.returncode)
