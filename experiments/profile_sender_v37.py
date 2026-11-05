#!/usr/bin/env python3
"""Six causal complex-scene direct sends under cProfile; diagnostic only."""
import cProfile,importlib.util,json,platform,pstats,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
FOLDER=ROOT/'experiments/python-game-direct-v37-study'
sys.path.insert(0,str(FOLDER))
spec=importlib.util.spec_from_file_location('profile37_sender_benchmark',FOLDER/'benchmark.py')
b=importlib.util.module_from_spec(spec);sys.modules[spec.name]=b;spec.loader.exec_module(b)
h=b.h

def main():
    pins=h.pins();pins['experiments/profile_sender_v37.py']=h.sha(Path(__file__))
    source=h.load(h.n.V24/'results.json')['inputs'][1]
    archived=h.load(FOLDER/'results.json')['cases'][1]
    hudcase=next(c for c in h.load(h.HUD/'results.json')['cases'] if c['scene']==source['scene'])
    profile=cProfile.Profile();rx=h.canonical.Receiver();ref=None;rid=h.m.NO_REF;tags=[]
    for src,prior,hu in zip(source['rows'][:6],archived['rows'][:6],hudcase['rows'][:6],strict=True):
        planes=h.n.source(src);hud=h.raw(hu['packet'],h.HUD)
        q=h.m.roi.declared_map(720,480,h.n.ROIS,8,16)
        wire,_,_=profile.runcall(b.sender,'direct',planes,ref,src['id'],rid,q,hud,False)
        expected=h.raw(prior['packet'],FOLDER);assert wire==expected
        (ref,_)=rx.receive(wire);rid=src['id'];tags.append(h.digest(wire))
    stats=pstats.Stats(profile);rows=[]
    for (filename,line,function),(primitive,total,selftime,cumulative,callers) in stats.stats.items():
        path=Path(filename)
        location=path.relative_to(ROOT).as_posix() if path.is_absolute() and path.is_relative_to(ROOT) else filename
        rows.append(dict(file=location,line=line,function=function,primitive_calls=primitive,total_calls=total,
                         self_seconds=selftime,cumulative_seconds=cumulative))
    rows.sort(key=lambda r:r['self_seconds'],reverse=True)
    result=dict(schema='gamebub-v37-sender-profile',source_sha256=pins,scene=source['scene'],frames=6,wire_sha256=tags,
                python=platform.python_version(),total_instrumented_seconds=stats.total_tt,
                top_self_time=rows[:30],top_cumulative_time=sorted(rows,key=lambda r:r['cumulative_seconds'],reverse=True)[:30],
                scope=['cProfile instrumentation changes runtime; this is diagnostic hotspot evidence, not the paired uninstrumented sender timing.',
                       'Profiles six actual causal direct sends: analysis through wrappedoutput. Every resulting byte equals retained directv37 archive.',
                       'Source/HUD fixture preparation, verification, receiver and network/display excluded. One complex clip prefix only.'])
    (ROOT/'docs/prototype-v37-sender-profile.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(scene=source['scene'],frames=6,instrumented_seconds=stats.total_tt,top_self_time=rows[:10])))

if __name__=='__main__':main()
