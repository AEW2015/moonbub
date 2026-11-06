"""Bounded physical-only experiment from a frozen checkpoint; no image/load."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,time
r=Path(__file__).resolve().parents[1]
a=argparse.ArgumentParser();a.add_argument('--parent',required=True);a.add_argument('--output',required=True);a.add_argument('--directive',default='AlternateReplication');args=a.parse_args()
assert args.directive in ['AlternateReplication','AggressiveExplore']
parent=Path(args.parent).resolve();out=Path(args.output).resolve();out.mkdir(parents=True,exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before=sha(parent)
script=r/'fpga/exports/cpl1-timing-fsmcopy-source-20261105-v002/implementation-chain/postroute-0.tcl'
shutil.copyfile(script,out/'executed-postroute.tcl');(out/'tmp').mkdir()
env=dict(os.environ);env['TEMP']=str(out/'tmp');env['TMP']=str(out/'tmp')
cmd=['C:/Xilinx/2025.2/Vivado/bin/vivado.bat','-mode','batch','-source',str(out/'executed-postroute.tcl'),'-log',str(out/'vivado.log'),'-journal',str(out/'vivado.jou'),'-tclargs',str(parent),str(out),args.directive]
t=time.monotonic();q=subprocess.run(cmd,cwd=out,env=env)
assert sha(parent)==before,'Parent checkpoint mutated'
(out/'execution.json').write_text(json.dumps(dict(command=cmd,returncode=q.returncode,wall_seconds=time.monotonic()-t,
    parent_checkpoint=str(parent),parent_sha256=before,parent_unchanged=True,physical_placement_changed=True,
    RTL_changed=False,constraints_changed=False,BIT=False,hardware=False,script_sha256=sha(out/'executed-postroute.tcl')),indent=2)+'\n')
raise SystemExit(q.returncode)
