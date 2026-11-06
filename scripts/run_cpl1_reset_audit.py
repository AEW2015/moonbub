"""Bind read-only Vivado reset/control-set reports to one checkpoint."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,time
r=Path(__file__).resolve().parents[1]
a=argparse.ArgumentParser();a.add_argument('--checkpoint',required=True);a.add_argument('--output',required=True);args=a.parse_args()
cp=Path(args.checkpoint).resolve();o=Path(args.output).resolve();o.mkdir(parents=True,exist_ok=False);(o/'tmp').mkdir()
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
before=sha(cp);shutil.copyfile(r/'scripts/audit_cpl1_reset.tcl',o/'executed.tcl')
env=dict(os.environ);env['TEMP']=str(o/'tmp');env['TMP']=str(o/'tmp')
cmd=['C:/Xilinx/2025.2/Vivado/bin/vivado.bat','-mode','batch','-source',str(o/'executed.tcl'),'-log',str(o/'vivado.log'),'-journal',str(o/'vivado.jou'),'-tclargs',str(cp),str(o)]
t=time.monotonic();p=subprocess.run(cmd,cwd=o,env=env)
assert sha(cp)==before
(o/'execution.json').write_text(json.dumps(dict(command=cmd,returncode=p.returncode,seconds=time.monotonic()-t,
 checkpoint_sha256=before,checkpoint_unchanged=True,script_sha256=sha(o/'executed.tcl'),hardware=False),indent=2)+'\n')
raise SystemExit(p.returncode)
