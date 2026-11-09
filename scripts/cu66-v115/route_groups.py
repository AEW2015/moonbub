#!/usr/bin/env python3
"""Group source-bound routed top-50 paths; never treat this sample as all paths."""
import collections
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'experiments/python-gamebub-v115'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pin(p):return {'path':str(p.relative_to(ROOT)),'sha256':sha(p)}
def main():
    rows=[]
    for folder in [AREA/'native',AREA/'refined/native',AREA/'final/native']:
        for p in sorted(folder.glob('*/receipt.json')):
            d=json.loads(p.read_text())
            if not d.get('component_route_finished'):continue
            path=p.parent/'reports/route-setup-paths.rpt'
            assert sha(path)==d['retained_artifact_sha256']['reports/route-setup-paths.rpt']
            parsed=[]
            for block in path.read_text().split('Slack (')[1:]:
                slack=re.search(r':\s+(-?[\d.]+)ns',block)
                source=re.search(r'Source:\s+([^\n]+)',block)
                target=re.search(r'Destination:\s+([^\n]+)',block)
                if slack and source and target:
                    parsed.append({'slack_ns':float(slack[1]),'source':source[1].strip(),'destination':target[1].strip()})
            assert len(parsed)==50 and parsed[0]['slack_ns']==d['result']['timing']['WNS_ns']
            groups=collections.defaultdict(list)
            for item in parsed:
                key=tuple(re.sub(r'\[[^]]*\]','[]',item[k])for k in ['source','destination'])
                groups[key].append(item['slack_ns'])
            rows.append({'receipt':pin(p),'report':pin(path),'period_ns':d['clock_period_ns'],
                         'source_identity':d['source_contract']['source_sha256'],
                         'sampled_paths':len(parsed),'worst':parsed[0],
                         'groups':[{'source':a,'destination':b,'sample_count':len(v),'worst_slack_ns':min(v)}for (a,b),v in groups.items()],
                         'owner_sequence_paths_in_sample':sum('owner_sequence' in x['source']or'owner_sequence'in x['destination']for x in parsed)})
    out={'schema':'v115-source-bound-routed-path-groups-v1','status':'ROUTED_DIAGNOSTIC_SAMPLE_ONLY',
         'runner':pin(Path(__file__).resolve()),'trials':rows,
         'limits':['Top50 is not an exhaustive endpoint/path census. Absence here is not absence from the design.',
                   'Use final routed setup/hold/clock/routing and complete source-bound receipts for timing qualification.']}
    (AREA/'route-groups.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'trials':len(rows),'status':out['status']}))
if __name__=='__main__':main()
