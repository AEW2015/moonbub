#!/usr/bin/env python3
"""Deterministic accounting comparison using verified retained native anchors.

No fresh native encode or decode in this script. Exact CS37 output equality
allows retained original-input v36 metrics to remain the comparison anchors.
"""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent

def load(path):return json.loads((ROOT/path).read_text())
def sha(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()

def build():
    custom='experiments/python-game-implicit-v37-study/results.json'
    original='experiments/python-game-canonical-v36-study/results.json'
    native='experiments/python-game-comparison-v36-study/results.json'
    data,legacy,anchors=load(custom),load(original),load(native)
    main=[c for c in data['cases'] if c['kind']=='main'];assert len(main)==2
    rows=[]
    for case in main:
        name=case['scene'];now=case['summary']
        before=next(c for c in legacy['cases'] if c['scene']==name)['summary']
        assert now['active_mse']==before['skip']['active_mse']
        entry=dict(scene=name,CS37_complete_bytes=now['complete_bytes'],CN36_complete_bytes=before['skip']['complete_bytes'],
                   matched_fixed_legacy_bytes=before['legacy_fixed']['complete_bytes'],active_mse=now['active_mse'],
                   same_HUD_bytes=before['skip']['hud_bytes'],binding_bytes=before['skip']['binding_bytes'],
                   CS37_remaining_codec_bytes=now['complete_bytes']-before['skip']['hud_bytes']-before['skip']['binding_bytes'],
                   CS37_saving_vs_CN36_percent=100*(1-now['complete_bytes']/before['skip']['complete_bytes']),
                   CS37_saving_vs_matched_fixed_legacy_percent=100*(1-now['complete_bytes']/before['legacy_fixed']['complete_bytes']),native=[])
        for p in anchors['points']:
            if p['scene']!=name:continue
            remaining=p['equal80_binding_budget_bytes']-entry['same_HUD_bytes']-entry['binding_bytes']
            entry['native'].append(dict(codec=p['codec'],parameter=p['parameter'],complete_equal80_budget_bytes=p['equal80_binding_budget_bytes'],
                                        remaining_codec_bytes=remaining,custom_to_native_codec_byte_ratio=entry['CS37_remaining_codec_bytes']/remaining,
                                        active_mse=p['active_mse'],native_smaller_and_lower_MSE=p['equal80_binding_budget_bytes']<now['complete_bytes'] and p['active_mse']<now['active_mse']))
        assert len(entry['native'])==2;rows.append(entry)
    paths=[custom,original,native,'experiments/compare_prototype_v37.py']
    return dict(schema='gamebub-v37-comparison',source_sha256={p:sha(p) for p in paths},cases=rows,
                fresh_native_encodes=0,fresh_native_decodes=0,
                scope=['Original-input native v36 anchors previously replayed and frozen; no new native encode/decode this iteration.',
                       'CS37 actual decode is exact to CN36skip. All metrics remain against original RGB565 source with identical exactHUD.',
                       'Equal80 binding budget plus actualHX33 and native extradataonce; native80 is modeled byteaccounting, not newwire.',
                       'Savings versusmatchedfixedlegacy use actualserializedcomplete bytes in bothcustomprofiles; searchedv35control is a differentpolicy.',
                       'Four sampled points, not matchedqualityBDrate, perceptual equivalence or measured equalFPGAresources.'])

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    data=build();path=ROOT/'docs/prototype-v37-comparison.json'
    if args.check:assert load('docs/prototype-v37-comparison.json')==data,'comparison changed'
    else:path.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(cases=data['cases'],fresh_native_encodes=0,fresh_native_decodes=0)))

if __name__=='__main__':main()
