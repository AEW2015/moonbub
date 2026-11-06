"""Separate DY71 functional integration from clean-raster/cadence qualification."""
from pathlib import Path
import argparse,hashlib,json,re
p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=Path(__file__).resolve().parents[3];run=a.run.resolve();o=a.output.resolve();assert not o.exists();sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();result=json.loads((run/'result.json').read_text());assert result['status']=='PASS_FUNCTIONAL_DY71_KEY_P_CANONICAL_HUD_AND_LCD'
pins=json.loads((run/'source-freeze.json').read_text())
for n,h in pins.items():assert sha(r/n)==h,n
text=(run/'frames.log').read_text();frames=[]
def values(line):return{k:int(v)for k,v in re.findall(r'(\w+)=(\d+)',line)}
for line in text.splitlines():
 if line.startswith('SYSTEM_FRAME_PASS'):frames.append(values(line))
summary=values(next(line for line in text.splitlines()if line.startswith('SYSTEM_PASS')))
assert len(frames)>=2 and frames[0]['key']==1 and frames[1]['key']==0 and frames[1]['processor_commit_calls']>=2
assert summary['RGB_reads_or_writes']==0 and summary['canonical_bytes_per_frame']==518400 and summary['HUD_functional_readback_words_per_frame']==21120
for f in frames:assert f['actual_writes']==428160,'Unexpectedphysicalcanonical/HUDbeatcount'
proofs={}
for name in ['result.json','source-freeze.json','execution.json','control.log','frames.log','tb.cpp','cu71_direct_system_sim.sv','model-verilator.sv']:
 f=run/name;proofs[f.relative_to(r).as_posix()]=sha(f)
d=r/'fpga/experiments/cu66-v71/direct-system';contract=r/'fpga/experiments/cu66-v71/direct-display/frozen-port-contract-v001.json'
for f in [d/'sources.json',d/'receiver-derivation.json',d/'system-derivation.json',d/'PROFILE.md',contract,Path(__file__).resolve()]:proofs[f.relative_to(r).as_posix()]=sha(f)
o.write_text(json.dumps({'status':'PASS_FUNCTIONAL_CADENCE_FAIL'if summary['total_underruns']else'PASS_FUNCTIONAL_NATIVE_FIXTURE','profile_magic':'0x44593731','profile_abi':'0x00010000','profile_capabilities':'0x0f','canonical_layout':'tile_major64','display_slots':'cache_context','frames':frames,'summary':summary,'source_pins':pins,'proofs':proofs,'hardware':False,'routed_timing':False,'CDC_qualified':False,'unique_clean_30fps_proven':False,'scope':'ActualqualifiedBL8controllermodel;fullcanonical/HUDreadbackandnativegoldenLCDexact-or-wholeblackscoring. CPUHUDserviceoutsideHDLtime; noESP/QSPI/CSR/networkqualification; unplacedbaseowner timingfails.','limits':['Two-stateVerilatormodelusesdisclosed1psmonitorcompatibility','Prepared/descriptorACKisnotcleanpresentation','Frozen32bitDMAcookiefailsclosedbeforewrap;longdurationpolicyunqualified']},indent=2)+'\n');print(json.dumps({'status':json.loads(o.read_text())['status'],'output':str(o),'sha256':sha(o),'underruns':summary['total_underruns']}))
