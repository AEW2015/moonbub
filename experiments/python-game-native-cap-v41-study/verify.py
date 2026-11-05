"""Independent native-AU replay/source/quality/accounting; never calls encode."""
from pathlib import Path
import hashlib,importlib.util,json,sys,zlib
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
SOURCE=HERE.parent/'python-game-source-v40-study';CONTROL=HERE.parent/'python-game-control-qual-v40-study'
spec=importlib.util.spec_from_file_location('nativecap41_verify_frozen_standard24',HERE.parent/'python-game-standard-v24-study/model.py')
std=importlib.util.module_from_spec(spec);sys.modules[spec.name]=std;spec.loader.exec_module(std)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path):return json.loads(Path(path).read_text())
def raw(folder,desc):
    packed=(folder/desc['path']).read_bytes();assert hashlib.sha256(packed).hexdigest()==desc['stored_sha256']
    dec=zlib.decompressobj();data=dec.decompress(packed,desc['raw_bytes']+1)
    assert dec.eof and not dec.unused_data and not dec.unconsumed_tail and len(data)==desc['raw_bytes']
    assert hashlib.sha256(data).hexdigest()==desc['raw_sha256'];return data
def main():
    data=load(HERE/'results.json');sources=load(SOURCE/'manifest.json');control=load(CONTROL/'results.json');sources['cases']=sources['cases'][-1:];control['cases']=control['cases'][-1:]
    for p,h in data['source_sha256'].items():assert sha(ROOT/p)==h,p
    assert len(data['cases'])==21
    identities={(c['codec'],c['parameter'],c['extra_options'],c['bitrate']) for c in data['cases']};assert len(identities)==21
    frame_count=0;supported=0;cap_failing_points=0
    for src,baseline in zip(sources['cases'],control['cases'],strict=True):
        scene=Path(src['media_file']).stem;assert scene==baseline['scene'];n=len(src['frames'])
        originals=[];patches=[];huds=[]
        for source,row in zip(src['frames'],baseline['rows'],strict=True):
            assert row['accepted']
            canvas=np.frombuffer(raw(SOURCE,source['canvas_rgb24']),np.uint8).reshape(480,720,3)
            original=std.C.corpus.rgb565(canvas);planes=std.C.gm.ft.rgb_to_planes(canvas)
            assert hashlib.sha256(b''.join(p.astype('u1').tobytes() for p in planes)).hexdigest()==source['common_yuv420_u8_sha256']==row['source_yuv_sha256']
            originals.append(original);patches.append(tuple(original[y:y+h,x:x+w] for x,y,w,h in std.RECTANGLES))
            huds.append(raw(CONTROL,row['hud_packets']['HX33_selected']))
        for case in data['cases']:
            if not case['supported']:assert case['error'];continue
            assert [r['id'] for r in case['rows']]==list(range(n));supported+=1
            packets=[dict(pts=r['pts'],dts=r['dts'],is_key=r['key'],data=raw(HERE,r['access_unit'])) for r in case['rows']]
            extra=raw(HERE,case['extradata']);outputs,work=std.decode(packets,extra,case['codec'])
            assert [p['pts'] for p in packets]==[p['dts'] for p in packets]==list(range(n))
            assert [p['pts'] for p in packets if p['is_key']]==list(range(0,n,24))
            assert not work['frames_only_at_decode_flush'] and all(c['output_pts']==[c['packet_pts']] for c in work['decode_calls'])
            sse=samples=total=failures=0;max_bytes=peak=0
            for source,row,packet,original,parts,hud in zip(src['frames'],case['rows'],packets,originals,patches,huds,strict=True):
                display=std.overlay(outputs[row['id']],parts);quality=std.metric(original,display)
                assert quality==row['metric'] and std.digest(display)==row['display_sha256']
                assert row['source_sha256']==source['common_yuv420_u8_sha256']
                assert row['source_pts']==source['pts'] and row['source_time_base']==source['time_base']
                once=len(extra) if row['id']==0 else 0
                size=len(packet['data'])+len(hud)+80+once
                assert row['access_unit_bytes']==len(packet['data']) and row['extradata_bytes_charged']==once
                assert row['binding_bytes']==80 and row['hud_bytes']==len(hud) and row['complete_bytes']==size and row['cap_fit']==(size<=49152)
                assert quality['hud_word_errors']==0
                total+=size;failures+=size>49152;max_bytes=max(max_bytes,size);peak=max(peak,quality['active_mse'])
                sse+=quality['active_squared_error'];samples+=quality['active_channel_samples'];frame_count+=1
            sm=case['summary'];assert(sm['frames'],sm['complete_bytes'],sm['maximum_complete_bytes'],sm['cap_failures'])==(n,total,max_bytes,failures)
            assert sm['active_mse']==sse/samples and sm['peak_frame_mse']==peak
            assert not case['encode']['unconsumed_options'] and not case['encode']['packets_only_at_flush']
            assert all(call['emitted_pts']==[call['id']] for call in case['encode']['frame_calls'])
            if case['codec']=='libx265':
                assert case['parameter'] in (22,24,26) and case['extra_options'] in {f'vbv-maxrate=4000:vbv-bufsize={b}:vbv-init=1' for b in (160,200,240)} and case['bitrate'] is None
            elif case['bitrate'] is None:
                assert case['parameter'] in (34,37) and case['extra_options'] in {f'mbr={r}:mbr-overshoot-pct=0' for r in (3000,4000,5000)}
            else:
                assert case['parameter']==34 and case['bitrate'] in (3000000,4000000,5000000)
                assert case['extra_options'] in {f'rc=2:tbr={case["bitrate"]//1000}:buf-sz={b}:buf-initial-sz={b}:buf-optimal-sz={b}:overshoot-pct=0' for b in (40,60)}
            cap_failing_points+=failures>0
    assert supported==21 and frame_count==2100
    print(json.dumps(dict(peak_rate_native_points=supported,redecoded_native_AUs=frame_count,cap_failing_points=cap_failing_points,
                          exact_source_and_HUD=True,encoding_called=False,physical_30fps_proven=False)))
if __name__=='__main__':main()
