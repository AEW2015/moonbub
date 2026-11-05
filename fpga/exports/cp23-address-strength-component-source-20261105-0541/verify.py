from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
b=json.loads((P/'source-bindings.json').read_text())
for n,h in b.items():assert sha(P/n)==h,n
for label in ['full01','physical-abort01']:
 d=P/'reports'/label
 for n,h in json.loads((d/'source-snapshot.json').read_text()).items():assert b[n.replace('\\','/')]==h,n
 assert json.loads((d/'execution.json').read_text())[-1]['returncode']==0
 assert json.loads((d/'result.json').read_text())['status'].startswith('PASS')
for n,h in json.loads((P/'reports/ooc01/source-snapshot.json').read_text()).items():
 n=n.replace('\\','/')
 if n=='synth.tcl':assert sha(P/'reports/ooc01/synth.tcl')==h
 else:assert sha(P/n)==h,n
for n,h in json.loads((P/'unit-bindings.json').read_text()).items():assert sha(P/n)==h,n
for n,h in json.loads((P/'reports/unit01/manifest.json').read_text()).items():assert sha(P/n.replace('\\','/'))==h,n
for n,h in json.loads((P/'reports/arithmetic02/source-snapshot.json').read_text()).items():assert sha(P/n.replace('\\','/'))==h,n
assert 'checks=740672' in(P/'reports/arithmetic02/simulation.log').read_text()
assert 'GATHER_BRAM_NATIVE_UNIT_PASS checked=349440' in(P/'reports/unit01/simulation.log').read_text()
r=json.loads((P/'resources.json').read_text());assert r['successor']['estimated_wns_ns']==-2.277 and not any(r['loops'].values())
original=P/'selected-experiment-manifest.json'
assert sha(original)=='c431bf86b882a91acc9b496365d0d50d39230a3f01f2ab1b31a2b4873a27df8c'
a={r['path']:r['sha256']for r in json.loads(original.read_text())['artifacts']}
for f in(P/'reports').rglob('*'):
 if not f.is_file()or 'fresh-copy'in f.parts:continue
 rel=f.relative_to(P/'reports').as_posix()
 origin=rel if rel.startswith(('ooc01/','address-paths01/'))else'evidence/'+rel
 assert sha(f)==a[origin],origin
for n,h in b.items():assert a[n]==h,n
if(P/'manifest.json').exists():
 for a in json.loads((P/'manifest.json').read_text())['artifacts']:assert sha(P/a['path'])==a['sha256'],a['path']
print('PORTABLE_NEW_SOURCE_AND_REPORT_BINDINGS_PASS',len(b))
