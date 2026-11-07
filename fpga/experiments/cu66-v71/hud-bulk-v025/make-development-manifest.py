"""Hash current deliverables without equating evidence presence to hardware readiness."""
from pathlib import Path
import hashlib,json,runpy
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
timing_helper=runpy.run_path(str(root/'scripts/cu66-v71/image_dy71_candidate.py'))
candidates=[]
for name in ['dy71-v025-20261107-v003','dy71-v025-20261107-v003/postroute01','dy71-v025-20261107-v003/postroute02','dy71-v026-20261107-v001','dy71-v027-20261107-v001']:
 candidate=root/name
 report=candidate/'timing-summary.rpt'
 row=dict(build=name,status='incomplete',hardware_tested=False)
 if report.is_file():
  add('candidate_timing',report)
  try:
   row['metrics']=timing_helper['timing_metrics'](report.read_text())
   row['status']='pass'
  except (AssertionError,ValueError) as error:
   row['status']='fail'
   row['reason']=str(error)
 candidates.append(row)
checks={
 'rtl_component':dict(status='pass',evidence=(p/'functional04/result.json').relative_to(root).as_posix()),
 'pin_control_cdc':dict(status='pass' if (p/'pins05/result.json').is_file() else 'incomplete',evidence=(p/'pins05/result.json').relative_to(root).as_posix()),
 'legacy_csr':dict(status='pass' if (p/'legacy05/result.json').is_file() else 'incomplete',evidence=(p/'legacy05/result.json').relative_to(root).as_posix()),
 'full_synth_cell':dict(status='pass' if (p/'xsim-full-synth02/result.json').is_file() else 'incomplete',evidence=(p/'xsim-full-synth02/result.json').relative_to(root).as_posix()),
 'routed_timing':dict(status=candidates[-1]['status'],evidence=candidates[-1]['build']+'/timing-summary.rpt'),
 'native_audit_and_image':dict(status='incomplete'),
 'exact_candidate_hardware':dict(status='incomplete'),
 'continuous_unique_30fps':dict(status='incomplete'),
}
selected=root/candidates[-1]['build']
for folder in ['audit01','image01']:
 for f in (selected/folder).glob('*'):
  if f.suffix in ['.json','.rpt','.tsv','.tcl','.bit']:add('selected_image_gate_evidence',f)
audit=selected/'audit01/execution.json'
if audit.is_file():
 receipt=json.loads(audit.read_text())
 assert receipt['returncode']==0 and receipt['completion_marker'] and not receipt['native_errors'] and receipt['checkpoint_unchanged'],receipt
 checks['native_audit']=dict(status='pass',evidence=audit.relative_to(root).as_posix())
image=selected/'image-flow/result.json'
if image.is_file():
 receipt=json.loads(image.read_text())
 assert receipt['status']=='LAB_BIT_EMITTED_PENDING_PHYSICAL_TEST' and receipt['hardware'] is False
 assert hashlib.sha256(Path(receipt['bit']).read_bytes()).hexdigest()==receipt['sha256']
 checks['native_audit_and_image']=dict(status='pass',evidence=image.relative_to(root).as_posix())
(p/'development-manifest.json').write_text(json.dumps(dict(overall='INCOMPLETE',selected_candidate=candidates[-1]['build'],artifacts=arts,checks=checks,candidates=candidates,c_check_handoff='UNAVAILABLE_MANUAL_HASH_INTEGRITY_ONLY',physical_baseline='V42/V023 endpoint held; no hardware mutations during this development',scope='Passing files are executed evidence; timing/image/hardware are separate mandatory gates.'),indent=2)+'\n')
print('INCOMPLETE_MANIFEST_WRITTEN',len(arts),'artifacts')
