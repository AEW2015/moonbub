#!/usr/bin/env python3
"""Replay retained V104 clocked control trace with independent integer geometry."""
import gzip
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
AREA=ROOT/'experiments/python-gamebub-v104/control'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    selected=json.loads((AREA/'results.json').read_text())
    receipt_path=ROOT/selected['selected_report']
    receipt=json.loads(receipt_path.read_text())
    assert selected['status']==receipt['status']=='PASS'
    for name,pin in receipt['source_sha256'].items():
        assert sha(ROOT/name)==pin,('source changed',name)
    for name,pin in receipt['artifacts_sha256'].items():
        assert sha(receipt_path.parent/name)==pin,('attempt artifact changed',name)
    verdict=receipt['terminal_verdict']
    assert verdict['status']=='TEST_PASS' and verdict['full_frames']==2 and verdict['directed_checks']==51
    assert verdict['half_cycle_public_comparisons']==3*verdict['clock_edges']
    trace=receipt_path.parent/receipt['trace_replay']['path']
    raw=gzip.decompress(trace.read_bytes())
    assert hashlib.sha256(raw).hexdigest()==receipt['trace_replay']['raw_sha256']
    previous=None;rows=0;advances=0;kills=0;full_wraps=0;planes=set();columns=set();row_pairs=set()
    for line in raw.splitlines():
        event=json.loads(line);p,t=event['plane'],event['tile']
        assert p in (0,1,2) and 0<=t<(5400 if p==0 else 1350)
        # Cartesian geometry, independent of the hardware column/parity recurrence.
        row,column=divmod(t,90) if p==0 else (0,0)
        qcell=(row//2)*45+column//2 if p==0 else t
        assert event['lookup']==event['cell']==qcell
        assert event['column']==column and event['odd']==row%2
        planes.add(p)
        if p==0:columns.add(column);row_pairs.add(row//2)
        if previous:
            assert previous['clock']<event['clock']
            killed=bool(event['reset'] or event['start'] or event['cancel'])
            if killed:
                assert (p,t,qcell,column)==(0,0,0,0);kills+=1
            elif event['advance']:
                pp,pt=previous['plane'],previous['tile'];limit=5400 if pp==0 else 1350
                expected=(pp,pt+1) if pt+1<limit else (min(pp+1,2),0)
                assert (p,t)==expected
                advances+=1
                if pp==2 and pt==1349:full_wraps+=1
            else:
                assert (p,t)==(previous['plane'],previous['tile'])
        previous=event;rows+=1
    assert rows==receipt['trace_replay']['rows'] and advances==receipt['trace_replay']['coordinate_advances']
    assert kills==receipt['trace_replay']['control_pulses']
    assert advances>=16200 and full_wraps==2 and planes=={0,1,2}
    assert columns==set(range(90)) and row_pairs==set(range(30))
    result=dict(schema='v104-control-independent-clocked-trace-audit-v1',status='PASS',
        selected_receipt=dict(path=str(receipt_path.relative_to(ROOT)),sha256=sha(receipt_path)),
        selected_summary=dict(path=str((AREA/'results.json').relative_to(ROOT)),sha256=sha(AREA/'results.json')),
        auditor=dict(path=str(Path(__file__).relative_to(ROOT)),sha256=sha(Path(__file__))),
        clock_edges=verdict['clock_edges'],half_cycle_public_comparisons=verdict['half_cycle_public_comparisons'],
        retained_trace_rows=rows,coordinate_advances=advances,control_pulses=kills,full_frame_wraps=full_wraps,
        planes=sorted(planes),Y_columns=len(columns),Y_row_pairs=len(row_pairs),trace_sha256=sha(trace),
        limits=['Actual-module two-state clocked interface test, not machine-checked formal or arbitrary internal-state equivalence.',
                'Trace retains every geometry advance/control pulse and state change plus periodic holds; SV compares production outputs at all low/high/low evaluations.',
                'No native timing, full decoder/HUD/C2, achieved hardware FPS or complete validated latency claim.'])
    (AREA/'trace-audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print('V104_CONTROL_TRACE_AUDIT',result['status'],rows,'rows',advances,'advances')


if __name__=='__main__':
    main()
