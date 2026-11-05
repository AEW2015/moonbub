"""Assess this clean source run without changing image selection or hardware."""
import argparse,hashlib,json,re
from pathlib import Path
p=Path(__file__).resolve().parent
a=argparse.ArgumentParser();a.add_argument('--out',default='build-clean-001');a=a.parse_args();d=p/a.out
sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
e=json.loads((d/'execution.json').read_text())
before=json.loads((d/'pre-source-hashes.json').read_text());after=json.loads((d/'post-source-hashes.json').read_text())
assert e['inputs_unchanged'] and before==after
for name,h in before.items():assert sha(p/name)==h,name
selection=json.loads((p/'selected-image.json').read_text());assert sha(p/selection['image']['path'])==selection['image']['sha256']=='b1ca685e457446838b9d6c78b86f02c4b793dad42eccb3b5c50075d17e20e260'
timing=(d/'timing-summary.rpt').read_text()
pattern=r'^\s+([+-]?[\d.]+)\s+([+-]?[\d.]+)\s+(\d+)\s+(\d+)\s+([+-]?[\d.]+)\s+([+-]?[\d.]+)\s+(\d+)\s+(\d+)\s+([+-]?[\d.]+)\s+([+-]?[\d.]+)\s+(\d+)\s+(\d+)\s*$'
m=re.search(pattern,timing,re.M);assert m,'Missing actual design timing summary'
metrics={'setup_wns_ns':float(m[1]),'setup_tns_ns':float(m[2]),'setup_failing_endpoints':int(m[3]),'hold_whs_ns':float(m[5]),'hold_failing_endpoints':int(m[7]),'pulse_worst_ns':float(m[9]),'pulse_failing_endpoints':int(m[11])}
skew=[float(m[3]) for m in re.finditer(r'^\s+Slow\s+([\d.]+)\s+([\d.]+)\s+([+-]?[\d.]+)\s*$',(d/'bus-skew.rpt').read_text(),re.M)]
route=(d/'route-status.rpt').read_text();routable=int(re.search(r'of routable nets[^\n]*?:\s*(\d+)',route)[1]);routed=int(re.search(r'of fully routed nets[^\n]*?:\s*(\d+)',route)[1]);errors=int(re.search(r'of nets with routing errors[^\n]*?:\s*(\d+)',route)[1])
drctext=(d/'drc-reqp1839-full.rpt').read_text();warnings=len(re.findall(r'^REQP-1839#\d+ Warning$',drctext,re.M))
proofs=all('ALL_ROM_EN_LOW_RESET_AND_RESET_WRITE_PINS_INACTIVE_PASS=1' in (d/x/'rom-reset-proof.txt').read_text() for x in ['pre-opt-proof','postroute-proof']) and 'ALL44_OVERLAY_RESET_LOW_PASS=1' in (d/'overlay-reset-proof.txt').read_text() and 'ALL106_BRAM_WARNING_CELL_COVERAGE_PASS=1' in (d/'reqp1839-inventory.txt').read_text()
timing_pass=all(metrics[x]>0 for x in ['setup_wns_ns','hold_whs_ns','pulse_worst_ns']) and all(metrics[x]==0 for x in ['setup_failing_endpoints','hold_failing_endpoints','pulse_failing_endpoints'])
passed=e['returncode']==0 and timing_pass and len(skew)==8 and min(skew)>0 and routable==routed and errors==0 and proofs and 'default_DRC_errors=0' in (d/'route-gates.txt').read_text() and 'CHECK-3' not in drctext
result={'status':'PASS' if passed else 'FAIL','scope':'Executed clean full source synthesis/implementation/reports; no input checkpoint, image generation or hardware','flow':e['flow'],'metrics':metrics,'bus_skew_groups':len(skew),'minimum_bus_skew_slack_ns':min(skew),'routable_nets':routable,'fully_routed_nets':routed,'route_errors':errors,'REQP1839_warnings':warnings,'all_ROM_overlay_BRAM_proofs':proofs,'tool_parameters_sha256':sha(d/'tool-parameters.txt'),'execution_sha256':sha(d/'execution.json'),'clean_routed_checkpoint':{'path':(d/'akd1-clean-routed.dcp').relative_to(p).as_posix(),'sha256':sha(d/'akd1-clean-routed.dcp')},'selected_image_unchanged':selection['image'],'new_image_generated':False,'physical_actions':'NONE','limits':'No bit-identical reproduction claim; provided BIT remains original resumed-flow image; external IO/warmPLL/audio/SDRAM qualifications unchanged'}
(p/'clean-build-result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['status','metrics','all_ROM_overlay_BRAM_proofs','selected_image_unchanged']},indent=2))
