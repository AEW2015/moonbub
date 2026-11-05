"""Extend frozen AB38/CS38 exact coding to both complete48-frame histories."""
import json,time
import numpy as np
import bridge as b
encoder=b.old.module('binary_full39_frozen_encoder',b.BASE/'model.py')

def main():
    pins=b.pins();sourcefolder=b.HERE.parent/'python-game-implicit-v37-study';prior=b.load(sourcefolder/'results.json');cases=[]
    for oldcase in [c for c in prior['cases'] if c['kind']=='main']:
        rows=[];rx=b.frame.Receiver();baseline=b.f.Receiver()
        for oldrow in oldcase['rows']:
            original=b.raw(oldrow['packet'],sourcefolder);meta=b.f.parse(original)
            outer=list(b.f.HEADER.unpack_from(original));inner=original[b.f.HEADER.size:b.f.HEADER.size+outer[11]]
            fields=list(b.f.m.HEADER.unpack_from(inner));maps=inner[b.f.m.HEADER.size:b.f.m.HEADER.size+fields[12]+fields[13]]
            payloads=[];attempts=[]
            for axis,(coeff,safe,previous) in enumerate(zip(meta['coefficients'],b.f.f.safe_blocks(),meta['plane_payloads'],strict=True)):
                options=[previous];trials=[]
                for compact in (False,True):
                    source=coeff[~safe.reshape(-1)] if compact else coeff;bw=1 if compact else(90 if axis==0 else 45)
                    start=time.perf_counter_ns();encoded,work=encoder.encode(source,bw);wall=(time.perf_counter_ns()-start)/1e6
                    np.testing.assert_array_equal(b.decoder.decode(encoded,len(source),bw),source)
                    candidate=bytes([6 if compact else 5])+encoded;options.append(candidate)
                    trials.append(dict(compact=compact,packet=b.blob(encoded),payload_bytes=len(candidate),encode_ms=wall,work=work))
                choice=min(range(3),key=lambda i:len(options[i]));payloads.append(options[choice])
                attempts.append(dict(plane=axis,old_bytes=len(previous),selected=choice,selected_bytes=len(payloads[-1]),trials=trials))
            fields[0]=b'GS38';fields[14:17]=map(len,payloads)
            newinner=b.frame.seal(b.f.m.HEADER.pack(*fields)+maps+b''.join(payloads))
            outer[0]=b'CS38';outer[8]=b.frame.PROFILE;outer[11]=len(newinner)
            packet=b.frame.seal(b.f.HEADER.pack(*outer)+newinner+meta['hud']);assert len(packet)<=len(original)
            a,parts,_,count=rx.receive(packet);c,oldparts,_=baseline.receive(original)
            for x,y in zip(a,c,strict=True):np.testing.assert_array_equal(x,y)
            for x,y in zip(parts,oldparts,strict=True):np.testing.assert_array_equal(x['words'],y['words'])
            rows.append(dict(id=oldrow['id'],packet=b.blob(packet),complete_bytes=len(packet),old_complete_bytes=len(original),
                             attempts=attempts,new_planes=count,hybrid=oldrow['hybrid'],normalized_tag=oldrow['normalized_tag'],display_sha256=oldrow['display_sha256']))
            if(oldrow['id']+1)%12==0:print(json.dumps(dict(scene=oldcase['scene'],frames=oldrow['id']+1)),flush=True)
        total=sum(r['complete_bytes'] for r in rows);previous=sum(r['old_complete_bytes'] for r in rows)
        summary=dict(frames=48,complete_bytes=total,old_complete_bytes=previous,percent_saved=100*(previous-total)/previous,
                     maximum_complete_bytes=max(r['complete_bytes'] for r in rows),new_planes=sum(r['new_planes'] for r in rows),
                     active_mse=sum(r['hybrid']['active_squared_error'] for r in rows)/sum(r['hybrid']['active_channel_samples'] for r in rows),
                     nominal_Mbps_at30=total*240/48/1e6,
                     mean_all_binary_candidate_encode_ms=sum(t['encode_ms'] for r in rows for a in r['attempts'] for t in a['trials'])/48)
        cases.append(dict(scene=oldcase['scene'],rows=rows,summary=summary));print(json.dumps(summary),flush=True)
    assert b.pins()==pins
    result=dict(schema='gamebub-binary-full-v39',source_sha256=pins,cases=cases,physical_30fps_proven=False,new_RTL_implemented=False,
                scope=['FrozenAB38/CS38syntax/code extendsfrom12to48frames/perscene, including actual key24 and fullcausal references. No retuning.',
                       '96actualframepackets and576full/compactarithmetic alternatives,oldpayloadfallbacktiespaidandretained.',
                       'InputCS37encodingexternallypaid; candidateencodeclocks only, proofadapter reencodesfrozenentropy, notoptimizednativepipeline.',
                       'Same two reusedclips; fulltemporalqualification is notheldoutsource evidence or standards/hardwarevictory.'])
    (b.HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
