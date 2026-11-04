#!/usr/bin/env python3
"""Read-only verification of retained acknowledged-reference evidence."""
import hashlib
import json
from pathlib import Path
import statistics

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent


def main():
    result=json.loads((HERE/'results.json').read_text())
    for original,expected in result['source_sha256'].items():
        marker='/moonbub-30fps-study/'
        path=ROOT/original.split(marker,1)[1] if marker in original else Path(original)
        assert hashlib.sha256(path.read_bytes()).hexdigest()==expected,original
    attempts=decoded=promotions=0;native_ids=0
    for scene in result['scenes']:
        manifest=scene['manifest'];n=manifest['frame_count']
        if scene['cohort']!='synthetic':native_ids+=n
        for profile,rows in scene['profiles'].items():
            assert [r['id'] for r in rows]==list(range(n))
            assert [r['input_sha256'] for r in rows]==manifest['frame_sha256']
            banks={'0':None,'1':None};admitted=[]
            for row in rows:
                attempts+=1
                assert row['prepare_ms']>0
                assert row['accepted']==(row['attempted_bytes']<=49152)
                if not row['accepted']:
                    assert row['pending_after_prepare']==0
                    if profile!='gm_immutable':assert row['acknowledged_banks']==banks
                    continue
                decoded+=1;admitted.append(row)
                assert row['decoded_rgb_sha256']==row['expected_rgb_sha256']
                assert row['packet_bytes']==row['attempted_bytes'] and row['packet_bytes']<=49152
                assert row['pending_after_feedback']==0
                assert abs(row['complete_service_ms']-(row['prepare_ms']+row['receive_ms']+row['feedback_ms']))<1e-9
                if profile!='gm_immutable':
                    assert row['same_reconstructed_banks']
                    info=row['encoder_info'];ri=row['receiver_info']
                    assert info['envelope_bytes']==60 and row['packet_bytes']==info['inner_bytes']+60
                    assert info['reference_read_array_bytes']==2*info['reference_read_bytes']
                    assert info['reconstruction_write_array_bytes']==2*info['reconstruction_write_bytes']
                    assert ri['reference_read_array_bytes']==2*ri['reference_read_bytes']
                    assert ri['reconstruction_write_array_bytes']==2*ri['reconstruction_write_bytes']
                    assert info['promotion_reconstruction_paid']==(row['key'] or row['promoted'])
                    if row['key']:
                        assert row['reference_bank']==255 and row['reference_id'] is None
                        banks={'0':dict(frame_id=row['id'],tag=row['stored_tag']),'1':None}
                    else:
                        slot='1' if banks['1'] is not None else '0'
                        assert row['reference_bank']==int(slot)
                        assert row['reference_id']==banks[slot]['frame_id']
                        assert row['reference_tag']==banks[slot]['tag']
                        if row['promoted']:
                            promotions+=1
                            assert row['destination_bank']==1
                            banks['1']=dict(frame_id=row['id'],tag=row['stored_tag'])
                        else:assert row['destination_bank']==255
                    assert row['acknowledged_banks']==banks
            summary=scene['summary'][profile]
            assert summary['attempts']==len(rows) and summary['admitted']==len(admitted)
            assert summary['rejected']==len(rows)-len(admitted)
            assert abs(summary['prepare_ms_all']['mean']-statistics.mean(r['prepare_ms'] for r in rows))<1e-9
            assert abs(summary['packet_bytes']['mean']-statistics.mean(r['packet_bytes'] for r in admitted))<1e-9
            if profile!='gm_immutable':
                assert summary['memory']['encoder_peak_retained_banks']<=2
                assert summary['memory']['receiver_peak_retained_banks']<=2
        for pair in scene['comparisons']:
            assert pair['gm_inner_equal'] and pair['immutable_pixels_equal'] and pair['envelope_bytes']==60
    assert native_ids==result['native_source_ids']==300
    assert attempts==result['attempted_packets']==924
    assert decoded==result['decoded_packets']
    print(json.dumps(dict(source_ids=native_ids,attempts=attempts,decoded=decoded,promotions=promotions,
                          source_bindings=len(result['source_sha256']),retained_banks_max=2,
                          scope='Immediatefeedbackalgorithm/referenceproof;nohardwareorfinitecadenceclaim'),indent=2))


if __name__=='__main__':main()
