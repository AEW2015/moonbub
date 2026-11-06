"""Balanced Tcl parse only, using headless Tcl interpreter; no Vivado calls."""
from pathlib import Path
import hashlib,json,tkinter
r=Path(__file__).resolve().parents[4];d=r/'fpga/experiments/cu66-v71/direct-system/board-math-v001';o=d/'evidence/draft-syntax02';o.mkdir(exist_ok=False);sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();t=tkinter.Tcl();files=[d/'physical-shell-proposal/constraints/timing-dy71-DRAFT.tcl',d/'lcd-first-stage-guard-DRAFT.tcl'];pins={Path(__file__).resolve().relative_to(r).as_posix():sha(Path(__file__).resolve())}
for f in files:
 assert int(t.call('info','complete',f.read_text()))==1,f
 (o/f.name).write_bytes(f.read_bytes());pins[f.relative_to(r).as_posix()]=sha(f)
(o/'result.json').write_text(json.dumps({'status':'PASS_TCL_BALANCED_PARSE_ONLY','Tcl_version':t.call('info','patchlevel'),'source_pins':pins,'executed_tool':'Python headless tkinter.Tcl(info complete); no Tk GUI or Vivado','initial_environment_attempt':'WSL tclsh unavailable; native headless Tcl used instead','scope':'Balanced Tcl commands/braces only; constraint, netlist object and fanout commands were not executed. Draft remains blocked.','hardware':False,'Vivado':False},indent=2)+'\n');print('PASS_TCL_BALANCED_PARSE_ONLY',t.call('info','patchlevel'))
