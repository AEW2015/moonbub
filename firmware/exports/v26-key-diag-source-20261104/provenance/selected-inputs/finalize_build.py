"""Bind the unflashed v26 target result. No programming or runtime claims."""
from pathlib import Path
import datetime,hashlib,json,re,shutil,struct,subprocess,sys
P=Path(__file__).resolve().parent;E=P/'evidence'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def readlog(name):
 b=(E/name).read_bytes();return b.decode('utf-16'if b.startswith((b'\xff\xfe',b'\xfe\xff'))else'utf-8-sig')
def main():
 stage=sys.argv[1];checkstage=sys.argv[2];target=Path(sys.argv[3])
 snap=E/f'prebuild-{stage}/snapshot.json';inputs=json.loads(snap.read_text())
 for rel,h in inputs['files'].items():assert sha(P/rel)==h,rel
 parent=json.loads((P/'parent-v25.json').read_text());base=Path(parent['origin'])
 assert sha(base/'evidence/manifest.json')==parent['manifest_sha256']
 for rel,h in parent['sources'].items():assert sha(base/rel)==h,rel
 for rel,row in parent['artifacts'].items():assert sha(base/rel)==row['sha256'],rel
 # Match checked application source/config with the final built source. Root
 # helpers/docs may have gained packaging evidence between the two snapshots.
 checked=json.loads((E/f'prebuild-{checkstage}/snapshot.json').read_text())
 for rel,h in inputs['files'].items():
  if rel.startswith(('handheld/','handheld-dfu/')):assert checked['files'][rel]==h,rel
 assert 'Finished `release`'in readlog(f'target-check-{checkstage}.log')
 assert 'Finished `release`'in readlog(f'target-build-{stage}.log')
 invocation=json.loads((E/f'target-build-{stage}-invocation.json').read_text(encoding='utf-8-sig'))
 assert invocation['snapshot_sha256']==sha(snap)
 assert Path(invocation['target']).resolve()==target.resolve()
 assert Path(invocation['source']).resolve()==(P/'handheld').resolve()
 rel=target/'xtensa-esp32s3-espidf/release'
 configs=list(rel.glob('build/esp-idf-sys-*/out/build/config/sdkconfig.h'));assert len(configs)==1
 sdk=configs[0];bindings=sdk.parents[2]/'bindings.rs';assert bindings.exists()
 shutil.copy2(sdk,E/'compiled-sdkconfig.h');shutil.copy2(bindings,E/'compiled-idf-bindings.rs')
 v24=P.parent/'v24-runtime-diagnostics-20261104'
 assert sdk.read_bytes()==(v24/'evidence/compiled-sdkconfig.h').read_bytes(),'SDK changed'
 assert not re.search(r'^#define CONFIG_SPIRAM 1$',sdk.read_text(),re.M)
 binding_text=bindings.read_text();assert re.search(r'pub type StackType_t\s*=\s*u8;',binding_text)
 idf=Path.home()/'.espressif/esp-idf/v5.4.3';tasks=idf/'components/freertos/FreeRTOS-Kernel/tasks.c';port=idf/'components/freertos/FreeRTOS-Kernel/portable/xtensa/include/freertos/portmacro.h'
 assert sha(tasks)=='e9b5676a35b5b8b9173b4b187173f9cbfae4808ddc902be2f25f0f9e5f463538'
 assert sha(port)=='3d7bfecf4a97874a41678612daf71ce763e29fc84ca8a81edba6739aa5e3d867'
 old=json.loads((v24/'evidence/build-manifest.json').read_text());size=Path(old['memory']['size_tool'])
 elf=P/'release/moonshine-rev4.elf';binary=P/'release/moonshine-rev4.bin';uf2=P/'release/moonshine-rev4.uf2'
 assert sha(elf)==sha(rel/'handheld')==sha(E/f'v26-key-diag-access-rev4-{stage}.elf')
 sections_log=subprocess.check_output([str(size),'-A',str(elf)],text=True);(E/'elf-sections.log').write_text(sections_log)
 sections={k:int(v)for k,v in re.findall(r'^(\.\S+)\s+(\d+)\s+\d+\s*$',sections_log,re.M)}
 static=sum(sections[k]for k in ['.dram0.dummy','.dram0.data','.dram0.bss'])
 r=subprocess.run(['python',str(P/'tools/check_memory_budget.py'),'--sdkconfig',str(sdk),'--elf',str(elf),'--size-tool',str(size)],capture_output=True,text=True);(E/'memory-budget.log').write_text(r.stdout+r.stderr);r.check_returncode()
 raw=binary.read_bytes();desc=raw[32:288];assert len(desc)==256 and struct.unpack_from('<I',desc)[0]==0xabcd5432
 assert desc[144:176].hex()==sha(elf),'SDK embedded ELF identity mismatch'
 app={name:desc[start:start+n].split(b'\0',1)[0].decode('ascii',errors='replace')for name,start,n in [('version',16,32),('project',48,32),('time',80,16),('date',96,16),('idf',112,32)]};app['sdk_embedded_elf_sha256']=desc[144:176].hex()
 blocks=uf2.stat().st_size//512;assert f'PASS: {blocks} blocks parsed by production DFU parser'in readlog('uf2-validation.log')
 assert 0<len(raw)<=0x500000
 frames=json.loads((E/'stack-frames-v26.json').read_text());assert frames['elf_sha256']==sha(elf)
 source_stage=json.loads((E/'source-stage-manifest.json').read_text())
 metadata={'variant':'v26-key-diag-access-20261104','board':'rev4','installed':False,'scope':'Application-only offline SDK candidate; physical diagnostic access NOT_RUN','images':{f.name:{'sha256':sha(f),'bytes':f.stat().st_size}for f in [elf,binary,uf2]},'prebuild_snapshot_sha256':sha(snap),'sdk_app_description':app,'physical_acceptance':'NOT_RUN'}
 (P/'release/moonshine-rev4.json').write_text(json.dumps(metadata,indent=2)+'\n')
 manifest={'overall':'INCOMPLETE','reason':'Offline source/host/target/package gates pass; KeyDiag stack remains provisional and physical exclusion/drain, stack/logger/heap/SPI WCET gates NOT_RUN.','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'variant':metadata['variant'],'installed':False,'hardware_actions':'NONE','prebuild':{'stage':stage,'check_stage':checkstage,'snapshot':snap.relative_to(P).as_posix(),'sha256':sha(snap),'inputs':len(inputs['files']),'post_build_match':True},'parent':{'source_inputs':len(parent['sources']),'artifacts':len(parent['artifacts']),'manifest_sha256':parent['manifest_sha256'],'status':'UNCHANGED'},'build':{'invocation':invocation,'toolchain':'esp193','rustc':subprocess.check_output([str(Path.home()/'.cargo/bin/rustc.exe'),'+esp193','-Vv'],text=True),'idf':'5.4.3','compiled_sdk_identical_v24':True,'compiled_sdk_sha256':sha(sdk),'compiled_idf_bindings_sha256':sha(bindings),'bindings_identical_v24':bindings.read_bytes()==(v24/'evidence/compiled-idf-bindings.rs').read_bytes()},'checks':{'model':source_stage['model_tests'],'SDK_host':source_stage['SDK_host_tests'],'compiler_expected_rejections':source_stage['compiler_expected_rejections'],'target_check':'PASS','target_build':'PASS','production_DFU_blocks':blocks,'SDK_defaults':'BYTE_IDENTICAL_V24','wire_audio':'UNCHANGED','physical':'NOT_RUN'},'memory':{'static_shared_sram_bytes':static,'v24_static_sram_bytes':old['memory']['static_shared_sram_bytes'],'static_delta_bytes':static-old['memory']['static_shared_sram_bytes'],'guardrail_bytes':163840,'size_tool':str(size),'PSRAM':False,'USB_stack_bytes':4096,'AV_stack_bytes':8192,'KeyDiag_stack_bytes':4096,'KeyDiag_stack_status':'PROVISIONAL_PENDING_STATIC_REVIEW_AND_PHYSICAL_GATE','selected_frames':'evidence/stack-frames-v26.json','actual_runtime_stack_heap':'NOT_MEASURED','stack_watermark_unit_bytes':1,'stack_unit_sources':{'bindings':sha(bindings),'tasks.c':sha(tasks),'portmacro.h':sha(port)}},'flash':{'binary_bytes':len(raw),'factory_start':0x100000,'factory_size':0x500000,'headroom_bytes':0x500000-len(raw),'UF2_blocks':blocks,'scope':'APP_ONLY_PRODUCTION_PARSER_PASS; NOT_INSTALLED'},'sdk_app_description':app,'limitations':['Source/fake SDK tests do not prove concurrent physical service exclusion/drain.','Selected ELF prologues/calls do not close indirect/SDK/FFI/logger/interrupt/thread stack bounds.','Fixed165-byte payload maximum plus64-byte framing reserve is not actual logger framing or stack proof.','Initial/action deadlines are cooperative; blocked synchronous SPI is not preempted.','AKD1 external-reset ABA is unobservable; exclusive operator/no external reset required.','Unowned boot/quarantined failures require explicit operator restart and fresh qualified FPGA configuration; no fabricated RecoveryConfirmed.','No hardware/COM/SD/JTAG/flash action, no existing stack/default/SDK/wire/audio identity change.']}
 manifest['artifacts']={f.relative_to(P).as_posix():{'bytes':f.stat().st_size,'sha256':sha(f)}for f in sorted(P.rglob('*'))if f.is_file() and not any(x in f.parts for x in ['target','__pycache__','.embuild','.git']) and f.relative_to(P).as_posix()not in inputs['files'] and f!=E/'build-manifest.json'}
 (E/'build-manifest.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
 print(json.dumps({'overall':manifest['overall'],'static_sram':static,'binary_bytes':len(raw),'UF2_blocks':blocks,'sdk_elf_sha256':app['sdk_embedded_elf_sha256'],'images':metadata['images'],'manifest_sha256':sha(E/'build-manifest.json')},indent=2))
if __name__=='__main__':main()
