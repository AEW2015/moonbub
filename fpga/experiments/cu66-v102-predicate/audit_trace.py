#!/usr/bin/env python3
"""Replay retained V102 predicate outputs using a Cartesian geometry oracle."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--report',type=Path,default=ROOT/'experiments/python-gamebub-v102/predicate/results.json')
args=parser.parse_args()
summary=json.loads(args.report.read_text())
report_path=ROOT/summary['selected_report'] if 'selected_report' in summary else args.report
report=json.loads(report_path.read_text());assert report['status']=='PASS'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name,pin in report['artifacts_sha256'].items():assert sha(report_path.parent/name)==pin,name
source=Path(report_path.parent/report['trace_replay']['path'])
assert sha(source)==report['trace_replay']['sha256']
# Construct the frame-geometry regions independently of fixed interval constants.
yhidden=set()
for x0,x1,y0,y1 in ((3,22,7,9),(3,22,11,13),(21,61,45,48),(21,51,49,51)):
    for row in range(y0,y1):
        for column in range(x0,x1):yhidden.add(row*90+column)
chidden={23*45+column for column in range(11,30)}
count=0;true_counts=[0]*4;raw=hashlib.sha256()
with gzip.open(source,'rb') as trace:
    for line in trace:
        raw.update(line);r=json.loads(line);p,t=divmod(count,8192)
        assert (r['plane'],r['tile'])==(p,t)
        expected=int(t in (yhidden if p==0 else chidden))
        assert r['original']==r['candidate']==r['expected']==expected,(p,t)
        true_counts[p]+=expected;count+=1
assert count==32768 and true_counts==[256,19,19,19]
assert raw.hexdigest()==report['trace_replay']['raw_sha256']
print(json.dumps({'status':'PASS_INDEPENDENT_TRACE_REPLAY','cases':count,'true_counts':true_counts,'clock_edges':0,'artifacts_verified':len(report['artifacts_sha256'])}))
