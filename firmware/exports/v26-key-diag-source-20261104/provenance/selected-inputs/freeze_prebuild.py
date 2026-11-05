"""Append-only source snapshot before each target attempt, never edits parents."""
from pathlib import Path
import hashlib,json,sys,datetime,shutil
P=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
stage=sys.argv[1];out=P/'evidence'/('prebuild-'+stage)
assert not out.exists(),'Prebuild stage already exists'
parent=json.loads((P/'parent-v25.json').read_text());base=Path(parent['origin'])
assert sha(base/'evidence/manifest.json')==parent['manifest_sha256']
for rel,h in parent['sources'].items():assert sha(base/rel)==h,rel
for rel,row in parent['artifacts'].items():assert sha(base/rel)==row['sha256'],rel
files={p.relative_to(P).as_posix():sha(p) for folder in ['handheld','handheld-dfu','tests','tools'] for p in(P/folder).rglob('*') if p.is_file() and not any(x in p.parts for x in ['target','__pycache__','.git'])}
for rel in parent['sources']:
 if rel not in files:files[rel]=sha(P/rel)
for p in P.iterdir():
 if p.is_file() and p.suffix in ['.py','.ps1','.md','.json']:files[p.name]=sha(p)
out.mkdir()
for rel,h in files.items():
 dest=out/'inputs'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(P/rel,dest)
for name in ['source-stage-manifest.json','source-bindings.json','integration.diff']:
 src=P/'evidence'/name
 if src.exists():shutil.copy2(src,out/name)
review=json.loads((P/'evidence/source-stage-manifest.json').read_text())
review_out=out/'review-evidence';review_out.mkdir()
for name,h in review['artifacts'].items():
 src=P/'evidence'/name;assert sha(src)==h,name;shutil.copy2(src,review_out/name)
result={'stage':stage,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':files,'parent_manifest_sha256':parent['manifest_sha256'],'parent_sources':len(parent['sources']),'parent_artifacts':len(parent['artifacts']),'reviewed_stage_manifest_sha256':sha(P/'evidence/source-stage-manifest.json'),'SDK_config_guards':{r:h for r,h in files.items() if 'sdkconfig'in r or r.endswith('handheld/Cargo.toml') or r.endswith('handheld/Cargo.lock')},'hardware_actions':'NONE'}
(out/'snapshot.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print('Frozen',stage,len(files),'files',sha(out/'snapshot.json'))
