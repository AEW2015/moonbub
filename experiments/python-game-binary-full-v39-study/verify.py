"""Full96-frame arithmetic causal replay; only frozen decoder imported."""
import sys
from pathlib import Path
import numpy as np
import bridge as b

def main():
    assert not any(Path(getattr(v,'__file__','')).resolve()==b.BASE/'model.py' for v in list(sys.modules.values()) if getattr(v,'__file__',None))
    data=b.load(b.HERE/'results.json')
    for p,h in data['source_sha256'].items():assert b.sha(b.ROOT/p)==h,p
    folder=b.HERE.parent/'python-game-implicit-v37-study';old=b.load(folder/'results.json');frames=alternatives=0
    for case in data['cases']:
        source=next(c for c in old['cases'] if c['kind']=='main'and c['scene']==case['scene'])
        assert [r['id'] for r in case['rows']]==list(range(48));rx=b.frame.Receiver();control=b.f.Receiver()
        for row,prior in zip(case['rows'],source['rows'],strict=True):
            original=b.raw(prior['packet'],folder);oldmeta=b.f.parse(original);packet=b.raw(row['packet'])
            outer=b.frame.HEADER.unpack_from(packet);inner=packet[b.frame.HEADER.size:b.frame.HEADER.size+outer[11]]
            fields=b.f.m.HEADER.unpack_from(inner);position=b.f.m.HEADER.size+fields[12]+fields[13]
            for axis,(coeff,safe,previous,attempt,size)in enumerate(zip(oldmeta['coefficients'],b.f.f.safe_blocks(),oldmeta['plane_payloads'],row['attempts'],fields[14:17],strict=True)):
                options=[previous]
                for compact,trial in zip((False,True),attempt['trials'],strict=True):
                    expected=coeff[~safe.reshape(-1)] if compact else coeff;bw=1 if compact else(90 if axis==0 else 45)
                    raw=b.raw(trial['packet']);np.testing.assert_array_equal(b.decoder.decode(raw,len(expected),bw),expected)
                    candidate=bytes([6 if compact else 5])+raw;assert len(candidate)==trial['payload_bytes'];options.append(candidate);alternatives+=1
                selected=min(range(3),key=lambda i:len(options[i]));assert attempt['selected']==selected
                assert inner[position:position+size]==options[selected];position+=size
            assert position==len(inner)-4
            a,hud,_,_=rx.receive(packet);c,oldhud,_=control.receive(original)
            for x,y in zip(a,c,strict=True):np.testing.assert_array_equal(x,y)
            for x,y in zip(hud,oldhud,strict=True):np.testing.assert_array_equal(x['words'],y['words'])
            display=b.f.f.n.overlay(b.f.m.C.corpus.rgb565(b.f.m.ft.planes_to_rgb(a)),tuple(p['words'] for p in hud))
            assert b.f.f.n.digest(display)==row['display_sha256']==prior['display_sha256']
            assert b.f.m.C.reference_tag(a).hex()==row['normalized_tag']==prior['normalized_tag']
            assert len(packet)==row['complete_bytes']<=row['old_complete_bytes']==len(original);frames+=1
        assert sum(r['complete_bytes'] for r in case['rows'])==case['summary']['complete_bytes']
    assert frames==96 and alternatives==576
    print(__import__('json').dumps(dict(exact_causal_frames=frames,arithmetic_alternatives=alternatives,key24_qualified=True,new_encoder_imported=False,physical_30fps_proven=False)))
if __name__=='__main__':main()
