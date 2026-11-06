from pathlib import Path
import hashlib,json,re
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/direct-system/tag-equality-v001';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();dirs={v:d/'evidence'/n for v,n in [('old','ooc-feedback-old01'),('balanced','ooc-feedback-balanced01')]};results={};refs={}
def path(f):
 t=f.read_text();m=re.search(r'Slack \([^)]*\)\s*:\s*([-0-9.]+)ns',t)
 if not m:return{'path_found':False}
 fields={n:re.search(p,t)[1].strip()for n,p in{'source':r'Source:\s*([^\n]+)','destination':r'Destination:\s*([^\n]+)','levels':r'Logic Levels:\s*([^\n]+)','data_path':r'Data Path Delay:\s*([^\n]+)'}.items()};return dict(path_found=True,slack_ns=float(m[1]),**fields)
for variant,e in dirs.items():
 assert json.loads((e/'execution.json').read_text())['returncode']==0
 t=(e/'timing.rpt').read_text();m=re.search(r'WNS\(ns\).*?\n\s*-+[^\n]*\n\s*([^\n]+)',t);v=m[1].split();u=(e/'utilization.rpt').read_text();line=next(x for x in u.splitlines()if re.match(r'\| cu71_tag_feedback_ooc\s*\|',x));c=[x.strip()for x in line.split('|')[1:-1]];log=(e/'console.log').read_text();errors=[x for x in log.splitlines()if x.startswith('ERROR:')]
 assert(e/'target-counts.txt').read_text().strip()=='DIGEST_C=256 WORKING_CE=256'
 results[variant]={'target_digest_to_working_CE':path(e/'digest-to-working-CE.rpt'),'global_unplaced':{'WNS_ns':float(v[0]),'WHS_ns':float(v[4]),'WPWS_ns':float(v[8])},'worst_setup':path(e/'setup-paths.rpt'),'LUTs':int(c[2]),'FFs':int(c[6]),'RAMB36':int(c[7]),'RAMB18':int(c[8]),'DSP':int(c[9]),'native_errors':errors}
 for f in e.iterdir():
  if f.is_file():refs[f.relative_to(r).as_posix()]=sha(f)
old_t=(dirs['old']/'executed.tcl').read_text();new_t=(dirs['balanced']/'executed.tcl').read_text();before='fpga/experiments/cu66-v71/direct-system/validpipe-v003/cu71_base_pipeline_math.sv';after='fpga/experiments/cu66-v71/direct-system/tag-equality-v001/cu71_base_pipeline_math.sv';assert old_t.replace(before,after)==new_t
bare=d/'evidence/ooc-old01';assert not path(bare/'digest-to-working-CE.rpt')['path_found'];refs[(bare/'digest-to-working-CE.rpt').relative_to(r).as_posix()]=sha(bare/'digest-to-working-CE.rpt')
for f in[d/'feedback-binding.json',d/'qualification-functional-v001.json',d/'sources.json',Path(__file__).resolve()]:refs[f.relative_to(r).as_posix()]=sha(f)
q={'status':'DIAGNOSTIC_MATCHED_CLOSED_FEEDBACK_OOC_NATIVE_ERROR_REVIEW_REQUIRED'if any(x['native_errors']for x in results.values())else'MATCHED_CLOSED_FEEDBACK_OOC_COMPLETE_NOT_BOARD_SIGNOFF','sources_one_base_change_only':True,'clocks_IO_constraints_and_wrapper_identical':True,'exact_target_counts':'256digest FF C ->256working FF CE','wrapper_scope':'Actual receiver ready/valid dependency closed, remaining owner qualifier arbitrary; not full receiver/board timing','bare_base_control':'No digest→working CE path; excluded from improvement comparison','results':results,'proofs_sha256':refs,'hardware':False,'BIT':False,'release':'No board/source selection. Raw native errors are retained and not waived; full board route/hold/DRC/CDC/fit required.'};o=d/'comparison-ooc-v001.json';assert not o.exists();o.write_text(json.dumps(q,indent=2)+'\n');print(json.dumps({'sha256':sha(o),'results':results},indent=2))
