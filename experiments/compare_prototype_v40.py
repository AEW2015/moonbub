#!/usr/bin/env python3
"""Compare sampled fresh native points under explicit custom quality/cap gates."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
def load(name):return json.loads((ROOT/name).read_text())
def sha(name):return hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
def build():
    files=dict(control='experiments/python-game-control-qual-v40-study/results.json',binary='experiments/python-game-binary-qual-v40-study/results.json',
               native='experiments/python-game-native-qual-v40-study/results.json',source='experiments/python-game-source-v40-study/manifest.json')
    data={k:load(v) for k,v in files.items()};cases=[]
    for case in data['binary']['cases']:
        scene=case['scene'];base=next(c for c in data['control']['cases'] if c['scene']==scene)
        s=case['summary'];quality=s['active_mse'];peak=max(r['quality']['active_mse'] for r in case['rows'])
        assert all(r['quality']==b['quality'] for r,b in zip(case['rows'],base['rows'],strict=True))
        hud=sum(r['hud_bytes'] for r in case['rows']);binding=80*len(case['rows']);points=[];best={}
        for codec in ('libx265','libsvtav1'):
            options=[]
            for p in data['native']['cases']:
                if p['scene']!=scene or p['codec']!=codec:continue
                if not p['supported']:points.append(dict(codec=codec,parameter=p['parameter'],supported=False,error=p['error']));continue
                v=p['summary'];all_frames=all(r['metric']['active_squared_error']<=b['quality']['active_squared_error'] for r,b in zip(p['rows'],base['rows'],strict=True))
                option=dict(codec=codec,parameter=p['parameter'],supported=True,complete_bytes=v['complete_bytes'],active_mse=v['active_mse'],
                            peak_frame_mse=v['peak_frame_mse'],cap_failures=v['cap_failures'],mean_quality_meets_custom=v['active_mse']<=quality,
                            peak_quality_meets_custom=v['peak_frame_mse']<=peak,all_frame_qualities_meet_custom=all_frames,
                            native_smaller=v['complete_bytes']<s['complete_bytes'])
                points.append(option);options.append(option)
            best[codec]={}
            for label,predicate in [('mean_only',lambda p:p['mean_quality_meets_custom']),
                                    ('mean_and_peak',lambda p:p['mean_quality_meets_custom']and p['peak_quality_meets_custom']),
                                    ('every_frame',lambda p:p['all_frame_qualities_meet_custom'])]:
                eligible=[p for p in options if p['cap_failures']==0 and predicate(p)]
                winner=min(eligible,key=lambda p:p['complete_bytes']) if eligible else None
                best[codec][label]=winner
        cases.append(dict(scene=scene,frames=s['frames'],CS37_complete_bytes=s['source_complete_bytes'],CS38_complete_bytes=s['complete_bytes'],
                          CS38_saving_percent=s['percent_saved'],CS38_active_mse=quality,CS38_peak_frame_mse=peak,
                          CS38_maximum_complete_bytes=s['maximum_complete_bytes'],CS38_minimum_cap_headroom=s['minimum_cap_headroom'],
                          actual_HUD_bytes=hud,binding_bytes=binding,CS38_remaining_codec_bytes=s['complete_bytes']-hud-binding,
                          sampled_native_points=points,best_sampled_feasible_points=best))
    paths=list(files.values())+['experiments/compare_prototype_v40.py']
    return dict(schema='gamebub-v40-comparison',source_sha256={p:sha(p) for p in paths},cases=cases,
                fresh_native_quality_points=48,fresh_native_AUs=5484,custom_source_frames=457,
                scope=['Freshnativepoints on exactsame457commonYUV inputs and actualHX33, originalRGB565metrics; same80modeledbinding/extradataonce.',
                       'BestamongSIXsampledparameters/codec underexplicitmean,mean+peak,orevery-frameMSE gates ANDzerocompletecapfailures.',
                       'NoMSE/rateinterpolation, noBDrate oroptimalnativeparameterclaim. Unequalqualityfeasibleconstraintcomparison, notexactmatchedMSE.',
                       'Means/peaksarenotperceptualquality. Precompressedrelatedgamewindows, sourcePTS/gapsmetadataretained; notnative30distinctcapture orFPGAresourcecomparison.'])
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args();data=build();target=ROOT/'docs/prototype-v40-comparison.json'
    if args.check:assert load('docs/prototype-v40-comparison.json')==data
    else:target.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(cases=[{k:v for k,v in c.items() if k!='sampled_native_points'} for c in data['cases']])))
if __name__=='__main__':main()
