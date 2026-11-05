import argparse,hashlib,json,re,tomllib
from pathlib import Path
p=Path(__file__).resolve().parent;refs=[];paths=[]
ap=argparse.ArgumentParser();ap.add_argument('--evidence',required=True);a=ap.parse_args();out=Path(a.evidence).resolve();assert not out.is_relative_to(p) and not out.exists();out.mkdir(parents=True)
sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
def local(f,text,kind):
 x=(f.parent/text).resolve()
 assert x.is_relative_to(p.resolve()) and x.is_file(),(kind,str(f),text)
 refs.append({'source':f.relative_to(p).as_posix(),'reference':text,'resolved':x.relative_to(p).as_posix(),'kind':kind,'sha256':sha(x)})
for f in (p/'handheld').rglob('*.rs'):
 for ref in re.findall(r'include_(?:bytes|str)!\s*\(\s*"([^"\n]+)"',f.read_text()):local(f,ref,'RustEmbeddedFile')
for f in (p/'handheld/res').rglob('*.slint'):
 text=f.read_text()
 for ref in re.findall(r'@image-url\("([^"\n]+)"\)',text):local(f,ref,'SlintImage')
 for ref in re.findall(r'\bfrom\s+"([^"\n]+)"|\bimport\s+"([^"\n]+)"',text):
  ref=next(x for x in ref if x)
  if ref=='std-widgets.slint':continue
  local(f,ref,'SlintImport')
for f in [p/'handheld/Cargo.toml',p/'tests/sdk-host/Cargo.toml',p/'handheld/tests/lcd-gamma/Cargo.toml',p/'handheld/tests/ui-preview/Cargo.toml']:
 def visit(value):
  if isinstance(value,dict):
   if 'path' in value:
    x=(f.parent/value['path']).resolve();assert x.is_relative_to(p.resolve()) and x.exists(),(str(f),value['path']);paths.append({'manifest':f.relative_to(p).as_posix(),'path':value['path'],'resolved':x.relative_to(p).as_posix()})
   for v in value.values():visit(v)
  elif isinstance(value,list):
   for v in value:visit(v)
 visit(tomllib.loads(f.read_text()))
local(p/'handheld/espflash.toml','bootloader.bin','DeclaredBootloaderInput');local(p/'handheld/espflash.toml','partitions.csv','DeclaredPartitionInput');local(p/'handheld/Cargo.toml','bindings_esp_tinyusb.h','IDFBindingsInput')
lock=tomllib.loads((p/'handheld/Cargo.lock').read_text())
(out/'source-dependencies.json').write_text(json.dumps({'status':'PASS','embedded_files_and_imports':refs,'Cargo_local_path_fields':paths,'locked_packages':len(lock['package']),'git_dependencies':[x for x in lock['package'] if x.get('source','').startswith('git+')],'git_identity_behavior':'Unchanged build.rs invokesgit and fallsbackaa281c073693bd92850720a2e43998f1d8faf569; portable launcher checksdiscovery ceiling','external_tools':'Rust esp193/IDF5.4.3/Cargo locked registry+Git crates/Espressif managedcomponents; not vendored'},indent=2)+'\n')
print('LOCAL_EMBEDDED_AND_PATH_DEPENDENCIES_PASS',len(refs),'references;',len(lock['package']),'locked packages')
