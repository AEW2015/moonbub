"""Actual native pin-model control+KEY/P/P with explicit v006 codec/parser."""
from pathlib import Path
reference=Path(__file__).with_name('run_fence_timeline.py');s=reference.read_text()
old="target='cu71_system_direct_math'if prior else'cu71_system_direct_syncsafe';selection='board-math-v001'if prior else'syncsafe-math-v002'"
new="assert not prior;target='cu71_system_core_v006';selection='core-integration-v006'"
assert s.count(old)==1;s=s.replace(old,new)
exec(compile(s,str(reference),'exec'),globals())
