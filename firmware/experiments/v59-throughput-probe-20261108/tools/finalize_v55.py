from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[1];V54=Path('C:/moon/dev/experiments/v54-stb1-failure-diag-20261108');V48=Path('C:/moon/publish/firmware/experiments/v48-dy71-selftest-control-20261107');HOST=Path('C:/moon/builds/v55-host01')
V49=V48.parent/'v49-dy71-canonical-huffman-20261107';V50=V48.parent/'v50-dy71-hud-read-slice-20261108';V51=V48.parent/'v51-dy71-free-probe-20261108';V53=ROOT.parent/'v53-hbu-status-batch-20261108'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def function(text,name):
 pos=text.index(name);start=text.rfind('\n',0,pos)+1;begin=text.index('{',pos);depth=1;end=begin+1
 while depth:depth+=(text[end]=='{')-(text[end]=='}');end+=1
 return text[start:end]
def manifest(root,dirs):return{str(p.relative_to(root)).replace('\\','/'):sha(p)for d in dirs for p in(root/d).rglob('*')if p.is_file()and '__pycache__'not in p.parts}
host=json.loads((HOST/'source-check.json').read_text());assert host['unchanged']
assert all(x['returncode']==0 for x in json.loads((HOST/'execution.json').read_text()))
assert json.loads((ROOT/'evidence/host-decoder-v001/result.json').read_text())['status']=='PASS'
assert json.loads((ROOT/'evidence/stb-adapter-v001/execution.json').read_text())['status']=='PASS'
assert all(x['returncode']==0 for x in json.loads((ROOT/'evidence/hbu-adapter-v001/execution.json').read_text())['commands'])
assert all(x['returncode']==0 for x in json.loads((ROOT/'evidence/free-probe-v001/execution.json').read_text()))
oracle=json.loads((ROOT/'evidence/native-oracles/result.json').read_text());assert oracle['status']=='PASS'
assert sha(ROOT/'native/hud.hpp')==sha(V49/'native/hud.hpp')
assert sha(ROOT/'native/endpoint.hpp')==sha(V50/'native/endpoint.hpp')
for p in(ROOT/'native').iterdir():
 if p.is_file()and p.name not in('hud.hpp','endpoint.hpp'):assert sha(p)==sha(V48/'native'/p.name)
cu=Path('handheld/src/cu66')
fragments={}
for src,dst,names in((V51/cu/'network_usb.rs',ROOT/cu/'network_usb.rs',['fn free_probe(','fn largest_probe(','fn internal_free(','fn internal_largest(']),(V53/cu/'local.rs',ROOT/cu/'local.rs',['fn hbu_status_words(']),(V53/cu/'local_usb.rs',ROOT/cu/'local_usb.rs',['fn hbu_status_words(']),(V53/cu/'network_driver.rs',ROOT/cu/'network_driver.rs',['fn bulk_status('])):
 for name in names:
  a=function(src.read_text(),name);b=function(dst.read_text(),name);assert a==b;fragments[str(dst.relative_to(ROOT))+'/'+name]=hashlib.sha256(b.encode()).hexdigest()
# Reverse only the selected named deltas and prove the remaining application logic is exactV54.
text=(ROOT/cu/'network_usb.rs').read_text();base=(V54/cu/'network_usb.rs').read_text()
for name in('fn free_probe(','fn largest_probe('):text=text.replace(function(text,name),function(base,name),1)
for name in('fn internal_free(','fn internal_largest('):text=text.replace(function(text,name)+'\n','',1)
assert text==base
text=(ROOT/cu/'network_driver.rs').read_text();base=(V54/cu/'network_driver.rs').read_text();assert text.replace(function(text,'fn bulk_status('),function(base,'fn bulk_status('),1)==base
for name in('local.rs','local_usb.rs'):
 text=(ROOT/cu/name).read_text();base=(V54/cu/name).read_text();text=text.replace(function(text,'fn hbu_status_words(')+'\n','',1)
 assert '\n'.join(x for x in text.splitlines()if x.strip())=='\n'.join(x for x in base.splitlines()if x.strip())
assert (ROOT/'handheld/src/diag_pages.rs').read_text().replace('v55-dy71-stb1-performance-20261108','v54-dy71-stb1-failure-diag-20261108')==(V54/'handheld/src/diag_pages.rs').read_text()
before=manifest(V54,('handheld','handheld-dfu','native'));after=manifest(ROOT,('handheld','handheld-dfu','native'));delta=sorted(k for k,v in after.items()if before.get(k)!=v)
assert len(delta)==7
for key in('handheld/src/cu66/stb1.rs','handheld/src/cu66/stb_failure.rs','handheld/src/cu66/network_io.rs','handheld/src/cu66/report_snapshot.rs','handheld/src/cu66/report_export.rs','handheld/src/cu66/network_wire.rs','handheld/src/cu66/framing.rs','handheld/sdkconfig.defaults'):assert after[key]==before[key]
usb=(ROOT/cu/'network_usb.rs').read_text();guards=['stack_size(16_384)','before.0<114_688||before.1<24_576','Hud::new(98_304)','hud.reserve_internal_heap(free_probe,8192)'];assert all(g in usb for g in guards)
counts={}
for p in HOST.glob('*-test.log'):
 m=re.search(r'test result: ok\. (\d+) passed',p.read_text())
 if m:counts[p.name]=int(m[1])
assert sum(counts.values())==213
result=dict(status='COMBINED_SOURCE_HOST_GATES_PASS_PENDING_REVIEW_TARGET_AND_PHYSICAL',variant='v55-dy71-stb1-performance-20261108',base=str(V54),changed_application_files=delta,exact_source_fragment_sha256=fragments,native_deltas=['V49exacthud.hpp','V50exactendpoint.hpp'],other_native_exactV48=True,V54failure_STB1_wire_guards_preserved=True,heap_stack_reserve_guards=guards,Rust_test_executions=213,callback_tests=4,SDKshim_STB_tests=7,SDKshim_HBU_tests=6,decoder_Python_tests=6,actual_Rust_decoder_vectors=2,native_oracles=oracle['results'],unique_HUD_words=oracle['unique_HUD_words'],full_and_256word_read_comparisons=oracle['full_and_256word_read_comparisons'],stack_risk='V49individualXtensaHuffman192->752(+560) andchannel144->160(+16), combinedcallchain+576bytes; combinedtarget/staticframes/runtimeUNMEASURED',target='NOT_BUILT;rootreviewrequired',physical='NOT_INSTALLED;V54firstphysicalcontrolunchanged',speed_or_FPS_claim=False)
(ROOT/'V55-READINESS.json').write_text(json.dumps(result,indent=2)+'\n')
(ROOT/'composition-delta-proof.json').write_text(json.dumps(dict(status='PASS',reverse_reconstruction='Onlytheexactnamedfragments/nativefiles/variantdifferfromV54',application_delta=delta,selected_source_pins=json.loads((ROOT/'composition.json').read_text())['source_pins'],fragment_sha256=fragments),indent=2)+'\n')
(ROOT/'final-source-bindings.json').write_text(json.dumps(manifest(ROOT,('handheld','handheld-dfu','native','tests','tools')),indent=2)+'\n')
print(json.dumps(result))
