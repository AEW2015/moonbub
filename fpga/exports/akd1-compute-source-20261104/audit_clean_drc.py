import argparse,hashlib,json,os,re,shutil,subprocess,time
from pathlib import Path
p=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--vivado',default=os.getenv('VIVADO_BIN'));ap.add_argument('--out',default='build-clean-001');a=ap.parse_args()
if not re.fullmatch(r'build-[A-Za-z0-9_.-]+',a.out) or '..' in a.out:raise SystemExit('Use a build-* output name')
d=p/a.out;e=json.loads((d/'execution.json').read_text());assert e['returncode']==0 and e['inputs_unchanged'] and e['flow']=='CLEAN_FULL_SOURCE_NO_INPUT_CHECKPOINT'
sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
for name,h in json.loads((d/'pre-source-hashes.json').read_text()).items():assert sha(p/name)==h,name
exe=a.vivado or shutil.which('vivado') or shutil.which('vivado.bat')
if not exe:raise SystemExit('Provide Vivado2025.2 with --vivado or VIVADO_BIN')
files=[d/'akd1-clean-routed.dcp',d/'execution.json',d/'drc-reqp1839-full.rpt',p/'audit_clean_drc.tcl',Path(__file__).resolve()]
before={x.relative_to(p).as_posix():sha(x) for x in files};out=d/'fresh-drc-audit';out.mkdir()
cmd=[exe,'-mode','batch','-source',str(p/'audit_clean_drc.tcl'),'-log',str(out/'vivado.log'),'-journal',str(out/'vivado.jou'),'-tclargs',str(d)]
start=time.time()
with (out/'launcher.log').open('wb') as f:r=subprocess.run(cmd,cwd=p,stdout=f,stderr=subprocess.STDOUT)
assert before=={x.relative_to(p).as_posix():sha(x) for x in files}
text=(out/'drc-reqp1839-full.rpt').read_text() if r.returncode==0 else ''
pattern=r'The RAMB36E1 (\S+) has an input control pin (\S+) \(net: (\S+)\) which is driven by a register \(([^)]+)\)'
rows=set(re.findall(pattern,text));old=set(re.findall(pattern,(d/'drc-reqp1839-full.rpt').read_text()))
passed=r.returncode==0 and rows==old and len(rows)==183 and 'Command      : report_drc -checks REQP-1839 -no_waivers' in text and 'CHECK-3' not in text and '| Design State : Routed' in (out/'timing-summary.rpt').read_text()
(out/'execution.json').write_text(json.dumps({'returncode':r.returncode,'wall_seconds':time.time()-start,'command':cmd,'sha256':before,'inputs_unchanged':True,'actual_warning_count':len(rows),'same_exact_warning_records':rows==old,'qualifying_report':'fresh-drc-audit/drc-reqp1839-full.rpt','status':'PASS' if passed else 'FAIL','scope':'Fresh readback of ONLY this clean full-source run checkpoint; malformed implementation-session header superseded'},indent=2)+'\n')
assert passed,'Fresh actual-rule DRC readback did not qualify'
print('PORTABLE_CLEAN_FRESH_DRC_READBACK_PASS;183 exact rows and routed-DCP hash bound')
