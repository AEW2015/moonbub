#!/usr/bin/env python3
"""Independent replay of every AB38 alternative and selected causal CS38 frame."""
import json,sys
from pathlib import Path
import numpy as np
import bridge as b

def main():
    result=b.load(b.HERE/'results.json');control=b.load(b.CONTROL/'results.json')
    sourcefolder=b.ROOT/'experiments/python-game-source-v40-study'
    for path,want in result['source_pins_sha256'].items():assert b.sha(b.ROOT/path)==want,path
    assert not any(Path(getattr(m,'__file__','')).resolve()==b.BASE/'model.py'
                   for m in sys.modules.values() if getattr(m,'__file__',None))
    assert result['total_frames']==457 and result['alternatives']==2742
    frames=alternatives=selected_new=0
    for case,control_case in zip(result['cases'],control['cases'],strict=True):
        assert case['scene']==control_case['scene']
        assert [r['id'] for r in case['rows']]==list(range(len(control_case['rows'])))
        rx=b.frame.Receiver();oldrx=b.f.Receiver();last_accepted=None
        for row,source_row in zip(case['rows'],control_case['rows'],strict=True):
            assert source_row['accepted'] is True
            original=b.raw(source_row['attempts'][0]['packet'],b.CONTROL)
            oldmeta=b.f.parse(original);fid=row['id'];key=(fid%24==0 or last_accepted is None)
            rid=b.f.m.NO_REF if key else last_accepted
            assert row['key']==key and row['reference_id']==rid
            assert oldmeta['frame_id']==fid and oldmeta['key']==key and oldmeta['reference_id']==rid
            assert row['source_rgb_sha256']==source_row['source_rgb_sha256']
            assert row['source_rgb565_sha256']==source_row['source_rgb565_sha256']
            packet=b.raw(row['packet']);assert len(packet)==row['complete_bytes']<=49152
            assert row['complete_bytes']<=row['source_complete_bytes']
            outer=list(b.f.HEADER.unpack_from(packet))
            assert outer[0]==b'CS38' and outer[3]==25 and outer[4]==fid and outer[5]==rid
            assert outer[11]+outer[12]+b.f.HEADER.size+4==len(packet)
            inner=packet[b.f.HEADER.size:b.f.HEADER.size+outer[11]]
            assert b.f.m.HEADER.unpack_from(inner)[0]==b'GS38'
            inner_fields=list(b.f.m.HEADER.unpack_from(inner))
            pos=b.f.m.HEADER.size+inner_fields[12]+inner_fields[13]
            payload_sizes=inner_fields[14:17]
            actual_payloads=[]
            for axis,(coeff,safe,previous,record,size) in enumerate(zip(oldmeta['coefficients'],b.f.f.safe_blocks(),
                    oldmeta['plane_payloads'],row['attempts'],payload_sizes,strict=True)):
                assert record['plane']==axis and len(record['trials'])==2
                options=[previous]
                for compact,trial in zip((False,True),record['trials'],strict=True):
                    encoded=b.raw(trial['packet']);expected=coeff[~safe.reshape(-1)] if compact else coeff
                    width=1 if compact else(90 if axis==0 else 45)
                    np.testing.assert_array_equal(b.decoder.decode(encoded,len(expected),width),expected)
                    candidate=bytes([6 if compact else 5])+encoded
                    assert len(candidate)==trial['payload_bytes'];options.append(candidate);alternatives+=1
                winner=min(range(3),key=lambda i:len(options[i]))
                assert record['selected']==winner
                actual=inner[pos:pos+size];assert actual==options[winner]
                assert len(actual)==record['selected_bytes'];actual_payloads.append(actual);pos+=size
                selected_new+=winner!=0
            assert pos==len(inner)-4
            assert len(actual_payloads)==3
            newplanes=inner_fields[14:17]
            got,parts,meta,count=rx.receive(packet)
            base,oldparts,oldmeta=b.f.Receiver.receive(oldrx,original)
            assert count==selected_new_count(actual_payloads)
            assert meta['frame_id']==fid and meta['reference_id']==rid and meta['key']==key
            for x,y in zip(got,base,strict=True):np.testing.assert_array_equal(x,y)
            for x,y in zip(parts,oldparts,strict=True):
                assert x['rect']==y['rect'];np.testing.assert_array_equal(x['words'],y['words'])
            assert sum(p['words'].size for p in parts)==21120 and len(parts)==4
            canvas=np.frombuffer(b.raw(source_row['source_canvas_object'],sourcefolder),np.uint8).reshape(480,720,3).copy()
            original_rgb565=b.f.f.m.C.corpus.rgb565(canvas).astype(np.uint16)
            assert b.digest(np.ascontiguousarray(original_rgb565,dtype='<u2').tobytes())==row['source_rgb565_sha256']
            display=b.f.f.n.overlay(b.f.f.m.C.corpus.rgb565(b.f.f.m.ft.planes_to_rgb(got)),tuple(p['words']for p in parts))
            quality=b.f.f.n.metric(original_rgb565,display)
            assert quality==row['quality']==source_row['quality'] and quality['hud_word_errors']==0
            display_hash=b.f.f.n.digest(display)
            old_display=b.f.f.n.overlay(b.f.f.m.C.corpus.rgb565(b.f.f.m.ft.planes_to_rgb(base)),tuple(p['words']for p in oldparts))
            old_display_hash=b.f.f.n.digest(old_display)
            assert display_hash==row['display_sha256']==old_display_hash
            tag=b.f.m.C.reference_tag(got).hex()
            assert tag==row['normalized_tag']==source_row['normalized_tag']
            last_accepted=fid;frames+=1
        total=sum(r['complete_bytes'] for r in case['rows']);oldtotal=sum(r['source_complete_bytes'] for r in case['rows'])
        assert total==case['summary']['complete_bytes'] and oldtotal==case['summary']['source_complete_bytes']
        assert max(r['complete_bytes'] for r in case['rows'])==case['summary']['maximum_complete_bytes']
        assert min(r['cap_headroom'] for r in case['rows'])==case['summary']['minimum_cap_headroom']
    assert frames==457 and alternatives==2742
    print(json.dumps(dict(causal_cs38_frames=frames,independent_ab38_alternatives=alternatives,
       selected_arithmetic_planes=selected_new,old_cs37_tie_fallbacks=457*3-selected_new,
       source_quality_hud_refs_and_display_exact=True,new_encoder_imported=False)))
def selected_new_count(payloads):return sum(p[0] in (5,6) for p in payloads)
if __name__=='__main__':main()
