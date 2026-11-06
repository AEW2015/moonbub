"""Bind selected BRAM/pipeline/burst sources to functional and leaf reports."""
from pathlib import Path
import argparse,hashlib,json
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/display'
a=argparse.ArgumentParser();a.add_argument('--output',required=True);args=a.parse_args()
o=(r/args.output).resolve();o.mkdir(parents=True,exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
artifacts=[];checks=[]
def bind(f,role):
 artifacts.append(dict(path=str(f.relative_to(r)).replace('\\','/'),role=role,sha256=sha(f)))
for variant,rtl,raster,control,impl in [
 ('pipeline','cu71_painter_strip_pipe.sv','painter-pipe-raster03','painter-pipe-control03','painter-pipe-ooc03'),
 ('burst','cu71_painter_strip_burst.sv','painter-burst-raster02','painter-burst-control02','painter-burst-ooc01')]:
 digest=sha(d/rtl);rp=d/'evidence'/raster;cp=d/'evidence'/control;ip=r/'fpga/experiments/cu66-v71/build'/impl
 m=json.loads((rp/'result.json').read_text());assert m['status']=='PASS_BRAM_PAINTER_EXACT_NATIVE_RASTERS'
 for n,h in m['source_sha256'].items():assert sha(rp/'source-snapshot'/n)==h,('Archived executed source mismatch',variant,n)
 assert m['source_sha256']['fpga/experiments/cu66-v71/display/'+rtl]==digest
 assert m['full_rasters']==26 and m['compared_words']==9984000
 m=json.loads((cp/'result.json').read_text());assert m['status']=='PASS_FOUR_STATE_BRAM_PAINTER_CONTROL' and m['sources'][rtl]==digest
 for n,h in m['sources'].items():assert sha(cp/n)==h,('Control snapshot mismatch',variant,n)
 m=json.loads((ip/'result.json').read_text());assert m['status']=='PASS_EXACT_DEVICE_BRAM_PAINTER_RESOURCE_GATE' and m['source_sha256']==digest
 for n,h in m['artifacts'].items():assert sha(ip/n)==h,('Native synthesis artifact mismatch',variant,n)
 lines=(ip/'synthesized-timing.rpt').read_text().splitlines();i=next(i for i,x in enumerate(lines)if x.strip().startswith('WNS(ns)'));v=lines[i+2].split()
 timing=dict(setup_ns=float(v[0]),setup_failing=int(v[2]),hold_ns=float(v[4]),hold_failing=int(v[6]),pulse_ns=float(v[8]),pulse_failing=int(v[10]))
 assert all(timing[k]>0 for k in ['setup_ns','hold_ns','pulse_ns']) and all(timing[k]==0 for k in ['setup_failing','hold_failing','pulse_failing'])
 checks.append(dict(id=variant,status='PASS_LEAF_ONLY',source_sha256=digest,counts=m['counts'],synthesized_timing=timing,scope='Functional native26rasters/Icaruscontrol plus exact-device synthesis; not routed-board timing'))
 bind(d/rtl,'source')
 for p in [rp/'result.json',rp/'execution.json',cp/'result.json',cp/'execution.json',ip/'result.json',ip/'execution.json',ip/'utilization.rpt',ip/'synthesized-timing.rpt',ip/'synthesized-paths.rpt',ip/'run.tcl',ip/'synthesized.dcp']:bind(p,'evidence')
for n in ['painter-pipe-origin.json','painter-burst-origin.json','HARDWARE-INTEGRATION.md']:bind(d/n,'source_or_scope')
for n in ['run_painter_bram.py','run_painter_control.py','synth_painter_bram.py',Path(__file__).name]:bind(r/'scripts/cu66-v71/display'/n,'reproduction_script')
checks.extend([dict(id='routed_board_timing',status='NOT_RUN'),dict(id='live_ESP32_and_full_CU66',status='NOT_RUN_BY_THIS_GATE'),dict(id='physical_playback_and_30fps',status='NOT_PROVEN')])
(o/'manifest.json').write_text(json.dumps(dict(overall='PASS_SELECTED_LEAF_GATES_BOARD_READINESS_INCOMPLETE',artifacts=artifacts,checks=checks,
 retained_failures=['painter-bram-raster01 synchronousstriptransitiondataerror','painter-bram-ooc02 setupnegative','painter-pipe-ooc01/ooc02 setupnegative and earlylintfailures'],
 archived_source_resolution='Native raster source_sha256 entries resolve under each evidence/source-snapshot, control sources under their evidence directory, native synthesis artifacts under their build directory. Historical executed helpers remain frozen even when current reproduction scripts gain variant options.',
 RGB_verification='Packet count48000 and384000words checked by independent native oracle via explicit8word drain adapter; actual RGB PHY integration is separate',
 map_cadence='Crossbankfront0improves,butfront1+canonical2fails; preserve banked-newmap-front1-CAN2-fast01/trace01. This manifest does not certify a map.'),indent=2)+'\n')
print('CU71_PAINTER_LEAF_HANDOFF_COMPLETE',o,flush=True)
