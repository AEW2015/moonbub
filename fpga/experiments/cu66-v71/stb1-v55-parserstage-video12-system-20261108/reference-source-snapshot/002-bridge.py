#!/usr/bin/env python3
"""Offline source-frame CU66 bridge. No socket, capture, firmware or hardware access."""
from pathlib import Path
import argparse, hashlib, importlib.util, json, struct, sys, time, zlib
sys.dont_write_bytecode = True
import numpy as np

HERE = Path(__file__).resolve().parent
EXPERIMENTS = HERE.parent

def digest(data): return hashlib.sha256(data).hexdigest()

def module(name, path, aliases=None):
    before = {k: sys.modules.get(k) for k in (aliases or {})}
    try:
        sys.modules.update(aliases or {})
        spec = importlib.util.spec_from_file_location(name, path)
        value = importlib.util.module_from_spec(spec)
        sys.modules[name] = value
        spec.loader.exec_module(value)
        return value
    finally:
        for k, v in before.items():
            if v is None: sys.modules.pop(k, None)
            else: sys.modules[k] = v

def load_models():
    h = module('bridge_integrated_helpers', EXPERIMENTS/'python-game-integrated-v38-study/helpers.py')
    integrated = module('bridge_integrated', EXPERIMENTS/'python-game-integrated-v38-study/model.py', {'helpers':h})
    analysis = module('bridge_analysis', EXPERIMENTS/'python-game-analysis-v37-study/model.py', {'helpers':h})
    cs37 = module('bridge_cs37', EXPERIMENTS/'python-game-implicit-v37-study/verify.py')
    hx32 = module('bridge_hx32', EXPERIMENTS/'python-game-hud-v32-study/model.py')
    baseline = module('bridge_baseline', EXPERIMENTS/'python-game-hud-runs-v33-study/baseline.py')
    hud_decoder = module('bridge_hud_decoder', EXPERIMENTS/'python-game-hud-runs-v33-study/decoder.py', {'baseline':baseline})
    hx33 = module('bridge_hx33', EXPERIMENTS/'python-game-hud-runs-v33-study/model.py', {'baseline':baseline, 'decoder':hud_decoder})
    binary_helper = module('bridge_binary_helpers', EXPERIMENTS/'python-game-binary-v38-study/helpers.py')
    binary_frame = module('bridge_binary_frame', EXPERIMENTS/'python-game-binary-v38-study/frame_verify.py', {'helpers':binary_helper})
    arithmetic = module('bridge_arithmetic', EXPERIMENTS/'python-game-binary-v38-study/model.py')
    canonical = module('bridge_canonical_helpers', EXPERIMENTS/'python-game-canonical-tag-v66-study/helpers.py')
    wire = canonical.bound('bridge_cu66_wire', canonical.HERE/'protocol.py', canonical)
    receiver = canonical.bound('bridge_cu66_receiver', canonical.HERE/'receiver.py', canonical)
    return h, integrated, analysis, cs37, hx32, baseline, hx33, binary_helper, binary_frame, arithmetic, canonical, wire, receiver

