#!/usr/bin/env python3
"""Actual candidate/discard/commit arithmetic with frozen byte-identical controls."""
import hashlib,json,time,platform
from pathlib import Path
import av,numpy as np,PIL
import candidate_codec as c
from ui_plugin import PatchSelector
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(a):return hashlib.sha256(a.tobytes()).hexdigest()
def pins():
    ancestor=HERE.parent/'python-game-local-refresh-study/results.json'
    paths={ROOT/p for p in json.loads(ancestor.read_text())['source_sha256']}
    paths|={ancestor,HERE/'candidate_codec.py',HERE/'benchmark.py',HERE/'verify.py',HERE/'test_candidate.py'}
    return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}
def state(e):
    return dict(last_issued=e.last_issued,generation=e._generation,geometry=e._geometry,pending=sorted(e.pending),
                banks={str(s):None if b is None else dict(id=b.frame_id,tag=b.tag.hex()) for s,b in e.banks.items()})
def timed(fn):
    started=time.perf_counter_ns();value=fn();return value,(time.perf_counter_ns()-started)/1e6
def source():
    path=HERE.parents[3]/'media/mass-effect-2600.mp4';frames=[];pts=[];native=[]
    with av.open(str(path)) as stream:
        video=next(s for s in stream.streams if s.type=='video')
        for f in stream.decode(video):
            if float(f.pts*f.time_base)<4:continue
            rgb=f.to_ndarray(format='rgb24');native.append(digest(rgb));pts.append(f.pts)
            frames.append(c.corpus._letterbox(rgb,720,480)[0])
            if len(frames)==12:break
    assert len(frames)==len(set(map(digest,frames)))==12
    return frames,dict(source=str(path),source_sha256=sha(path),pts=pts,native_rgb_hashes=native,canvas_hashes=list(map(digest,frames)),active='720x405@row37inside720x480',scope='Offline precompressed12nativeframes from prior4sregression, notfreshvalidation/livecapture')
def main():
    before=pins();frames,manifest=source();rows=[];started=time.perf_counter()
    scale=c.gm.roi.declared_map(720,480,((16,48,192,80),(160,352,400,80)),8,16)
    for mode in ('gm','exact'):
        for policy in ('all_commit','reject0_3_5'):
            e=c.Encoder(mode=mode,patch_builder=PatchSelector());r=c.Receiver()
            frozen=c.frozen.Encoder(mode=mode,patch_builder=PatchSelector());fr=c.frozen.Receiver()
            for i,rgb in enumerate(frames):
                kw=dict(scale_map=scale,promote=i in (2,5,8),force_key=i in (3,9))
                prior=state(e);x,build_ms=timed(lambda:e.build(rgb,i,**kw))
                assert state(e)==prior and x.accepted and e.active_candidate is x
                row=dict(mode=mode,policy=policy,id=i,input_sha256=digest(rgb),bytes=len(x.packet),build_ms=build_ms,
                    internal_build_ms=x.service_ms,analyze_calls=x.info['analyze_calls'],forward_calls=x.info['forward_calls'],
                    key=x.key,promoted=x.promoted,reference_bank=x.reference_bank,reference_id=x.reference_id,
                    source_pin_during_build=e.readers,state_before=prior,state_after_build=state(e),packet_sha256=sha_bytes(x.packet))
                if policy!='all_commit' and i in (0,3,5):
                    _,drop_ms=timed(lambda:e.discard(x));assert state(e)==prior and e.readers==0
                    row.update(action='discard',discard_ms=drop_ms,state_after=state(e),readers_after=0)
                else:
                    d,commit_ms=timed(lambda:e.commit(x));fd,frozen_prepare_ms=timed(lambda:frozen.prepare(rgb,i,**kw))
                    assert d.packet==fd.packet
                    (out,info,ack),receive_ms=timed(lambda:r.receive(d.packet));fout,finfo,fack=fr.receive(fd.packet)
                    assert ack==fack and np.array_equal(out,fout)
                    mismatches=0
                    for patch in info['patches']:
                        px,py,pw,ph=patch['rect'];mismatches+=int(np.count_nonzero(c.corpus.rgb565(rgb[py:py+ph,px:px+pw])!=c.corpus.rgb565(out[py:py+ph,px:px+pw])))
                    assert mismatches==0 and info['selected_pixels']==21120
                    _,ack_ms=timed(lambda:e.ack(ack));frozen.ack(fack)
                    assert state(e)==state(frozen) and e.readers==0
                    row.update(action='commit',commit_ms=commit_ms,receive_ms=receive_ms,ack_ms=ack_ms,
                        frozen_prepare_ms=frozen_prepare_ms,state_after=state(e),readers_after=0,
                        byte_identical_frozen=True,decoded_sha256=digest(out),frozen_decoded_sha256=digest(fout),
                        base_rgb_sha256=info['base_rgb_sha256'],selected_words=info['selected_pixels'],selected_word_errors=mismatches,
                        decoded_yuv_tags={str(s):None if b is None else b.tag.hex() for s,b in r.banks.items()})
                rows.append(row)
    # Independent small noise probes exercise paid over-cap P rejection and reuse
    # the same unconsumed ID; no full-frame/noise FPS claim is inferred.
    rng=np.random.default_rng(1807);e=c.Encoder(mode='gm');r=c.Receiver()
    d=e.prepare(np.full((48,64,3),70,np.uint8),0);_,_,ack=r.receive(d.packet);e.ack(ack);e.frame_cap=128
    cap_rows=[]
    for trial in range(4):
        prior=state(e);rgb=rng.integers(0,256,(48,64,3),dtype=np.uint8)
        x,elapsed=timed(lambda:e.build(rgb,1));assert not x.accepted and state(e)==prior and e.readers==0
        _,drop_ms=timed(lambda:e.discard(x));assert state(e)==prior and e.readers==0
        cap_rows.append(dict(trial=trial,id=1,build_ms=elapsed,discard_ms=drop_ms,complete_attempted_bytes=x.info['bytes'],cap=128,
                             state_before=prior,state_after=state(e),readers_after=0))
    assert before==pins(),'sources changed'
    result=dict(evidence='Actual AR03 candidate/commit/discard with pinned frozen byte/pixel controls',source_sha256=before,input=manifest,
        rows=rows,cap_rejections=cap_rows,native_decisions=len(rows),native_commits=sum(x['action']=='commit' for x in rows),
        native_discards=sum(x['action']=='discard' for x in rows),native_selected_exact_words=sum(x.get('selected_words',0) for x in rows),
        total_python_wall_seconds=time.perf_counter()-started,versions=dict(python=platform.python_version(),numpy=np.__version__,pillow=PIL.__version__,pyav=av.__version__),
        limits=['Component control, not pacedtransport/FIFO/deadline/FPS model','Outer build/commit/discard/receive/ack clocks measured; frozencontrol separatelytimed; sourceBOX/maps/offlineload/errororacles outsidecomponent clocks',
                'Discarded expensivecandidatework is measured; no identity/geometry/publicationreservation consumed; transient sourcelease/caches/counters are real sideeffects',
                'Onecandidate plus pending/reconstruction/reference/cache storage is not nativeheap/BRAM fit','Canonical sourceYUV stillint16; no standardHEVC/AV1 or installedAR03 peer'])
    (HERE/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('native_decisions','native_commits','native_discards','native_selected_exact_words','total_python_wall_seconds')},indent=2))
def sha_bytes(data):return hashlib.sha256(data).hexdigest()
if __name__=='__main__':main()
