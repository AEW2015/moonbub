from pathlib import Path
import hashlib,json,shutil
root=Path('C:/moon');p=root/'publish/firmware/experiments/v45-dy71-ingress-cache-20261107';release=p/'release-ingress-cache-v001';build=root/'builds/v45-target-run02';system=root/'maintenance/v45-system-cached5';out=p/'evidence/readiness-v001';out.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
b=json.loads((build/'result.json').read_text());assert b['returncode']==0 and not b['source_changes'] and not b['native_changes']
for label,base in [('source',p/'handheld'),('native',p/'native')]:
 for name,h in json.loads((build/f'{label}-before.json').read_text()).items():assert sha(base/name)==h,name
for name,h in json.loads((release/'hashes.json').read_text()).items():assert sha(release/name)==h,name
assert all(x['returncode']==0 for x in json.loads((release/'verification/commands.json').read_text()))
s=json.loads((system/'result.json').read_text());assert (s['frames'],s['accepted'],s['presented'],s['rejected'],s['underruns'])==(5,5,5,0,0)
assert s['actual_HUD_words_written_and_compared']==105600 and s['actual_bus_command21_count']==0
assert s['native_arena_limit']==98304 and s['native_hud_sha256']==sha(p/'native/hud.hpp')
assert s['driver_sha256']==sha(p/'handheld/src/cu66/network_driver.rs')
assert s['native_DLL_sha256']==sha(Path(s['native_DLL_runtime_path']))
for frame in s['canonical_and_raster_comparison']['frames']:assert frame['canonical_mismatched_bytes']==frame['composed_mismatched_pixels']==frame['black_border_mismatches']==0
binding=json.loads((system/'source-binding.json').read_text())
for name,h in binding['files_sha256'].items():assert sha(Path(name))==h,name
loop=root/'maintenance/v45-localhost/run01';n=json.loads((loop/'RESULT.json').read_text());assert n['status']=='PASS' and len(n['host_outcomes'])==12 and all(x['status']=='presented'for x in n['host_outcomes'])
v=json.loads((loop/'independent-telemetry-validation.json').read_text());assert len(v['valid_attempts'])==1 and v['valid_attempts'][0]['received_rows']==31
bit=root/'dev/dy71-v027-20261107-v001/image01/moonbub-v027-lab.bit';assert sha(bit)=='9922aa617c21a03e8a31f932d45e22d905e91d4e263ef593692898d363d07dee'
copies={'target-build.json':build/'result.json','target-source-pins.json':build/'source-before.json','target-native-pins.json':build/'native-before.json','system-result.json':system/'result.json','system-source-binding.json':system/'source-binding.json','system-native-run.log':system/'native-run.log','system-comparison.json':system/'comparison.json','localhost-result.json':loop/'RESULT.json','localhost-telemetry.json':loop/'independent-telemetry-validation.json','localhost-telemetry-negatives.json':loop/'validator-negative-results.json','native-memory-fix.json':root/'maintenance/v45-native-inplace/selected-fix.json','native-corpus.log':root/'maintenance/v45-native-inplace/corpus.log','independent-review.md':root/'maintenance/v45-sequence/INDEPENDENT-REVIEW.md','independent-review-pins.json':root/'maintenance/v45-sequence/INDEPENDENT-REVIEW-PINS.json','telemetry-tests.log':root/'maintenance/v45-telemetry/tests.log','host-qualification.json':root/'maintenance/v45-sequence/HOST-RESULT.json'}
artifacts=[]
for name,src in copies.items():
 assert src.is_file() and src.stat().st_size,src
 dst=out/name;shutil.copyfile(src,dst);artifacts.append({'role':'executed_evidence','path':str(dst),'sha256':sha(dst)})
for name in ['moonshine-rev4.elf','moonshine-rev4.bin','moonshine-rev4.uf2']:artifacts.append({'role':'firmware_image','path':str(release/name),'sha256':sha(release/name)})
artifacts.append({'role':'unchanged_fpga_image','path':str(bit),'sha256':sha(bit)})
manifest={'overall':'INCOMPLETE','offline_candidate_status':'PASS_READY_FOR_CACHED3_THEN_CONDITIONAL_CACHED12_HARDWARE','physical_status':'V45_NOT_INSTALLED_OR_TESTED; V44 FINAL ENDPOINT REMAINS HELD','profile':'dy71-sequence-v3','artifacts':artifacts,'checks':{'target_build':'pass','effective_sdk_static_sram':'pass','production_uf2_parser':'pass','native_driver_wire_tests':'pass','telemetry_and_validator_fault_tests':'pass','localhost_cached12':'pass','selected_system_cached5':'pass','independent_review':'pass','physical_v45_runtime':'incomplete'},'formal_handoff_checker':'UNAVAILABLE_NOT_RUN; manual source/artifact checks only','limits':['Finite bounded diagnostic, not120-second video or30fps.','RTL wrapper excludes physicalSPI/CDC/PLL and targetCPU timing; stable snapshots add delay.','Full HUD readback retained; actual target memory/stack and telemetry completeness must pass before cached12.','Failed replay using wrong DLL and overbroad uncompiled source drift preserved separately; final replay checks actual loaded DLL and compiled inputs.']}
manifest['checks']={name:{'status':status,'evidence':str(out/'system-result.json') if name=='selected_system_cached5' else ('Pending controlled physical trial' if status=='incomplete' else 'Source-bound executed evidence indexed in artifacts')} for name,status in manifest['checks'].items()}
(out/'readiness.json').write_text(json.dumps(manifest,indent=2)+'\n');print(manifest['offline_candidate_status']);print(out/'readiness.json')
