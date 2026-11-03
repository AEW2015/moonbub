#!/usr/bin/env python3
"""Read-only verification of saved final-build hashes and report summaries."""
import hashlib,json,re,sys
from pathlib import Path
root=Path(__file__).resolve().parents[6];out=Path(sys.argv[1]);build=root/'fpga/build-final'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
bindings=json.loads((build/'source-bindings.json').read_text());missing=[];mismatch=[]
for b in bindings:
 p=root/b['path']
 if not p.is_file():missing.append(b['path'])
 elif sha(p)!=b['sha256']:mismatch.append(b['path'])
if missing or mismatch:raise SystemExit(f'bindings fail: missing={missing}, mismatched={mismatch}')
seed_file=root/'fpga/attempts/v3-routed/source-bindings.json'
seed=json.loads(seed_file.read_text())
seed_rtl=[b for b in seed if b['path'].startswith(('fpga/rtl/','fpga/vendor/'))]
seed_bad=[b['path'] for b in seed_rtl if not (root/b['path']).is_file() or sha(root/b['path'])!=b['sha256']]
if seed_bad:raise SystemExit(f'seed RTL bindings fail: {seed_bad}')
u=(build/'utilization.rpt').read_text();t=(build/'timing_summary.rpt').read_text();route=(build/'route_status.rpt').read_text();gate=(build/'gate.txt').read_text()
def row(name):
 m=re.search(r'^\|\s*'+re.escape(name)+r'\s*\|\s*([0-9.]+)\s*\|\s*\d+\s*\|\s*\d+\s*\|\s*([0-9.]+)\s*\|',u,re.M)
 if not m:raise ValueError('missing utilization '+name)
 return {'used':float(m[1]),'available':float(m[2])}
ram=row('Block RAM Tile');dsp=row('DSPs');lut=row('Slice LUTs');ff=row('Slice Registers')
m=re.search(r'WNS\(ns\).*?\n\s*-+.*?\n\s*([0-9.]+)\s+([0-9.]+)\s+(\d+)\s+\d+\s+([0-9.]+)\s+([0-9.]+)\s+(\d+)\s+\d+\s+([0-9.]+)',t,re.S)
if not m:raise ValueError('timing summary')
setup,tns,setup_failing,hold,ths,hold_failing,pulse=m.groups()
if not re.search(r'# of fully routed nets[^:\n]*:\s*13535',route) or not re.search(r'# of nets with routing errors[^:\n]*:\s*0',route):raise ValueError('route summary')
if 'setup_wns='+setup not in gate or 'hold_whs='+hold not in gate or 'drc_errors=0' not in gate:raise ValueError('gate mismatch')
pairs=[('fpga/vendor/core_jpeg/src_v/jpeg_idct_x.v','fpga/experiments/throughput30/burst/idct-dsp-study/narrow-x/jpeg_idct_x_narrow.v'),('fpga/vendor/core_jpeg/src_v/jpeg_idct_y.v','fpga/experiments/throughput30/burst/idct-dsp-study/narrow-y-coeff/jpeg_idct_y_coeff.v')]
candidates=[{'baseline_path':a,'baseline_sha256':sha(root/a),'candidate_path':b,'candidate_sha256':sha(root/b),'byte_identical':sha(root/a)==sha(root/b)} for a,b in pairs]
if any(x['byte_identical'] for x in candidates):raise ValueError('candidate unexpectedly identical')
bound_paths={x['path'] for x in bindings}
if any(x['candidate_path'] in bound_paths for x in candidates):raise ValueError('candidate is unexpectedly bound')
paths=['source-bindings.json','utilization.rpt','timing_summary.rpt','route_status.rpt','gate.txt','moonshine-rev4.1.bit','moonshine_routed.dcp','synthesized.dcp']
r={'scope':'existing routed baseline only; source manifest is a snapshot and does not cryptographically bind the output artifact','bindings_total':len(bindings),'bindings_matched':len(bindings),'missing':missing,'mismatch':mismatch,'seed_rtl_bindings_matched':len(seed_rtl),'seed_bindings_sha256':sha(seed_file),
 'report_device':'xc7a100tcsg324-1','report_tool':'Vivado 2025.2 win64','utilization':{'bram_tiles':ram,'dsps':dsp,'slice_luts':lut,'slice_registers':ff},
 'arithmetic_unused':{'bram_tile_equivalents':ram['available']-ram['used'],'dsps':dsp['available']-dsp['used']},
 'timing_ns':{'setup_wns':float(setup),'tns':float(tns),'setup_failing_endpoints':int(setup_failing),'hold_whs':float(hold),'ths':float(ths),'hold_failing_endpoints':int(hold_failing),'pulse_width_wpws':float(pulse)},
 'routing':{'routable':13535,'fully_routed':13535,'errors':0},'gate_drc_errors':0,'files_sha256':{x:sha(build/x) for x in paths},'candidate_sources':candidates}
out.write_text(json.dumps(r,indent=2)+'\n');print('BASELINE_AUDIT_PASS',len(bindings),'bindings match; BRAM',ram['used'],'/',ram['available'],'DSP',dsp['used'],'/',dsp['available'],'WNS/WHS',setup,hold)
