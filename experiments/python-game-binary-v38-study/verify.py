"""Independent AB38 alternatives and CS38 causal replay; no encoder import."""
import struct
import numpy as np
import helpers as h
decoder=h.module('binary38_verify_arithmetic',h.HERE/'decoder.py')
frame=h.module('binary38_verify_frames',h.HERE/'frame_verify.py')

def main():
    from pathlib import Path
    import sys
    assert not any(Path(getattr(value,'__file__','')).resolve()==h.HERE/'model.py' for value in list(sys.modules.values()) if getattr(value,'__file__',None)), 'new encoder imported'
    data=h.load(h.HERE/'results.json')
    for path,tag in data['source_sha256'].items():assert h.sha(h.ROOT/path)==tag,path
    sourcefolder=h.HERE.parent/'python-game-implicit-v37-study';source=h.load(sourcefolder/'results.json')
    frames=alternatives=selected=0;products=renorm=0
    for case in data['cases']:
        oldcase=next(c for c in source['cases'] if c['kind']=='main' and c['scene']==case['scene'])
        assert [r['id'] for r in case['rows']]==list(range(12))
        rx=frame.Receiver();control=h.f.Receiver()
        for row,prior in zip(case['rows'],oldcase['rows'][:12],strict=True):
            original=h.raw(prior['packet'],sourcefolder);meta=h.f.parse(original)
            packet=h.raw(row['packet']);fields=frame.HEADER.unpack_from(packet)
            inner=packet[frame.HEADER.size:frame.HEADER.size+fields[11]];base=list(h.f.m.HEADER.unpack_from(inner))
            pos=h.f.m.HEADER.size+base[12]+base[13];expected_payloads=[]
            for axis,(coeff,safe,oldpayload,attempt,size) in enumerate(zip(meta['coefficients'],h.f.f.safe_blocks(),meta['plane_payloads'],row['attempts'],base[14:17],strict=True)):
                options=[oldpayload];assert attempt['plane']==axis and len(attempt['trials'])==2
                for compact,trial in zip((False,True),attempt['trials'],strict=True):
                    assert trial['compact']==compact
                    sourcecoeff=coeff[~safe.reshape(-1)] if compact else coeff;bw=1 if compact else (90 if axis==0 else 45)
                    raw=h.raw(trial['packet']);decoded=decoder.decode(raw,len(sourcecoeff),bw)
                    np.testing.assert_array_equal(decoded,sourcecoeff)
                    candidate=bytes([6 if compact else 5])+raw;assert len(candidate)==trial['payload_bytes'];options.append(candidate)
                    header=decoder.FRAME.unpack_from(raw)
                    if header[2]==0:
                        lengths=header[6:10];p=decoder.FRAME.size
                        for length,work in zip(lengths,trial['work']['streams'],strict=True):
                            k0,k1,bits=struct.unpack_from('<BBI',raw,p);p+=length
                            assert work['renorm_steps']==bits-18
                            assert work['probability_products']==work['binary_decisions']
                            assert 0<=work['max_renorm_per_bit']<=16
                            products+=work['probability_products'];renorm+=work['renorm_steps']
                    alternatives+=1
                winner=min(range(3),key=lambda i:len(options[i]));assert winner==attempt['selected']
                assert inner[pos:pos+size]==options[winner];pos+=size;expected_payloads.append(options[winner])
                assert attempt['selected_bytes']==len(options[winner])<=attempt['old_bytes']==len(oldpayload)
                selected+=winner!=0
            assert pos==len(inner)-4
            a,parts,meta,newplanes=rx.receive(packet);b,oldparts,_=control.receive(original)
            for x,y in zip(a,b,strict=True):np.testing.assert_array_equal(x,y)
            for x,y in zip(parts,oldparts,strict=True):np.testing.assert_array_equal(x['words'],y['words'])
            display=h.f.f.n.overlay(h.f.m.C.corpus.rgb565(h.f.m.ft.planes_to_rgb(a)),tuple(p['words'] for p in parts))
            assert h.f.f.n.digest(display)==row['display_sha256']==prior['display_sha256']
            assert h.f.m.C.reference_tag(a).hex()==row['normalized_tag']==prior['normalized_tag']
            assert len(packet)==row['complete_bytes']<=row['old_complete_bytes']==len(original)
            frames+=1
        assert sum(r['complete_bytes'] for r in case['rows'])==case['summary']['complete_bytes']
        assert sum(r['old_complete_bytes'] for r in case['rows'])==case['summary']['old_complete_bytes']
    assert frames==24 and alternatives==144
    print(__import__('json').dumps(dict(exact_causal_frames=frames,arithmetic_alternatives=alternatives,selected_binary_planes=selected,
          trial_probability_products=products,trial_renorm_steps=renorm,new_encoder_imported=False,new_RTL_implemented=False,physical_30fps_proven=False)))

if __name__=='__main__':main()
