"""Run the same gates against the cell exported from the actual full synthesis."""
from pathlib import Path
import hashlib,json
p=Path(__file__).resolve().parent
b=Path('C:/mb70/dy71-v025-20261107-v003')
e=json.loads((b/'synth-execution.json').read_text())
assert e['returncode']==0 and e['completion_marker'] and e['inputs_unchanged']
freeze=json.loads((b/'source-freeze.json').read_text())
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert all(sha(b/'inputs'/n)==h for n,h in freeze.items())
src=b/'inputs/fpga/experiments/cu66-v71/hud-bulk-v025/dy71_hud_bulk_v025.sv'
assert sha(src)==sha(p/'dy71_hud_bulk_v025.sv')
s=(p/'run-xsim-vendor-v004.py').read_text(encoding='utf-8-sig')
s=s.replace("e=p/'xsim-vendor04'", "e=p/'xsim-full-synth02'")
s=s.replace("p/'mapping04/funcsim.v'", "Path('C:/mb70/dy71-v025-20261107-v003/bulk-funcsim.v')")
s=s.replace("p/'mapping04/dy71_hud_bulk_v025.sv'", "Path('C:/mb70/dy71-v025-20261107-v003/inputs/fpga/experiments/cu66-v71/hud-bulk-v025/dy71_hud_bulk_v025.sv')")
s=s.replace('Actual synthesized standalone bulk engine / AMD unisims_ver;', 'Actual full-design synthesis exported bulk cell / AMD unisims_ver;')
(p/'run-xsim-full-synth-executed.py').write_text(s)
exec(compile(s,str(p/'run-xsim-full-synth-executed.py'),'exec'))
