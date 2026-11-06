"""Copy a verified source/report subset to the owned publishing worktree; no commit/push."""
from pathlib import Path
import argparse,hashlib,json,subprocess
r=Path(__file__).resolve().parents[1]
a=argparse.ArgumentParser();a.add_argument('--full-manifest',required=True);args=a.parse_args()
w=r.parent/'moonbub-overnight-publish-20261105'
assert subprocess.check_output(['git','branch','--show-current'],cwd=w,text=True).strip()=='feature/fpga-timing-cleanup-20261105'
assert not subprocess.check_output(['git','status','--porcelain'],cwd=w,text=True).strip(),'Publishing worktree must be clean'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifests=[Path(args.full_manifest).resolve(),r/'fpga/diagnostics/sdr1-20261105/image03-alternate01/completion-manifest.json']
files={};omitted=[]
for path in manifests:
 m=json.loads(path.read_text());assert m['overall']=='PASS'
 for item in m['artifacts']:
  p=(r/item['path']).resolve();p.relative_to(r);assert sha(p)==item['sha256'],p
  if p.suffix.lower()in ['.bit','.dcp']:
   omitted.append(item);continue
  files[item['path']]=p
 files[path.relative_to(r).as_posix()]=path
for n in ['RESET-REDUCTION-PLAN-20261105.md','SDR1-BITSTREAM-COMPLETION-20261105.md','CPL1-RESET-BITSTREAM-COMPLETION-20261105.md']:
 p=r/'docs'/n;assert p.exists();files[p.relative_to(r).as_posix()]=p
for n in ['package_build_manifest.py','publish_reset_bitstream_evidence.py']:
 p=r/'scripts'/n;files[p.relative_to(r).as_posix()]=p
records=[]
for name,p in sorted(files.items()):
 dest=w/name;dest.resolve().relative_to(w)
 if dest.exists()and sha(dest)!=sha(p)and name.startswith('fpga/exports/cpl1-timing-fsmcopy-source-20261105-v002/'):
  raise AssertionError('Refusing to change a sealed historical export: '+name)
 dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes());assert sha(dest)==sha(p)
 records.append(dict(path=name,sha256=sha(p)))
public=w/'evidence/reset-bitstreams-public-20261105-v001';public.mkdir(exist_ok=False)
record=dict(overall='INCOMPLETE',scope='Public source/report subset; completed local BIT/DCP files deliberately omitted',
 local_build_gate_status='PASS',files=records,local_binary_artifacts_not_copied=omitted,
 hardware_programmed=False,hardware_correctness_proven=False)
(public/'availability.json').write_text(json.dumps(record,indent=2)+'\n')
names=list(files)+['evidence/reset-bitstreams-public-20261105-v001/availability.json']
(r/'evidence/reset-bitstream-public-paths-20261105.txt').write_text('\n'.join(names)+'\n')
print('PUBLIC_SUBSET_COPIED_NO_COMMIT_NO_PUSH',len(records))
