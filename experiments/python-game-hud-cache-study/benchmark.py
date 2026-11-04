#!/usr/bin/env python3
"""Actual HC21 display sidecars; legacy AR03 base bytes are accounting only."""
from pathlib import Path
import hashlib,json,os,platform,time,zlib
import numpy as np
import model as m
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
source=m.load('hc21_native_source',HERE.parent/'python-game-service-study/benchmark.py')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pins():
    old=json.loads((HERE.parent/'python-game-mandatory-hud-study/results.json').read_text())
    paths={ROOT/p for p in old['source_sha256']}
    paths|={HERE.parent/'python-game-mandatory-hud-study/results.json',Path(m.legacy.__file__),Path(m.hd.__file__),Path(source.__file__)}
    paths|={HERE/n for n in ('model.py','benchmark.py','verify.py','test_model.py')}
    return {p.relative_to(ROOT).as_posix():sha(p)for p in sorted(paths)}
def blob(data):
    stored=zlib.compress(data,9);digest=hashlib.sha256(stored).hexdigest();name='objects/'+digest+'.zlib';p=HERE/name;p.parent.mkdir(exist_ok=True)
    if not p.exists():p.write_bytes(stored)
    return dict(path=name,raw_bytes=len(data),raw_sha256=hashlib.sha256(data).hexdigest(),stored_sha256=digest)
def measured(fn):
    t=time.perf_counter_ns();value=fn();return value,(time.perf_counter_ns()-t)/1e6

def run_case(name,frames,manifest,oldrows=None):
    s,r=m.Sender(),m.Receiver();rows=[]
    for frame,rgb in enumerate(frames):
        (packet,info),encode_ms=measured(lambda:s.prepare(rgb,frame))
        ack,decode_ms=measured(lambda:r.receive(packet));_,ack_ms=measured(lambda:s.accept_ack(ack))
        expected=m.extract(rgb)
        errors=sum(int(np.count_nonzero(a!=b))for a,b in zip(expected,r.display['patches']))
        assert errors==0
        old=None if oldrows is None else oldrows[frame]
        if old is not None:assert info['legacy_patch_bytes']==old['mandatory_patch_bytes']
        delta_modes={0:'raw',1:'copy',2:'span_xor'}
        info['mode_names']=[p['kind']if p['kind']=='legacy'else delta_modes[p['kind']]for p in info['patches']]
        info.update(encode_ms=encode_ms,decode_ms=decode_ms,ack_apply_ms=ack_ms,source_sha256=hashlib.sha256(rgb.tobytes()).hexdigest(),exact_word_errors=errors,
            packet=blob(packet),ack=blob(ack),original_patches=[blob(a.astype('<u2').tobytes())for a in expected])
        if old is not None:
            info.update(v20_complete_packet_bytes=old['packet_bytes'],v20_inner_bytes=old['inner_bytes'],v20_input_sha256=old['input_sha256'],
                accounting_only_replaced_total=old['packet_bytes']-old['mandatory_patch_bytes']+len(packet))
            assert info['source_sha256']==old['input_sha256']
        rows.append(info)
    summary=dict(name=name,frames=len(rows),exact_words=sum(x['exact_words']for x in rows),exact_word_errors=sum(x['exact_word_errors']for x in rows),
        legacy_patch_bytes=sum(x['legacy_patch_bytes']for x in rows),sidecar_bytes=sum(x['sidecar_bytes']for x in rows),ack_bytes=sum(x['ack_bytes']for x in rows),
        maximum_sidecar_bytes=max(x['sidecar_bytes']for x in rows),mode_counts={name:sum(x['mode_names'].count(name)for x in rows)for name in ('legacy','raw','copy','span_xor')},
        mean_encode_ms=sum(x['encode_ms']for x in rows)/len(rows),mean_decode_ms=sum(x['decode_ms']for x in rows)/len(rows),
        maximum_sender_pixel_bytes=max(x['sender_pixel_bytes']for x in rows),maximum_legacy_cache_bytes=max(x['sender_legacy_cache_bytes']for x in rows),
        receiver_two_banks_plus_atomic_stage_bytes=3*m.BANK_BYTES)
    summary['patch_forward_saving_fraction']=1-summary['sidecar_bytes']/summary['legacy_patch_bytes']
    if oldrows is not None:
        summary.update(v20_complete_bytes=sum(x['v20_complete_packet_bytes']for x in rows),accounting_only_replaced_bytes=sum(x['accounting_only_replaced_total']for x in rows),
            accounting_only_cap_failures=sum(x['accounting_only_replaced_total']>49152 for x in rows))
    return dict(name=name,manifest=manifest,rows=rows,summary=summary)
