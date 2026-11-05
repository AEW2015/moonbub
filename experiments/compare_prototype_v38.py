#!/usr/bin/env python3
"""Freshly decode retained original-input native12frameprefixes for v38."""
from pathlib import Path
import argparse,importlib.util,json,sys
ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('compare38_frozen35',ROOT/'experiments/python-game-aligned-v35-study/helpers.py')
h=importlib.util.module_from_spec(spec);sys.modules[spec.name]=h;spec.loader.exec_module(h)

def build():
    nativepath=h.HERE/'results.json';native=h.load(nativepath)
    binarypath=ROOT/'experiments/python-game-binary-v38-study/results.json'
    spatialpath=ROOT/'experiments/python-game-spatial-v38-study/results.json'
    binary,spatial=h.load(binarypath),h.load(spatialpath)
    inputs=h.load(h.n.V24/'results.json')['inputs'];points=[];decodes=0
    for case in native['native_cases']:
        if case['processed']!='original':continue
        rows=case['rows'][:12];packets=[dict(pts=r['pts'],dts=r['dts'],is_key=r['key'],data=h.raw(r['access_unit'],h.HERE)) for r in rows]
        extra=h.raw(case['extradata'],h.HERE);outputs,work=h.standard.decode(packets,extra,case['encoder'])
        assert [r['pts'] for r in packets]==[r['dts'] for r in packets]==list(range(12))
        assert [r['pts'] for r in packets if r['is_key']]==[0]
        assert not work['frames_only_at_decode_flush'] and all(c['output_pts']==[c['packet_pts']] for c in work['decode_calls'])
        inp=next(c for c in inputs if c['scene']==case['scene']);costs=[];sse=samples=0;huds=[]
        for src,row,pkt in zip(inp['rows'][:12],rows,packets,strict=True):
            original=h.n.original(src);parts=tuple(original[y:y+hh,x:x+w] for x,y,w,hh in h.n.RECTS)
            display=h.n.overlay(outputs[row['id']],parts);quality=h.n.metric(original,display)
            assert quality==row['hybrid'] and h.n.digest(display)==row['hybrid_sha256']
            hud=h.raw(row['hud_packet'],h.HUD);huds.append(hud)
            once=len(extra) if row['id']==0 else 0
            assert row['body_bytes']==len(pkt['data'])+len(hud)+60+once
            costs.append(len(pkt['data'])+len(hud)+80+once)
            sse+=quality['active_squared_error'];samples+=quality['active_channel_samples'];decodes+=1
        custom=next(c for c in binary['cases'] if c['scene']==case['scene']);s=custom['summary']
        points.append(dict(scene=case['scene'],codec=case['encoder'],parameter=case['parameter'],complete_equal80_budget_bytes=sum(costs),
                           maximum_equal80_budget_bytes=max(costs),active_mse=sse/samples,cap_fit=max(costs)<=49152,
                           CS38_complete_bytes=s['complete_bytes'],CS38_active_mse=sum(r['hybrid']['active_squared_error'] for r in custom['rows'])/samples,
                           native_smaller_and_lower_MSE=sum(costs)<s['complete_bytes'] and sse/samples<sum(r['hybrid']['active_squared_error'] for r in custom['rows'])/samples))
        for policy in ('mode0control','spatial'):
            sc=next(c for c in spatial['cases'] if c['scene']==case['scene'] and c['policy']==policy)
            for row,hu,src in zip(sc['rows'],huds,inp['rows'][:12],strict=True):
                assert h.raw(row['hud_packet'],ROOT/'experiments/python-game-spatial-v38-study')==hu
                assert row['source_sha256']==src['common_yuv420_u8_sha256']
            sm=sum(r['hybrid']['active_squared_error'] for r in sc['rows'])/samples
            points[-1][policy]=dict(complete_bytes=sum(r['complete_bytes'] for r in sc['rows']),active_mse=sm,
                                   native_smaller_and_lower_MSE=sum(costs)<sum(r['complete_bytes'] for r in sc['rows']) and sse/samples<sm)
    assert decodes==48 and len(points)==4
    paths={ROOT/p for p in native['source_sha256']};paths|={nativepath,binarypath,spatialpath,Path(__file__).resolve()}
    return dict(schema='gamebub-v38-comparison',source_sha256={p.relative_to(ROOT).as_posix():h.sha(p) for p in sorted(paths)},points=points,
                retained_native_AUs_redecoded=decodes,fresh_native_encodes=0,
                scope=['Fourretainedoriginal-input lowdelaynativeanchors freshlydecodedon matching12frameprefixes. No freshnativeencode.',
                       'SamecommonYUVsource and exactHUD; originalRGB565metrics. Equal80modeledbinding budgetandextradataonce; no nativeCS38/SP38 syntaximplementation.',
                       'Fourpoints only, notmatchedqualityBDrate, perceptual equivalence, optimalnativeencode or equalFPGAresource comparison.'])

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    data=build();path=ROOT/'docs/prototype-v38-comparison.json'
    if args.check:assert h.load(path)==data,'comparison changed'
    else:path.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(retained_native_AUs_redecoded=data['retained_native_AUs_redecoded'],fresh_native_encodes=0,points=data['points'])))

if __name__=='__main__':main()
