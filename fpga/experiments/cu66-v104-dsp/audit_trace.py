#!/usr/bin/env python3
"""Independently replay retained DSP-probe clock traces with Python state/math."""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
AREA=ROOT/'experiments/python-gamebub-v104/dsp'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    runner=ROOT/'scripts/cu66-v104/dsp.py'
    spec=importlib.util.spec_from_file_location('v104_dsp_probe',runner)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    selected=json.loads((AREA/'results.json').read_text());report_path=ROOT/selected['selected_report']
    report=json.loads(report_path.read_text());folder=report_path.parent
    assert selected['status']==report['status']=='PASS'
    assert report['source_sha256'][str(runner.relative_to(ROOT))]==sha(runner)
    for name,digest in report['source_sha256'].items():assert sha(ROOT/name)==digest,('source',name)
    for name,digest in report['artifacts_sha256'].items():assert sha(folder/name)==digest,('artifact',name)
    for name,production in [('original',ROOT/'fpga/experiments/cu66-v69/inverse/cu66_dequant.sv'),('candidate',ROOT/'fpga/experiments/cu66-v104-dsp/cu66_dequant.sv')]:
        adapter=ROOT/('fpga/experiments/cu66-v104-dsp/dequant_'+name+'.sv')
        assert adapter.read_text().replace('module dequant_'+name+' (','module cu66_dequant (',1)==production.read_text()
    runs=[]
    for row in report['runs']:
        replay=module.replay(folder/row['trace']['path'],row['verdict'])
        assert replay==row['trace_replay']
        runs.append(dict(seed=row['seed'],trace_sha256=sha(folder/row['trace']['path']),**replay))
    data=dict(schema='v104-dsp-independent-trace-audit-v1',status='PASS',selected_report=str(report_path.relative_to(ROOT)),selected_report_sha256=sha(report_path),audit_script_sha256=sha(Path(__file__)),runs=runs,total_clock_edges=sum(r['rows'] for r in runs),scope='Python state/math replay of actual clocked RTL traces, plus exact complete-body adapters and all declared source/artifact checksums; no mapped-netlist or native performance proof.')
    (AREA/'trace-audit.json').write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    print('V104_DSP_TRACE_AUDIT',data['status'],data['total_clock_edges'])


if __name__=='__main__':main()
