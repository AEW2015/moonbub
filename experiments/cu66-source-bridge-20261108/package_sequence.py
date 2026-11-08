"""Emit existing Sequence-loader package only after executed oracle/fault gates."""
from pathlib import Path
import hashlib,importlib.util,json,shutil,sys
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
OUT=HERE/'package12'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
result=json.loads((HERE/'video12/result.json').read_text())
source=json.loads((HERE/'video12-source.json').read_text())
assert len(result['rows'])==12
for name in ('native04','endpoint04'):
    run=json.loads((HERE/name/'execution.json').read_text());assert run['status']=='PASS' and all(r['exit_code']==0 for r in run['commands'])
negative=json.loads((HERE/'native04/video12-negative.stdout').read_text())
endpoint=json.loads((HERE/'endpoint04/video12.stdout').read_text())
assert negative==dict(negative_cases=38,final_frame=11,rollback_and_prior_ownership=True)
assert endpoint['frames']==12 and endpoint['HUD_words']==253440 and endpoint['allocation_failures']==0 and endpoint['arena_cap']==98304 and endpoint['arena_peak']<=98304
assert endpoint['malformed_and_late_failure_checks']==24 and endpoint['recovery_checks']==12
assert all(len({r[key] for r in result['rows']})==12 for key in ('source_rgb24_sha256','canonical_yuv_u8_sha256','hud_words_u16le_sha256','display_rgb565_u16le_sha256'))
if OUT.exists():raise ValueError('fresh package required')
OUT.mkdir()
rows=[]
for row in result['rows']:
    src=HERE/'video12'/row['packet'];assert sha(src)==row['sha256'] and src.stat().st_size==row['bytes']<=49152
    shutil.copyfile(src,OUT/src.name)
    rows.append(dict(id=row['id'],reference_id=row['reference_id'],key=row['key'],files={'cu66':dict(path=src.name,bytes=row['bytes'],sha256=row['sha256'])},source_rgb24_sha256=row['source_rgb24_sha256'],canonical_yuv_u8_sha256=row['canonical_yuv_u8_sha256'],hud_words_u16le_sha256=row['hud_words_u16le_sha256'],display_rgb565_u16le_sha256=row['display_rgb565_u16le_sha256'],dispatch=row['dispatches'],hud_envelope=row['hud_envelope']))
manifest=dict(schema='dy71-sequence-manifest-v3',profile='dy71-sequence-v3',status='PASS_FRESH_SOFTWARE_REFERENCE_AND_FAULTS',qualified_frame_count=12,dimensions=[720,480],source_kind='NEW local motion-test first12 decoded frames; NOT original Mass Effect120s clip; offline encoding, no live encoder claim',source=source,frames=rows,qualification={'native_oracle':'exact cu66-native-v69 snapshot native04','native_full_frame_oracles':12,'native_fault_cases':38,'HUD_endpoint':'exact V48 native,host64bit98,304-byte arena','HUD_endpoint_result':endpoint,'hardware_status':'NOT_TESTED','network_status':'NOT_SENT','physical_30fps_proven':False},evidence_sha256={str(p.relative_to(HERE)).replace('\\','/'):sha(p) for p in (HERE/'video12/result.json',HERE/'native04/execution.json',HERE/'native04/video12-oracle.stdout',HERE/'native04/video12-negative.stdout',HERE/'endpoint04/execution.json',HERE/'endpoint04/video12.stdout')})
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
# Import and run only pure Sequence loading/read validation. Never call main/upload.
loader=Path('C:/moon/publish/host/dy71-sequence-v3/sequence_sender.py')
sys.path.insert(0,str(loader.parent));spec=importlib.util.spec_from_file_location('qualified_source_sequence_loader',loader);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
seq=mod.Sequence(OUT/'manifest.json','dy71-sequence-v3',12)
for i in range(12):seq.read(i)
(OUT/'loader-validation.json').write_text(json.dumps(dict(status='PASS',packets=12,loader_sha256=sha(loader),core_sha256=sha(loader.with_name('dyn1_sequence_core.py')),manifest_sha256=sha(OUT/'manifest.json'),network_opened=False),indent=2)+'\n')
snapshot=HERE/'dependencies'
snapshot.mkdir()
for name,expected in result['source_sha256'].items():
    p=Path(name);assert sha(p)==expected
    rel=p.relative_to(HERE.parent);dest=snapshot/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
(snapshot/'source-bindings.json').write_text(json.dumps(result['source_sha256'],indent=2)+'\n')
print(json.dumps(dict(status=manifest['status'],package=str(OUT),manifest_sha256=sha(OUT/'manifest.json'),pure_loader_pass=True,dependency_python_files=len(result['source_sha256']),network_opened=False)))
