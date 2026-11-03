#!/usr/bin/env python3
"""Actual GF02/GA01 functional replay with frozen GM01 golden payloads."""
import hashlib
import json
from pathlib import Path
import struct
import sys
import zlib
import numpy as np
import transport as t
from delivery import codec,decode_completed

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
GOLD=HERE.parent/'python-game-link-study/fixtures'
sys.path.insert(0,str(HERE.parent/'python-codec-study'))
import corpus


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def ingest(data,epoch,frame,ingress,now,*,reverse=True,duplicate=True):
    chunks=t.datagrams(data,epoch,frame);order=list(reversed(chunks)) if reverse else chunks
    done=None;duplicate_count=0
    for index,part in enumerate(order):
        now+=1;done=ingress.feed(part,now)
        if duplicate and index==0 and done is None:
            now+=1;assert ingress.feed(part,now) is None;duplicate_count+=1
    return done,chunks,now,duplicate_count


def main():
    sources=[HERE/'benchmark.py',HERE/'transport.py',HERE/'delivery.py',Path(codec.__file__),
             Path(codec.roi.__file__),Path(codec.mt.__file__),Path(codec.ft.__file__),
             Path(codec.word_coeff.__file__),Path(codec.word_coeff.frozen_codec.__file__),Path(corpus.__file__)]
    hashes={str(p):digest(p) for p in sources};manifest=json.loads((GOLD/'manifest.json').read_text())
    epoch=None;ingress=None;receiver=None;now=0;records=[]
    for case in manifest['cases']:
        if case['epoch']!=epoch:
            if ingress is not None:assert not ingress.pending
            epoch=case['epoch'];ingress=t.Reassembler(epoch);receiver=codec.Receiver(epoch)
        packet=(GOLD/case['packet']).read_bytes();before=receiver.last_frame_id
        done,wire,now,duplicates=ingest(packet,epoch,case['frame_id'],ingress,now)
        assert done is not None and receiver.last_frame_id==before
        rgb,info,feedback,error=decode_completed(done,ingress,receiver)
        assert error is None
        assert corpus.rgb565(rgb).astype('<u2').tobytes()==(GOLD/case['rgb565']).read_bytes()
        decoded=t.parse_feedback(feedback)
        assert decoded.status==t.ACK and t.matches_feedback(decoded,epoch,case['frame_id'],t.content_crc(packet))
        assert not t.matches_feedback(decoded,epoch+1,case['frame_id'],t.content_crc(packet))
        assert not t.matches_feedback(decoded,epoch,case['frame_id']+1,t.content_crc(packet))
        assert not ingress.pending
        records.append({'name':case['name'],'epoch':epoch,'frame':case['frame_id'],
                        'packet_sha256':hashlib.sha256(packet).hexdigest(),'packet_bytes':len(packet),
                        'whole_crc':zlib.crc32(packet),'body_tag':t.content_crc(packet),
                        'chunks':len(wire),'duplicate_chunks':duplicates,'chunk_header_bytes':t.HEADER.size,
                        'unique_forward_ipv4_udp_bytes':sum(len(p)+28 for p in wire),
                        'duplicate_forward_ipv4_udp_bytes':duplicates*(len(wire[-1])+28),
                        'feedback_bytes':len(feedback),'reverse_ipv4_udp_bytes':len(feedback)+28,
                        'decode_anchor_id':info['anchor_id'],'feedback_matches_content':True,
                        'decoded_rgb565_exact':True,'payload_bytes_after_decode':ingress.payload_bytes()})
    packet=(GOLD/manifest['cases'][0]['packet']).read_bytes();faults=[]
    # Regression: a metadata/duplicate fault must not release a delivered reader.
    r=t.Reassembler();rx=codec.Receiver();done,wire,clock,_=ingest(packet,1,0,r,0)
    held=r.payload_bytes();fields=list(t.HEADER.unpack_from(wire[0]));fields[-1]^=1
    errors=(t.HEADER.pack(*fields)+wire[0][t.HEADER.size:],wire[0][:-1]+bytes([wire[0][-1]^1]))
    for bad in errors:
        clock+=1
        try:r.feed(bad,clock)
        except ValueError:pass
        else:raise AssertionError('conflict accepted')
        assert r.payload_bytes()==held and r.pending[0]['complete'] is done
    rgb,info,feedback,error=decode_completed(done,r,rx)
    assert error is None and not r.pending
    faults.append({'kind':'delivered_conflicting_metadata_and_duplicate','pin_bytes_before':held,
                   'pin_bytes_after_each_conflict':held,'decoded_after_conflicts':True,'drained':not r.pending})
    # A missing fragment expires partial assembly and can produce a bound NACK.
    r=t.Reassembler(timeout_ms=10);rx=codec.Receiver();wire=t.datagrams(packet,1,0)
    r.feed(wire[0],0);expired=r.expire(10)
    feedback=t.feedback_datagram(1,0,t.NACK,t.content_crc(packet),3)
    f=t.parse_feedback(feedback)
    assert expired==[0] and not r.pending and rx.last_frame_id==-1 and f.status==t.NACK
    assert t.matches_feedback(f,1,0,t.content_crc(packet))
    faults.append({'kind':'missing_chunk_timeout','codec_last_frame':rx.last_frame_id,'nack_bytes':len(feedback),'drained':not r.pending})
    # Bad inner GM01 CRC may pass newly recomputed GF02 wrapping; no ACK/reference.
    damaged=packet[:-1]+bytes([packet[-1]^1]);r=t.Reassembler();rx=codec.Receiver()
    done,_,_,_=ingest(damaged,1,0,r,0)
    rgb,info,feedback,error=decode_completed(done,r,rx)
    assert error is not None and t.parse_feedback(feedback).status==t.NACK
    assert rx.last_frame_id==-1 and not r.pending
    faults.append({'kind':'valid_outer_bad_inner_crc','codec_last_frame':rx.last_frame_id,'nack_bytes':len(feedback),'drained':not r.pending})
    assert hashes=={str(p):digest(p) for p in sources},'source changed'
    result={'evidence':'Actual new GF02 chunks and GA01 feedback over frozen GM01 golden data; in-process functional, not network/hardware timing',
            'source_sha256':hashes,'golden_manifest_sha256':digest(GOLD/'manifest.json'),
            'records':records,'faults':faults,'forward_header_bytes':t.HEADER.size,'feedback_bytes':t.FEEDBACK_SIZE,
            'forward_ipv4_udp_overhead_per_chunk':t.HEADER.size+28,'reverse_ipv4_udp_overhead_per_feedback':t.FEEDBACK_SIZE+28,
            'logical_payload_capacity':2*49152,'all_resources_drained':all(f['drained'] for f in faults),
            'crc_residue_observation':{'distinct_valid_full_frame_crcs':len({r['whole_crc'] for r in records}),
                                       'distinct_body_tags':len({r['body_tag'] for r in records})},
            'scope':'Monotonic integer test events are ordering labels, not measured latency. Decode completion precedes ACK creation; sender ACK state/finite services are tested in the pipeline study. No auth/capability negotiation/firmware support.'}
    (HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'golden_decodes':len(records),'fault_campaigns':len(faults),'header_bytes':t.HEADER.size,
                      'feedback_bytes':t.FEEDBACK_SIZE,'all_resources_drained':result['all_resources_drained'],
                      'distinct_full_crc_values':result['crc_residue_observation']['distinct_valid_full_frame_crcs'],
                      'distinct_body_tags':result['crc_residue_observation']['distinct_body_tags']},indent=2))


if __name__=='__main__':main()
