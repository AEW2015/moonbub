"""Fresh fixed-grid native encodes on96 additional temporal-window frames24–47."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,sys,time,zlib
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
SOURCE=HERE.parent/'python-game-source-v40-study';CONTROL=HERE.parent/'python-game-control-qual-v40-study'
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(spec);sys.modules[name]=v;spec.loader.exec_module(v);return v
std=module('native_temporal61_frozen_standard24',HERE.parent/'python-game-standard-v24-study/model.py')
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(data):return hashlib.sha256(data).hexdigest()
def load(path):return json.loads(Path(path).read_text())
def raw(folder,desc):
    stored=(folder/desc['path']).read_bytes();assert digest(stored)==desc['stored_sha256']
    dec=zlib.decompressobj();data=dec.decompress(stored,desc['raw_bytes']+1)
    assert dec.eof and not dec.unused_data and not dec.unconsumed_tail and len(data)==desc['raw_bytes'] and digest(data)==desc['raw_sha256'];return data
def blob(data):
    packed=zlib.compress(data,9);name='objects/'+digest(packed)+'.zlib';(HERE/'objects').mkdir(exist_ok=True);(HERE/name).write_bytes(packed)
    return dict(path=name,raw_bytes=len(data),raw_sha256=digest(data),stored_sha256=digest(packed))
def pins():
    data=load(CONTROL/'results.json');paths={ROOT/p for p in data['source_pins_sha256']}
    paths|={CONTROL/'results.json',SOURCE/'manifest.json',HERE/'benchmark.py',HERE.parent/'python-game-standard-v24-study/model.py'}
    return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}
def inputs(source,control):
    planes=[];words=[];parts=[];hud=[];tags=[]
    assert len(source['frames'])==len(control['rows'])
    for src,row in zip(source['frames'],control['rows'],strict=True):
        assert row['accepted'] and row['id']==src['id']
        canvas=np.frombuffer(raw(SOURCE,src['canvas_rgb24']),np.uint8).reshape(480,720,3)
        planar=tuple(std.C.gm.ft.rgb_to_planes(canvas));original=std.C.corpus.rgb565(canvas)
        tag=digest(b''.join(a.astype('u1').tobytes() for a in planar));assert tag==src['common_yuv420_u8_sha256']==row['source_yuv_sha256']
        assert digest(original.astype('<u2').tobytes())==src['rgb565_sha256']==row['source_rgb565_sha256']
        planes.append(planar);words.append(original);tags.append(tag)
        parts.append(tuple(original[y:y+h,x:x+w] for x,y,w,h in std.RECTANGLES))
        hud.append(raw(CONTROL,row['hud_packets']['HX33_selected']))
    return planes,words,parts,hud,tags
def run(scene,source,control,name,q,prepared):
    planes,words,parts,hud,tags=prepared;n=len(planes)
    start=time.perf_counter_ns();packets,extra,enc=std.encode(planes,name,q);outputs,dec=std.decode(packets,extra,name)
    wall=(time.perf_counter_ns()-start)/1e6
    assert [p['pts'] for p in packets]==[p['dts'] for p in packets]==list(range(n))
    assert [p['pts'] for p in packets if p['is_key']]==list(range(0,n,24))
    assert not enc['packets_only_at_flush'] and not dec['frames_only_at_decode_flush']
    assert all(c['emitted_pts']==[c['id']] for c in enc['frame_calls']) and all(c['output_pts']==[c['packet_pts']] for c in dec['decode_calls'])
    rows=[]
    for packet,original,patches,hu,tag,src in zip(packets,words,parts,hud,tags,source['frames'],strict=True):
        fid=packet['pts'];display=std.overlay(outputs[fid],patches);metric=std.metric(original,display);once=len(extra) if fid==0 else 0
        complete=len(packet['data'])+len(hu)+80+once
        rows.append(dict(id=fid,pts=fid,dts=packet['dts'],key=packet['is_key'],source_id=src['id'],source_pts=src['pts'],source_time_base=src['time_base'],
                         source_sha256=tag,access_unit=blob(packet['data']),access_unit_bytes=len(packet['data']),
                         extradata_bytes_charged=once,hud_bytes=len(hu),binding_bytes=80,complete_bytes=complete,cap_fit=complete<=49152,
                         metric=metric,display_sha256=std.digest(display)))
    sse=sum(r['metric']['active_squared_error'] for r in rows);samples=sum(r['metric']['active_channel_samples'] for r in rows)
    summary=dict(frames=n,complete_bytes=sum(r['complete_bytes'] for r in rows),maximum_complete_bytes=max(r['complete_bytes'] for r in rows),
                 cap_failures=sum(not r['cap_fit'] for r in rows),active_mse=sse/samples,active_squared_error=sse,active_channel_samples=samples,
                 peak_frame_mse=max(r['metric']['active_mse'] for r in rows),all_HUD_errors=sum(r['metric']['hud_word_errors'] for r in rows),
                 nominal_Mbps_at30=sum(r['complete_bytes'] for r in rows)*240/n/1e6,wall_encode_decode_ms=wall)
    return dict(scene=scene,codec=name,parameter=q,rows=rows,summary=summary,extradata=blob(extra),encode=enc,decode=dec)
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--resume',action='store_true');args=parser.parse_args()
    before=pins();source=load(SOURCE/'manifest.json');control=load(CONTROL/'results.json');target=HERE/'results.json'
    for c in source['cases']:c['frames']=c['frames'][24:48];assert [r['id'] for r in c['frames']]==list(range(24,48))
    for c in control['cases']:c['rows']=c['rows'][24:48];assert [r['id'] for r in c['rows']]==list(range(24,48))
    cases=load(target)['cases'] if args.resume and target.exists() else []
    done={(c['scene'],c['codec'],c['parameter']) for c in cases}
    for src,ctrl in zip(source['cases'],control['cases'],strict=True):
        scene=Path(src['media_file']).stem;assert ctrl['scene']==scene
        prepared=inputs(src,ctrl)
        for name,grid in (('libx265',(20,24,28,32,36,40)),('libsvtav1',(28,34,40,46,52,58))):
            for q in grid:
                if(scene,name,q)in done:continue
                try:item=run(scene,src,ctrl,name,q,prepared);item['supported']=True
                except Exception as exc:item=dict(scene=scene,codec=name,parameter=q,supported=False,error=repr(exc))
                cases.append(item);assert pins()==before
                result=dict(schema='gamebub-native-temporal-v61',source_sha256=before,cases=cases,physical_30fps_proven=False,new_RTL_implemented=False,
                            scope=['Fresh48pointnativegridon96sourceIDs24–47fromfourknownv40clips;notgloballyunseencaptures.',
                                   'Frozenstd24samepredeclaredsinglethreadlowdelaysettingsand6qualities/codec;no53/59parameterretuning.',
                                   'NativePTSreset0–23,key0,immediateoutput;actualsourceIDs24–47/PTS/HUDglobalIDsretainedandframe0extradatacharged.',
                                   'SamecommonYUV/originalRGB565/actualHX33+80Bbindingbudget;allcap/qualitymissesretained.',
                                   'Actual1152newAUs,nothardwareFPGAdecoder/physical30fpsoroptimalnativefrontierproof.'])
                target.write_text(json.dumps(result,indent=2)+'\n')
                print(json.dumps({k:v for k,v in item.items() if k not in('rows','extradata','encode','decode')}),flush=True)
    print(json.dumps(dict(completed_points=len(cases),fresh_native_frames=sum(c.get('summary',{}).get('frames',0) for c in cases))),flush=True)
if __name__=='__main__':main()
