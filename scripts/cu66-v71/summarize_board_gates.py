"""Read completed native reports. Numeric gates do not replace CDC/I/O review."""
from pathlib import Path
import argparse, hashlib, json, re
p = argparse.ArgumentParser()
p.add_argument('--directory', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
assert not a.output.exists(), 'Use a new evidence path'
r = a.directory.resolve()
sha = lambda q: hashlib.sha256(q.read_bytes()).hexdigest()
files = ['timing-summary.rpt', 'route-status.rpt', 'drc.rpt', 'check-timing.rpt',
         'setup-paths.rpt', 'hold-paths.rpt', 'cdc.rpt', 'exceptions.rpt', 'bus-skew.rpt',
         'source-freeze.json', 'selection.json', 'execution.json', 'routed.dcp']
missing = [n for n in files if not (r/n).is_file() or not (r/n).stat().st_size]
result = dict(directory=str(r), missing=missing, BIT_allowed=False, hardware_allowed=False)
if missing:
    result['status'] = 'INCOMPLETE_NATIVE_REPORT_SET'
else:
    text = (r/'timing-summary.rpt').read_text()
    lines = text.splitlines()
    first = next(i for i,s in enumerate(lines) if 'WNS(ns)' in s and 'TNS Total Endpoints' in s)
    row = next(s.split() for s in lines[first+1:] if re.match(r'^\s+-?\d+\.\d+\s+-?\d+\.\d+\s+\d+\s+\d+\s+',s))
    assert len(row) == 12, row
    metrics = dict(WNS_ns=float(row[0]), TNS_ns=float(row[1]), setup_failures=int(row[2]),
                   setup_total=int(row[3]), WHS_ns=float(row[4]), THS_ns=float(row[5]),
                   hold_failures=int(row[6]), hold_total=int(row[7]), WPWS_ns=float(row[8]),
                   TPWS_ns=float(row[9]), pulse_failures=int(row[10]), pulse_total=int(row[11]))
    route = (r/'route-status.rpt').read_text()
    def count(label):
        m = re.search(re.escape(label)+r'\.*\s*:\s*(\d+)', route)
        assert m, label
        return int(m.group(1))
    routes = {k:count(v) for k,v in dict(routable='of routable nets', fully_routed='of fully routed nets', errors='of nets with routing errors').items()}
    execution = json.loads((r/'execution.json').read_text())
    timing_ok = all(metrics[k]>0 for k in ['WNS_ns','WHS_ns','WPWS_ns']) and all(metrics[k]==0 for k in ['setup_failures','hold_failures','pulse_failures'])
    route_ok = routes['routable']==routes['fully_routed'] and routes['errors']==0
    native_ok = execution['returncode']==0
    if 'completion_marker' in execution:
        native_ok = native_ok and execution['completion_marker'] and execution.get('required_reports_present', False)
    result.update(status='PASS_NUMERIC_TIMING_ROUTE_NATIVE_MANUAL_REVIEW_REQUIRED' if timing_ok and route_ok and native_ok else 'FAIL_NUMERIC_GATES',
                  timing=metrics, routing=routes, native_execution_ok=native_ok,
                  manual_open=['DRC errors/warnings and their individual justification',
                               'CDC topology, first-stage fanout and held-data protocol pairing',
                               'Exception coverage, bus-skew coverage and absence of path segmentation',
                               'Unconstrained/asynchronous I/O scope and board/electrical timing limits',
                               'Exact functional, firmware and final BIT handoff binding'],
                  artifacts={n:dict(bytes=(r/n).stat().st_size,sha256=sha(r/n)) for n in files})
a.output.parent.mkdir(parents=True,exist_ok=True)
a.output.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='artifacts'},indent=2))
