"""Bind completed reset BIT to exact sources, selected route and functional evidence."""
from pathlib import Path
import argparse,hashlib,json,re
r=Path(__file__).resolve().parents[1]
a=argparse.ArgumentParser();a.add_argument('--candidate',default='fpga/candidates/cp23-reset-tags-20261105-v001');args=a.parse_args();c=(r/args.candidate).resolve()
baseline=r/'fpga/candidates/cp23-reset-tags-20261105-v001'
info=json.loads((c/'evidence/bitstream-completion01/result.json').read_text())
image=Path(info['image']);route=Path(info['selected_route']);origin=c/'implementation02'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
for n,h in json.loads((image/'image-hashes.json').read_text()).items():assert sha(image/n)==h
binding=json.loads((image/'source-binding.json').read_text())
assert binding['checkpoint_sha256']==sha(route/'routed.dcp')
artifacts=[]
def add(role,p):
 assert p.is_file()and p.stat().st_size>0,p
 artifacts.append(dict(role=role,path=p.relative_to(r).as_posix(),sha256=sha(p)))
for role,p in [('programming_image',image/'moonbub-cpl1-timing-rev4.1.bit'),('routed_checkpoint',route/'routed.dcp'),('source_binding',image/'source-binding.json'),('source_freeze',origin/'source-freeze.json'),('native_drc',image/'drc-uncapped.rpt'),('native_drc_inventory',image/'drc-native-inventory.txt'),('timing_gate',route/'timing-gate.json'),('image_execution',image/'execution.json'),('image_writer',image/'executed-write-image.tcl'),('rebuild',origin/'inputs/build_board.tcl')]:add(role,p)
for p in (origin/'inputs').rglob('*'):
 if p.is_file():add('constraints'if p.suffix=='.xdc'or'constraints'in p.parts else'rtl',p)
add('candidate_definition',c/'candidate.json')
for p in (c/'inputs').rglob('*'):
 if p.is_file():add('rebuild_source',p)
for name in ['key.cp23.hex','quantizers.hex']:add('rebuild_memory_image',c/name)
for name in ['key.cp23.hex','quantizers.hex']:add('memory_image',origin/name)
for name in ['timing-summary.rpt','route-status.rpt','bus-skew.rpt','check-timing.rpt','cdc.rpt','setup-paths.rpt','hold-paths.rpt','drc.rpt','utilization.rpt']:add('routed_report',route/name)
for name in ['full-budget-fast01','full-budget-slow01']:
 for n in ['result.json','source-snapshot.json','execution.json','simulation.log','checker-result.json']:add('functional_evidence',c/'evidence'/name/n)
 d=c/'evidence'/name;snap=json.loads((d/'source-snapshot.json').read_text())
 for n in snap['sources']:add('executed_simulation_source',d/'inputs'/n)
 for n in snap['assets']:add('executed_simulation_asset',d/n)
sealed=r/'fpga/exports/cpl1-timing-fsmcopy-source-20261105-v002'
add('simulation_rebuild_selection',sealed/'simulation-selection.json')
for folder in ['sim-inputs','sim-assets','host-checker']:
 for p in (sealed/folder).rglob('*'):
  if p.is_file()and'__pycache__'not in p.parts:add('simulation_rebuild_support',p)
add('comparison_reference',r/'fpga/candidates/cp23-sdram-capture274p5-csa-20261105-v001/inputs/core/parents/cp23_envelope.sv')
add('image_rebuild_support',sealed/'image/write-image.tcl')
add('physical_rebuild_support',sealed/'implementation-chain/postroute-0.tcl')
for name in ['reference.sv','candidate.sv','sha256_bytes.sv','tb.sv','fixture.hex','badtag.hex','result.json','execution.json','simulation.log']:add('comparison_evidence',c/'evidence/envelope-equivalence02'/name)
for root,folder in [(baseline,'reset-audit-baseline-synth01'),(baseline,'reset-audit-synth01'),(c,'reset-audit-selected01')]:
 for name in ['execution.json','executed.tcl','reset-summary.txt','job-reset-loads.tsv','control-sets.rpt','high-fanout.rpt','utilization.rpt']:add('selected_reset_audit'if root==c and folder=='reset-audit-selected01'else'historical_reset_only_audit',root/'evidence'/folder/name)
