#!/usr/bin/env python3
"""Portable inventory for the v40 source and causal qualification checkpoint."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
FOLDERS=('source','key-cap','control-qual','binary-qual','exact','native-qual');PREFIX='experiments/python-game-';MUTABLE=('README.md','docs/gamebub-application-specific-codec-plan.md')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def passing(p):
 text=p.read_text();m=re.search(r'^Ran (\d+) tests? in ',text,re.M);assert m and text.rstrip().endswith('OK'),p;return int(m[1])
def main():
 old=json.loads((ROOT/'docs/prototype-v39-provenance.json').read_text());frozen={p:h for p,h in old['file_sha256'].items() if p not in MUTABLE}
 for p,h in frozen.items():assert sha(ROOT/p)==h,('frozen39',p)
 paths={ROOT/p for p in old['file_sha256']};paths|={ROOT/p for p in ('docs/prototype-v39-provenance.json','docs/custom-codec-prototype-v40-2026-11-05.md','docs/v40-qualification-audit.md','docs/prototype-v40-comparison.json','experiments/compare_prototype_v40.py','experiments/export_prototype_v40.py','experiments/verify_prototype_v40.py','experiments/verify_source_archive_v40.py')};runs={};tests={}
 for name in FOLDERS:
  folder=ROOT/(PREFIX+name+'-v40-study');paths|={p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
  artifact=folder/('manifest.json' if name=='source' else 'results.json');data=json.loads(artifact.read_text());key=next(k for k in ('source_sha256','source_pins_sha256','source_code_sha256') if k in data);runs[artifact.relative_to(ROOT).as_posix()]=key
  if name=='exact':
   for n in ('tests.log','tests_verify.log'):tests[(folder/n).relative_to(ROOT).as_posix()]=passing(folder/n)
 runs['docs/prototype-v40-comparison.json']='source_sha256'
 for name,key in runs.items():
  for raw,h in json.loads((ROOT/name).read_text())[key].items():
   p=Path(raw);assert not p.is_absolute() and '..' not in p.parts;assert sha(ROOT/p)==h,('producer',name,raw);paths.add(ROOT/p)
 helpers=['experiments/verify_source_archive_v40.py']+[PREFIX+n+'-v40-study/verify.py' for n in FOLDERS if n!='source']
 data=dict(schema='gamebub-v40-provenance',parent_commit='efeeaa84dfb89d704c4699a0c32ab42a0def25f2',file_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)},frozen_v39_sha256=frozen,passing_test_logs=tests,run_artifacts=runs,stored_helpers=helpers,limitations=['Sixhourrunstillactive;intermediatecheckpoint.','457uniqueadditionalcanvasesaredifferenttimestampwindowsfromrelatedsamegameprecompressedsources,notnative30fpscapturesorindependentgames.','NoHUD/base/arithmeticcomponentclockprovescompletepipelineFPS.','Nativegridis48sampledpoints,notexhaustive;combatpeakcontrolsarestillunderinvestigation.','Noendpointfirmware,newRTL,physical30fps,FPGAfit,orHEVC/AV1superiorityproof.'])
 (ROOT/'docs/prototype-v40-provenance.json').write_text(json.dumps(data,indent=2,sort_keys=True)+'\n');print(json.dumps(dict(files=len(paths),frozen_v39_files=len(frozen),new_passing_tests=sum(tests.values()))))
if __name__=='__main__':main()
