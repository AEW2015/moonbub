from pathlib import Path
import hashlib,json,re
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/staging-timing';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();dirs={v:d/'evidence'/n for v,n in [('old','ooc-old02'),('credit','ooc-credit01'),('safe','ooc-safe01')]};results={};proofs={}
def firstpath(f):
 t=f.read_text();m=re.search(r'Slack \([^)]*\)\s*:\s*([-0-9.]+)ns',t)
 if not m:return {'path_found':False}
 a=re.search(r'Source:\s*([^\n]+)',t);b=re.search(r'Destination:\s*([^\n]+)',t);ll=re.search(r'Logic Levels:\s*([^\n]+)',t);delay=re.search(r'Data Path Delay:\s*([^\n]+)',t)
 return {'path_found':True,'slack_ns':float(m[1]),'source':a[1].strip(),'destination':b[1].strip(),'logic_levels':ll[1].strip(),'data_path':delay[1].strip()}
for variant,e in dirs.items():
 assert json.loads((e/'execution.json').read_text())['returncode']==0
 t=(e/'timing.rpt').read_text();m=re.search(r'WNS\(ns\).*?\n\s*-+[^\n]*\n\s*([^\n]+)',t);assert m;values=m[1].split();global_timing={'WNS_ns':float(values[0]),'WHS_ns':float(values[4]),'WPWS_ns':float(values[8])}
 util=(e/'utilization.rpt').read_text();line=next(x for x in util.splitlines()if re.match(r'\| dy71_staging_ooc\s*\|',x));cols=[x.strip()for x in line.split('|')[1:-1]]
 log=(e/'native.log').read_text();warnings=[x for x in log.splitlines()if x.startswith('WARNING:')and('18-402'in x or 'invalid startpoint'in x or 'segmentation'in x)]
 results[variant]={'global_unplaced':global_timing,'LUTs':int(cols[2]),'FFs':int(cols[6]),'RAMB36':int(cols[7]),'worst_setup':firstpath(e/'setup-paths.rpt'),'held_enable':firstpath(e/'staging-held-enable.rpt'),'packet_to_held':firstpath(e/'packet-to-held.rpt'),'credit_update':firstpath(e/'credit-update.rpt'),'legacy_constraint_warnings':warnings}
 for f in e.iterdir():
  if f.is_file():proofs[f.relative_to(r).as_posix()]=sha(f)
assert len({sha(e/'executed.tcl')for e in dirs.values()})==1
assert len({sha(e/'cu71_bus_cdc_split.sv')for e in dirs.values()})==1
assert len({sha(e/'cu70_memory_map.svh')for e in dirs.values()})==1
q={'status':'MATCHED_OOC_COMPLETE_NO_ROUTED_BOARD_QUALIFICATION','part':'xc7a100tcsg324-1','SPI_MHz':200,'core_MHz':100,'max_IO_budget_ns':1,'executed_Tcl_identical_all_variants':True,'bridge_PHY_clock_constraints_unchanged':True,'results':results,'proofs_sha256':proofs,'scope':'Synthesis/unplaced estimates only. Global hold remains separate; broad legacy bundle object warnings retained, no CDC signoff. No BIT/board/hardware. Safety changes malformed discard behavior intentionally.','hardware':False,'BIT':False}
o=d/'comparison-ooc-v001.json';assert not o.exists();o.write_text(json.dumps(q,indent=2)+'\n');print(json.dumps({'comparison_sha256':sha(o),'results':results},indent=2))
