#!/usr/bin/env python3
"""Extract all retained setup paths, with no Fmax inference or endpoint coverage claim."""
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'experiments/python-gamebub-v107'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def parse(path):
    text=path.read_text()
    blocks=re.split(r'(?=^Slack \()',text,flags=re.M)[1:]
    rows=[]
    for block in blocks:
        def grab(pattern):
            m=re.search(pattern,block,re.M)
            assert m,(path,pattern)
            return m
        slack=float(grab(r'^Slack \([^\n]+?\)\s*:\s*([-\d.]+)ns')[1])
        source=grab(r'^\s*Source:\s*(\S+)')[1]
        dest=grab(r'^\s*Destination:\s*(\S+)')[1]
        delay=grab(r'^\s*Data Path Delay:\s*([\d.]+)ns\s*\(logic ([\d.]+)ns \([\d.]+%\)\s*route ([\d.]+)ns')
        levels=grab(r'^\s*Logic Levels:\s*(\d+)\s*(.*)')
        req=float(grab(r'^\s*Requirement:\s*([\d.]+)ns')[1])
        assert req==10.0
        route_ns=float(delay[3]);total=float(delay[1]);logic=float(delay[2])
        assert abs(total-logic-route_ns)<0.002
        rows.append(dict(source=source,destination=dest,slack_ns=slack,requirement_ns=req,
            data_delay_ns=total,logic_delay_ns=logic,route_delay_ns=route_ns,
            logic_levels=int(levels[1]),logic_types=levels[2].strip(),route_share=round(route_ns/total,6)))
    assert rows and all(rows[i]['slack_ns']<=rows[i+1]['slack_ns'] for i in range(len(rows)-1))
    return rows


def main():
    trials=[];hashes={}
    for folder in sorted((AREA/'native').iterdir()):
        receipt_path=folder/'receipt.json';receipt=json.loads(receipt_path.read_text())
        if not receipt.get('routing_checkpoint_written') or receipt.get('observed_exit_code')!=0:continue
        inputs=folder/'inputs.json';variant=json.loads(inputs.read_text())['variant']
        for f in (receipt_path,inputs):hashes[str(f.relative_to(ROOT))]=sha(f)
        stages={}
        for stage in ('synth','place','route'):
            p=folder/'reports'/(stage+'-setup-paths.rpt')
            if p.is_file():
                hashes[str(p.relative_to(ROOT))]=sha(p);stages[stage]=parse(p)
        assert 'route' in stages
        trials.append(dict(variant=variant,receipt=str(receipt_path.relative_to(ROOT)),stages=stages))
    assert trials
    result=dict(schema='v107-retained-setup-path-analysis-v1',source_sha256=hashes,trials=trials,
        scope='Top reported setup paths at each stage only; absence from a bounded list does not prove endpoint closure. Reported clock remains10ns; no derived achieved Fmax.',
        parser_sha256=sha(Path(__file__)),hardware_qualified=False)
    (AREA/'path-analysis.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(trials=len(trials),paths=sum(len(v) for t in trials for v in t['stages'].values()))))


if __name__=='__main__':main()
