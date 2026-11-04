#!/usr/bin/env python3
"""Retained exact source-word replay, full ACK binding and atomic CRC negatives."""
from pathlib import Path
import hashlib,json,zlib
import numpy as np
import model as m
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def raw(desc):
    p=Path(desc['path'])
    assert not p.is_absolute()and'..'not in p.parts
    data=(HERE/p).read_bytes();assert hashlib.sha256(data).hexdigest()==desc['stored_sha256']
    dec=zlib.decompressobj();out=dec.decompress(data,desc['raw_bytes']+1)
    assert dec.eof and not dec.unused_data and not dec.unconsumed_tail and len(out)==desc['raw_bytes']
    assert hashlib.sha256(out).hexdigest()==desc['raw_sha256'];return out

def main():
    d=json.loads((HERE/'results.json').read_text());assert d['schema']=='gamebub-hud-cache-v21'
    for p,h in d['source_sha256'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
    n=words=negatives=0
    for c in d['cases']:
        rx=m.Receiver();sumlegacy=sumside=sumack=0
        for row in c['rows']:
            packet=raw(row['packet']);ack=raw(row['ack']);before=(rx.last_frame,rx.last_generation,rx.last_bodytag)
            corrupt=packet[:-1]+bytes([packet[-1]^1])
            try:rx.receive(corrupt)
            except ValueError:pass
            else:raise AssertionError('badCRCaccepted')
            assert before==(rx.last_frame,rx.last_generation,rx.last_bodytag);negatives+=1
            assert rx.receive(packet)==ack and rx.receive(packet)==ack
            a=m.parse_ack(ack);meta=m.parse(packet)
            assert a=={k:meta[k]for k in a}
            for patch,rect,desc in zip(rx.display['patches'],m.RECTANGLES,row['original_patches']):
                expected=np.frombuffer(raw(desc),dtype='<u2').reshape(rect[3],rect[2]);np.testing.assert_array_equal(patch,expected);words+=patch.size
            assert row['exact_word_errors']==0 and row['exact_words']==21120
            assert len(packet)==row['sidecar_bytes']and len(ack)==row['ack_bytes']and len(packet)<=49152
            assert len(rx.banks)==2 and not any(rx.readers)
            sumlegacy+=row['legacy_patch_bytes'];sumside+=len(packet);sumack+=len(ack);n+=1
            if 'v20_complete_packet_bytes'in row:
                assert row['source_sha256']==row['v20_input_sha256']
                assert row['accounting_only_replaced_total']==row['v20_complete_packet_bytes']-row['legacy_patch_bytes']+len(packet)
        assert c['summary']['legacy_patch_bytes']==sumlegacy and c['summary']['sidecar_bytes']==sumside and c['summary']['ack_bytes']==sumack
        assert c['summary']['exact_words']==21120*len(c['rows'])
    assert n==132 and words==n*21120
    print(json.dumps(dict(decisions=n,exact_words=words,atomic_crc_negative_rejections=negatives,source_pins=len(d['source_sha256']),physical_30fps_proven=False),indent=2))
if __name__=='__main__':main()
