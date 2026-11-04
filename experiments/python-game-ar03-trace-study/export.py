#!/usr/bin/env python3
"""Native AR03 lifecycle vectors and exact selected entropy traces."""
import hashlib,json,os,struct,time,zlib
from fractions import Fraction
from pathlib import Path
import av
import numpy as np
import trace_codec as t
from ui_plugin import PatchSelector
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def blob(data,kind,compress=False):
    raw=bytes(data);h=hashlib.sha256(raw).hexdigest();stored=zlib.compress(raw,9) if compress else raw
    name='objects/'+h+'.'+kind+('.zlib' if compress else '.bin');path=HERE/name;path.parent.mkdir(exist_ok=True)
    if path.exists():assert path.read_bytes()==stored
    else:path.write_bytes(stored)
    return dict(path=name,encoding='zlib' if compress else 'raw',raw_bytes=len(raw),raw_sha256=h,stored_sha256=hashlib.sha256(stored).hexdigest())
def array(a,dtype):
    a=np.asarray(a,dtype=dtype);return dict(shape=list(a.shape),dtype=np.dtype(dtype).str,blob=blob(a.tobytes(),'array',True))
def banks(obj):
    return {str(k):None if b is None else dict(id=b.frame_id,tag=b.tag.hex(),planes=[array(p,'<i2') for p in b.planes]) for k,b in obj.banks.items()}
def native(path,n=6):
    frames=[];pts=[]
    with av.open(str(path)) as c:
        s=next(x for x in c.streams if x.type=='video');fps=str(s.average_rate)
        for f in c.decode(s):
            if Fraction(f.pts)*f.time_base<4:continue
            frames.append(f.to_ndarray(format='rgb24'));pts.append(f.pts)
            if len(frames)==n:break
    assert len(frames)==n
    return frames,dict(source=str(path),source_sha256=sha(path),selected_pts=pts,source_fps=fps,scope='Six related precompressed native frames at4seconds; offline load/BOX, not live capture')
def pins():
    paths={HERE/n for n in ('trace_codec.py','export.py','verify.py','test_trace.py')}
    for name in ('python-game-local-refresh-study','python-game-unified-codec-study'):
        d=json.loads((HERE.parent/name/'results.json').read_text())
        for p in d['source_sha256']:
            paths.add(ROOT/p.split('/moonbub-30fps-study/',1)[-1])
    paths|={Path(t.codec.__file__),Path(t.transport.__file__),HERE.parent/'python-game-local-refresh-study/results.json',HERE.parent/'python-game-unified-codec-study/results.json'}
    return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}
def make_cohort(name,frames,mode,ui,requests):
    selector=PatchSelector() if ui else None;e=t.codec.Encoder(epoch=18,mode=mode,patch_builder=selector);r=t.codec.Receiver(epoch=18);rows=[]
    for i,rgb in enumerate(frames):
        h,w=rgb.shape[:2]
        if w==720:map_=t.codec.gm.roi.declared_map(w,h,((16,48,192,80),(160,352,400,80)),8,16)
        else:mw,mh=t.codec.gm.roi.geometry(w,h);map_=np.full((mh,mw),16,np.uint8)
        before=banks(r);req=requests[i];d=e.prepare(rgb,i,scale_map=map_,**req);assert d.accepted
        meta=t.codec.identity(d.packet,decode=True);trace=t.parse_packet(d.packet)
        task=r.begin(d.packet);decoded=task.planes;actual,info,ack=r.complete(task)
        assert e.expected_hash(i)==hashlib.sha256(actual.tobytes()).hexdigest();assert e.ack(ack)
        selected=0;source_words=t.codec.corpus.rgb565(rgb);display_words=t.codec.corpus.rgb565(actual)
        for p in meta['patches']:
            x,y,rw,rh=p['rect'];selected+=rw*rh
            np.testing.assert_array_equal(source_words[y:y+rh,x:x+rw],display_words[y:y+rh,x:x+rw])
        if ui:assert selected==21120
        chunks=t.transport.datagrams(d.packet,18,i)
        rows.append(dict(id=i,request=req,source_rgb888=array(rgb,'|u1'),scale_map=array(map_,'|u1'),
            ar03=blob(d.packet,'ar03'),gf02=[blob(p,'gf02') for p in chunks],af03=blob(ack,'af03'),
            pre_banks=before,post_banks=banks(r),decoded_yuv=[array(p,'<i2') for p in decoded],display_rgb565=array(display_words,'<u2'),
            rgb888_sha256=hashlib.sha256(actual.tobytes()).hexdigest(),base_rgb888_sha256=info['base_rgb_sha256'],selected_pixels=selected,
            trace=blob(json.dumps(trace,separators=(',',':'),sort_keys=True).encode(),'trace',True),
            trace_summary=dict(codec=trace['inner_codec'],packet_bytes=len(d.packet),blocks=sum(p['blocks_w']*p['blocks_h'] for p in trace['planes']),
                stripes=sum(len(p['stripes']) for p in trace['planes']),general=sum(s['general'] for p in trace['planes'] for s in p['stripes']),
                dc=sum(s['dc'] for p in trace['planes'] for s in p['stripes']),zero=sum(s['zero'] for p in trace['planes'] for s in p['stripes']))))
    return dict(name=name,mode=mode,ui=ui,rows=rows)
def main():
    before=pins();started=time.perf_counter();media=Path(os.environ.get('GAMEBUB_MEDIA_DIR',str(HERE.parents[3]/'media')))
    raw,manifest=native(media/'mass-effect-2600.mp4');frames=[t.codec.corpus._letterbox(a,720,480)[0] for a in raw]
    req=[dict(force_key=i in (0,3),promote=i in (1,5)) for i in range(6)]
    cohorts=[make_cohort('native-'+mode,frames,mode,True,req) for mode in ('gm','exact')]
    partial=[np.full((18,34,3),128+i,np.uint8) for i in range(4)]
    cohorts.append(make_cohort('partial-flat-sr',partial,'exact',False,[dict(force_key=i==0,promote=i==2) for i in range(4)]))
    assert before==pins()
    rows=[r for c in cohorts for r in c['rows']];files=list((HERE/'objects').iterdir())
    out=dict(schema='gamebub-ar03-exact-traces-v1',epoch=18,source_sha256=before,input_media=manifest,cohorts=cohorts,
        counts=dict(cohorts=len(cohorts),frames=len(rows),native_frames=12,unique_native_acquisitions=6,gf02_datagrams=sum(len(r['gf02']) for r in rows),
            selected_ui_words=sum(r['selected_pixels'] for r in rows),coefficient_blocks=sum(r['trace_summary']['blocks'] for r in rows),
            objects=len(files),stored_object_bytes=sum(p.stat().st_size for p in files)),
        elapsed_python_seconds=time.perf_counter()-started,
        limits=['No hardware/native/ISA/physical30fps proof','Exact entropy walkers use two<=64bit reservoirs; inputpacket/fulloutput/oracle/trace storage outside bound','Header/CRC/map preflight complete before coefficient walk; not onepasswire decoder',
                'Only selected actual syntax decoded; losingencoder candidates not estimated','Six related native sourceframes repeatedGM/exact, not twelve independentcaptures','Nojointnetwork/decode/memory timing; traces are decoderwork contracts not rates'])
    (HERE/'results.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out['counts']))
if __name__=='__main__':main()
