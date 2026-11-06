"""Mechanical strict-width derivative; preserve the frozen controller algorithm."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[3]
AREA=Path(__file__).resolve().parent
source=ROOT/'fpga/rtl/moonshine_sdram.sv'
s=source.read_text()
changes=[('refresh_count<REFRESH_CYCLES',"32'(refresh_count)<REFRESH_CYCLES"),
         ('delay<=POWERUP_CYCLES',"delay<=16'(POWERUP_CYCLES)"),
         ('refresh_count>=REFRESH_CYCLES',"32'(refresh_count)>=REFRESH_CYCLES"),
         ('  WRITE_WAIT=11,REFRESH_PRE=12,REFRESH=13;','  REFRESH_PRE=12,REFRESH=13;')]
for before,after in changes:
 assert s.count(before)==1,before
 s=s.replace(before,after)
p=AREA/'controller/moonshine_sdram.sv';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
report=dict(schema='cu66-v91l-strict-controller-derivative-v1',original=str(source.relative_to(ROOT)),original_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),derived=str(p.relative_to(ROOT)),derived_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),changes=[dict(before=a,after=b) for a,b in changes],scope='Only explicit width casts and unused constant name removal; all state values, ports, command and timing behavior retained.')
(AREA/'controller-derivation.json').write_text(json.dumps(report,indent=2)+'\n')
print('CONTROLLER_DERIVED',report['derived_sha256'])
