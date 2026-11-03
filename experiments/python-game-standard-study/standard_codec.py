"""Native HEVC/AV1 offline reference encodes; not a Game Bub target decoder."""
from fractions import Fraction
import hashlib
import time
import av


def options(name,crf):
    if name=='libx265':
        return {'preset':'ultrafast','tune':'zerolatency','crf':str(crf),
                'x265-params':'log-level=error:pools=none:frame-threads=1:wpp=0:keyint=30:min-keyint=30:scenecut=0:repeat-headers=1'}
    if name=='libsvtav1':
        return {'preset':'8','crf':str(crf),
                'svtav1-params':'pred-struct=1:lookahead=0:enable-tf=0:scd=0:lp=1:tune=1'}
    raise ValueError('explicit reference encoder required')


def run(frames,name,crf):
    if not frames:raise ValueError('nonempty source required')
    h,w=frames[0].shape[:2];tb=Fraction(1,30)
    encoder=av.CodecContext.create(name,'w');encoder.width=w;encoder.height=h
    encoder.pix_fmt='yuv420p';encoder.time_base=tb;encoder.framerate=Fraction(30,1)
    encoder.thread_count=1;encoder.gop_size=30;encoder.max_b_frames=0
    requested=options(name,crf);encoder.options=requested.copy()
    begun=time.perf_counter_ns();encoder.open();open_ms=(time.perf_counter_ns()-begun)/1e6
    if encoder.options:raise ValueError('unconsumed options: '+repr(encoder.options))
    outputs=[];packets=[];frame_calls=[]
    for index,rgb in enumerate(frames):
        started=time.perf_counter_ns()
        frame=av.VideoFrame.from_ndarray(rgb,format='rgb24').reformat(format='yuv420p')
        frame.pts=index;frame.time_base=tb
        converted_ms=(time.perf_counter_ns()-started)/1e6
        started=time.perf_counter_ns();batch=encoder.encode(frame);cost=(time.perf_counter_ns()-started)/1e6
        packets.extend(batch)
        frame_calls.append({'id':index,'convert_ms':converted_ms,'encode_call_ms':cost,
                            'emitted_pts':[p.pts for p in batch],'emitted_bytes':sum(p.size for p in batch),
                            'packets_emitted_so_far':len(packets)})
    started=time.perf_counter_ns();tail=encoder.encode(None);flush_ms=(time.perf_counter_ns()-started)/1e6
    packets.extend(tail)
    decoder=av.CodecContext.create('hevc' if name=='libx265' else 'libdav1d','r');decoder.thread_count=1
    # Codec bytes and extradata are included in accounting, independent of mux framing.
    if encoder.extradata:decoder.extradata=encoder.extradata
    decode_calls=[];records=[]
    for packet in packets:
        data=bytes(packet);copy=av.Packet(data);copy.pts=packet.pts;copy.dts=packet.dts;copy.time_base=tb
        started=time.perf_counter_ns();decoded=decoder.decode(copy);decode_ms=(time.perf_counter_ns()-started)/1e6
        convert_ms=0
        for frame in decoded:
            t=time.perf_counter_ns();rgb=frame.to_ndarray(format='rgb24');convert_ms+=(time.perf_counter_ns()-t)/1e6
            outputs.append((frame.pts,rgb))
        decode_calls.append({'packet_pts':packet.pts,'decode_ms':decode_ms,'rgb_convert_ms':convert_ms,'output_pts':[f.pts for f in decoded]})
        records.append({'pts':packet.pts,'dts':packet.dts,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'is_keyframe':packet.is_keyframe})
    started=time.perf_counter_ns();tail=decoder.decode(None);decode_flush_ms=(time.perf_counter_ns()-started)/1e6
    for frame in tail:outputs.append((frame.pts,frame.to_ndarray(format='rgb24')))
    pts=[p for p,_ in outputs]
    if sorted(pts)!=list(range(len(frames))):raise AssertionError(('decoder output association',pts))
    outputs=dict(outputs)
    if len(outputs)!=len(frames):raise AssertionError('missing/duplicate reference decode')
    return outputs,{'encoder':name,'requested_options':requested,'unconsumed_options':encoder.options,
        'width':w,'height':h,'time_base':str(tb),'input_frames':len(frames),'packets':records,
        'frame_calls':frame_calls,'decode_calls':decode_calls,'encoder_open_ms':open_ms,'encode_flush_ms':flush_ms,
        'packets_returned_only_at_flush':len(packets)-sum(len(c['emitted_pts']) for c in frame_calls),
        'decode_flush_ms':decode_flush_ms,'extradata_bytes':len(encoder.extradata or b''),
        'coded_bytes':sum(p.size for p in packets)+len(encoder.extradata or b''),
        'output_pts':pts,'codec_library_versions':{k:list(v) for k,v in av.library_versions.items()},
        'scope':'Native CPU software reference. InputRGB->YUV and decodedYUV->RGB usePyAVdefaults, not GM01exactcolorarithmetic. No packetdeadline/nativecapture/targetdecodeorbufferproof.'}
