#!/usr/bin/env python3
"""Selected final-vs-initial V115 cycle fences, with conditional clocks only."""
import csv
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'experiments/python-gamebub-v115/final'
INITIAL=ROOT/'experiments/python-gamebub-v115/spatial/results.json'
INITIAL_SHA='52697a476f23ec0c44c17fc80026daeb63755d5481f2c360c8af9b4f557fc907'
INITIAL_RAW_SHA='fb381cd142dfb9c4712bf8dacb280b45555859591af264bde244fa8f4ccff573'
HELPER=ROOT/'scripts/cu66-v115/performance.py'
HELPER_SHA='10d43b5966eca31252a626539ddc1ca1c0214f61103cbd36f2ee002bea5300f2'
# Reuse the frozen source-bound transcript parser, including normal-transport
# pairing which excludes two later retry cases rather than overwriting a key.
spec=importlib.util.spec_from_file_location('v115_cycle_parser',HELPER)
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
p.require(p.sha(HELPER)==HELPER_SHA,'frozen cycle parser changed')

def main():
 selected_path=AREA/'spatial/results.json'
 if not selected_path.exists()or p.load(selected_path).get('status')!='PASS_V115_FINAL_SPATIAL_CANONICAL':
  print('PREREQUISITES_NOT_READY: selected final spatial PASS absent; no ledger written.');return
 pins={}
 candidate,receipt=p.selected(selected_path,'PASS_V115_FINAL_SPATIAL_CANONICAL',pins)
 baseline,base_receipt=p.selected(INITIAL,'PASS_V115_SPATIAL_CANONICAL',pins)
 p.pin(INITIAL,pins,INITIAL_SHA);p.pin(base_receipt,pins,INITIAL_RAW_SHA)
 oracle,_=p.selected(p.ORACLE,'PASS_V113_SPATIAL_CANONICAL',pins);p.pin(p.ORACLE,pins,p.ORACLE_SHA)
 p.require(candidate['inputs']==baseline['inputs'],'matched inputs changed')
 origins,old=candidate['source_origins'],baseline['source_origins']
 p.require(len(origins)==18 and set(origins)==set(old),'origin contract')
 changed=[a for a in origins if origins[a]['sha256']!=old[a]['sha256']]
 p.require(set(changed)=={'fpga/experiments/cu66-v91h/br88_packet_ingress_sync_v91h.sv','fpga/experiments/cu66-v91g2/packed_scratch_v91g2.sv','fpga/experiments/cu66-v91k/cs88_pipeline_v91k.sv'},'expected final ingress/scratch/owner source cuts')
 for q in (candidate,baseline):
  for o in q['source_origins'].values():p.require(q['source_sha256'][o['path']]==o['sha256'],'origin/proof source binding')
 p.require(candidate['candidate_model_reused']is False and candidate['canonical_reused_actual_RTL']is False,'fresh candidate proof required')
 rows=[]
 for seed in p.SEEDS:
  for group in ('runs','transport_runs'):
   runs=[next(r for r in q[group]if r['seed']==seed)for q in (candidate,baseline,oracle)]
   p.require(len({r['artifacts']['canonical_actual']['raw_sha256']for r in runs})==1,'frozen V113 canonical bytes differ')
  for kind in ('component','transport'):
   current,fences=p.transcript(candidate,receipt,kind,seed,pins)
   before,base_fences=p.transcript(baseline,base_receipt,kind,seed,pins)
   p.require(current.keys()==before.keys(),'successful corpus differs')
   for key,row in current.items():
    oldrow=before[key];done,pixel=p.latency(row);old_done,old_pixel=p.latency(oldrow)
    result=dict(kind=kind,seed=seed,case=key[0],profile=key[1],
      baseline_case_cycles=oldrow['cycles'],candidate_case_cycles=row['cycles'],change_case_cycles=row['cycles']-oldrow['cycles'],
      baseline_first_decoder_byte_to_done_cycles=old_done,candidate_first_decoder_byte_to_done_cycles=done,change_first_decoder_byte_to_done_cycles=done-old_done,
      baseline_first_decoder_byte_to_last_pixel_cycles=old_pixel,candidate_first_decoder_byte_to_last_pixel_cycles=pixel,change_first_decoder_byte_to_last_pixel_cycles=pixel-old_pixel,
      conditional_done_ms_at100MHz=done/100000,conditional_done_ms_at125MHz=done/125000,
      conditional_strict_under10ms_at125MHz=done<p.BUDGET,conditional_10ms_cycle_margin_at125MHz=p.BUDGET-done,
      baseline_transport_start_to_report_cycles=None,candidate_transport_start_to_report_cycles=None,change_transport_start_to_report_cycles=None,
      candidate_ingress_commit_to_decoder_done_cycles=None)
    if kind=='transport':
     a,b=fences[key],base_fences[key]
     result.update(baseline_transport_start_to_report_cycles=b['elapsed_cycles'],candidate_transport_start_to_report_cycles=a['elapsed_cycles'],
                   change_transport_start_to_report_cycles=a['elapsed_cycles']-b['elapsed_cycles'],candidate_ingress_commit_to_decoder_done_cycles=a['decoder_done_cycle']-a['ingress_commit_cycle'])
    result['matched_successful_fence_cycles_equal']=all(result[n]==0 for n in ('change_case_cycles','change_first_decoder_byte_to_done_cycles','change_first_decoder_byte_to_last_pixel_cycles'))and result['change_transport_start_to_report_cycles']in (None,0)
    rows.append(result)
 equal=all(r['matched_successful_fence_cycles_equal']for r in rows)
 report=dict(schema='v115-final-vs-initial-actual-component-transport-cycles-v1',
  status='MEASURED_RTL_CYCLES_CONDITIONAL_CLOCK_CONVERSIONS_ONLY'if equal else 'MEASURED_RTL_CYCLES_WITH_INITIAL_V115_FENCE_DIFFERENCES',
  qualification=dict(path=p.rel(selected_path),sha256=p.sha(selected_path)),baseline=dict(path=p.rel(INITIAL),sha256=INITIAL_SHA,receipt_sha256=INITIAL_RAW_SHA),
  canonical_oracle=dict(path=p.rel(p.ORACLE),sha256=p.ORACLE_SHA),
  source_sha256={p.rel(Path(__file__).resolve()):p.sha(Path(__file__)),p.rel(HELPER):HELPER_SHA},selected_input_sha256=pins,
  composition=dict(changed_aliases=changed,candidate_origins=origins,initial_origins=old),
  successful_component_case_profiles=24,successful_transport_case_profiles=24,rows=rows,profiles=p.summary(rows),
  matched_successful_fence_cycles_equal=equal,fence_difference_rows=[r for r in rows if not r['matched_successful_fence_cycles_equal']],
  expected_added_external_cycles=0,whole_interface_cycle_equivalence_proved_by_this_ledger=False,
  candidate_contract=candidate['contract'],baseline_contract=baseline['contract'],assumed_conversion_clocks_Hz=[100000000,125000000],
  strict_under10ms_at125MHz_requires_fewer_than_cycles=p.BUDGET,conditional_30fps_service_budget_cycles_at125MHz=125000000/30,
  achieved_clock_validated_by_this_ledger=False,hardware_30fps=False,complete_validated_decode_under10ms=False,full_frame_publication=False,
  limits=[
   'Actual successful component and V97 transport fences compared against initial V115 with identical corpus/seeds and canonical bytes; negative frames and later abort/reset retries excluded from latency distributions.',
   'First byte is first accepted decoder byte; transport start-to-report includes earlier command and finite FIFO prefill, and is reported separately.',
   'Zero matched fence deltas are bounded observations, not proof of every public value on every possible input cycle; separate focused pair checks retain their own scope.',
   'The final owner authorization/address cut and inherited header/tile slots are intended to preserve initial V115 external cycles; every observed difference is retained rather than ignored.',
   'Local decoder done/last canonical pixel exclude complete C2/HUD/seal validation and parent publication. The separate live-parent partition is not included here.',
   '100/125-MHz conversion is conditional arithmetic; achieved route clocks, full-system latency, ESP32 execution and sustained hardware30fps remain separate.',
   'Fitting a33.333ms conditional service interval is not hardware30fps; strictly under10ms requires fewer than1.25million cycles at assumed125MHz.'])
 AREA.mkdir(parents=True,exist_ok=True)
 (AREA/'performance.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 with(AREA/'performance.csv').open('w',newline='')as f:
  writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
 print(json.dumps(dict(matched_successful_fence_cycles_equal=equal,profiles=report['profiles']),sort_keys=True))
if __name__=='__main__':main()
