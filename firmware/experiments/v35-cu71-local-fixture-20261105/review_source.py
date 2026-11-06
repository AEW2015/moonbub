from pathlib import Path
import hashlib,json,sys
p=Path(__file__).resolve().parent
h=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def files():return {f.relative_to(p).as_posix():h(f) for folder in ['handheld','handheld-dfu','native','tests','tools'] for f in sorted((p/folder).rglob('*')) if f.is_file() and not any(n in f.parts for n in ['target','.embuild','__pycache__','.git'])}
snapshot=p/'evidence/source-snapshot-v004.json'
if '--freeze' in sys.argv:
 assert not snapshot.exists();snapshot.write_text(json.dumps({'variant':'v35-cu71-local-fixture-20261105','files':files(),'hardware':False},indent=2)+'\n')
else:assert files()==json.loads(snapshot.read_text())['files'],'selected source changed'
print('V35_SOURCE_MATCH')
