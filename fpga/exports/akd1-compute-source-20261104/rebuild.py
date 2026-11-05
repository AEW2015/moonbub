"""One-command clean source build plus independent fresh report readback."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
p=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--vivado');ap.add_argument('--out',default='build-local-001');ap.add_argument('--threads',type=int,default=4);ap.add_argument('--adopt-completed-source-build',action='store_true');a=ap.parse_args()
args=['--out',a.out]+(['--vivado',a.vivado] if a.vivado else [])
if not a.adopt_completed_source_build:subprocess.run([sys.executable,str(p/'build.py'),*args,'--threads',str(a.threads)],cwd=p,check=True)
else:
 e=json.loads((p/a.out/'execution.json').read_text());assert e['returncode']==0 and e['inputs_unchanged'] and e['flow']=='CLEAN_FULL_SOURCE_NO_INPUT_CHECKPOINT'
subprocess.run([sys.executable,str(p/'audit_clean_drc.py'),*args],cwd=p,check=True)
subprocess.run([sys.executable,str(p/'review_build.py'),'--out',a.out],cwd=p,check=True)
sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
(p/a.out/'workflow-execution.json').write_text(json.dumps({'full_source_build_executed':True,'source_build_launched_by_this_wrapper':not a.adopt_completed_source_build,'adopted_previously_executed_clean_build':a.adopt_completed_source_build,'source_execution_sha256':sha(p/a.out/'execution.json'),'fresh_readback_execution_sha256':sha(p/a.out/'fresh-drc-audit/execution.json'),'selected_image_replaced':False,'image_generation':'NOT_RUN','hardware':'NOT_ACCESSED'},indent=2)+'\n')
print('Portable clean source and fresh-readback workflow complete; selectedimage unchanged')
