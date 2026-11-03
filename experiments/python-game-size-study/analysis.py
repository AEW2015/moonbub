#!/usr/bin/env python3
"""Derive branch-specific preflight costs from frozen paired call records."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def summarize(rows):
    n=len(rows)
    old=sum(r['full_ms'] for r in rows)/n;new=sum(r['preflight_ms'] for r in rows)/n
    return {'n':n,'full_mean_ms':old,'preflight_mean_ms':new,'relative_service_change':new/old-1,
            'accepted':sum(r['accepted'] for r in rows),'preflight_serializations':sum(a['serialized'] for r in rows for a in r['attempts_preflight'])}


def main():
    path=HERE/'results.json';doc=json.loads(path.read_text())
    groups={kind:summarize([r for r in doc['rows'] if r['kind']==kind])
            for kind in ('seeded_noise_reject','real_pressure','real_normal')}
    for attempts in (1,2):
        rows=[r for r in doc['rows'] if r['kind']=='real_pressure' and len(r['attempts_full'])==attempts]
        groups[f'pressure_{attempts}_attempts']=summarize(rows)
    for row in doc['rows']:
        assert [(r['bytes'],r['fits']) for r in row['attempts_full']]==[(r['bytes'],r['fits']) for r in row['attempts_preflight']]
        assert row['accepted']==(row['packet_sha256'] is not None)
        assert all(not r['serialized'] for r in row['attempts_preflight'] if not r['fits'])
        assert sum(r['serialized'] for r in row['attempts_preflight'])==int(row['accepted'])
    prior=json.loads((HERE/'prior-check.json').read_text())
    assert prior['regenerated_packet_sha_matches']==72 and prior['exact_plane_length_checks']==216
    result={'source_sha256':{str(HERE/'analysis.py'):sha(HERE/'analysis.py')},
            'result_sha256':sha(path),'prior_check_sha256':sha(HERE/'prior-check.json'),'groups':groups,
            'selection':'Optional high-entropy rejection experiment, not a default normal-path speedup; fallback-only difference is negligible under uncontrolled load.'}
    (HERE/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(groups,indent=2))


if __name__=='__main__':main()
