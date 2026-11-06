#!/usr/bin/env python3
"""Derive explicit milestone budgets from actual V76 phase/trace evidence."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];AREA=ROOT/'fpga/experiments/cu66-v76'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 phase=AREA/'phases/results.json';trace=AREA/'service/trace.json'
 d=json.loads(phase.read_text());t=json.loads(trace.read_text())
 assert d['status']=='PASS_FUNCTIONAL_EXACT_FRAMEBUFFERS_AND_PHASES' and d['campaign_complete'] and len(d['runs'])==8
 assert t['YUV_bursts']==32400 and t['HUD_bursts']==2640 and t['wire_bytes']==560640
 clkps=d['clocks']['memory_period_ps'];fps=30;panel_hz=1e12/(541*834*34058)
 rows=[]
 for r in d['runs']:
  e=r['timings'][1];v=e['validated_ready_cycle']-e['packet_complete_cycle'];c=e['rgb_ready_cycle']-e['validated_ready_cycle'];tr=e['commit_ack_cycle']-e['packet_complete_cycle']
  assert e['validated_decode_model_cycles']==v and e['composition_model_cycles']==c and e['transaction_model_cycles']==tr
  rows.append(dict(hud_mode=r['hud_mode'],offset_cycles=r['offset_cycles'],validated_model_ms=v*clkps/1e9,composition_model_ms=c*clkps/1e9,transaction_model_ms=tr*clkps/1e9,
   serial_30fps_service_budget_pass=tr*clkps*fps<=10**12,validated_under10ms_pass=v*clkps<10**10,
   optimistic_decode_compose_overlap_period_model_ms=max(v,c)*clkps/1e9,
   optimistic_overlap_serial_stage_budget_pass=max(v,c)*clkps*fps<=10**12))
 # This is a payload-only load budget at assumed target rates, not controller service.
 loads=dict(direct_display_YUV_and_HUD_bytes_s=560640*panel_hz,canonical_upload_bytes_s=518400*fps,reference_payload_bytes_s=7806*64*fps,processor_HUD_upload_and_readback_bytes_s=2*42240*fps)
 current=dict(loads);current.pop('direct_display_YUV_and_HUD_bytes_s');current.update(painter_YUV_HUD_input_bytes_s=560640*fps,RGB_canvas_write_bytes_s=768000*fps,RGB_scanout_read_bytes_s=691200*panel_hz)
 result=dict(schema='cu76-milestone-budget-v1',status='PASS_DERIVED_BUDGET_ACCOUNTING',rows=rows,
  qualification=dict(target_source_fps=30,modeled_fixed_arrival_frames=1800,modeled_fixed_arrival_seconds=60,physical_frames=18000,physical_seconds=600,validated_max_exclusive_ns=10000000,observed_cases=len(rows),physical30fps_proven=False,target_under10ms_proven=False),
  payload_only_budget=dict(panel_refresh_hz=panel_hz,direct_YUV_components=loads,direct_total_bytes_s=sum(loads.values()),current_RGB_components=current,current_total_bytes_s=sum(current.values()),raw_assumed_bytes_s=200000000,notes=['Target30fps source payload and65.0755Hz panel loads; no measured modelorphysicalthroughputclaim','Reference payload7806tiles×64B/P, counts/mapping qualified separately','Excludes packet/CPU/command/turnaround/refresh and protocol overhead; servicebench does not necessarily include every listed client','Overlapping the measured stages is only an optimistic comparison; no overlapping RTL or directYUV renderer is implemented']),
  input_sha256={str(p.relative_to(ROOT)):sha(p)for p in [phase,trace]},source_sha256={str(Path(__file__).resolve().relative_to(ROOT)):sha(Path(__file__).resolve()),'docs/cu66-v76/milestones.md':sha(ROOT/'docs/cu66-v76/milestones.md')},limitations=['Same frozenV75RTL, no new timing/fit/CDC or bitstream','Finite phase snapshots, not sustained fixed-arrival30fps or validatedtargetWCET proof','Counter intervals cannot be subtracted as nonoverlapping critical-path decomposition'])
 (AREA/'milestone-budget.json').write_text(json.dumps(result,indent=2)+'\n');print('V76_MILESTONE_BUDGET_PASS cases=8 physical30fps_proven=false target_under10ms_proven=false')
if __name__=='__main__':main()
