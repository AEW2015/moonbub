"""Diagnostic whole HUD chain after v42; profiling is not uninstrumented speed."""
from pathlib import Path
import cProfile,json,pstats
import numpy as np
import helpers as h
model=h.module('hudfast42_profile_model',h.HERE/'model.py')
SOURCE=h.HERE.parent/'python-game-source-v40-study'

def main():
    qualification=h.load(h.QUAL/'results.json');source=h.load(SOURCE/'manifest.json');profiler=cProfile.Profile();frames=[];paths={h.ROOT/p for p in h.pins()}
    paths.add(Path(__file__).resolve())
    for case in qualification['cases']:
        inputs=next(c for c in source['cases']if c['name']==case['scene']);reference=None
        for src,old in zip(inputs['frames'][:6],case['rows'][:6],strict=True):
            canvas=np.frombuffer(h.raw(src['canvas_rgb24'],SOURCE),np.uint8).reshape(480,720,3)
            paths.add(SOURCE/src['canvas_rgb24']['path']);baseline=h.raw(old['hud_packets']['HU25'],h.QUAL)
            rectangles=h.p._parse_hud(baseline)['rectangles'];fid=old['id'];rid=old['reference_id']
            expected_ref=None if rid==h.p.NO_REF else rid
            def generate():
                selected=h.p.ui.PatchSelector(rectangles=rectangles).select(canvas,98304)
                hu25,_=h.p.encode_hud(selected.patches,reference=reference,epoch=25,frame_id=fid,reference_id=rid,motion=True,width=720,height=480)
                hx32,_=model.encode_hud32(hu25,reference,expected_reference_id=expected_ref)
                hx33,_=model.encode_hud33(hu25,hx32,reference,expected_reference_id=expected_ref)
                return hu25,hx32,hx33
            packets=profiler.runcall(generate)
            for name,packet in zip(('HU25','HX32','HX33_selected'),packets,strict=True):assert packet==h.raw(old['hud_packets'][name],h.QUAL)
            reference,_=h.hud33.decode_hud(packets[-1],reference,expected_epoch=25,expected_reference_id=expected_ref)
            frames.append(dict(scene=case['scene'],id=fid,selected_HX33_sha256=h.digest(packets[-1])))
    stats=pstats.Stats(profiler);rows=[]
    for(filename,line,function),(primitive,total,self_seconds,cumulative,callers)in stats.stats.items():
        p=Path(filename);where=p.relative_to(h.ROOT).as_posix()if p.is_absolute()and p.is_relative_to(h.ROOT)else filename
        rows.append(dict(file=where,line=line,function=function,primitive_calls=primitive,total_calls=total,self_seconds=self_seconds,cumulative_seconds=cumulative))
    result=dict(schema='gamebub-hud-fast-whole-chain-profile-v42',source_sha256={p.relative_to(h.ROOT).as_posix():h.sha(p)for p in sorted(paths)},
        frames=frames,total_instrumented_seconds=stats.total_tt,top_self_time=sorted(rows,key=lambda r:r['self_seconds'],reverse=True)[:30],
        top_cumulative_time=sorted(rows,key=lambda r:r['cumulative_seconds'],reverse=True)[:30],
        scope=['Diagnostic24framewholeHUDchain:selector+HU25motiongeneration+fastHX32+fastHX33;allpacketbytesmatchqualifiedarchives.',
               'cProfile instrumentation changes runtime; do not compare directly against paired uninstrumented stage times or old different profiles.',
               'SourceimageI/O/decompression,finalsemanticdecode/assertions,archives,network/displayoutsideprofile. NoFPSorwholegamepipelineclaim.'])
    (h.HERE/'whole-chain-profile.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(frames=len(frames),total_instrumented_seconds=stats.total_tt,top_self_time=result['top_self_time'][:10])))
if __name__=='__main__':main()
