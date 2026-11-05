"""Full locked/offline application graph, no target compilation."""
import argparse,json,os,shutil,subprocess,tempfile
from pathlib import Path
p=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--cargo');a=ap.parse_args();cargo=a.cargo or shutil.which('cargo') or str(Path.home()/'.cargo/bin/cargo.exe')
out=p/'checks/metadata';out.mkdir(parents=True,exist_ok=True);env=dict(os.environ);env['GIT_CEILING_DIRECTORIES']=str(p)
with tempfile.TemporaryDirectory(prefix='v26-full-meta-') as temp:
 env['CARGO_TARGET_DIR']=temp
 cmd=[cargo,'+esp193','metadata','--offline','--locked','--format-version','1','--filter-platform','xtensa-esp32s3-espidf','--features','rev4','--manifest-path',str(p/'handheld/Cargo.toml')]
 r=subprocess.run(cmd,cwd=p,env=env,capture_output=True,text=True,encoding='utf-8')
 (out/'full-application-metadata.stderr.log').write_text(r.stderr,encoding='utf-8');r.check_returncode();m=json.loads(r.stdout)
 local=[x for x in m['packages'] if x.get('source') is None];assert all(Path(x['manifest_path']).resolve().is_relative_to(p) for x in local)
 record={'status':'PASS','command':cmd,'returncode':r.returncode,'packages':len(m['packages']),'local_packages':[x['name'] for x in local],'git_sources':sorted({x['source'] for x in m['packages'] if (x.get('source') or '').startswith('git+')}),'resolved_package_license_inventory':[{'name':x['name'],'version':x['version'],'source':x.get('source'),'license':x.get('license')} for x in m['packages']],'scope':'Full selectedrev4 dependency metadata resolvedfromexternalinstalledCargo cache; no target compilation; dependenciesnotvendored'}
 (out/'full-application-result.json').write_text(json.dumps(record,indent=2)+'\n')
 print('FULL_LOCKED_OFFLINE_REV4_METADATA_PASS',len(m['packages']),'packages; localpackages',[x['name'] for x in local])
