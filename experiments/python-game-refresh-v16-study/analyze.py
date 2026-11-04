#!/usr/bin/env python3
"""Untimed matched-ID analysis of retained refresh evidence."""
import argparse
import hashlib
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def build():
    path=HERE/'results.json';d=json.loads(path.read_text());cases={c['profile']:c for c in d['cases']}
    regular=cases['gm_refresh30'];coarse=cases['gm_refresh30_coarse'];repeat=cases['gm_refresh30_repeat']
    def keymap(c):return {p['id']:p for p in c['result']['packets'] if p['admitted'] and p['refresh_key']}
    a,b,t=map(keymap,(regular,coarse,repeat));ids=sorted(a.keys()&b.keys()&t.keys())
    assert ids==[31,62,93,124,155]
    assert regular['manifest']==coarse['manifest']==repeat['manifest']
    pairs=[]
    for i in ids:
        assert a[i]['reference_id'] is None and b[i]['reference_id'] is None
        assert a[i]['packet_sha256']==t[i]['packet_sha256']
        assert a[i]['info']['selected_pixels']==b[i]['info']['selected_pixels']==21120
        pairs.append(dict(id=i,input_sha256=regular['manifest']['frame_sha256'][i],
                          regular_bytes=a[i]['bytes'],coarse_bytes=b[i]['bytes'],
                          saved_bytes=a[i]['bytes']-b[i]['bytes']))
    total=sum(x['regular_bytes'] for x in pairs);smaller=sum(x['coarse_bytes'] for x in pairs)
    def commits(c):return {p['id']:p for p in c['result']['commits']}
    ca,cb=map(commits,(regular,coarse));common=sorted(ca.keys()&cb.keys())
    quality=sum(cb[i]['active_rgb565_mse']-ca[i]['active_rgb565_mse'] for i in common)/len(common)
    rows=[]
    for c in d['cases']:
        r=c['result'];presented=r['presented'];decoded=commits(c)
        ids_steady=[p['id'] for p in presented if 500<=p['at_ms']<5500]
        assert len(ids_steady)==len({c['manifest']['frame_sha256'][i] for i in ids_steady})==len({decoded[i]['rgb_sha256'] for i in ids_steady})
        rows.append(dict(profile=c['profile'],strict=r['presented_strict'],eventual=r['presented_eventual'],
                         steady_distinct_input_and_decoded_images=len(ids_steady),modeled_ids_per_second=len(ids_steady)/5,
                         committed_ids=sorted(decoded),mean_source_rgb565_mse=sum(p['active_rgb565_mse'] for p in decoded.values())/len(decoded)))
    return dict(results_sha256=sha(path),analyzer_sha256=sha(HERE/'analyze.py'),
        matched_independent_key_pairs=pairs,matched_key_total_regular_bytes=total,matched_key_total_coarse_bytes=smaller,
        matched_key_complete_body_saving_percent=100*(1-smaller/total),
        regular_and_coarse_common_decoded_ids=common,common_decoded_source_rgb565_mse_delta=quality,
        profiles=rows,
        limit='Key-only byte comparison has same independent-key source/mappriority/UIcoverage; coarsebackgroundchangesquality. P histories/admission differ, so aggregate wire/quality gains are not same-output compression. Repeat unchanged keyhashes controls bytes, not causal walltimes. Reused v15regression material, not new validation.')
def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args();out=build();path=HERE/'matched-refresh.json'
    if args.check:assert json.loads(path.read_text())==out
    else:path.write_text(json.dumps(out,indent=2)+'\n')
    print('PASS:5same-input independent refreshkey pairs;all4exactUI;sourcequality/matchedIDs and repeatvariability retained;nosustainedhardwareclaim')
if __name__=='__main__':main()
