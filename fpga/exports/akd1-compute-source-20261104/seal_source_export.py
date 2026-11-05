"""Self-contained derivative sealing: no omitted/external files are required."""
import hashlib,json
from pathlib import Path
p=Path(__file__).resolve().parent
sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
d=json.loads((p/'derivation.json').read_text());parent=p/d['parent_manifest_path']
assert sha(parent)==d['parent_manifest_sha256']=='852f12839e39dae04e87659c1d0c34b0c4a2eb148ca686d52b8e7da02bc9d902'
parent_artifacts={a['path']:a['sha256'] for a in json.loads(parent.read_text())['artifacts']}
for name,h in d['clean_build_input_hashes'].items():assert sha(p/name)==h==parent_artifacts[name],name
for name in d['portable_scripts_byte_identical']:assert sha(p/name)==parent_artifacts[name],name
for item in d['inherited_records']:assert sha(p/item['copy'])==item['sha256']==parent_artifacts[item['parent_path']],item['copy']
assert not list(p.rglob('*.dcp')) and not list(p.rglob('*.vvp'))
assert not list(p.rglob('.Xil')) and not list(p.rglob('__pycache__'))
for test,marker in [('controls','PASS controller checks=20'),('ordering','AKD1_CSR_ORDERING_PASS checks=58')]:
 r=p/'evidence/derivative-smoke'/test;e=json.loads((r/'execution.json').read_text())
 assert e['compile_returncode']==e['simulation_returncode']==0 and e['inputs_unchanged'] and not e['stub']
 assert marker in (r/'simulation.log').read_text()
 for name,h in e['sha256'].items():assert sha(p/name)==h,(test,name)
selection=json.loads((p/'selected-image.json').read_text());assert 'qualified_checkpoint' not in selection
assert sha(p/selection['image']['path'])==selection['image']['sha256']=='b1ca685e457446838b9d6c78b86f02c4b793dad42eccb3b5c50075d17e20e260'
assert len([x for x in json.loads((p/'design-inputs.json').read_text())['files'] if x['path'].endswith('.sv')])==21
artifacts=[]
for x in sorted(p.rglob('*')):
 if not x.is_file() or x.name=='manifest.json' or not x.stat().st_size:continue
 assert x.suffix not in {'.dcp','.vvp','.pyc','.zip'},x
 assert x.stat().st_size<100*1024*1024,x
 role='rtl' if x.suffix=='.sv' and x.parent.name in {'rtl','compute'} else 'constraints' if x.parent.name=='constraints' else 'image' if x.suffix=='.bit' else 'license' if x.parent.name=='licenses' else 'rebuild' if x.parent==p and x.suffix in {'.py','.tcl'} else 'evidence'
 artifacts.append({'role':role,'path':x.relative_to(p).as_posix(),'sha256':sha(x),'bytes':x.stat().st_size})
checks={'parent_binding':{'status':'pass','evidence':'provenance/parent-manifest.json'},'byte_identical_clean_inputs_and_launchers':{'status':'pass','evidence':'derivation.json'},'included_files_self_contained':{'status':'pass','scope':'NoDCP/VVP/caches;manifest binds includedfiles only'},'relocated_controls_ordering_smoke':{'status':'pass','evidence':['evidence/derivative-smoke/controls/execution.json','evidence/derivative-smoke/ordering/execution.json']},'inherited_executed_clean_build':{'status':'pass','evidence':'evidence/inherited-clean-build/execution.json','scope':'Parentexecutedcleanbuild;not newlyrunforpackaging'},'selected_original_BIT':{'status':'pass','evidence':'selected-image.json'},'new_full_build_and_BIT':{'status':'incomplete','reason':'NOT_RUN forpackaging;portablelauncherssupplied;no image replacement'},'hardware_and_publication':{'status':'incomplete','reason':'NONE bythistask;scope limitations unchanged'}}
m={'overall':'INCOMPLETE','source_only_derivative':'PASS','scope':'Git-sizedsource package with suppliedoriginalBIT and compact inheritedevidence; no newfullbuild/hardware','parent_manifest':{'path':'provenance/parent-manifest.json','sha256':sha(parent)},'selected_image':selection['image'],'files_bytes':sum(a['bytes'] for a in artifacts),'largest_file_bytes':max(a['bytes'] for a in artifacts),'omitted_binary_hashes':d['omitted_binary_artifacts'],'checks':checks,'artifacts':artifacts}
(p/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
for a in artifacts:assert sha(p/a['path'])==a['sha256']
print('SOURCE_ONLY_DERIVATIVE_PASS',len(artifacts),'artifacts;',m['files_bytes'],'includedbytes;largest',m['largest_file_bytes'],'manifestSHA',sha(p/'manifest.json'))
