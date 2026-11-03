#!/usr/bin/env python3
"""Verify fixture bytes, decode GM01 through bounded GF01 and compare outputs."""
import hashlib
import json
from pathlib import Path
import struct
import sys

import numpy as np
import chunks
from harness import codec,decode_complete

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'python-codec-study'))
import corpus


def main():
    directory=HERE/'fixtures';manifest=json.loads((directory/'manifest.json').read_text())
    for name,row in manifest['files'].items():
        data=(directory/name).read_bytes()
        assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256'],name
    epoch=None;rx=None;ingress=None;now=0;decoded=0
    for case in manifest['cases']:
        if case['epoch']!=epoch:
            if ingress is not None:assert not ingress.pending
            epoch=case['epoch'];rx=codec.Receiver(epoch);ingress=chunks.Reassembler(epoch)
        frame=case['frame_id'];packet=(directory/case['packet']).read_bytes()
        raw=(directory/case['packed_datagrams']).read_bytes();position=0;wire=[]
        while position<len(raw):
            length=struct.unpack_from('!H',raw,position)[0];position+=2
            wire.append(raw[position:position+length]);position+=length
        assert position==len(raw) and len(wire)==case['datagrams']
        complete=None
        for part in reversed(wire):
            now+=1;complete=ingress.feed(part,now)
        assert complete is not None and complete.data==packet
        actual,info=decode_complete(complete,ingress,rx)
        assert info['frame_id']==frame and info['anchor_id']==case['anchor_id']
        assert corpus.rgb565(actual).astype('<u2').tobytes()==(directory/case['rgb565']).read_bytes()
        assert hashlib.sha256(actual.tobytes()).hexdigest()==case['decoded_rgb_sha256']
        parsed=codec.parse(packet,epoch)
        assert parsed['scale_map'].tobytes()==(directory/case['map']).read_bytes()
        for c,name,shape in zip(parsed['coefficients'],case['coefficients'],case['coefficient_shapes']):
            assert list(c.shape)==shape and c.astype('<i2').tobytes()==(directory/name).read_bytes()
        assert not ingress.pending;decoded+=1
    print(json.dumps({'golden_frames_decoded':decoded,'fixture_files_verified':len(manifest['files']),
                      'all_decoded_outputs_exact':True,'all_resources_drained':not ingress.pending,
                      'scope':'Functional in-process replay, no physical or real-time test'},indent=2))


if __name__=='__main__':main()
