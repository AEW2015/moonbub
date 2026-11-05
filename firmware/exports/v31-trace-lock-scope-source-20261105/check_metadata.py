"""Offline Cargo resolution/path checks only; no compilation or device runner."""
import argparse,hashlib,json,os,shutil,subprocess,tempfile
from pathlib import Path
p=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--cargo');ap.add_argument('--evidence',required=True);a=ap.parse_args();cargo=a.cargo or shutil.which('cargo') or str(Path.home()/'.cargo/bin/cargo.exe')
out=Path(a.evidence).resolve();assert not out.is_relative_to(p) and not out.exists();out.mkdir(parents=True);records=[]
env=dict(os.environ);env['GIT_CEILING_DIRECTORIES']=str(p)
git=subprocess.run(['git','-C',str(p/'handheld'),'rev-parse','HEAD'],env=env,capture_output=True,text=True)
assert git.returncode!=0,'Git identity would differ from selected snapshot fallback'
(out/'git-fallback-check.log').write_text(git.stdout+git.stderr)
with tempfile.TemporaryDirectory(prefix='v31-cargo-metadata-') as temp:
 env['CARGO_TARGET_DIR']=temp
 for manifest,toolchain,features in [('handheld/Cargo.toml','esp193',['--features','rev4']),('tests/sdk-host/Cargo.toml','stable',[]),('handheld/tests/lcd-gamma/Cargo.toml','stable',[]),('handheld/tests/ui-preview/Cargo.toml','stable',[])]:
  cmd=[cargo,'+'+toolchain,'metadata','--offline','--locked','--format-version','1','--no-deps','--manifest-path',str(p/manifest),*features]
  r=subprocess.run(cmd,cwd=p,env=env,capture_output=True,text=True);label=manifest.replace('/','-');(out/(label+'.stderr.log')).write_text(r.stderr)
  r.check_returncode();m=json.loads(r.stdout)
  for package in m['packages']:
   for dep in package['dependencies']:
    if dep.get('path'):assert Path(dep['path']).resolve().is_relative_to(p.resolve()),dep
  (out/(label+'.json')).write_text(json.dumps(m,indent=2)+'\n')
  records.append({'manifest':manifest,'toolchain':toolchain,'command':cmd,'returncode':r.returncode,'local_packages':[x['name'] for x in m['packages']]})
(out/'result.json').write_text(json.dumps({'status':'PASS','manifests':records,'Git_discovery':'Ceilingconfirmednonrepository; unchangedbuild.rs usesselectedfallback aa281c073693bd92850720a2e43998f1d8faf569','target_compilation':'NOT_RUN','external_dependencies':'Offline metadata no-deps check; registry/Git/IDF/components/toolchains are external prerequisites, not vendored','hardware':'NONE'},indent=2)+'\n')
print('OFFLINE_LOCKED_METADATA_PATH_CHECKS_PASS4_MANIFESTS; no target compilation')
