"""Audit combined binding and native evidence; not routed/hardware release."""
from pathlib import Path
import hashlib,json,re,shutil
r=Path(__file__).resolve().parents[4];d=r/'fpga/experiments/cu66-v71/direct-system/core-integration-v006';o=d/'evidence/full-pin01';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((d/'sources.json').read_text());der=json.loads((d/'derivation.json').read_text());pins=json.loads((o/'source-freeze.json').read_text());result=json.loads((o/'result.json').read_text())
assert result['status']=='PASS_FUNCTIONAL_DY71_KEY_P_CANONICAL_HUD_AND_LCD'and result['frames']==3
for n,h in m['sources_sha256'].items():assert sha(r/n)==h,n
for n,h in pins.items():assert sha(r/n)==h,n
for v in der['derived_files']:
 assert sha(r/v['parent'])==v['parent_sha256']and sha(r/v['output'])==v['sha256'];s=(r/v['output']).read_text()
 for old,new in reversed(v['token_changes']):assert s.count(new)==1;s=s.replace(new,old)
 assert s==(r/v['parent']).read_text()
log=(o/'frames.log').read_text();control=(o/'control.log').read_text();assert 'SYSTEM_CONTROL_PASS'in control
assert 'clean_lines=5452 black_lines=0 observed_pixels=2617264 total_underruns=0'in log
frames=[]
for line in log.splitlines():
 if line.startswith('SYSTEM_FRAME_PASS '):
  row={k:int(v)for k,v in re.findall(r'(\w+)=(\d+)',line)};assert row['actual_writes']==428160 and row['underruns']==0;frames.append(row)
assert len(frames)==3 and [x['fid']for x in frames]==[0,1,2]
extras=[d/'sources.json',d/'derivation.json',d/'README.md',Path(__file__),Path(__file__).with_name('prepare_core_v006.py'),Path(__file__).with_name('run_core_v006.py'),Path(__file__).with_name('run_fence_timeline.py'),Path(__file__).parents[1]/'run_timeline.py',Path(__file__).parents[1]/'run.py']
copy=o/'binding-audit';copy.mkdir(exist_ok=True)
for p in extras:
 q=copy/str(p.relative_to(r));q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
summary=dict(component_status='PASS_ACTUAL_NATIVE_PIN_CORE_V006_KEY_P_P',manifest_sha256=sha(d/'sources.json'),source_freeze_sha256=sha(o/'source-freeze.json'),frames_log_sha256=sha(o/'frames.log'),frame_counters=frames,clean_lines=5452,whole_black_lines=0,scored_pixels=2617264,underruns=0,rgb_traffic=False,limits=['ActualqualifiedSDRAMpinmodel, notphysicalhardware','NativeC++HUDsemanticserviceoutsideHDLtime','Finalowner/HUD/eventcleanupandfull1371entropyqualificationremainseparate','NoESP/CSR/QSPI/network/routedtimingor30fpsclaim'],c_check_handoff='Unavailable; manual source/hash/content audit only')
(o/'binding-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
files=[r/n for n in m['sources']]+extras+[o/n for n in ['source-freeze.json','execution.json','result.json','build.log','control.log','frames.log','tb.cpp','cu71_direct_system_sim.sv','model-verilator.sv','binding-summary.json']]+list(copy.rglob('*'))
files=sorted(set(p for p in files if p.is_file()and p.stat().st_size))
arts=[dict(role='source'if p.suffix in ['.sv','.svh','.py']else'evidence',path=str(p.relative_to(r)).replace('\\','/'),sha256=sha(p))for p in files]
checks=dict(native_control=dict(status='pass',evidence=str((o/'control.log').relative_to(r)).replace('\\','/')),native_canonical_hud_pixels=dict(status='pass',evidence=str((o/'result.json').relative_to(r)).replace('\\','/')),reversible_binding=dict(status='pass',evidence=str((d/'derivation.json').relative_to(r)).replace('\\','/')),final_owner_pair=dict(status='incomplete',note='Differentfutureownersource requiresseparatecombinedproof'),routed_hardware=dict(status='incomplete',note='Notperformed, noVivado/hardwareinthisscope'))
(o/'handoff.json').write_text(json.dumps(dict(overall='INCOMPLETE',component_status=summary['component_status'],scope='Functionalcombinedcorequalified; finalowner/routed/hardwarereleasegatesexcludedandopen',artifacts=arts,checks=checks),indent=2)+'\n')
assert all(sha(r/v['path'])==v['sha256']for v in arts)
print(json.dumps(dict(component_status=summary['component_status'],artifacts=len(arts),overall='INCOMPLETE'),indent=2))
