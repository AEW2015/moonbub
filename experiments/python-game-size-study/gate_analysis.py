#!/usr/bin/env python3
"""Derived branch costs and one-sided-bound correctness from stored gate pairs."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def summarize(rows):
    n=len(rows);old=sum(r['full_ms'] for r in rows)/n;new=sum(r['gate_ms'] for r in rows)/n
    return {'n':n,'full_mean_ms':old,'gate_mean_ms':new,'relative_service_change':new/old-1,
            'accepted':sum(r['accepted'] for r in rows),'actual_gate_serializations':sum(a['serialized'] for r in rows for a in r['attempts_gate'])}


def main():
    path=HERE/'gate-results.json';doc=json.loads(path.read_text())
    groups={kind:summarize([r for r in doc['rows'] if r['kind']==kind])
            for kind in ('seeded_noise_reject','real_pressure','real_normal')}
    for attempts in (1,2):
        groups[f'pressure_{attempts}_attempts']=summarize([r for r in doc['rows'] if r['kind']=='real_pressure' and len(r['attempts_full'])==attempts])
    for row in doc['rows']:
        assert len(row['attempts_full'])==len(row['attempts_gate'])<=2
        assert row['accepted']==(row['packet_sha256'] is not None)
        for a,b in zip(row['attempts_full'],row['attempts_gate']):
            assert a['label']==b['label'] and a['fits']==b['fits'] and b['lower_bytes']<=a['bytes']
            if b['provably_rejected']:assert b['lower_bytes']>row['cap'] and not b['serialized'] and b['bytes'] is None
            else:assert b['serialized'] and b['bytes']==a['bytes']
    result={'source_sha256':{str(HERE/'gate_analysis.py'):sha(HERE/'gate_analysis.py')},
            'result_sha256':sha(path),'groups':groups,
            'selection':'Useful dense-noise rejection guard on this fixture; weak real oversize bounds and normal timing variation remain, no deadline/FPS guarantee.'}
    (HERE/'gate-summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(groups,indent=2))


if __name__=='__main__':main()
