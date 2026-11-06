"""Carry physical budgets and explicit CDC checks into the new CU71 hierarchy."""
from pathlib import Path
import argparse,hashlib,json
r=Path(__file__).resolve().parents[2];a=argparse.ArgumentParser();a.add_argument('--board',required=True);args=a.parse_args()
o=(r/args.board).resolve();target=o/'constraints/timing-cu71-reviewed.tcl';assert not target.exists()
p=Path('C:/Users/lavat/codex/moonbub/fpga/candidates/cp23-sdr2-balancedtag-20261105-v001/inputs/constraints/timing-cpl1-reviewed.tcl')
s=p.read_text().replace('diagnostic/core/memory/controller','system_core/memory/controller').replace('diagnostic/core/lcd/','system_core/scanout/lcd/')
s=s.replace('first_stage core_pll_status {status_(service|panel)_lock_sync_reg\\[0\\]}','first_stage configuration_quarantine {quarantine_sync_reg\\[0\\]}')
s=s.replace('{rst(100|200|pixel)_reg.*}', '{joint_(core|spi|pixel)_reset_reg.*}')
begin=s.index('set job_reset_cells ');end=s.index('foreach spec ',begin)
s=s[:begin]+'''set joint_reset_cells [required_cells joint_reset_chains {joint_(core|spi|pixel)_reset_reg\\[[0-3]\\]}]
if {[llength $joint_reset_cells]!=12} {error "Expected three four-stage joint reset chains"}
'''+s[end:]
s=s.replace('required_cells actual_compute {diagnostic/core/key/base/.*}', 'required_cells actual_compute {system_core/receiver/base/.*}')
s=s.replace('required_cells actual_packet_store {diagnostic/core/key/packet_ram.*}', 'required_cells actual_packet_store {control_plane/staging/bytes_reg.*}')
s=s.replace('required_cells actual_rom {diagnostic/loader/rom.*}\n','')
assert 'diagnostic/' not in s,'An obsolete parent hierarchy guard remains'
assert 'diagnostic/core' not in s and 'job_reset_chain' not in s and 'status_service' not in s
assert 'set_input_delay -clock sdram_forwarded -max 7.0' in s
assert 'set_input_delay -clock sdram_forwarded -min 2.0' in s
assert 'set_multicycle_path 2 -setup' in s
target.write_text('# CU71 hierarchy-specific derivative; identical pin budgets and selected100MHz read profile.\n'+s,newline='\n')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(o/'constraints/derivation.json').write_text(json.dumps(dict(parent=str(p),parent_sha256=sha(p),candidate_sha256=sha(target),scope='Hierarchy/reset first-stage selectors only; numeric clocks, delays, pulse and strong hold intent retained. Native object binding/CDC/STA pending.'),indent=2)+'\n')
print(target)
