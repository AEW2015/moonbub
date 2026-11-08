"""Separate source-frozen STB1 runner; requires root review receipt. No BIT or hardware action."""
from pathlib import Path
import argparse,hashlib,json,os,re,subprocess,time
p=Path(__file__).resolve().parent;a=argparse.ArgumentParser();a.add_argument('phase',choices=['synth','implementation']);a.add_argument('--review-receipt',type=Path,default=p/'review-approval.json');args=a.parse_args();sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
freeze=json.loads((p/'source-freeze.json').read_text());assert all(sha(p/'inputs'/n)==h for n,h in freeze.items())
review=json.loads(args.review_receipt.read_text());binding=json.loads((p/'overlay-binding.json').read_text());assert review['overlay_binding_sha256']==sha(p/'overlay-binding.json') and all(sha(p/n)==h for n,h in binding['script_sha256'].items()),'reviewed build scripts required';assert review['source_freeze_sha256']==sha(p/'source-freeze.json') and review.get('allow_'+args.phase) is True,'root reviewed source/phase approval required'
if args.phase=='implementation':
 prior=json.loads((p/'synth-execution.json').read_text());assert prior['returncode']==0 and prior['completion_marker'] and prior['inputs_unchanged'] and (p/'constrained.dcp').is_file()
tmp=Path('C:/moon/tmp')/('stb1-'+args.phase+'-'+str(time.time_ns()));tmp.mkdir(parents=True)
script=p/(args.phase+'.tcl');cmd=['C:/Xilinx/2025.2/Vivado/bin/vivado.bat','-mode','batch','-source',str(script),'-log',str(p/(args.phase+'-vivado.log')),'-journal',str(p/(args.phase+'-vivado.jou')),'-tclargs',str(p)]
start=time.monotonic();env=dict(os.environ,TEMP=str(tmp),TMP=str(tmp));env.pop('NoDefaultCurrentDirectoryInExePath',None)
with(p/(args.phase+'-console.log')).open('x')as f:
 q=subprocess.Popen(cmd,cwd=p,env=env,stdout=f,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW);(p/(args.phase+'-launch.json')).write_text(json.dumps({'cmd':cmd,'pid':q.pid,'script_sha256':sha(script),'source_freeze_sha256':sha(p/'source-freeze.json'),'review_receipt_sha256':sha(args.review_receipt)},indent=2));code=q.wait()
log=(p/(args.phase+'-console.log')).read_text(errors='replace');marker='STB1_SYNTHESIS_CONSTRAINTS_COMPLETE_NO_BIT'if args.phase=='synth'else'STB1_BOARD_REPORTS_COMPLETE_NO_BIT_OR_HARDWARE'
v={'phase':args.phase,'returncode':code,'seconds':time.monotonic()-start,'completion_marker':any(x.strip()==marker for x in log.splitlines()),'native_errors':re.findall(r'^ERROR:.*',log,re.M),'inputs_unchanged':all(sha(p/'inputs'/n)==h for n,h in freeze.items()),'BIT':False,'hardware':False}
(p/(args.phase+'-execution.json')).write_text(json.dumps(v,indent=2));print(json.dumps(v));assert code==0 and v['completion_marker']and not v['native_errors']and v['inputs_unchanged']
