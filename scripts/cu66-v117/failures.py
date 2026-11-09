#!/usr/bin/env python3
"""Index retained terminal failures; never label provisional receipts as failed runs."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT/'experiments/python-gamebub-v117'
NOTES = AREA/'orchestration/attempt-notes.json'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def pin(path):
    return dict(path=str(path.relative_to(ROOT)), sha256=sha(path))

def main():
    prior=json.loads(NOTES.read_text())
    known={row['path']:row for row in prior.get('actual_RTL_failures', [])}
    reasons={
        'throughput-study/live-parent/attempts/20261109T115949823661Z/receipt.json':('parent_observation_boundary','Original wrapper exported a raw residual during its documented one-edge registered producer cancellation gap. Public external grants were masked; new isolated wrapper masks two exported observations and independently accounts for raw private work. Original failed wrapper is not relabeled PASS.'),
        'throughput-study/live-diagnostic/attempts/20261109T120816086878Z/receipt.json':('diagnostic_replay','Additive flushed trace, unchanged old need, confirmed cycle195383 join fault/raw residual first cancellation gap; no new independent functional PASS.'),
        'throughput-study/live-guard/attempts/20261109T123151283675Z/receipt.json':('postprocessor_type','First byte RTL/guard/C2 profile returned TEST_PASS, but Python used identity False on numeric JSON0 for pending owner. New immutable final runner requires literal integer0; RTL/bench/zero-debt condition unchanged. Fresh full four-profile execution qualified separately.'),
        'reconstruct-wordbank/attempts/20261109T124955603501Z/receipt.json':('source_generation_syntax','Generated for-loop replacement omitted trailing whitespace, concatenating endcount_residuals. Strict compile failed before RTL execution. Newline-only recipe/source/probe fix and fresh strict execution retained all old oracles.'),
    }
    actual=[];not_executed=[]
    for path in sorted(AREA.glob('**/attempts/*/receipt.json')):
        relative=path.relative_to(AREA)
        if any(x in relative.parts for x in ('sources','source-snapshot','compile-sources','snapshot')):
            continue
        raw=json.loads(path.read_text())
        if raw.get('status')!='FAIL' or 'wall_seconds' not in raw or not raw.get('artifact_sha256',raw.get('artifacts_sha256')):
            continue
        row={**known.get(str(path.relative_to(ROOT)), {}), **pin(path), 'status':raw['status'], 'actual_RTL_run':raw.get('actual_RTL_run',False)}
        if str(relative) in reasons:
            row['classification'],row['reason']=reasons[str(relative)]
        row.setdefault('classification','retained_terminal_failure')
        row.setdefault('reason','See immutable source snapshot, command exit and first causal raw diagnostic; no automatic claim of an RTL defect.')
        row['old_oracle_checks_removed']=False
        (actual if row['actual_RTL_run'] else not_executed).append(row)
    reviewers=[]
    for path in sorted((AREA/'audit').glob('*.json')):
        raw=json.loads(path.read_text())
        if str(raw.get('status','')).startswith('FAIL'):
            reviewers.append({**pin(path), 'status':raw['status'], 'scope':'Reviewer/parser/assumption report; separate from actual tool/RTL execution. Corrected PASS reports remain distinct.'})
    misses=[];native_failures=[]
    for path in sorted(AREA.glob('*/native/*/receipt.json')):
        raw=json.loads(path.read_text())
        if raw['status']=='RUNNING':
            continue
        entry={**pin(path),'status':raw['status'],'clock_period_ns':raw['clock_period_ns'],'timing':(raw.get('result') or {}).get('timing'),'clean_repeat_of':raw.get('clean_repeat_of')}
        if raw.get('component_route_finished') and entry['timing'] and entry['timing']['WNS_ns']<0:
            misses.append(entry)
        elif not raw.get('component_route_finished'):
            native_failures.append(entry)
    result=dict(schema='v117-retained-actual-and-review-failures-v2',actual_RTL_failures=actual,compile_or_preparation_failures=not_executed,reviewer_failures=reviewers,native_timing_misses=misses,native_tool_or_resource_failures=native_failures,source_refinement_note=prior.get('source_refinement_note'),scope='Only terminal receipts indexed. Expected malformed packet errors within a passing campaign and active provisional FAIL fields are not campaign failures. Raw successes inside a failed postprocessor attempt do not qualify its whole campaign.')
    NOTES.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print('V117_FAILURE_INDEX',len(actual),'actual-run failures',len(not_executed),'pre-execution failures',len(misses),'native setup misses')

if __name__=='__main__':
    main()
