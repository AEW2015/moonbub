#!/usr/bin/env python3
"""Retain a live predecessor/completion check before a serialized matrix row."""
import argparse
import datetime
import json
from pathlib import Path
import subprocess

import native as frozen

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--next',required=True,choices=['m3','m4','m5']);a=ap.parse_args()
    coord=frozen.AREA/'coordination';grant_path=coord/(a.next+'-grant.json');grant=frozen.load(grant_path)
    assert grant['trial_id']==a.next and grant['enabled'] and grant['heavy_slot_granted']
    previous=grant['required_previous_trial_terminal'];assert previous=='m'+str(int(a.next[1:])-1)
    receipts=[];active=[]
    for p in (frozen.AREA/'native').glob('*/receipt.json'):
        r=frozen.load(p)
        if r['status']=='RUNNING':active.append(frozen.rel(p))
        if r['trial_id']==previous and r['start_mode']=='checkpoint':receipts.append((p,r))
    assert not active,('No concurrent matrix row permitted',active)
    assert len(receipts)==1
    path,receipt=receipts[0];assert receipt['status']!='RUNNING' and isinstance(receipt['observed_exit_code'],int)
    dispatch=receipt['predispatch'];dispatch_path=frozen.ROOT/dispatch['path'];assert frozen.sha(dispatch_path)==dispatch['sha256']
    build=Path(receipt['build_external']).name;completion_path=coord/('native-completion-'+build+'.json');completion=frozen.load(completion_path)
    assert completion['dispatch']==frozen.rel(dispatch_path) and completion['dispatch_sha256']==frozen.sha(dispatch_path) and isinstance(completion['runner_exit_code'],int)
    gate_path=coord/(a.next+'-pre-native-audit.json');gate=frozen.load(gate_path)
    assert gate['status']=='PASS_V108_NATIVE_PREFLIGHT_AUDIT' and gate['grant_sha256']==frozen.sha(grant_path)
    assert gate['policy_sha256']==frozen.sha(frozen.POLICY)
    containers=subprocess.check_output(['docker','ps','--filter','name=gamebub-v108','--format','{{.Names}}'],text=True).splitlines()
    assert len(containers)<=1,('Other global lane already occupied by more than one owned job',containers)
    record=dict(schema='v108-live-serial-predecessor-check-v1',status='PASS_LIVE_PREDECESSOR_AND_COMPLETION',timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        next_trial=a.next,required_previous_trial_terminal=previous,previous_receipt=dict(path=frozen.rel(path),sha256=frozen.sha(path),status=receipt['status']),
        previous_dispatch=dict(path=frozen.rel(dispatch_path),sha256=frozen.sha(dispatch_path)),previous_completion=dict(path=frozen.rel(completion_path),sha256=frozen.sha(completion_path)),
        next_grant=dict(path=frozen.rel(grant_path),sha256=frozen.sha(grant_path)),next_independent_gate=dict(path=frozen.rel(gate_path),sha256=frozen.sha(gate_path)),
        active_owned_heavy_containers=containers,owned_heavy_count_before=len(containers),owned_heavy_count_with_next=len(containers)+1,
        checker_sha256=frozen.sha(Path(__file__)))
    target=coord/(a.next+'-live-predecessor-check.json')
    with target.open('x') as f:f.write(json.dumps(record,indent=2,sort_keys=True)+'\n')
    print('V108_LIVE_SERIAL_CHECK_PASS',a.next,frozen.rel(target),frozen.sha(target),flush=True)

if __name__=='__main__':main()