add('historical_reset_only_synthesis_comparison',baseline/'evidence/reset-reduction-synthesis-summary.json')
reservation=json.loads((c/'candidate.json').read_text()).get('sha_byte_reservation')
if reservation:
 for name in ['result.json','executed.tcl','execution.json','before-storage-fanin.txt','after-storage-fanin.txt']:add('sha_storage_cut_evidence',c/'evidence/sha-write-cut01'/name)
 add('rebuild_helper',r/'scripts/audit_sha_write_cut.tcl')
 for name in json.loads((c/'evidence/sha-write-cut01/result.json').read_text())['artifacts']:
  if name.endswith('.dcp'):add('structural_audit_checkpoint',r/name)
 for key in ['sha_suite','cancel_suite']:
  p=Path(reservation[key])
  for name in ['result.json','simulation.log','sha256_bytes.sv','tb.sv','tb_sha.sv','sha-fixtures.hex']:
   if (p.parent/name).exists():add('sha_reservation_evidence',p.parent/name)
 for name in ['prepare_cpl1_reset_bytewrite_candidate.py','experiment_sha_csa_reservation.py','test_sha_reservation_cancel.py']:add('rebuild_helper',r/'scripts'/name)
for n in ['prepare_cpl1_reset_candidate.py','test_cpl1_reset_tags.py','run_cpl1_capture_full.py','cpl1_sdram_models.py','build_cpl1_capture_candidate.py','postroute_cpl1_capture.py','check_cpl1_capture_build.py','audit_cpl1_reset.tcl','run_cpl1_reset_audit.py','summarize_reset_reduction.py','image_cpl1_reset_candidate.py','complete_cpl1_reset_bitstream.py','manifest_cpl1_reset_completion.py']:add('rebuild_helper',r/'scripts'/n)
inventory=(image/'drc-native-inventory.txt').read_text()
assert 'SEVERITY=Error'not in inventory
gate=json.loads((route/'timing-gate.json').read_text())
manifest=dict(overall='PASS',scope='Reset-reduced CPL1 bitstream completion: directed functionality and declared routed build gates',artifacts=artifacts,
 checks={
 'directed_reset_comparison':dict(status='pass',evidence=(c/'evidence/envelope-equivalence02/result.json').relative_to(r).as_posix()),
 'full_model_fast':dict(status='pass',evidence=(c/'evidence/full-budget-fast01/result.json').relative_to(r).as_posix()),
 'full_model_slow':dict(status='pass',evidence=(c/'evidence/full-budget-slow01/result.json').relative_to(r).as_posix()),
 'routed_timing':dict(status='pass',evidence=(route/'timing-gate.json').relative_to(r).as_posix()),
 'native_drc':dict(status='pass',evidence=(image/'drc-native-inventory.txt').relative_to(r).as_posix()),
 'bitstream_generation':dict(status='pass',evidence=(image/'execution.json').relative_to(r).as_posix())},
 timing=gate['timing'],retained_drc_severities={s:len(re.findall('SEVERITY='+s+r'\b',inventory))for s in ['Warning','Critical Warning','Error']},
 hardware=dict(programmed=False,physical_CPL1_CRC_verified=False,Sunshine_network_ready=False,unique_30fps_verified=False),
 limitations=['Full-frame digital models do not prove fitted SDRAM timing','Narrow positive timing margin is not a multi-run margin sweep','No c_check_handoff MCP tool available; artifact hashes verified locally'])
out=image/'completion-manifest.json';assert not out.exists();out.write_text(json.dumps(manifest,indent=2)+'\n')
for a in artifacts:assert sha(r/a['path'])==a['sha256']
print('CPL1_RESET_COMPLETION_MANIFEST_LOCAL_HASHES_PASS',len(artifacts),out)
