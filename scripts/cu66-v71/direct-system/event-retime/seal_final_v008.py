from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[4];d=r/'fpga/experiments/cu66-v71/direct-system/final-integration-v008';o=d/'evidence/full-pin01';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(d/'sources.json')=='15cc325a837720ae4f54dbb98b30d457d76271f416b7ef1576c198a68fde4b69'
m=json.loads((d/'sources.json').read_text());pins=json.loads((o/'source-freeze.json').read_text())
for n,h in m['sources_sha256'].items():assert sha(r/n)==h,n
for n,h in pins.items():assert sha(r/n)==h,n
runner=json.loads((d/'native-runner-derivation.json').read_text())
assert sha(r/runner['runner'])==runner['runner_sha256']and sha(r/runner['parent_runner'])==runner['parent_runner_sha256']
patch=json.loads((r/'fpga/experiments/cu66-v71/direct-system/event-retime-v001/patch.json').read_text());receiver=(d/'cu71_receiver_final_v008.sv').read_text()
for old,new in patch['swaps'][1:]:assert receiver.count(new)==1
assert json.loads((o/'result.json').read_text())['status']=='PASS_FUNCTIONAL_DY71_KEY_P_CANONICAL_HUD_AND_LCD'
assert json.loads((o/'core-baseline-comparison.json').read_text())['status'].startswith('PASS_')
base=r/'fpga/experiments/cu66-v71/direct-system/core-integration-v006/evidence/full-pin01';prefix=('DY71_','SYSTEM_FRAME_PASS','SYSTEM_PASS','SYSTEM_CONTROL_PASS')
for name in ['control.log','frames.log']:assert [x for x in(o/name).read_text().splitlines()if x.startswith(prefix)]==[x for x in(base/name).read_text().splitlines()if x.startswith(prefix)]
assert 'EVENT_DIAG_CHECKS checks=1280 traces=6'in(o/'control.log').read_text()and 'EVENT_DIAG_CHECKS checks=3264 traces=24'in(o/'frames.log').read_text()
files=[r/n for n in m['sources']]+[r/n for n in pins]+[d/n for n in ['sources.json','derivation.json','native-runner-derivation.json','native-functional-results.md']]+[Path(__file__),r/runner['runner'],r/runner['parent_runner']]
for p in o.rglob('*'):
 if p.is_file()and p.stat().st_size and 'build'not in p.parts and p.name!='native-handoff.json'and p.suffix in ['.sv','.svh','.cpp','.json','.log']:files.append(p)
arts=[dict(role='source'if p.suffix in ['.sv','.svh','.py']else'evidence',path=p.relative_to(r).as_posix(),sha256=sha(p))for p in sorted(set(files))]
checks=dict(native_control=dict(status='pass',evidence=(o/'control.log').relative_to(r).as_posix()),actual_event_public_diag=dict(status='pass',evidence=(o/'core-baseline-comparison.json').relative_to(r).as_posix()),combined_key_p_p=dict(status='pass',evidence=(o/'result.json').relative_to(r).as_posix()),routed_hardware=dict(status='incomplete',note='Parentownedindependentgates; noVivado/hardwareinthistask'))
(o/'native-handoff.json').write_text(json.dumps(dict(overall='INCOMPLETE',component_status='PASS_FINAL_V008_ACTUAL_NATIVE_COMBINED_KEY_P_P_AND_PUBLIC_DIAG',artifacts=arts,checks=checks,c_check_handoff='Unavailable; manualsource/hash/contentauditonly'),indent=2)+'\n')
assert all(sha(r/x['path'])==x['sha256']for x in arts)
print(json.dumps(dict(component_status='PASS_FINAL_V008_NATIVE',artifacts=len(arts),overall='INCOMPLETE'),indent=2))
