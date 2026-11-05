#!/usr/bin/env python3
"""Transcode all accepted causal v40 CS37 packets to frozen CS38/AB38."""
import json,time
import numpy as np
import bridge as b
encoder=b.old.module('binary_qual_v40_frozen_encoder',b.BASE/'model.py')

def main():
    pins=b.pins();control=b.load(b.CONTROL/'results.json');cases=[]
    assert sum(c['summary']['accepted_frames'] for c in control['cases'])==457
    for oldcase in control['cases']:
        rows=[];rx=b.frame.Receiver();baseline=b.f.Receiver();last_accepted=None
        for oldrow in oldcase['rows']:
            assert oldrow['accepted'] is True
            selected=[a for a in oldrow['attempts'] if a.get('selected')]
            assert len(selected)==1
            input_packet=b.raw(selected[0]['packet'],b.CONTROL)
            oldmeta=b.f.parse(input_packet);fid=oldrow['id']
            key=(fid%24==0 or last_accepted is None)
            assert oldmeta['frame_id']==fid and oldmeta['key']==key
            expected_rid=b.f.m.NO_REF if key else last_accepted
            assert oldmeta['reference_id']==expected_rid==oldrow['reference_id']
            outer=list(b.f.HEADER.unpack_from(input_packet))
            inner=input_packet[b.f.HEADER.size:b.f.HEADER.size+outer[11]]
            fields=list(b.f.m.HEADER.unpack_from(inner))
            maps=inner[b.f.m.HEADER.size:b.f.m.HEADER.size+fields[12]+fields[13]]
            payloads=[];attempts=[]
            for axis,(coeff,safe,previous) in enumerate(zip(oldmeta['coefficients'],b.f.f.safe_blocks(),oldmeta['plane_payloads'],strict=True)):
                options=[previous];trials=[]
                for compact in (False,True):
                    source=coeff[~safe.reshape(-1)] if compact else coeff
                    width=1 if compact else (90 if axis==0 else 45)
                    began=time.perf_counter_ns();encoded,work=encoder.encode(source,width)
                    encode_ms=(time.perf_counter_ns()-began)/1e6
                    np.testing.assert_array_equal(b.decoder.decode(encoded,len(source),width),source)
                    candidate=bytes([6 if compact else 5])+encoded
                    options.append(candidate)
                    trials.append(dict(compact=compact,packet=b.blob(encoded),payload_bytes=len(candidate),
                                       encode_ms=encode_ms,work=work,decoded_exact=True))
                winner=min(range(3),key=lambda i:len(options[i]))
                payloads.append(options[winner])
                attempts.append(dict(plane=axis,old_bytes=len(previous),selected=winner,
                                     selected_bytes=len(payloads[-1]),trials=trials))
            fields[0]=b'GS38';fields[14:17]=[len(v) for v in payloads]
            newinner=b.frame.seal(b.f.m.HEADER.pack(*fields)+maps+b''.join(payloads))
            outer[0]=b'CS38';outer[8]=b.frame.PROFILE;outer[11]=len(newinner)
            packet=b.frame.seal(b.f.HEADER.pack(*outer)+newinner+oldmeta['hud'])
            assert len(packet)<=len(input_packet) and len(packet)<=49152
            a,parts,meta,newplanes=rx.receive(packet)
            c,oldparts,_=baseline.receive(input_packet)
            for x,y in zip(a,c,strict=True):np.testing.assert_array_equal(x,y)
            for x,y in zip(parts,oldparts,strict=True):
                assert x['rect']==y['rect'];np.testing.assert_array_equal(x['words'],y['words'])
            assert meta['frame_id']==fid and meta['reference_id']==expected_rid and meta['key']==key
            # Exact source-domain score from the paired CS37 qualification input.
            canvas_raw=b.raw(oldrow['source_canvas_object'],b.ROOT/'experiments/python-game-source-v40-study')
            canvas=np.frombuffer(canvas_raw,np.uint8).reshape(480,720,3).copy()
            original=b.f.f.m.C.corpus.rgb565(canvas).astype(np.uint16)
            assert b.digest(np.ascontiguousarray(original,dtype='<u2').tobytes())==oldrow['source_rgb565_sha256']
            display=b.f.f.n.overlay(b.f.f.m.C.corpus.rgb565(b.f.f.m.ft.planes_to_rgb(a)),tuple(p['words'] for p in parts))
            quality=b.f.f.n.metric(original,display)
            assert quality==oldrow['quality'] and quality['hud_word_errors']==0
            display_sha=b.f.f.n.digest(display)
            row=dict(id=fid,pts=oldrow['pts'],time_base=oldrow['time_base'],timestamp_fraction=oldrow['timestamp_fraction'],
                decoded_order=oldrow['decoded_order'],source_rgb_sha256=oldrow['source_rgb_sha256'],
                source_rgb565_sha256=oldrow['source_rgb565_sha256'],source_yuv_sha256=oldrow['source_yuv_sha256'],
                key=key,reference_id=expected_rid,reference_tag=outer[9].hex(),hud_bytes=len(oldmeta['hud']),
                source_complete_bytes=len(input_packet),packet=b.blob(packet),complete_bytes=len(packet),
                bytes_saved=len(input_packet)-len(packet),cap_headroom=49152-len(packet),new_planes=newplanes,
                attempts=attempts,old_complete_packet=selected[0]['packet'],
                normalized_tag=b.f.m.C.reference_tag(a).hex(),display_sha256=display_sha,quality=quality)
            rows.append(row);last_accepted=fid
            if(fid+1)%24==0:print(json.dumps(dict(scene=oldcase['scene'],frames=fid+1)),flush=True)
        total=sum(r['complete_bytes'] for r in rows);oldtotal=sum(r['source_complete_bytes'] for r in rows)
        summary=dict(frames=len(rows),source_complete_bytes=oldtotal,complete_bytes=total,
            bytes_saved=oldtotal-total,percent_saved=100*(oldtotal-total)/oldtotal,
            maximum_complete_bytes=max(r['complete_bytes'] for r in rows),minimum_cap_headroom=min(r['cap_headroom'] for r in rows),
            fallback_planes=sum(a['selected']==0 for r in rows for a in r['attempts']),
            full_arithmetic_planes=sum(a['selected']==1 for r in rows for a in r['attempts']),
            compact_arithmetic_planes=sum(a['selected']==2 for r in rows for a in r['attempts']),
            arithmetic_candidate_encodes=sum(len(a['trials']) for r in rows for a in r['attempts']),
            mean_candidate_encode_ms=sum(t['encode_ms'] for r in rows for a in r['attempts'] for t in a['trials'])/len(rows),
            total_candidate_encode_ms=sum(t['encode_ms'] for r in rows for a in r['attempts'] for t in a['trials']),
            active_mse=sum(r['quality']['active_squared_error'] for r in rows)/sum(r['quality']['active_channel_samples'] for r in rows),
            key_frames=sum(r['key'] for r in rows))
        cases.append(dict(scene=oldcase['scene'],summary=summary,rows=rows));print(json.dumps(dict(scene=oldcase['scene'],summary=summary)),flush=True)
    assert b.pins()==pins
    result=dict(schema='gamebub-binary-qualification-v40',source_pins_sha256=pins,cases=cases,
      total_frames=sum(len(c['rows']) for c in cases),alternatives=sum(len(r['attempts'])*2 for c in cases for r in c['rows']),
      scope=['All457 actually accepted causal CS37 inputs from the frozen v40 control qualification; exact frame IDs, key24 rule, prior accepted reference IDs and exact HUD are checked.',
       'For each source plane, old CS37 payload plus actually encoded AB38 full and compact alternatives are compared by complete dispatch-payload bytes. Fallback wins ties; all alternatives are archived.',
       'CS38 arithmetic component encoding is timed with CS37 packet preparation externally paid. AB38 decode assertions, packet wrap, causal receiver proof, source loading, quality and archive I/O are outside candidate encode clocks.',
       'CS38 frame proof uses the frozen independent arithmetic decoder/frame adapter and CS37 receiver; no new encoder is used by the offline verifier. No native or FPS result follows.'])
    assert result['total_frames']==457 and result['alternatives']==2742
    (b.HERE/'results.json').write_text(json.dumps(result,separators=(',',':'),allow_nan=False)+'\n')
    print(json.dumps(dict(done=True,frames=result['total_frames'],alternatives=result['alternatives'])),flush=True)
if __name__=='__main__':main()
