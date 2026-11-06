#!/usr/bin/env python3
"""Ablate registered cache reads and guarded full-BL8 HUD against frozen V74."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];AREA=ROOT/'fpga/experiments/cu66-v75/system'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 paths=[ROOT/'fpga/experiments/cu66-v74/system/full-strip/results.json',AREA/'full-strip-scalar/results.json',AREA/'full-strip-burst/results.json',AREA/'history-4-strip-burst/results.json']
 old,scalar,burst,hist=[json.loads(p.read_text())for p in paths]
 assert all(d['status']=='PASS_FUNCTIONAL_MEMORY_AND_FRAMEBUFFERS' and d['summary']['total_underruns']==0 for d in [old,scalar,burst,hist])
 assert old['clocks']==scalar['clocks']==burst['clocks']==hist['clocks']
 common=old['source_sha256'].keys()&scalar['source_sha256'].keys();assert common and all(old['source_sha256'][p]==scalar['source_sha256'][p]for p in common)
 assert scalar['source_sha256']==burst['source_sha256'],'HUDablation must use same RTL/TB/script/fixture pins'
 history_common=burst['source_sha256'].keys()&hist['source_sha256'].keys();assert history_common and all(burst['source_sha256'][p]==hist['source_sha256'][p]for p in history_common)
 for d,n in [(old,2),(scalar,2),(burst,2),(hist,4)]:assert len(d['frames'])==len(d['timings'])==d['summary']['distinct_complete_presentations']==n
 assert hist['frames'][:2]==burst['frames']
 ms=burst['clocks']['memory_period_ps']/1e9;rows=[]
 for a,b,c,ta,tb,tc in zip(old['frames'],scalar['frames'],burst['frames'],old['timings'],scalar['timings'],burst['timings'],strict=True):
  assert (a['fid'],a['key'],a['generation'])==(b['fid'],b['key'],b['generation'])==(c['fid'],c['key'],c['generation'])
  assert a['actual_writes']==b['actual_writes']==c['actual_writes']==664320
  assert b['actual_write_commands']==101520 and c['actual_write_commands']==83040
  assert b['actual_write_bus_beats']==812160 and c['actual_write_bus_beats']==664320
  assert b['hud_write_requests']==b['hud_read_requests']==21120 and c['hud_write_requests']==c['hud_read_requests']==2640
  rows.append(dict(fid=c['fid'],key=bool(c['key']),v74=a,v75_scalar=b,v75_burst=c,
    v74_transaction_model_ms=a['cycles']*ms,v75_scalar_transaction_model_ms=b['cycles']*ms,v75_burst_transaction_model_ms=c['cycles']*ms,
    v74_validated_interval_model_ms=ta['validated_decode_model_cycles']*ms,v75_scalar_validated_interval_model_ms=tb['validated_decode_model_cycles']*ms,v75_burst_validated_interval_model_ms=tc['validated_decode_model_cycles']*ms,
    v74_composition_model_ms=ta['composition_model_cycles']*ms,v75_scalar_composition_model_ms=tb['composition_model_cycles']*ms,v75_burst_composition_model_ms=tc['composition_model_cycles']*ms,
    scalar_configuration_cycle_change_percent=100*(b['cycles']-a['cycles'])/a['cycles'],hud_burst_cycle_reduction_percent=100*(b['cycles']-c['cycles'])/b['cycles'],combined_cycle_reduction_percent=100*(a['cycles']-c['cycles'])/a['cycles']))
 result=dict(status='PASS_EXACT_OUTPUT_ABLATION',frames=rows,clocks=burst['clocks'],input_sha256={str(p.relative_to(ROOT)):sha(p)for p in paths},script_sha256=sha(Path(__file__).resolve()),shared_frozen_source_pins=len(common),shared_history_source_pins=len(history_common),new_scalar_burst_source_pins_identical=True,history_transaction_model_ms=[f['cycles']*ms for f in hist['frames']],validated_interval_model_min_ms=min(t['validated_decode_model_cycles']for t in hist['timings'])*ms,validated_interval_model_max_ms=max(t['validated_decode_model_cycles']for t in hist['timings'])*ms,scope='Same packets/clock/controller model and exact native output; V74-to-V75scalar shows cache-read scheduling plus idle-capability guard changes, V75scalar-to-burst isolates HUD runtime mode under identical RTL/TB',limitations=['No target fit/route/Fmax/CDC or physical30fps/sub10ms proof','Short decoder-paced history; not fixed-arrival qualification','nativeHUD CPU and liveESP32 transport service unmodeled','Background LCD/refresh duration and phase change; totalread/ACT/PRE are not normalized comparison rates'])
 (AREA/'comparison.json').write_text(json.dumps(result,indent=2)+'\n')
 for r in rows:print(f"FRAME{r['fid']} V74_ms={r['v74_transaction_model_ms']:.5f} V75scalar_ms={r['v75_scalar_transaction_model_ms']:.5f} V75burst_ms={r['v75_burst_transaction_model_ms']:.5f} combined_reduction={r['combined_cycle_reduction_percent']:.3f}%")
 print('V75_ABLATION_PASS physical30fps_proven=false targetsub10ms_proven=false')
if __name__=='__main__':main()
