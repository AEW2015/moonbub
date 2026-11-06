#!/usr/bin/env python3
"""Compare frozen V73 and tile-major V74 exact-output command-model results."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'fpga/experiments/cu66-v74/system'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 paths=[ROOT/'fpga/experiments/cu66-v73/system/full-strip/results.json',AREA/'full-strip/results.json',AREA/'history-4-strip/results.json']
 old,new,hist=[json.loads(p.read_text())for p in paths]
 assert old['clocks']==new['clocks']==hist['clocks']
 new_history_common=new['source_sha256'].keys()&hist['source_sha256'].keys()
 assert new_history_common and all(new['source_sha256'][p]==hist['source_sha256'][p]for p in new_history_common)
 common=old['source_sha256'].keys()&new['source_sha256'].keys()
 assert common and all(old['source_sha256'][p]==new['source_sha256'][p]for p in common)
 for d,n in [(old,2),(new,2),(hist,4)]:
  assert d['status']=='PASS_FUNCTIONAL_MEMORY_AND_FRAMEBUFFERS' and d['summary']['total_underruns']==0
  assert d['summary']['distinct_complete_presentations']==n and len(d['frames'])==n
 rows=[];period=new['clocks']['memory_period_ps']/1e9
 for a,b,ta,tb in zip(old['frames'],new['frames'],old['timings'],new['timings'],strict=True):
  assert (a['fid'],a['key'],a['generation'])==(b['fid'],b['key'],b['generation'])
  assert a['actual_writes']==b['actual_writes']==664320
  assert a['actual_write_commands']==133920 and b['actual_write_commands']==101520
  assert a['actual_write_bus_beats']==1071360 and b['actual_write_bus_beats']==812160
  assert b['painter_read_commands']==35040 and b['painter_read_words']==280320
  assert b['p0_cache_hits']+b['p0_cache_misses']==b['p0_row_reads']
  row=dict(fid=b['fid'],key=bool(b['key']),v73=a,v74=b,
    v73_transaction_model_ms=a['cycles']*period,v74_transaction_model_ms=b['cycles']*period,
    v73_validated_interval_model_ms=ta['validated_decode_model_cycles']*period,v74_validated_interval_model_ms=tb['validated_decode_model_cycles']*period,
    v73_composition_model_ms=ta['composition_model_cycles']*period,v74_composition_model_ms=tb['composition_model_cycles']*period,
    transaction_reduction_percent=100*(a['cycles']-b['cycles'])/a['cycles'],
    write_bus_beat_reduction_percent=100*(a['actual_write_bus_beats']-b['actual_write_bus_beats'])/a['actual_write_bus_beats'])
  if b['p0_row_reads']:
   row.update(reference_useful_bytes=b['p0_row_reads']*16,reference_wire_bytes=b['p0_cache_misses']*16,
    v73_reference_useful_bytes=a['p0_row_reads']*8,v73_reference_wire_bytes=a['p0_cache_misses']*16)
  rows.append(row)
 result=dict(status='PASS_EXACT_OUTPUT_COMPARISON',frames=rows,clocks=new['clocks'],shared_frozen_source_pins=len(common),shared_new_history_source_pins=len(new_history_common),
  history_model_ms=[r['cycles']*period for r in hist['frames']],input_sha256={str(p.relative_to(ROOT)):sha(p)for p in paths},script_sha256=sha(Path(__file__).resolve()),
  scope='Same chronological key/P source packets, actual controller/model and exact framebuffer oracle. V74 changes physical canonical layout AND painter request shape; not an isolated single-change ablation.',
  p0_counter_semantics='V73 p0_row_reads carries four useful words per request; V74 carries eight. Both count accepted API calls, not logical rows across versions.',
  limitations=['Decoder-paced two/four-frame campaign, not fixed-arrival30fps','Model100MHz memory clock is not targetFmax or physical30fps evidence','No targetsub10ms validated decoding proof','NativeHUD CPU and liveESP32/QSPI service not charged','Different transaction duration and phase alter background LCD/refresh work; total reads/ACT/PRE not normalized'])
 (AREA/'comparison.json').write_text(json.dumps(result,indent=2)+'\n')
 for r in rows:print(f"FRAME{r['fid']} V73_ms={r['v73_transaction_model_ms']:.5f} V74_ms={r['v74_transaction_model_ms']:.5f} reduction={r['transaction_reduction_percent']:.3f}%")
 print('V74_COMPARISON_PASS target30fps_proven=false targetsub10ms_proven=false')
if __name__=='__main__':main()
