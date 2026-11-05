"""Offline parser tests plus actual exported Rust formatter interoperability."""
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path
import test_cpl1_snapshot as vectors

P=Path(__file__).resolve().parent
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--firmware-export',type=Path,required=True)
ap.add_argument('--evidence',type=Path,required=True)
ap.add_argument('--rustc',default=str(Path.home()/'.cargo/bin/rustc.exe'))
a=ap.parse_args();F=a.firmware_export.resolve();O=a.evidence.resolve()
assert not O.exists() and not O.is_relative_to(P) and not P.is_relative_to(O)
assert not O.is_relative_to(F) and not F.is_relative_to(O)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={p.relative_to(P).as_posix():sha(p)for p in P.rglob('*')if p.is_file()and'__pycache__'not in p.parts}
manifest=sha(F/'manifest.json');O.mkdir();steps=[]
env=dict(os.environ);env['PYTHONDONTWRITEBYTECODE']='1'
def run(name,command,code=0):
    r=subprocess.run(command,cwd=P,env=env,capture_output=True,text=True)
    log=O/(name+'.log');log.write_text(r.stdout+r.stderr,encoding='utf-8')
    steps.append(dict(name=name,command=command,returncode=r.returncode,log_sha256=sha(log)))
    assert r.returncode==code,(name,r.returncode,r.stdout,r.stderr)
    return r.stdout
run('firmware-before',[sys.executable,str(F/'verify_source.py')])
run('parser-unit',[sys.executable,'-B','-m','unittest','discover','-s',str(P),'-v'])
paths={name:F/'handheld/src'/name for name in ['cpl1.rs','diag_pages.rs','streaming/telemetry.rs']}
for path in paths.values():assert path.is_file()
source='\n'.join([
    '#[path='+json.dumps(str(paths['streaming/telemetry.rs']))+'] pub mod telemetry;',
    'mod streaming {pub use crate::telemetry;}',
    '#[path='+json.dumps(str(paths['diag_pages.rs']))+'] mod diag_pages;',
    '#[path='+json.dumps(str(paths['cpl1.rs']))+'] mod cpl1;',
    'fn main(){let mut words=['+','.join(str(x)+'u32'for x in vectors.words())+'];',
    'if std::env::args().any(|x|x=="bad-crc"){words[33]=0x12345678;}',
    'let s=cpl1::Snapshot{words};for i in 0..10{println!("{}",cpl1::page(&s,i).unwrap().as_str());}}',
])
program=O/'actual_formatter.rs';program.write_text(source,encoding='utf-8')
exe=O/'actual_formatter.exe'
run('rust-version',[a.rustc,'+stable','-Vv'])
run('formatter-compile',[a.rustc,'+stable','--edition=2021',str(program),'-o',str(exe)])
for label,args,expected in [('valid',[],0),('bad-crc',['bad-crc'],2)]:
    text=run(label+'-formatter',[str(exe),*args])
    log=O/(label+'-pages.log');log.write_text(text,encoding='utf-8')
    result=O/(label+'-result.json')
    run(label+'-parser',[sys.executable,str(P/'cpl1_snapshot.py'),'--log',str(log),'--expectation',str(P/'frame0-expectation.json'),'--require-fixture','--output',str(result)],expected)
    r=json.loads(result.read_text());assert r['fixture']['matches']==(expected==0)
    assert r['fields']['canvas_crc32_hex']==('4c5725e5'if expected==0 else'12345678')
run('firmware-after',[sys.executable,str(F/'verify_source.py')]);assert sha(F/'manifest.json')==manifest
after={p.relative_to(P).as_posix():sha(p)for p in P.rglob('*')if p.is_file()and'__pycache__'not in p.parts};assert before==after
result=dict(status='PASS',scope='Synthetic snapshot serialized by actual exported v32 formatter; offline host interoperability only',
    parser_tests=16,selected_firmware_manifest_sha256=manifest,
    actual_formatter_source_bindings={n:sha(p)for n,p in paths.items()},host_source_bindings=before,
    fixture_expectation_sha256=sha(P/'frame0-expectation.json'),valid_snapshot_match=True,bad_actual_crc_preserved_and_rejected=True,
    steps=steps,source_unchanged=True,hardware='NONE',target_build='NOT_RUN',physical_values='NOT_MEASURED')
(O/'result.json').write_text(json.dumps(result,indent=2)+'\n')
rows=[dict(path=p.relative_to(O).as_posix(),sha256=sha(p),bytes=p.stat().st_size)for p in sorted(O.rglob('*'))if p.is_file()]
(O/'manifest.json').write_text(json.dumps(dict(files=rows),indent=2)+'\n')
print('CPL1_OFFLINE_FORMATTER_INTEROP_PASS')
