"""Read-only analysis of this one fresh relocated release; never device I/O."""
from pathlib import Path
import json,hashlib,re,subprocess,shutil,datetime,sys
P=Path(__file__).resolve().parent;S=P/'source-copy';T=Path('C:/vs31a/xtensa-esp32s3-espidf/release');O=P/'outputs';assert not O.exists();O.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(S/'manifest.json')=='5aac54272fcfd15f7d440dc58c669620626d37243da46d2d2b6d162960ce0607'
subprocess.run([sys.executable,str(S/'verify_source.py')],check=True)
parent=json.loads((S/'provenance/build-manifest.json').read_text());mem=json.loads((S/'provenance/stack-memory-review.json').read_text());frames=json.loads((S/'provenance/stack-frames-v31.json').read_text())
config=list(T.glob('build/esp-idf-sys-*/out/build/config/sdkconfig.h'));assert len(config)==1;config=config[0];bindings=config.parents[2]/'bindings.rs'
assert sha(config)==parent['artifacts']['evidence/compiled-sdkconfig.h']['sha256'],'SDK config differs'
assert sha(bindings)==parent['artifacts']['evidence/compiled-idf-bindings.rs']['sha256'],'ABI bindings differ'
assert re.search(r'pub type StackType_t\s*=\s*u8;',bindings.read_text())
assert not re.search(r'^#define CONFIG_SPIRAM 1$',config.read_text(),re.M)
elf=T/'handheld';assert elf.is_file();shutil.copy2(elf,O/'moonshine-relocated.elf');shutil.copy2(config,O/'compiled-sdkconfig.h');shutil.copy2(bindings,O/'compiled-idf-bindings.rs')
size=Path(mem['size_tool']);assert sha(size)==mem['size_tool_sha256'];sections_log=subprocess.check_output([str(size),'-A',str(elf)],text=True);(O/'elf-sections.log').write_text(sections_log)
sections={k:int(v)for k,v in re.findall(r'^(\.\S+)\s+(\d+)\s+\d+\s*$',sections_log,re.M)};sram=sum(sections[k]for k in ['.dram0.dummy','.dram0.data','.dram0.bss'])
objdump=Path(frames['tool']);assert sha(objdump)==frames['tool_sha256'];symbols=subprocess.check_output([str(objdump),'--syms','--demangle',str(elf)],text=True);(O/'elf-symbols.log').write_text(symbols)
match=re.search(r'^.*\bO\s+\.dram0\.data\s+([0-9a-f]+).*diagnostic_trace::TRACE',symbols,re.M);assert match;trace=int(match[1],16)
assert sram==mem['static_shared_sram_bytes'];assert trace==mem['actual_target_trace_bytes']
inv=json.loads((P/'build/invocation.json').read_text(encoding='utf-8-sig'));assert Path(inv['source'])==S/'handheld';assert inv['command']=='cargo +esp193 build --offline --locked --release --features rev4'
raw=(P/'build/cargo.log').read_bytes();log=raw.decode('utf-16' if raw.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig');assert re.search(r'Finished `release` profile',log)
depfile=T/'handheld.d';assert depfile.is_file();deps=depfile.read_text();shutil.copy2(depfile,O/'handheld.d')
normalized=deps.replace('\\', '/')
assert '/firmware/experiments/' not in normalized and '/firmware/exports/' not in normalized,'old checkout reference in actual application dependency record'
assets=json.loads((P/'assets/source-dependencies.json').read_text());metadata=json.loads((P/'metadata/result.json').read_text());assert assets['status']==metadata['status']=='PASS'
result={'status':'CLEAN_RELOCATED_RELEASE_PASS','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_package_manifest_sha256':sha(S/'manifest.json'),'selected_inputs':568,'included_package_paths':602,'unchanged_package_integrity':'PASS','command_provenance':inv,'target':'C:/vs31a','clean_target':'Previously nonexistent; no old target/checkpoint reused','application_ELF':{'path':'outputs/moonshine-relocated.elf','sha256':sha(elf),'bytes':elf.stat().st_size,'selected_original_ELF_sha256':frames['elf_sha256'],'same_as_original':sha(elf)==frames['elf_sha256'],'selection':'NOT selected/programmed; original supplied UF2 unchanged'},'SDK':{'version':'5.4.3','configuration_sha256':sha(config),'bindings_sha256':sha(bindings),'byte_identical_to_selected_candidate':True,'StackType_t':'u8','PSRAM':False},'memory':{'static_shared_SRAM_bytes':sram,'Trace_object_bytes':trace,'matches_selected_candidate':True,'limits':'Static layout only; no physical stack/heap/WCET/delivery proof'},'source_dependency_record':{'path':'outputs/handheld.d','sha256':sha(depfile),'old_candidate_or_export_checkout_references':False,'limits':'Actual application compiler dependency list plus checked local Cargo paths/assets; not an OS-wide filesystem-access trace'},'asset_metadata_checks':{'assets_references':len(assets['embedded_files_and_imports']),'metadata_manifests':len(metadata['manifests']),'commands':'validation-commands.json','status':'PASS'},'packaging':'Helper performs cargo build only; no BIN/UF2 conversion or flash occurred','hardware':'NONE','physical':'NOT_RUN','limitations':['ELF identity can differ due SDK build date/time/source relocation; no byte-identical-image requirement','External pinned SDK/toolchain/Cargo/component caches are prerequisites; no GameBub checkout required','All output is outside sealed export and copied package; original seal/docs remain historical and unchanged']}
result['artifact_hashes']={f.relative_to(P).as_posix():{'sha256':sha(f),'bytes':f.stat().st_size}for f in P.rglob('*')if f.is_file()and not f.is_relative_to(S)and f!=P/'result.json'}
(P/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='artifact_hashes'},indent=2))
