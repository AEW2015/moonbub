"""New window/anchor adapter; unchanged57/60 implementations and source files."""
from pathlib import Path
import numpy as np
import helpers as h

def originals(scene):
    case=next(c for c in h.load(h.SOURCE/'manifest.json')['cases']if Path(c['media_file']).stem==scene);words=[];rgb=[];ids=[]
    for f in case['frames'][24:48]:
        canvas=np.frombuffer(h.raw(f['canvas_rgb24'],h.SOURCE),np.uint8).reshape(480,720,3)
        w=h.h.m.C.corpus.rgb565(canvas);assert h.digest(w.astype('<u2').tobytes())==f['rgb565_sha256']
        w.setflags(write=False);words.append(w);rgb.append(h.h.m.C.corpus.expand565(w));ids.append(f['id'])
    assert ids==list(range(24,48));return words,rgb

def anchor(points,target_sse,target_samples):
    rows=[]
    for point in points:
        case=point['case'];summary=case.get('summary',{});supported=case.get('supported',True)
        eligible=(supported and summary.get('cap_failures')==0 and summary.get('active_channel_samples')==target_samples and summary.get('active_squared_error',target_sse+1)<=target_sse)
        rows.append(dict(source=point['source'],source_case=point['source_case'],codec=case['codec'],parameter=case['parameter'],
            extra_options=case.get('extra_options'),bitrate=case.get('bitrate'),supported=supported,eligible=bool(eligible),summary=summary))
    eligible=[i for i,p in enumerate(rows)if p['eligible']]
    chosen=min(eligible,key=lambda i:(rows[i]['summary']['complete_bytes'],rows[i]['summary']['active_squared_error'],rows[i]['parameter'],i))if eligible else None
    return chosen,rows

def cases(require_all_sources=True):
    custom=h.load(h.CUSTOM/'results.json');native=[];missing=[]
    for folder in h.NATIVE_SOURCES:
        if not(folder/'results.json').exists():
            missing.append(folder.name);continue
        native_data=h.load(folder/'results.json')
        for i,c in enumerate(native_data['cases']):
            scene=c.get('scene',native_data.get('source_scene'));assert scene is not None
            view=dict(c,scene=scene);summary=dict(c.get('summary',{}))
            if c.get('supported',True):
                rows=c['rows'];actual_bytes=sum(r['complete_bytes']for r in rows);cap=sum(r['complete_bytes']>49152 for r in rows)
                assert summary['complete_bytes']==actual_bytes and summary['cap_failures']==cap and len(rows)==24
                summary.update(active_squared_error=sum(r['metric']['active_squared_error']for r in rows),active_channel_samples=sum(r['metric']['active_channel_samples']for r in rows))
            view['summary']=summary
            native.append(dict(source=(folder/'results.json').relative_to(h.ROOT).as_posix(),source_case=i,case=view))
    if require_all_sources and missing:raise ValueError('Await declared native inputs: '+','.join(missing))
    result=[];anchors=[]
    for ci,c in enumerate(custom['cases']):
        assert [r['id']for r in c['rows']]==list(range(24,48));scene=c['scene']
        for policy in('zero','adaptive'):
            entries=[r['zero_qualification']if policy=='zero'else r for r in c['rows']]
            result.append(dict(kind='custom',scene=scene,policy=policy,codec=None,source=(h.CUSTOM/'results.json').relative_to(h.ROOT).as_posix(),source_case=ci,
                complete_bytes=sum(r['complete_bytes']for r in entries),cap_failures=sum(r['complete_bytes']>49152 for r in entries)))
        target_sse=sum(r['zero_qualification']['quality']['active_squared_error']for r in c['rows']);samples=sum(r['zero_qualification']['quality']['active_channel_samples']for r in c['rows'])
        for codec in('libx265','libsvtav1'):
            points=[p for p in native if p['case']['scene']==scene and p['case']['codec']==codec];index,table=anchor(points,target_sse,samples)
            choice=dict(scene=scene,codec=codec,target_zero_active_SSE=target_sse,target_samples=samples,points=table,selected=index,
                criterion='supported+cap0+mean originalRGB565SSE<=zero; min(actualcompletebytes,SSE,parameter,inputorder)',anchor_selection_exploratory=True)
            anchors.append(choice)
            if index is None:continue
            point=points[index];data=point['case'];result.append(dict(kind='native',scene=scene,policy=codec,codec=codec,parameter=data['parameter'],extra_options=data.get('extra_options'),bitrate=data.get('bitrate'),
                source=point['source'],source_case=point['source_case'],complete_bytes=data['summary']['complete_bytes'],cap_failures=data['summary']['cap_failures'],anchor_selection=len(anchors)-1))
    return result,anchors,missing

def presentations(case,words):
    folder=(h.ROOT/case['source']).parent;source=h.load(h.ROOT/case['source'])['cases'][case['source_case']]
    if case['kind']=='custom':
        rx=h.io.direct.Receiver()
        for i,row in enumerate(source['rows']):
            fid=row['id'];entry=row['zero_qualification']if case['policy']=='zero'else row
            packet=h.raw(entry['packet'],folder);out,patches,meta,count=rx.receive(packet)
            planes=tuple(p.astype(np.uint8)for p in out)
            for p in planes:p.setflags(write=False)
            display=h.h.f.f.n.overlay(h.h.m.C.corpus.rgb565(h.h.m.ft.planes_to_rgb(planes)),tuple(p['words']for p in patches))
            assert h.h.f.f.n.digest(display)==entry['display_sha256'];assert h.h.m.C.reference_tag(out).hex()==entry['normalized_tag']
            tag=h.canonical_digest(out)
            yield dict(id=fid,native_pts=None,planes=planes,canonical=out,patches=patches,baseline=display,complete_bytes=len(packet),
                expected_quality=entry['quality'],expected_display_sha256=entry['display_sha256'],source_packet=entry['packet'],canonical_sha256=tag)
            assert h.canonical_digest(rx.ref)==tag
    else:
        std=h.io.std;codec=std.av.CodecContext.create('hevc'if case['codec']=='libx265'else'libdav1d','r');codec.thread_count=1
        extra=h.raw(source['extradata'],folder)
        if extra:codec.extradata=extra
        assert len(source['rows'])==24
        for i,row in enumerate(source['rows']):
            assert row['pts']==row['id']==i and row['source_id']==i+24
            packet=std.av.Packet(h.raw(row['access_unit'],folder));packet.pts,packet.dts,packet.time_base=row['pts'],row['dts'],std.TB
            frames=codec.decode(packet);assert len(frames)==1 and frames[0].pts==i
            planes=std.planes_from_frame(frames[0])
            for p in planes:p.setflags(write=False)
            patches=[]
            for rect in h.h.f.f.n.RECTS:
                x,y,w,hh=rect;view=words[i][y:y+hh,x:x+w].view();view.setflags(write=False);patches.append(dict(rect=rect,words=view))
            display=h.h.f.f.n.overlay(h.h.m.C.corpus.rgb565(h.h.m.ft.planes_to_rgb(planes)),tuple(p['words']for p in patches))
            assert h.h.f.f.n.digest(display)==row['display_sha256']
            yield dict(id=row['source_id'],native_pts=i,planes=planes,canonical=None,patches=tuple(patches),baseline=display,complete_bytes=row['complete_bytes'],
                expected_quality=row['metric'],expected_display_sha256=row['display_sha256'],source_packet=row['access_unit'],canonical_sha256=None)
        assert not codec.decode(None)
