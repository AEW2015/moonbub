#!/usr/bin/env python3
"""Diagnostic exact HUD pipeline profile on six additional-scene frames."""
from pathlib import Path
import cProfile,hashlib,importlib.util,json,pstats,sys,time,zlib
import numpy as np
ROOT=Path(__file__).resolve().parent.parent
SOURCE=ROOT/'experiments/python-game-source-v40-study';CONTROL=ROOT/'experiments/python-game-control-qual-v40-study'
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(spec);sys.modules[name]=v;spec.loader.exec_module(v);return v
def load(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def raw(folder,d):
    stored=(folder/d['path']).read_bytes();assert hashlib.sha256(stored).hexdigest()==d['stored_sha256']
    data=zlib.decompress(stored);assert len(data)==d['raw_bytes'] and hashlib.sha256(data).hexdigest()==d['raw_sha256'];return data
def main():
    h=module('helpers',ROOT/'experiments/python-game-integrated-v38-study/helpers.py')
    hud32=module('hud_profile41_frozen32',ROOT/'experiments/python-game-hud-v32-study/model.py')
    baseline=module('baseline',ROOT/'experiments/python-game-hud-runs-v33-study/baseline.py')
    module('decoder',ROOT/'experiments/python-game-hud-runs-v33-study/decoder.py')
    hud33=module('hud_profile41_frozen33',ROOT/'experiments/python-game-hud-runs-v33-study/model.py');p=baseline.p
    source=load(SOURCE/'manifest.json')['cases'][1];control=load(CONTROL/'results.json');case=control['cases'][1]
    pins=dict(control['source_pins_sha256']);pins['experiments/profile_hud_v41.py']=sha(Path(__file__))
    pins['experiments/python-game-control-qual-v40-study/results.json']=sha(CONTROL/'results.json')
    profiles=[];instrumented_wall_ns=0;ref=None;ids=[];hashes=[]
    def generate(canvas,reference,fid,rid):
        selected=p.ui.PatchSelector(rectangles=h.n.RECTS).select(canvas,98304)
        hu25,_=p.encode_hud(selected.patches,reference=reference,epoch=25,frame_id=fid,reference_id=rid,motion=True,width=720,height=480)
        hx32,_=hud32.encode_hud(hu25,reference,expected_reference_id=None if reference is None else rid)
        hx33,_=hud33.encode_hud(hu25,hx32,reference,expected_reference_id=None if reference is None else rid)
        return hu25,hx32,hx33
    for src,old in zip(source['frames'][:6],case['rows'][:6],strict=True):
        fid=src['id'];rid=p.NO_REF if fid==0 else fid-1
        canvas=np.frombuffer(raw(SOURCE,src['canvas_rgb24']),np.uint8).reshape(480,720,3)
        profiler=cProfile.Profile();started=time.perf_counter_ns()
        packets=profiler.runcall(generate,canvas,ref,fid,rid)
        instrumented_wall_ns+=time.perf_counter_ns()-started;profiles.append(profiler)
        for name,packet in zip(('HU25','HX32','HX33_selected'),packets,strict=True):assert packet==raw(CONTROL,old['hud_packets'][name])
        ref,_=hud33.decode_hud(packets[-1],ref,expected_epoch=25,expected_reference_id=None if fid==0 else rid)
        ids.append(fid);hashes.append(hashlib.sha256(packets[-1]).hexdigest())
    # Frozen dependency modules are loaded under several names. pstats keys
    # (filename,line,name) can collide and overwrite distinct code objects.
    # Aggregate raw profiler entries explicitly, retaining every alias's self time.
    aggregate={};raw_entries=0;self_total=0.0
    for profiler in profiles:
        for entry in profiler.getstats():
            code=entry.code;raw_entries+=1;self_total+=entry.inlinetime
            if isinstance(code,str):filename,line,function='~',0,code
            else:filename,line,function=code.co_filename,code.co_firstlineno,code.co_name
            path=Path(filename);where=path.relative_to(ROOT).as_posix() if path.is_absolute() and path.is_relative_to(ROOT) else filename
            key=(where,line,function)
            row=aggregate.setdefault(key,dict(file=where,line=line,function=function,primitive_calls=0,total_calls=0,self_seconds=0.0,cumulative_seconds=0.0,raw_entries=0))
            row['primitive_calls']+=entry.callcount-entry.reccallcount;row['total_calls']+=entry.callcount
            row['self_seconds']+=entry.inlinetime;row['cumulative_seconds']+=entry.totaltime;row['raw_entries']+=1
    rows=list(aggregate.values())
    assert abs(sum(r['self_seconds'] for r in rows)-self_total)<1e-8
    rows.sort(key=lambda r:r['self_seconds'],reverse=True)
    result=dict(schema='gamebub-hud-profile-v41',source_sha256=pins,scene=case['scene'],frames=6,source_ids=ids,selected_HX33_sha256=hashes,
                profiler_total_self_seconds=self_total,instrumented_runcall_wall_seconds=instrumented_wall_ns/1e9,profile_instances=len(profiles),raw_profiler_entries=raw_entries,grouped_function_keys=len(rows),aggregation='sum raw cProfile entries, including distinct frozen-module code aliases; pstats key-overwrite totals not used',top_self_time=rows[:30],top_cumulative_time=sorted(rows,key=lambda r:r['cumulative_seconds'],reverse=True)[:30],
                scope=['SixactualcausalHUDgenerations match all HU25/HX32/HX33packetbytes fromfrozenqualification.',
                       'cProfile diagnostic overhead; this is notpairedunprofiledtime or newencoder optimization.',
                       'Sourcecanvasread/conversion andHUDdecodechecksoutsideprofile; measuredselector+allcodec candidates+framing.',
                       'HUDoptimizationwouldbenefitbothcustomandnativehybrid pipelines, notcustomcodec-onlycompression advantage.'])
    (ROOT/'docs/prototype-v41-hud-profile.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(scene=case['scene'],frames=6,profiler_total_self_seconds=self_total,instrumented_runcall_wall_seconds=instrumented_wall_ns/1e9,profile_instances=len(profiles),raw_profiler_entries=raw_entries,grouped_function_keys=len(rows),aggregation='sum raw cProfile entries, including distinct frozen-module code aliases; pstats key-overwrite totals not used',top_self_time=rows[:10])))
if __name__=='__main__':main()
