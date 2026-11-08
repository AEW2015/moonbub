from pathlib import Path
import json,hashlib,importlib.util,sys,time
sys.dont_write_bytecode=True
p=Path('C:/moon/dev/experiments/stb1-v55-video12-real-rust-system-20261108');bridge=Path('C:/moon/dev/experiments/cu66-source-bridge-20261108');deps=bridge/'dependencies';sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest();pins=json.loads((deps/'source-bindings.json').read_text())
for f,h in pins.items():assert sha(deps/Path(f).relative_to(bridge.parent))==h,f
spec=importlib.util.spec_from_file_location('video12_independent_bridge',bridge/'bridge.py');mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod);mod.EXPERIMENTS=deps;models=mod.load_models();h=models[0];rx=models[-1].Receiver('CU66');m=json.loads((bridge/'package12/manifest.json').read_text());rows=[];t=time.monotonic()
for i,row in enumerate(m['frames']):
 a=rx.receive((bridge/'package12'/row['files']['cu66']['path']).read_bytes());planes=b''.join(x.astype('uint8').tobytes()for x in a[0]);hud=b''.join(x['words'].astype('<u2').tobytes()for x in a[1]);display=h.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(a[0])),tuple(x['words']for x in a[1])).astype('<u2').tobytes()
 for label,data,key,suffix in [('canonical',planes,'canonical_yuv_u8_sha256','canonical.u16'),('hud',hud,'hud_words_u16le_sha256','hud'),('display',display,'display_rgb565_u16le_sha256','rgb565')]:
  assert hashlib.sha256(data).hexdigest()==row[key];assert data==(p/'goldens'/f'frame{i}.{suffix}').read_bytes(),(i,label)
 rows.append({'id':i,'canonical_HUD_display_match_manifest_and_native69':True})
actual={str(Path(x.__file__).resolve()):sha(Path(x.__file__).resolve())for x in list(sys.modules.values())if getattr(x,'__file__',None)and str(Path(x.__file__).resolve()).lower().startswith(str(bridge.parent).lower())and Path(x.__file__).suffix=='.py'}
(p/'python-reference-result.json').write_text(json.dumps({'status':'PASS_FROZEN_PYTHON_NATIVE69_MANIFEST_ALL12_IDENTICAL','frames':rows,'wall_seconds':time.monotonic()-t,'imported_sources_sha256':actual,'preserved_dependency_source_count':len(pins),'packet_manifest_sha256':sha(bridge/'package12/manifest.json')},indent=2));print('PASS frozen Python/native69 all12 goldens',time.monotonic()-t)
