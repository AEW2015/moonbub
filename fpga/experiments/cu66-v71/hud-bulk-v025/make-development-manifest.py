"""Hash current deliverables without equating evidence presence to hardware readiness."""
from pathlib import Path
import hashlib,json
root=Path('C:/mb70');p=Path(__file__).resolve().parent;b=root/'dy71-v025-20261107-v003';fw=root/'firmware/experiments/v43-dy71-bulk-hud-20261107'
arts=[]
def add(role,f):
 if f.is_file() and f.stat().st_size:arts.append(dict(role=role,path=f.relative_to(root).as_posix(),sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
for f in p.glob('*.sv'):add('rtl_or_testbench',f)
for f in [b/'selection.json',b/'source-freeze.json',b/'synth.tcl',b/'implementation.tcl',b/'run-phase.py']:add('rebuild',f)
for f in (b/'inputs').rglob('*'):
 if f.is_file():add('frozen_input',f)
for folder in ['functional04','pins05','legacy05','xsim-vendor04','xsim-boundary01','xsim-full-synth02']:
 for f in (p/folder).glob('*'):
  if f.suffix in ['.json','.log']:add('functional_evidence',f)
for f in fw.joinpath('release-bulk-hud-v002').glob('*'):add('esp32_image',f)
for f in ['synth-execution.json','implementation-execution.json','timing-summary.rpt','route-status.rpt','drc.rpt','routed.dcp','bulk-port-gate.json']:add('implementation_evidence',b/f)
checks={
 'rtl_component':dict(status='pass',evidence=(p/'functional04/result.json').relative_to(root).as_posix()),
 'pin_control_cdc':dict(status='pass' if (p/'pins05/result.json').is_file() else 'incomplete',evidence=(p/'pins05/result.json').relative_to(root).as_posix()),
 'legacy_csr':dict(status='pass' if (p/'legacy05/result.json').is_file() else 'incomplete',evidence=(p/'legacy05/result.json').relative_to(root).as_posix()),
 'full_synth_cell':dict(status='pass' if (p/'xsim-full-synth02/result.json').is_file() else 'incomplete',evidence=(p/'xsim-full-synth02/result.json').relative_to(root).as_posix()),
 'routed_timing':dict(status='incomplete',evidence=(b/'timing-summary.rpt').relative_to(root).as_posix()),
 'native_audit_and_image':dict(status='incomplete'),
 'exact_candidate_hardware':dict(status='incomplete'),
 'continuous_unique_30fps':dict(status='incomplete'),
}
(p/'development-manifest.json').write_text(json.dumps(dict(overall='INCOMPLETE',artifacts=arts,checks=checks,c_check_handoff='UNAVAILABLE_MANUAL_HASH_INTEGRITY_ONLY',physical_baseline='V42/V023 endpoint held; no hardware mutations during this development',scope='Passing files are executed evidence; timing/image/hardware are separate mandatory gates.'),indent=2)+'\n')
print('INCOMPLETE_MANIFEST_WRITTEN',len(arts),'artifacts')
