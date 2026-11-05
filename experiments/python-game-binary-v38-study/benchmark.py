"""Actual CS38 fallback packets and AB38 alternatives on24retained frames."""
import json,time
import numpy as np
import helpers as h
model=h.module('binary38_producer_model',h.HERE/'model.py')
decoder=h.module('binary38_producer_decoder',h.HERE/'decoder.py')
frame_verify=h.module('binary38_frame_proof',h.HERE/'frame_verify.py')

def main():
    pins=h.pins();folder=h.HERE.parent/'python-game-implicit-v37-study';prior=h.load(folder/'results.json');cases=[]
    for oldcase in [c for c in prior['cases'] if c['kind']=='main']:
        rows=[];rx=frame_verify.Receiver();baseline=h.f.Receiver()
        for oldrow in oldcase['rows'][:12]:
            packet=h.raw(oldrow['packet'],folder);parsed=h.f.parse(packet);outer=list(h.f.HEADER.unpack_from(packet))
            inner=packet[h.f.HEADER.size:h.f.HEADER.size+outer[11]];fields=list(h.f.m.HEADER.unpack_from(inner))
            maps=inner[h.f.m.HEADER.size:h.f.m.HEADER.size+fields[12]+fields[13]];payloads=[];attempts=[]
            for axis,(coeff,safe,oldpayload) in enumerate(zip(parsed['coefficients'],h.f.f.safe_blocks(),parsed['plane_payloads'],strict=True)):
                options=[oldpayload];trials=[]
                for compact in (False,True):
                    source=coeff[~safe.reshape(-1)] if compact else coeff;bw=1 if compact else (90 if axis==0 else 45)
                    start=time.perf_counter_ns();encoded,work=model.encode(source,bw);wall=(time.perf_counter_ns()-start)/1e6
                    decoded=decoder.decode(encoded,len(source),bw);np.testing.assert_array_equal(decoded,source)
                    candidate=bytes([6 if compact else 5])+encoded;options.append(candidate)
                    trials.append(dict(compact=compact,packet=h.blob(encoded),payload_bytes=len(candidate),encode_ms=wall,work=work))
                index=min(range(3),key=lambda i:len(options[i]));payloads.append(options[index])
                attempts.append(dict(plane=axis,old_bytes=len(oldpayload),selected=index,selected_bytes=len(payloads[-1]),trials=trials))
            fields[0]=b'GS38';fields[14:17]=map(len,payloads)
            rebuilt=frame_verify.seal(h.f.m.HEADER.pack(*fields)+maps+b''.join(payloads))
            outer[0]=b'CS38';outer[8]=frame_verify.PROFILE;outer[11]=len(rebuilt)
            new=frame_verify.seal(h.f.HEADER.pack(*outer)+rebuilt+parsed['hud'])
            assert len(new)<=len(packet)
            a,parts,meta,newplanes=rx.receive(new);b,oldhud,oldmeta=baseline.receive(packet)
            for x,y in zip(a,b,strict=True):np.testing.assert_array_equal(x,y)
            for x,y in zip(parts,oldhud,strict=True):np.testing.assert_array_equal(x['words'],y['words'])
            rows.append(dict(id=oldrow['id'],packet=h.blob(new),old_packet=oldrow['packet'],complete_bytes=len(new),old_complete_bytes=len(packet),
                             attempts=attempts,new_planes=newplanes,hybrid=oldrow['hybrid'],normalized_tag=oldrow['normalized_tag'],display_sha256=oldrow['display_sha256']))
            print(json.dumps(dict(scene=oldcase['scene'],frame=oldrow['id'],old=len(packet),new=len(new),new_planes=newplanes)),flush=True)
        total=sum(r['complete_bytes'] for r in rows);oldtotal=sum(r['old_complete_bytes'] for r in rows)
        summary=dict(frames=len(rows),complete_bytes=total,old_complete_bytes=oldtotal,percent_saved=100*(oldtotal-total)/oldtotal,
                     new_planes=sum(r['new_planes'] for r in rows),actual_binary_alternatives=6*len(rows),
                     maximum_complete_bytes=max(r['complete_bytes'] for r in rows),
                     mean_all_binary_candidate_encode_ms=sum(t['encode_ms'] for r in rows for a in r['attempts'] for t in a['trials'])/len(rows))
        cases.append(dict(scene=oldcase['scene'],rows=rows,summary=summary));print(json.dumps(summary),flush=True)
    assert h.pins()==pins
    result=dict(schema='gamebub-binary-v38',source_sha256=pins,cases=cases,profile=dict(outer='CS38',inner='GS38',dispatch=[5,6],wrapper_bytes=80,profile_tag=frame_verify.PROFILE.hex()),
                physical_30fps_proven=False,new_RTL_implemented=False,
                scope=['24retained frames in two12frame causal prefixes; actualCS38payloadfallback preserves all coefficients/references/display exactly.',
                       'Adaptiveprobability coding is new syntax; Riceparameters use minimum uncodedRice cost ratherthan an arithmetic-optimal search.',
                       'All6binarycandidate encodes/frame paid and archived, including losers. ExistingCS37 sourceencoding already externallypaid.',
                       'Independentarithmeticdecoder importsnoencoder. Frameproofadapter reencodesdecodedcoefficients in frozenentropy then uses frozenreceiver, so it is not a native receivearchitecture/timing result.',
                       '17x8 probabilityproduct/bit and352Bprobabilitystate describe arithmetic only, not FPGA DSP assignment, cycles, fit or measuredservice.',
                       'No newnativecomparison or hardware; matchedquality standards victory unproved.'])
    (h.HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main()
