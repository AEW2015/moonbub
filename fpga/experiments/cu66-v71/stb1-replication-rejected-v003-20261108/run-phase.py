from pathlib import Path
import argparse,json,hashlib,subprocess,time,os
p=Path(__file__).resolve().parent;b=Path('C:/moon/builds/stb1-v001');sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
a=argparse.ArgumentParser();a.add_argument('phase',choices=['query','optimize']);args=a.parse_args();phase=args.phase
bindings=json.loads((p/'prepared-bindings.json').read_text());assert all(sha(Path(f))==h for f,h in bindings['baseline'].items()),'immutable base changed';assert all(sha(p/f)==h for f,h in bindings['scripts'].items()),'prepared script changed'
freeze=json.loads((b/'source-freeze.json').read_text());assert all(sha(b/'inputs'/r)==h for r,h in freeze.items()),'frozen inputs changed'
approval=json.loads((p/'review-approval.json').read_text());assert approval.get('allow_'+phase) is True,'root launch clearance required'
script=p/(phase+'.tcl');extra=[]
if phase=='optimize':
 proof=p/'target-review.tsv';assert approval.get('target_review_sha256')==sha(proof),'root-reviewed postplace target required'
 target=dict(line.split('\t',1)for line in proof.read_text().splitlines());extra=[target[k]for k in ['endpoint','net','driver_pin','driver_cell','driver_ref','driver_init','leaf_loads']]
 prior=json.loads((p/'query-execution.json').read_text());assert prior['returncode']==0 and prior['completion_marker'],'query must complete first'
cmd=['C:/Xilinx/2025.2/Vivado/bin/vivado.bat','-mode','batch','-source',str(script),'-log',str(p/(phase+'-vivado.log')),'-journal',str(p/(phase+'-vivado.jou')),'-tclargs',str(p)]+extra
tmp=Path('C:/moon/tmp')/('stb1-margin-v003-'+phase);tmp.mkdir(exist_ok=False);env=dict(os.environ,TEMP=str(tmp),TMP=str(tmp));env.pop('NoDefaultCurrentDirectoryInExePath',None)
start=time.monotonic();(p/(phase+'-launch.json')).write_text(json.dumps({'command':cmd,'script_sha256':sha(script),'approval_sha256':sha(p/'review-approval.json'),'source_freeze_sha256':sha(b/'source-freeze.json')},indent=2))
with(p/(phase+'-console.log')).open('x')as f:r=subprocess.run(cmd,cwd=p,env=env,stdout=f,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
log=(p/(phase+'-vivado.log')).read_text(errors='replace');marker='STB1_MARGIN_V003_POSTPLACE_READONLY_COMPLETE'if phase=='query'else'STB1_MARGIN_V003_POSTPLACE_REPORTS_COMPLETE_NO_BIT_OR_HARDWARE';v={'returncode':r.returncode,'seconds':time.monotonic()-start,'completion_marker':any(line.strip()==marker for line in log.splitlines()),'inputs_unchanged':all(sha(b/'inputs'/n)==h for n,h in freeze.items()),'baseline_unchanged':all(sha(Path(f))==h for f,h in bindings['baseline'].items()),'native_errors':[line for line in log.splitlines()if line.startswith('ERROR:')],'BIT':False,'hardware':False};(p/(phase+'-execution.json')).write_text(json.dumps(v,indent=2));print(json.dumps(v));assert r.returncode==0 and v['completion_marker'] and v['inputs_unchanged'] and v['baseline_unchanged'] and not v['native_errors']
