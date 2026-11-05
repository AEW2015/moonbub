"""Source-only manifest; never opens omitted release images or SDK caches."""
import hashlib,json,subprocess,sys
from pathlib import Path
p=Path(__file__).resolve().parent
sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
subprocess.run([sys.executable,str(p/'verify_source.py')],cwd=p,check=True)
b=json.loads((p/'source-bindings.json').read_text())
assert b['selected_inputs']==575 and b['selected_artifacts_verified']==3844
host=json.loads((p/'checks/host/result.json').read_text());assert host['status']=='PASS' and (host['model_tests'],host['SDK_host_tests'],host['expected_compiler_rejections'])==(39,66,24)
assert json.loads((p/'checks/source-dependencies.json').read_text())['status']=='PASS'
meta=json.loads((p/'checks/metadata/result.json').read_text());assert meta['status']=='PASS' and len(meta['manifests'])==4
full=json.loads((p/'checks/metadata/full-application-result.json').read_text());assert full['status']=='PASS' and full['packages']==424 and full['local_packages']==['handheld']
pre=json.loads((p/'checks/preflight-only.json').read_text());assert pre['status']=='PASS' and pre['target_build']=='NOT_RUN' and pre['launcher_sha256']==sha(p/'build_rev4.ps1')
assert not list(p.rglob('*.elf')) and not list(p.rglob('*.uf2')) and not list(p.rglob('*.exe')) and not list(p.rglob('*.pdb'))
assert not list(p.rglob('target')) and not list(p.rglob('__pycache__'))
source_paths={x['path'] for x in b['source_files']}
artifacts=[]
for x in sorted(p.rglob('*')):
 if not x.is_file() or x.name=='manifest.json' or not x.stat().st_size:continue
 assert x.stat().st_size<100*1024*1024,x
 if x.suffix=='.bin':assert x.relative_to(p).as_posix() in source_paths,x
 role='selected_input' if x.relative_to(p).as_posix() in source_paths else 'license' if x.parent.name=='licenses' else 'portable_tool' if x.parent==p and x.suffix in {'.py','.ps1'} else 'evidence'
 artifacts.append({'role':role,'path':x.relative_to(p).as_posix(),'sha256':sha(x),'bytes':x.stat().st_size})
checks={'selected575_source_integrity':{'status':'pass','evidence':'source-bindings.json'},'parent3844_artifacts_preserved':{'status':'pass','evidence':'provenance/selected-build-manifest.json','scope':'All3844 verifiedbeforecopy; originalsnotmodified'},'embedded_images_and_paths':{'status':'pass','evidence':'checks/source-dependencies.json','scope':'125references,608lockedentries; no missinglocalcheckoutasset'},'relocated_host':{'status':'pass','evidence':'checks/host/result.json','scope':'39model/66SDK-host/24expectedrejections;fakeSDKnotphysicalorESPABI'},'Cargo_metadata':{'status':'pass','evidence':['checks/metadata/result.json','checks/metadata/full-application-result.json'],'scope':'4lockedoffline manifests plus424-package selectedrev4graph; externalcachesnotvendored'},'portable_target_preflight':{'status':'pass','evidence':'checks/preflight-only.json','scope':'Exactesp193/IDF5.4.3 andGitfallback checked; no target compilation'},'inherited_target_build':{'status':'pass','evidence':'provenance/inherited-target/BUILD-RESULTS.md','scope':'Originalselected575-inputesp193/IDF5.4.3rev4build/UF2parser evidence; NOT rerunhere'},'new_target_build_or_package':{'status':'incomplete','reason':'NOT_RUN; suppliedofflinecheck/buildlauncher; originalUF2/BIN/ELFomittedandpreserved'},'hardware_publication':{'status':'incomplete','reason':'No firmwareedit/reflash/COM/USB/SD/JTAG/hardware/publication bythistask'}}
m={'overall':'INCOMPLETE','source_export':'PASS','scope':'Complete selectedv26 app/source/assets/harnesses pluscompact inheritedtargetevidence; no newtargetbuild/images/hardware','selected_variant':'v26-key-diag-access-20261104','selected_build_manifest':{'path':'provenance/selected-build-manifest.json','sha256':b['selected_manifest_sha256'],'original_artifacts':3844},'selected_snapshot':{'path':'provenance/selected-prebuild-snapshot.json','sha256':b['selected_snapshot_sha256'],'inputs':575},'original_selected_images_omitted':b['original_selected_images'],'files_bytes':sum(x['bytes'] for x in artifacts),'largest_file_bytes':max(x['bytes'] for x in artifacts),'checks':checks,'artifacts':artifacts}
(p/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
for a in artifacts:assert sha(p/a['path'])==a['sha256']
print('V26_PORTABLE_SOURCE_EXPORT_PASS',len(artifacts),'artifacts;',m['files_bytes'],'bytes;largest',m['largest_file_bytes'],'manifestSHA256',sha(p/'manifest.json'))
