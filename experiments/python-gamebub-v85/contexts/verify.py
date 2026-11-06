#!/usr/bin/env python3
"""Independent retained count/identity verification; no native recompilation."""
import argparse,hashlib,importlib.util,json,sys
from pathlib import Path

AREA=Path(__file__).resolve().parent
ROOT=AREA.parents[2]


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m


def main():
    p=argparse.ArgumentParser();p.add_argument('--verify',action='store_true');args=p.parse_args()
    index=json.loads((AREA/'index.json').read_text())
    new=load('cu85_verify_context_data',AREA/'data.py')
    old=load('cu85_verify_aggregate',ROOT/'experiments/python-gamebub-v84/entropy/data.py')
    shared={k:0 for k in new.FIELDS};contexts=[dict(shared)for _ in range(4)];frames=tiles=0
    for current,original in zip(new.iter_frames(),old.iter_frames(),strict=True):
        for key in('cohort','ordinal','fid','key','packet_sha256','canonical_sha256','hud_sha256','display_sha256','zero_mask','dispatches','plane_bytes','coefficient_sha256'):
            assert current[key]==original[key],key
        for s,cs,aggregate in zip(current['shared_work'],current['context_work'],original['tile_work'],strict=True):
            for name in new.FIELDS:
                assert s[name]+sum(c[name]for c in cs)==aggregate[name]
                shared[name]+=s[name]
                for i,c in enumerate(cs):contexts[i][name]+=c[name]
            assert s['emits']==1 and all(c['emits']==0 for c in cs)
            tiles+=1
        frames+=1
    assert frames==457 and tiles==3701700
    assert shared==index['shared_totals'] and contexts==index['context_totals']
    for name,digest in index['source_sha256'].items():assert sha(ROOT/name)==digest,name
    result=dict(schema='cu66-v85-context-verification-v1',status='PASS',frames=frames,tiles=tiles,
                exact_v84_per_tile_counter_parity=True,identities_and_original_digests_match=True,
                source_sha256={str(Path(__file__).relative_to(ROOT)):sha(Path(__file__)),
                               str((AREA/'index.json').relative_to(ROOT)):sha(AREA/'index.json'),
                               str((AREA/'data.py').relative_to(ROOT)):sha(AREA/'data.py')},
                shared_totals=shared,context_totals=contexts,
                scope='Native observation consistency and integrity, not cycle/timing proof.')
    destination=AREA/'verification.json'
    if args.verify:assert json.loads(destination.read_text())==result
    else:
        if destination.exists():raise FileExistsError(destination)
        destination.write_text(json.dumps(result,indent=2)+'\n')
    print('V85_CONTEXT_DATA_PASS frames=457 tiles=3701700 exact_v84_tile_parity=1')


if __name__=='__main__':main()
