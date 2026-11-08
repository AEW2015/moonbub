#!/usr/bin/env python3
"""Collect completed observations without upgrading running/negative trials to passes."""
import hashlib
import json
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT/'experiments/python-gamebub-v108'


def main():
    rows = []
    paths = sorted([*(AREA/'native').glob('*/receipt.json'), *(AREA/'outtile-native').glob('*/receipt.json')])
    for p in paths:
        d = json.loads(p.read_text())
        result = d.get('result', {})
        kind = 'qualified_composition' if p.parent.parent.name == 'outtile-native' else ('matrix' if d['start_mode'] == 'checkpoint' else 'original_source_clean_repeat')
        rows.append(dict(trial_id=d['trial_id'], status=d['status'], start_mode=d['start_mode'],
                         observation_kind=kind,
                         receipt=str(p.relative_to(ROOT)), receipt_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
                         directives=d['directives'], clock_period_ns=d['clock_period_ns'],
                         synthesis_executed=d['synthesis_executed'],
                         timing=result.get('timing'), worst_setup_path=result.get('worst_setup_path'),
                         component_internal_100MHz_pass=result.get('component_internal_100MHz_pass', False),
                         wall_seconds=d.get('wall_seconds')))
    matrix = [x for x in rows if x['start_mode'] == 'checkpoint']
    finished = [x for x in matrix if x['timing'] is not None]
    best = max(finished, key=lambda x:x['timing']['WNS_ns']) if finished else None
    summary = dict(schema='v108-observation-summary-v1', initial_matrix_complete=len(finished)==6,
                   native_observations=rows, best_completed_matrix_trial=best,
                   reproducible_component_100MHz_qualified=False, hardware_30fps=False,
                   complete_validated_decode_under10ms=False,
                   limits=['Running observations are provisional; only retained final route metrics enter ranking.',
                           'Reproducible closure requires independent final-receipt audit and clean RTL repeat.',
                           'Component timing is separate from parent IO/CDC and hardware throughput.'])
    out = AREA/'progress-summary.json'
    out.write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    with (AREA/'native-comparison.csv').open('w', newline='') as f:
        fields = ['trial_id','observation_kind','status','clock_period_ns','WNS_ns','TNS_ns','setup_failing','setup_total','WHS_ns','hold_failing','hold_total','WPWS_ns','pulse_failing','pulse_total','component_internal_100MHz_pass','wall_seconds','receipt','receipt_sha256']
        writer = csv.DictWriter(f,fieldnames=fields)
        writer.writeheader()
        for row in rows:
            flat = {k:row[k] for k in fields if k in row}
            flat.update(row['timing'] or {})
            writer.writerow({k:flat.get(k,'') for k in fields})
    for row in rows:
        t=row['timing']
        print(row['trial_id'],row['status'], ('WNS='+str(t['WNS_ns'])+'ns setupfails='+str(t['setup_failing'])) if t else 'pending')


if __name__ == '__main__':
    main()
