"""Record exact SDR1 build artifacts and gates; does not claim physical readback."""
from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[1];c=r/'fpga/diagnostics/sdr1-20261105'
image=c/'image03-alternate01';route=c/'postroute03-alternate01';origin=c/'implementation03'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert json.loads((image/'execution.json').read_text())['returncode']==0
hashes=json.loads((image/'image-hashes.json').read_text())
for n,h in hashes.items():assert sha(image/n)==h
gate=json.loads((image/'gate.json').read_text())
assert sha(route/'routed.dcp')==gate['checkpoint_sha256']
artifacts=[]
def add(role,p):
 assert p.is_file()and p.stat().st_size>0,p
 artifacts.append(dict(role=role,path=p.relative_to(r).as_posix(),sha256=sha(p)))
for role,p in [('programming_image',image/'moonbub-sdr1.bit'),('debug_probes',image/'moonbub-sdr1.ltx'),('routed_checkpoint',route/'routed.dcp'),('build_gate',image/'gate.json'),('image_execution',image/'execution.json'),('image_writer',image/'executed.tcl'),('native_drc',image/'drc-native.rpt'),('rebuild',origin/'build.tcl'),('constraints',origin/'memory-timing.tcl'),('source_binding',origin/'source-freeze.json'),('physical_execution',route/'execution.json'),('physical_rebuild',route/'executed-postroute.tcl')]:add(role,p)
for p in (origin/'inputs').rglob('*'):
 if p.is_file():add('constraints'if p.suffix=='.xdc'else'rtl',p)
add('generated_ip_configuration',origin/'project/sdr1.srcs/sources_1/ip/sdr1_vio/sdr1_vio.xci')
for n in ['timing-summary.rpt','route-status.rpt','cdc.rpt','check-timing.rpt','drc.rpt']:add('routed_report',route/n)
for name in ['simulation04','simulation05']:
 for n in ['result.json','simulation.log','tb.sv','model.sv','primitives.sv','engine.sv','controller.sv']:add('functional_evidence',c/name/n)
for n in ['prepare_sdr1_probe.py','build_sdr1_probe.py','test_sdr1_engine.py','cpl1_sdram_models.py','postroute_cpl1_capture.py','image_sdr1_probe.py','manifest_sdr1_completion.py']:add('rebuild_helper',r/'scripts'/n)
manifest=dict(overall='PASS',scope='SDR1 programming-artifact completion and declared digital/routed gates only',artifacts=artifacts,
 checks={
 'functional_fast_model':dict(status='pass',evidence=(c/'simulation04/result.json').relative_to(r).as_posix()),
 'functional_slow_model':dict(status='pass',evidence=(c/'simulation05/result.json').relative_to(r).as_posix()),
 'routed_timing':dict(status='pass',evidence=(image/'gate.json').relative_to(r).as_posix()),
 'native_drc':dict(status='pass',evidence=(image/'drc-native.rpt').relative_to(r).as_posix()),
 'cdc':dict(status='pass',evidence=(route/'cdc.rpt').relative_to(r).as_posix()),
 'bitstream_generation':dict(status='pass',evidence=(image/'execution.json').relative_to(r).as_posix())},
 hardware=dict(programmed=False,physical_memory_correctness_proven=False,network_endpoint=False),
 limitations=['Narrow positive timing margin, not a margin sweep','Four aligned bursts, first SDRAM chip only','Four retained vendor debug-IP DRC warnings','No independent handoff-check MCP tool is available; hashes verified locally'])
out=image/'completion-manifest.json';assert not out.exists();out.write_text(json.dumps(manifest,indent=2)+'\n')
for a in artifacts:assert sha(r/a['path'])==a['sha256']
print('SDR1_COMPLETION_MANIFEST_LOCAL_HASHES_PASS',len(artifacts),out)
