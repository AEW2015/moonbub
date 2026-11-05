from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
b=json.loads((P/'source-bindings.json').read_text())
for n,h in b.items():assert sha(P/n)==h,n
for label in ['full01','physical-abort01','held-hud-abort01','hud-tag01','private-drain01','memory-edge01']:
 d=P/'reports'/label
 for n,h in json.loads((d/'source-snapshot.json').read_text()).items():assert b[n.replace('\\','/')]==h,n
 assert json.loads((d/'execution.json').read_text())[-1]['returncode']==0
 assert json.loads((d/'result.json').read_text())['status'].startswith('PASS')
for n,h in json.loads((P/'reports/ooc01/source-snapshot.json').read_text()).items():
 n=n.replace('\\','/')
 if n=='synth.tcl':assert sha(P/'reports/ooc01/synth.tcl')==h
 else:assert sha(P/n)==h,n
if (P/'manifest.json').exists():
 for a in json.loads((P/'manifest.json').read_text())['artifacts']:assert sha(P/a['path'])==a['sha256'],a['path']
print('PORTABLE_SOURCE_AND_HISTORICAL_REPORT_BINDINGS_PASS',len(b))
