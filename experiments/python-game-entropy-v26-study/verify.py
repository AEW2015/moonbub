#!/usr/bin/env python3
"""Offline actual CP26/EC26 replay against frozen v25 packets and sources."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys
import zlib
import numpy as np
import model as e
import protocol as p

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
OLD=HERE.parent/'python-game-capped-key-v25-study'
V24=HERE.parent/'python-game-standard-v24-study'


def load(path):return json.loads(Path(path).read_text())
def digest(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def raw(d,folder=HERE):
    path=Path(d['path']);assert not path.is_absolute() and '..' not in path.parts
    assert 0<d['raw_bytes']<=1000000
    stored=(folder/path).read_bytes();assert hashlib.sha256(stored).hexdigest()==d['stored_sha256']
    dc=zlib.decompressobj();out=dc.decompress(stored,d['raw_bytes']+1)
    assert dc.eof and not dc.unused_data and not dc.unconsumed_tail and len(out)==d['raw_bytes']
    assert hashlib.sha256(out).hexdigest()==d['raw_sha256'];return out


def main():
    data=load(HERE/'results.json');assert data['schema']=='gamebub-entropy-v26'
    for relative,sha in data['source_sha256'].items():
        q=Path(relative);assert not q.is_absolute() and '..' not in q.parts
        assert hashlib.sha256((ROOT/q).read_bytes()).hexdigest()==sha,relative
    old=load(OLD/'results.json');inputs=load(V24/'results.json')['inputs'];pairs=words=0
    for case in data['cases']:
        baseline=next(c for c in old['cases'] if c['scene']==case['scene'] and c['profile']=='capped_key_zero_rdo1')
        source=next(c for c in inputs if c['scene']==case['scene'])
        rx=p.Receiver(epoch=25);oldref=None;totals=oldtotals=sse=samples=0
        assert [r['id'] for r in case['rows']]==list(range(48))
        for r,b,s in zip(case['rows'],baseline['rows'],source['rows']):
            original=raw(b['base_packet'],OLD)
            oldplanes,oldmeta=e.old.decode(original,None if b['key'] else oldref,expected_epoch=25,expected_reference_id=None if b['key'] else b['reference_id'])
            packet=raw(r['packet']);meta=p.parse_pair(packet)
            assert meta['base']==raw(r['base_packet']) and meta['hud']==raw(r['hud_packet'])==raw(b['hud_packet'],OLD)
            out,hud,ack=rx.receive(packet);assert ack==raw(r['ack']);p.validate_ack(ack,packet)
            for a,c in zip(oldplanes,out):np.testing.assert_array_equal(a,c)
            for a,c in zip(oldmeta['coefficients'],e.parse(meta['base'])['coefficients']):np.testing.assert_array_equal(a,c)
            fields=e.HEADER.unpack_from(meta['base']);pos=e.HEADER.size+fields[-5]+fields[-4]
            for plane,(size,coeff) in enumerate(zip(fields[-3:],oldmeta['coefficients'])):
                section=meta['base'][pos:pos+size];pos+=size
                if section[0]==3:
                    encoded=section[1:];flags=e.COEFF.unpack_from(encoded)[2]
                    if flags in (0,1):
                        bw=((720 if plane==0 else 360)+7)//8
                        for expected,actual in zip(coeff,e.iter_block_major(encoded,len(coeff),bw)):np.testing.assert_array_equal(expected,actual)
            bare=e.C.corpus.rgb565(e.ft.planes_to_rgb(out));hybrid=bare.copy()
            sourcewords=np.frombuffer(raw(s['original_rgb565'],V24),'<u2').reshape(480,720)
            for patch in hud:
                x,y,w,h=patch['rect'];np.testing.assert_array_equal(patch['words'],sourcewords[y:y+h,x:x+w]);hybrid[y:y+h,x:x+w]=patch['words'];words+=w*h
            assert digest(bare)==r['bare_rgb565_sha256']==b['bare_rgb565_sha256']
            assert digest(hybrid)==r['hybrid_rgb565_sha256']==b['hybrid_rgb565_sha256']
            error=(e.C.corpus.expand565(hybrid).astype(np.int64)-e.C.corpus.expand565(sourcewords).astype(np.int64))**2
            actual=int(error[37:442].sum());assert actual==r['hybrid']['active_squared_error']==b['hybrid']['active_squared_error']
            assert len(packet)==r['complete_bytes']==len(meta['base'])+len(meta['hud'])+60<=r['old_complete_bytes']<=49152
            assert len(meta['base'])==r['base_bytes'] and len(meta['hud'])==r['hud_bytes']
            sse+=actual;samples+=720*405*3;totals+=len(packet);oldtotals+=r['old_complete_bytes'];pairs+=1;oldref=oldplanes
        summary=case['summary'];assert summary['complete_bytes']==totals and summary['old_complete_bytes']==oldtotals
        assert summary['active_squared_error']==sse and summary['active_channel_samples']==samples
        assert summary['active_mse']==sse/samples and summary['coded_body_Mbps_at30']==totals*5/1e6
    assert pairs==192 and words==4055040
    print(json.dumps(dict(source_pins=len(data['source_sha256']),accepted_pairs=pairs,exact_hud_words=words,
                          exact_coefficients_planes_and_RGB=True,physical_30fps_proven=False)))


if __name__=='__main__':main()