def synthetic():
    rng=np.random.default_rng(2104)
    for name in ('static','small_change','noise'):
        frames=[];a=np.zeros((480,720,3),np.uint8)
        for x,y,w,h in m.RECTANGLES:a[y:y+h,x:x+w]=np.array([44,96,156],np.uint8)
        for f in range(12):
            b=a.copy()
            if name=='small_change':
                for x,y,w,h in m.RECTANGLES:b[y+f%h,x+2*f:x+2*f+2]=[236,32,8]
            elif name=='noise':
                for x,y,w,h in m.RECTANGLES:b[y:y+h,x:x+w]=rng.integers(0,256,(h,w,3),np.uint8)
            frames.append(b)
        yield name,frames

def main():
    before=pins();cases=[];old=json.loads((HERE.parent/'python-game-mandatory-hud-study/results.json').read_text())
    media=Path(os.environ.get('GAMEBUB_MEDIA_DIR',str(HERE.parents[3]/'media')))
    for scene in ('mass-effect-2600','mass-effect-7200'):
        native,manifest=source.native(media/(scene+'.mp4'),n=48,start=4)
        frames=[];box=[]
        for a in native:
            (b,_),elapsed=measured(lambda:m.legacy.codec.corpus._letterbox(a,720,480));frames.append(b);box.append(elapsed)
        manifest['box_ms']=box
        original=next(c for c in old['cases']if c['scene']==scene and c['policy']=='mandatory')
        case=run_case(scene,frames,manifest,original['rows']);cases.append(case);print(json.dumps(case['summary']),flush=True)
    for name,frames in synthetic():
        case=run_case('synthetic-'+name,frames,dict(synthetic=True,seed=2104,frames=12));cases.append(case);print(json.dumps(case['summary']),flush=True)
    assert before==pins(),'source mutated during run'
    d=dict(schema='gamebub-hud-cache-v21',source_sha256=before,cases=cases,counts=dict(native_frames=96,synthetic_frames=36,decisions=132),
        header_bytes=m.HEADER.size,crc_bytes=4,ack_bytes=m.ACK.size+4,bank_pixel_bytes=m.BANK_BYTES,
        scope=['Standalone negotiated HC21/HA21 display sidecar; not AR03-compatible bytes or implemented firmware.',
        'Same native96sourceframes asv20; legacyfullandnewdelta candidates bothpaid, all21120wordsexact eachacceptedupdate.',
        'Two persistent receiver pixel banks plus whole HUD staging=126720bytes before decoder scratch/packet/parser/metadata; no memory fit claim.',
        'One in-flight update. Exact retransmission retries packet/ACKloss; no nextframe beforeACK. No wire/deadline/RTT schedule modeled.',
        'Existingv20base/map/reference history held unchanged for byte-accounting comparison only; not remuxed intoAR03.',
        'Python stage wall time includes actualcandidateencoding/hash/validation/publication; offlinePyAVsourceexcluded. No ESP32native/RF/FPGA/physical30fps proof.'],
        versions=dict(python=platform.python_version(),numpy=np.__version__))
    (HERE/'results.json').write_text(json.dumps(d,separators=(',',':'),allow_nan=False)+'\n')
if __name__=='__main__':main()
