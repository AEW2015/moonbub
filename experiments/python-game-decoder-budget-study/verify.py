#!/usr/bin/env python3
"""Recompute retained operation/service arithmetic without encoding new packets."""
import hashlib
import json
from pathlib import Path
import budget
from dataclasses import replace
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def main():
    d=json.loads((HERE/'results.json').read_text())
    for name,expected in d['source_sha256'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected,name
    assert len(d['traces'])==d['trace_count']==19 and d['actual_packet_traces']==18
    traces={t['label']:t for t in d['traces']}
    for t in traces.values():
        assert sum(p['blocks'] for p in t['planes'])==sum(p['general_inverse']+p['zero']+p['dc_only'] for p in t['planes'])
        if t['packet_sha256'] is not None:
            assert t['packet_bytes']<=49152
            import benchmark
            expected=benchmark.trace_packet(bytes.fromhex(t['packet_hex']),t['label']); expected['trace_scope']=t['trace_scope'];assert t==expected
        else:assert t['packet_hex'] is None
    assert len(d['estimates'])==57
    for row in d['estimates']:
        arch=budget.Architecture(**row['estimate']['architecture'])
        assert row['estimate']==budget.estimate(traces[row['trace']],arch)
    for row in d['clock_sweep']:
        t=traces[row['trace']];first=row['first_passing_clock_mhz']
        for mhz in range(50,201):
            e=budget.estimate(t,replace(budget.Architecture(),clock_hz=mhz*1_000_000,dsp_lanes=row['dsp_lanes']))
            assert e['passes_average_30fps_budget']==(first is not None and mhz>=first)
    assert d['capacity_bytes']==budget.capacity() and d['capacity_total']==sum(budget.capacity().values())
    assert d['capacity_total']>d['modeled_memory_capacity_bytes']
    print('PASS:18actualAR02coefficienttraces+1analyticaldensecase;57conditionalbudgets;sourcepins;capacity;nohardwareordeadlineproof')
if __name__=='__main__':main()
