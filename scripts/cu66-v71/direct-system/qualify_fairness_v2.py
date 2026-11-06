"""Bind the stronger within-held-window control test without changing DUT."""
from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/direct-system/grouped-v001';o=d/'qualification-fairness-v002.json';assert not o.exists();p=d/'evidence/fairness02';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();j=json.loads((p/'result.json').read_text())
for n,h in j['source_pins'].items():assert sha(r/n)==h,n
assert 'held_window_progress_checked=1 checks=24258' in(p/'executed.log').read_text()
files=[p/'result.json',p/'execution.json',p/'executed.log',d/'qualification-components-v001.json',Path(__file__).resolve()]
o.write_text(json.dumps({'status':j['status'],'bridge_sha256':sha(d/'source/cu71_word_bridge_direct.sv'),'scope':'Explicitstablevalid/data/errorandLCD+BGprogresswhileotherresponseheld100clocks;DUTunchanged,previousproofspreserved','proofs':{f.relative_to(r).as_posix():sha(f)for f in files},'source_pins':j['source_pins'],'hardware':False},indent=2)+'\n');print(sha(o))
