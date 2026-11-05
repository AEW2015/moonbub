#!/usr/bin/env python3
"""Freeze raster exactness, HUD profile and native cap follow-up evidence."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
MUTABLE=('README.md','docs/gamebub-application-specific-codec-plan.md');FOLDERS=('raster','native-cap')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def passing(p):
 text=p.read_text();m=re.search(r'^Ran (\d+) tests? in ',text,re.M);assert m and text.rstrip().endswith('OK');return int(m[1])
def main():
 old=json.loads((ROOT/'docs/prototype-v40-provenance.json').read_text());frozen={p:h for p,h in old['file_sha256'].items() if p not in MUTABLE}
 for p,h in frozen.items():assert sha(ROOT/p)==h,('frozen40',p)
 paths={ROOT/p for p in old['file_sha256']};names=('docs/prototype-v40-provenance.json','docs/custom-codec-prototype-v41-2026-11-05.md','docs/v41-evidence-audit.md','docs/prototype-v41-hud-profile.json','docs/prototype-v41-native-cap-comparison.json','experiments/profile_hud_v41.py','experiments/compare_native_cap_v41.py','experiments/export_prototype_v41.py','experiments/verify_prototype_v41.py');paths|={ROOT/p for p in names};runs=['docs/prototype-v41-hud-profile.json','docs/prototype-v41-native-cap-comparison.json'];tests={}
 for name in FOLDERS:
  folder=ROOT/('experiments/python-game-'+name+'-v41-study');paths|={p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'};runs.append((folder/'results.json').relative_to(ROOT).as_posix())
  if name=='raster':
   for n in('tests.log','tests_verify.log'):tests[(folder/n).relative_to(ROOT).as_posix()]=passing(folder/n)
 for name in runs:
  for p,h in json.loads((ROOT/name).read_text())['source_sha256'].items():assert not Path(p).is_absolute() and '..' not in Path(p).parts;assert sha(ROOT/p)==h,('producer',name,p);paths.add(ROOT/p)
 d=dict(schema='gamebub-v41-provenance',parent_commit='a125335a5349a41bdeb1caa2159779d9d2e0bcaa',file_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)},frozen_v40_sha256=frozen,passing_test_logs=tests,run_artifacts=runs,stored_helpers=['experiments/python-game-'+n+'-v41-study/verify.py' for n in FOLDERS],limitations=['Sixhourrunactive;intermediatecheckpoint.','Onlyflatfixturehasnewspatialbytewin;gameplaycandidatesrejected.','Native21pointtargetedcombatresearchclosescoarsegridgap;HEVCeveryframegatewinsmeasuredbytes,notFPGAfit.','Profilerclocksinstrumented;noFPSorwholepipelineclaim.','NonewRTL/firmware/physicalhardwareproof.'])
 (ROOT/'docs/prototype-v41-provenance.json').write_text(json.dumps(d,indent=2,sort_keys=True)+'\n');print(json.dumps(dict(files=len(paths),frozen_v40_files=len(frozen),new_passing_tests=sum(tests.values()))))
if __name__=='__main__':main()
