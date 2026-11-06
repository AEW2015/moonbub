#!/usr/bin/env python3
"""Report finite campaign cadence and latency without promoting model clocks to hardware."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'fpga/experiments/cu66-v78/system'
def main():
 runs=[];pins={}
 for path in sorted(AREA.glob('*/results.json')):
  d=json.loads(path.read_text())
  if d['schema']!='cu78-actual-decode-direct-system-v1':continue
  pins[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest()
  ts=d['timings'];clock=d['clocks']['memory_period_ps'];n=len(ts)
  def milliseconds(cycles):return cycles*clock/1e9
  validated=[milliseconds(t['validated_ready_cycle']-t['packet_complete_cycle'])for t in ts]
  commit=[milliseconds(t['commit_ack_cycle']-t['packet_complete_cycle'])for t in ts]
  display=[(t['first_complete_raster_end_ps']-t['packet_complete_cycle']*clock)/1e9 for t in ts]
  starts=[t['first_complete_raster_start_ps']for t in ts]
  gaps=[(b-a)/1e9 for a,b in zip(starts,starts[1:])]
  def stats(values):return dict(min=min(values),median=statistics.median(values),max=max(values))
  runs.append(dict(run=path.parent.name,frames=n,arrival_mode=d['arrival_mode'],tac_ns=d['tac_ns'],
   validated_ms=stats(validated),ingress_to_commit_ack_ms=stats(commit),
   ingress_to_first_full_raster_end_ms=stats(display),
   first_full_raster_start_gap_ms=stats(gaps),
   finite_first_to_last_source_cadence_fps=(n-1)*1e12/(starts[-1]-starts[0]),
   maximum_release_to_admission_ms=max(milliseconds(t['queue_cycles'])for t in ts),
   distinct_sources_with_correct_raster=sum(t['complete_rasters']>0 for t in ts),
   serial_33ms_passes=sum(t['met_serial_30fps_budget']for t in ts),
   strict_under10ms_passes=sum(t['met_validated_under10ms']for t in ts),
   all_rasters_including_repeats=sum(t['complete_rasters']for t in ts),
   physical_fps_proven=False))
 out=dict(schema='cu78-finite-campaign-analysis-v1',source_sha256=pins,runs=runs,
  boundaries=['Cadence uses N-1 source intervals between first complete-raster starts; excludes initial load and final drain; short diagnostic only.',
   'Full-raster latency includes native refresh quantization; first_correct_pixel may be black margin and is not first game-image photon.',
   'Modeled clock is100MHz, nativeHUD CPU/control is zero-simtime, no liveESP32 transport.',
   'Serial33.33ms ACK budget is not a display latency bound or the1800-source/60s sustained proof.',
   'max_input_queue in producer includes source in service; no validated ESP32 queue capacity.'])
 (AREA/'analysis.json').write_text(json.dumps(out,indent=2)+'\n')
 for r in runs:print(r['run'],json.dumps({k:r[k]for k in ('frames','validated_ms','ingress_to_commit_ack_ms','ingress_to_first_full_raster_end_ms','finite_first_to_last_source_cadence_fps')}))
if __name__=='__main__':main()