def synthetic(fid):
    """New deterministic RGB24 frames: smooth gradients, moving box and exact HUD."""
    y, x = np.indices((480,720), dtype=np.int32)
    out = np.stack(((x//4+fid*5)%256, (y//3+fid*3)%256, ((x+y)//8+fid*7)%256), axis=2).astype(np.uint8)
    left = 120+fid*16
    out[160:240,left:left+80] = (220,80+fid*10,35)
    return out

def encode_sequence(canvases, output):
    output = Path(output)
    if output.exists(): raise ValueError('fresh output directory required')
    output.mkdir(parents=True)
    h, integrated, analysis, cs37, hx32, baseline, hx33, bh, bf, arithmetic, ch, wire, cr = load_models()
    source_paths={Path(m.__file__).resolve() for m in tuple(sys.modules.values()) if getattr(m,'__file__',None) and str(Path(m.__file__).resolve()).lower().startswith(str(EXPERIMENTS).lower()) and Path(m.__file__).suffix in ('.py','.hpp')}
    before_pins={str(p):digest(p.read_bytes()) for p in sorted(source_paths)}
    cs37_rx, cs38_rx, cu66_rx = cs37.Receiver(), ch.oldrx.Receiver(), cr.Receiver('CU66')
    ref = hud_ref = None
    prior = None
    rows, index = [], []
    for fid, canvas in enumerate(canvases):
        if not isinstance(canvas,np.ndarray) or canvas.dtype != np.uint8 or canvas.shape != (480,720,3):
            raise ValueError('source must be exact uint8 RGB24 480x720x3')
        key = fid == 0 or fid % 24 == 0
        rid = baseline.p.NO_REF if key else prior
        incoming = None if key else ref
        incoming_hud = None if key else hud_ref
        began = time.perf_counter()
        source = tuple(np.asarray(v,dtype=np.int16) for v in h.m.ft.rgb_to_planes(canvas))
        selector = baseline.p.ui.PatchSelector(rectangles=tuple(h.n.RECTS))
        chosen = selector.select(canvas,98304)
        hu25, _ = baseline.p.encode_hud(chosen.patches, reference=incoming_hud, epoch=25,frame_id=fid,reference_id=rid,motion=True,width=720,height=480)
        hx32_bytes, _ = hx32.encode_hud(hu25,incoming_hud,expected_reference_id=None if key else rid)
        hud_bytes, _ = hx33.encode_hud(hu25,hx32_bytes,incoming_hud,expected_reference_id=None if key else rid)
        prepared = analysis.analyze_planes(source,incoming,epoch=25,frame_id=fid,reference_id=rid,block_size=32,motion_mode='zero',penalty=0,motion_precision='half')
        tries=[]
        for background in (16,32):
            try:
                q = h.m.roi.declared_map(720,480,h.n.ROIS,8,background)
                old_packet, normalized, _ = integrated.encode_prepared(prepared,q,hud_bytes,rdo_lambda=1)
                break
            except ValueError as exc: tries.append(str(exc))
        else: raise ValueError('no bounded CS37 candidate: '+repr(tries))
        old_output = cs37_rx.receive(old_packet)
        for a,b in zip(old_output[0],normalized,strict=True): np.testing.assert_array_equal(a,b)
        metadata = cs37.parse(old_packet)
        outer=list(cs37.HEADER.unpack_from(old_packet))
        inner=old_packet[cs37.HEADER.size:cs37.HEADER.size+outer[11]]
        fields=list(cs37.m.HEADER.unpack_from(inner))
        maps=inner[cs37.m.HEADER.size:cs37.m.HEADER.size+fields[12]+fields[13]]
        payloads=[]
        dispatches=[]
        for axis,(coeff,safe) in enumerate(zip(metadata['coefficients'],bh.f.f.safe_blocks(),strict=True)):
            options=[]
            for compact in (False,True):
                coefficients=coeff[~safe.reshape(-1)] if compact else coeff
                width=1 if compact else (90 if axis==0 else 45)
                encoded,_=arithmetic.encode(coefficients,width)
                candidate=bytes([6 if compact else 5])+encoded
                np.testing.assert_array_equal(bf.decoder.decode(encoded,len(coefficients),width),coefficients)
                options.append(candidate)
            payload=min(options,key=len)
            payloads.append(payload);dispatches.append(payload[0])
        fields[0]=b'GS38';fields[14:17]=[len(v) for v in payloads]
        newinner=bf.seal(cs37.m.HEADER.pack(*fields)+maps+b''.join(payloads))
        outer[0]=b'CS38';outer[8]=bf.PROFILE;outer[11]=len(newinner)
        cs38_packet=bf.seal(cs37.HEADER.pack(*outer)+newinner+metadata['hud'])
        if len(cs38_packet)>49152: raise ValueError('CS38 arithmetic-only profile exceeds cap')
        expected=cs38_rx.receive(cs38_packet)
        packet,_=wire.convert(cs38_packet,'CU66',reference=incoming,normalized=expected[0])
        actual=cu66_rx.receive(packet)
        assert len(packet)<=49152
        for result in (expected,actual):
            for a,b in zip(result[0],old_output[0],strict=True): np.testing.assert_array_equal(a,b)
            for a,b in zip(result[1],old_output[1],strict=True):
                assert a['rect']==b['rect'];np.testing.assert_array_equal(a['words'],b['words'])
        original=h.m.C.corpus.rgb565(canvas)
        for patch in actual[1]:
            x,y,w,hh=patch['rect'];np.testing.assert_array_equal(patch['words'],original[y:y+hh,x:x+w])
        planes=b''.join(p.astype(np.uint8).tobytes() for p in actual[0])
        hud=b''.join(p['words'].astype('<u2').tobytes() for p in actual[1])
        display=h.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(actual[0])),tuple(p['words'] for p in actual[1])).astype('<u2').tobytes()
        rel=f'frame{fid:03d}.cu66';(output/rel).write_bytes(packet)
        (output/f'frame{fid:03d}.hud').write_bytes(hud)
        prepare_body=struct.pack('<4sBBHIQIII',b'HC70',1,1,0,len(metadata['hud']),fid+1,fid,rid,int(key))+metadata['hud']
        prepare=prepare_body+struct.pack('<I',zlib.crc32(prepare_body))
        (output/f'frame{fid:03d}.prepare').write_bytes(prepare)
        row=dict(id=fid,key=key,reference_id=rid,packet=rel,bytes=len(packet),sha256=digest(packet),source_rgb24_sha256=digest(canvas.tobytes()),canonical_yuv_u8_sha256=digest(planes),hud_words_u16le_sha256=digest(hud),display_rgb565_u16le_sha256=digest(display),dispatches=dispatches,hud_envelope=metadata['hud'][:4].decode(),selected_background=background,offline_wall_seconds=time.perf_counter()-began)
        rows.append(row)
        index.append('\t'.join(map(str,(0,fid,rel,digest(planes),digest(hud),digest(display)))))
        ref,hud_ref,prior=actual[0],actual[1],fid
        print(json.dumps(row),flush=True)
    (output/'index.tsv').write_text('\n'.join(index)+'\n')
    source_paths={Path(m.__file__).resolve() for m in tuple(sys.modules.values()) if getattr(m,'__file__',None) and str(Path(m.__file__).resolve()).lower().startswith(str(EXPERIMENTS).lower()) and Path(m.__file__).suffix in ('.py','.hpp')}
    pins={str(p):digest(p.read_bytes()) for p in sorted(source_paths)}
    assert pins==before_pins, 'imported source changed during generation'
    result=dict(schema='cu66-source-bridge-v1',source='new synthetic RGB24 frames' if all(np.array_equal(c,synthetic(i)) for i,c in enumerate(canvases)) else 'explicit caller-provided RGB24 canvases',rows=rows,source_sha256=pins,hardware_used=False,network_used=False,target_fit_or_fps_proven=False)
    (output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--count',type=int,default=3)
    parser.add_argument('--rgb24-npy',type=Path,help='Optional uint8 N x 480 x 720 x 3 prepared RGB canvases; no implicit scaling')
    args=parser.parse_args()
    if not 1<=args.count<=12: raise ValueError('offline experiment count1..12')
    canvases=np.load(args.rgb24_npy,allow_pickle=False) if args.rgb24_npy else np.stack([synthetic(i) for i in range(args.count)])
    if len(canvases)!=args.count: raise ValueError('explicit count must match input')
    encode_sequence(canvases,args.output)
