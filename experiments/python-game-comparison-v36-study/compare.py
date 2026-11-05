#!/usr/bin/env python3
"""Replay retained ORIGINAL-input standards; normalize sideband byte budgets.

No fresh encode, no BD-rate claim and no native CN36 implementation implied.
"""
from pathlib import Path
import argparse,importlib.util,json,sys,hashlib

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('comparison36_frozen35',HERE.parent/'python-game-aligned-v35-study/helpers.py')
h=importlib.util.module_from_spec(spec);sys.modules[spec.name]=h;spec.loader.exec_module(h)

def build():
    native_path=h.HERE/'results.json'
    custom_path=HERE.parent/'python-game-canonical-v36-study/results.json'
    data=h.load(native_path);custom=h.load(custom_path)
    assert custom['profile']['wrapper_bytes']==80
    inputs=h.load(h.n.V24/'results.json')['inputs'];points=[];decoded_frames=0
    for case in data['native_cases']:
        if case['processed']!='original':continue
        assert case['supported']
        packets=[dict(pts=r['pts'],dts=r['dts'],is_key=r['key'],data=h.raw(r['access_unit'],h.HERE)) for r in case['rows']]
        extra=h.raw(case['extradata'],h.HERE)
        output,work=h.standard.decode(packets,extra,case['encoder'])
        assert [p['pts'] for p in packets]==[p['dts'] for p in packets]==list(range(48))
        assert [p['pts'] for p in packets if p['is_key']]==[0,24]
        assert not work['frames_only_at_decode_flush'] and all(c['output_pts']==[c['packet_pts']] for c in work['decode_calls'])
        inp=next(c for c in inputs if c['scene']==case['scene'])
        costs=[];sse=samples=0
        for src,row,packet in zip(inp['rows'],case['rows'],packets,strict=True):
            original=h.n.original(src)
            patches=tuple(original[y:y+hh,x:x+w] for x,y,w,hh in h.n.RECTS)
            display=h.n.overlay(output[row['id']],patches);quality=h.n.metric(original,display)
            assert quality==row['hybrid'] and h.n.digest(display)==row['hybrid_sha256']
            hud=h.raw(row['hud_packet'],h.HUD)
            assert row['access_unit_bytes']==len(packet['data'])
            once=len(extra) if row['id']==0 else 0
            assert row['extradata_bytes_charged']==once
            assert row['body_bytes']==len(packet['data'])+len(hud)+once+60
            costs.append(len(packet['data'])+len(hud)+once+80)
            sse+=quality['active_squared_error'];samples+=quality['active_channel_samples'];decoded_frames+=1
        total=sum(costs);assert total==case['summary']['complete_bytes']+20*48
        target=next(c for c in custom['cases'] if c['scene']==case['scene'])['summary']['skip']
        points.append(dict(scene=case['scene'],codec=case['encoder'],parameter=case['parameter'],
                           original_retained_complete_bytes=case['summary']['complete_bytes'],
                           equal80_binding_budget_bytes=total,maximum_equal80_budget_bytes=max(costs),
                           cap_fit=max(costs)<=49152,active_mse=sse/samples,
                           nominal_Mbps_at30=total*240/48/1e6,
                           custom_skip_complete_bytes=target['complete_bytes'],custom_skip_active_mse=target['active_mse'],
                           native_smaller_and_lower_MSE=total<target['complete_bytes'] and sse/samples<target['active_mse']))
    assert len(points)==4 and decoded_frames==192
    paths={ROOT/p for p in data['source_sha256']}
    paths|={native_path,custom_path,HERE/'compare.py'}
    return dict(schema='gamebub-comparison-v36',source_sha256={p.relative_to(ROOT).as_posix():h.sha(p) for p in sorted(paths)},
                points=points,retained_native_AUs_redecoded=decoded_frames,fresh_native_encodes=0,
                scope=['Same original commonYUV source inputs and exactHUD, metric measured against original RGB565 source.',
                       'Native packets are reused v35 original-input anchors, freshly decoded and hash/metric/PTS/key verified here.',
                       'Both budgets charge80 binding bytes perframe plus actual exactHX33 and native extradata once. Native80 is modeled accounting, not CN36 syntax.',
                       'CN36 normalization changes its inloop reference, not its original input; no source-mask benefit is withheld from native codecs.',
                       'Four sampled points, not matchedquality BDrate or an optimalencoder/resource comparison; hardware30fps remains unproved.'])

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    result=build();path=HERE/'results.json'
    if args.check:assert json.loads(path.read_text())==result,'comparison evidence changed'
    else:path.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(retained_native_AUs_redecoded=result['retained_native_AUs_redecoded'],fresh_native_encodes=0,
                          points=result['points'])))

if __name__=='__main__':main()
