#!/usr/bin/env python3
"""V39 accounting against previously verified original-input native anchors."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
def load(name):return json.loads((ROOT/name).read_text())
def sha(name):return hashlib.sha256((ROOT/name).read_bytes()).hexdigest()

def build():
    names=dict(full='experiments/python-game-binary-full-v39-study/results.json',rank='experiments/python-game-mode-rank-v39-study/results.json',
               signal='experiments/python-game-signal-v39-study/results.json',native_full='experiments/python-game-comparison-v36-study/results.json',
               native_prefix='docs/prototype-v38-comparison.json',canonical='experiments/python-game-canonical-v36-study/results.json')
    data={k:load(v) for k,v in names.items()};full=[];prefix=[]
    for case in data['full']['cases']:
        old=next(c for c in data['canonical']['cases'] if c['scene']==case['scene'])['summary']['skip']
        fixed=old['hud_bytes']+old['binding_bytes'];custom=case['summary'];points=[]
        for p in data['native_full']['points']:
            if p['scene']!=case['scene']:continue
            remainder=p['equal80_binding_budget_bytes']-fixed
            points.append(dict(codec=p['codec'],parameter=p['parameter'],complete_bytes=p['equal80_binding_budget_bytes'],active_mse=p['active_mse'],
                               remaining_codec_bytes=remainder,custom_to_native_codec_byte_ratio=(custom['complete_bytes']-fixed)/remainder,
                               native_smaller_and_lower_MSE=p['equal80_binding_budget_bytes']<custom['complete_bytes'] and p['active_mse']<custom['active_mse']))
        full.append(dict(scene=case['scene'],frames=48,CS38_complete_bytes=custom['complete_bytes'],CS38_active_mse=custom['active_mse'],
                         HUD_plus_binding_bytes=fixed,CS38_remaining_codec_bytes=custom['complete_bytes']-fixed,native=points))
    for p in data['native_prefix']['points']:
        points=[]
        for c in data['signal']['cases']:
            if c['kind']!='main'or c['scene']!=p['scene']:continue
            s=c['summary'];points.append(dict(policy=c['policy'],complete_bytes=s['complete_bytes'],active_mse=s['active_mse'],
                         native_smaller_and_lower_MSE=p['complete_equal80_budget_bytes']<s['complete_bytes'] and p['active_mse']<s['active_mse']))
        prefix.append(dict(scene=p['scene'],codec=p['codec'],parameter=p['parameter'],frames=12,native_complete_bytes=p['complete_equal80_budget_bytes'],
                           native_active_mse=p['active_mse'],signal_points=points))
    paths=list(names.values())+['experiments/compare_prototype_v39.py']
    return dict(schema='gamebub-v39-comparison',source_sha256={p:sha(p) for p in paths},full48_points=full,prefix12_points=prefix,
                fresh_native_encodes=0,fresh_native_decodes=0,
                scope=['Frozenverifiedoriginal-inputnativefull48andprefix12anchors reused, no newnativeencode/decode in v39.',
                       'SameoriginalcommonYUV andexactHUD,metricsagainstoriginalRGB565. Equal80bindingbudget+actualHUD+nativeextradataonce.',
                       'Complete custom bytes actualserializedpackets; nativebinding is modeledaccounting, notnewwire/nativeprotocolsupport.',
                       'Full48/12prefix comparisons distinct. No matchedqualityBDrate, optimalstandardsencode or equalFPGAresources inference.'])
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args();result=build();path=ROOT/'docs/prototype-v39-comparison.json'
    if args.check:assert load('docs/prototype-v39-comparison.json')==result
    else:path.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(full48_points=result['full48_points'],prefix_native_points=len(result['prefix12_points']),fresh_native_encodes=0,fresh_native_decodes=0)))
if __name__=='__main__':main()
