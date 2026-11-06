from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[4];d=r/'fpga/experiments/cu66-v71/direct-system/event-retime-v001';o=d/'evidence/full-pin02';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
patch=json.loads((d/'patch.json').read_text());source=(d/'cu71_receiver_eventpipe.sv').read_text();assert sha(d/'cu71_receiver_eventpipe.sv')==patch['source_sha256']
for old,new in reversed(patch['swaps']):assert source.count(new)==1;source=source.replace(new,old)
assert source==(r/patch['parent']).read_text()and sha(r/patch['parent'])==patch['parent_sha256']
for name,side in [('event_old.sv',0),('event_new.sv',1)]:
 s=(d/name).read_text()
 for pair in patch['swaps'][1:]:assert pair[side]in s
for n,h in json.loads((d/'sources.json').read_text())['sources_sha256'].items():assert sha(r/n)==h
for n,h in json.loads((o/'source-freeze.json').read_text()).items():assert sha(r/n)==h,n
assert json.loads((o/'result.json').read_text())['status']=='PASS_FUNCTIONAL_DY71_KEY_P_CANONICAL_HUD_AND_LCD'
assert json.loads((o/'baseline-comparison.json').read_text())['status'].startswith('PASS_')
assert 'checks=2590434 cycles=1264'in(d/'evidence/focused02/simulation.log').read_text()
base=r/'fpga/experiments/cu66-v71/direct-system/syncsafe-math-v002/evidence/new-fence-three01';prefix=('DY71_','SYSTEM_FRAME_PASS','SYSTEM_PASS','SYSTEM_CONTROL_PASS')
for name in ['control.log','frames.log']:
 assert [x for x in(o/name).read_text().splitlines()if x.startswith(prefix)]==[x for x in(base/name).read_text().splitlines()if x.startswith(prefix)]
scripts=list(Path(__file__).parent.glob('*.py'));files=[d/'cu71_receiver_eventpipe.sv',d/'cu71_system_eventpipe.sv',d/'patch.json',d/'sources.json',d/'event_old.sv',d/'event_new.sv',d/'tb_event.sv',d/'README.md',*scripts]
for b in [d/'evidence/focused01',d/'evidence/focused02',o]:
 for p in b.rglob('*'):
  if p.is_file()and p.stat().st_size and 'build'not in p.parts and p.name!='handoff.json'and p.suffix in ['.json','.sv','.svh','.cpp','.py','.log','.vvp']:files.append(p)
files=sorted(set(files));arts=[dict(role='source'if'/evidence/'not in p.as_posix()else'evidence',path=p.relative_to(r).as_posix(),sha256=sha(p))for p in files]
checks=dict(four_state_exact_ring=dict(status='pass',evidence=(d/'evidence/focused02/result.json').relative_to(r).as_posix()),actual_receiver_failure_success_diag=dict(status='pass',evidence=(o/'control.log').relative_to(r).as_posix()),actual_key_p_p=dict(status='pass',evidence=(o/'result.json').relative_to(r).as_posix()),exact_original_public_logs=dict(status='pass',evidence=(o/'baseline-comparison.json').relative_to(r).as_posix()),composed_owner_pair=dict(status='incomplete',note='IndependentlycomposedfutureHUD/metadataownerneedswholepairproof'),timing_hardware=dict(status='incomplete',note='NoVivadoorhardwareperformedbythistask'))
(o/'handoff.json').write_text(json.dumps(dict(overall='INCOMPLETE',component_status='PASS_REVERSIBLE_EVENT_RETIME_FOURSTATE_AND_ACTUAL_RECEIVER_DIAG_KEY_P_P',artifacts=arts,checks=checks,c_check_handoff='Unavailable; manualsource/hash/contentauditonly'),indent=2)+'\n')
assert all(sha(r/x['path'])==x['sha256']for x in arts)
print(json.dumps(dict(component_status='PASS_EVENT_RETIME',artifacts=len(arts),receiver_sha256=patch['source_sha256'],overall='INCOMPLETE'),indent=2))
