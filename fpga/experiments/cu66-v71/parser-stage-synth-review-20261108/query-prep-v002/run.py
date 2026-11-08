from pathlib import Path
import argparse,json,hashlib,subprocess,time,os,re,shutil
p=Path(__file__).resolve().parent
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
a=argparse.ArgumentParser();a.add_argument('--checkpoint',required=True,type=Path);a.add_argument('--out',required=True,type=Path);a.add_argument('--review-receipt',type=Path,default=p/'review-approval.json');args=a.parse_args()
manifest=json.loads((p/'prepared-manifest.json').read_text())
assert sha(p/'inspect.tcl')==manifest['inspect_sha256'] and sha(Path(__file__))==manifest['runner_sha256'],'query scripts changed'
review=json.loads(args.review_receipt.read_text(encoding='utf-8-sig'))
assert review.get('allow_query')is True and review.get('prepared_manifest_sha256')==sha(p/'prepared-manifest.json'),'explicit root query approval required'
checkpoint=args.checkpoint.resolve();out=args.out.resolve();build=Path(manifest['build']).resolve()
assert checkpoint==build/'constrained.dcp','only reviewed constrained checkpoint is allowed'
assert checkpoint.is_file()and sha(checkpoint)==review.get('checkpoint_sha256'),'reviewed checkpoint SHA required'
assert out.parent==Path('C:/moon/dev/evidence').resolve() and out.name.startswith('parser-stage-synth-cone-')and not out.exists(),'unique bounded evidence output required'
receipt=json.loads((build/'synth-execution.json').read_text());assert receipt['returncode']==0 and receipt['completion_marker']and receipt['inputs_unchanged'],'synthesis must finish first'
source=json.loads((build/'source-freeze.json').read_text());assert source==json.loads(Path(manifest['candidate_production_freeze']).read_text())
assert sha(build/'source-freeze.json')==manifest['build_sourcefreeze_sha256']and all(sha(build/'inputs'/n)==h for n,h in source.items()),'exact source freeze changed'
q=subprocess.run(['powershell','-NoProfile','-Command',"@(Get-CimInstance Win32_Process -Filter \"Name='vivado.exe'\" | Select-Object ProcessId,CommandLine) | ConvertTo-Json -Compress"],capture_output=True,text=True,check=True)
assert not q.stdout.strip()or json.loads(q.stdout)==[],'one Vivado process at a time'
tag=out.name;tmp=Path('C:/moon/tmp')/tag;tmp.mkdir(exist_ok=False)
env=dict(os.environ,TEMP=str(tmp),TMP=str(tmp));env.pop('NoDefaultCurrentDirectoryInExePath',None)
log=p/(tag+'.log');jou=p/(tag+'.jou');console=p/(tag+'-console.log');launch=p/(tag+'-launch.json')
assert not any(f.exists()for f in [log,jou,console,launch]),'unique run files required'
before={'checkpoint_sha256':sha(checkpoint),'script_sha256':sha(p/'inspect.tcl'),'review_sha256':sha(args.review_receipt),'prepared_manifest_sha256':sha(p/'prepared-manifest.json'),'sourcefreeze_sha256':sha(build/'source-freeze.json')}
cmd=['C:/Xilinx/2025.2/Vivado/bin/vivado.bat','-mode','batch','-source',str(p/'inspect.tcl'),'-log',str(log),'-journal',str(jou),'-tclargs',str(checkpoint),str(out)]
launch.write_text(json.dumps(dict(command=cmd,bindings=before),indent=2)+'\n')
t=time.monotonic()
with console.open('x')as f:r=subprocess.run(cmd,cwd=p,env=env,stdout=f,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
text=log.read_text(errors='replace')
result={'returncode':r.returncode,'seconds':time.monotonic()-t,'marker':any(line.strip()=='PARSER_SYNTH_CONE_READONLY_COMPLETE_NO_ROUTED_OR_HARDWARE_CLAIM'for line in text.splitlines()),'checkpoint_unchanged':sha(checkpoint)==before['checkpoint_sha256'],'script_unchanged':sha(p/'inspect.tcl')==before['script_sha256'],'sources_unchanged':all(sha(build/'inputs'/n)==h for n,h in source.items()),'errors':re.findall(r'^ERROR:.*',text,re.M),'routed_claim':False,'hardware':False}
resultfile=p/(tag+'-execution.json');resultfile.write_text(json.dumps(result,indent=2)+'\n')
if out.is_dir():
 for f in [log,jou,console,launch,resultfile]:shutil.copyfile(f,out/f.name)
print(json.dumps(result),flush=True)
assert r.returncode==0 and result['marker']and result['checkpoint_unchanged']and result['script_unchanged']and result['sources_unchanged']and not result['errors']
