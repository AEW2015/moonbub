#!/usr/bin/env python3
"""Verify stored HUD packet/area accounting and source bindings; no encoding."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent


def resolve(path):
    marker='/moonbub-30fps-study/'
    return ROOT/path.split(marker,1)[1] if marker in path else Path(path)


def main():
    doc=json.loads((HERE/'results.json').read_text())
    for path,expected in doc['source_sha256'].items():assert hashlib.sha256(resolve(path).read_bytes()).hexdigest()==expected,path
    assert doc['source_inputs']==len(doc['scenes'])==18
    records=wrapped=patches=over=0
    for scene in doc['scenes']:
        assert scene['input_sha256']==scene['manifest']['frame_sha256'][scene['source_index']]
        rows=scene['profiles']
        for label,row in rows.items():
            assert row['over_48k_cap']==(row['bytes']>49152)
            a,b=row['metrics']['roi'],row['metrics']['background'];active=row['metrics']['active']
            assert a['pixels']+b['pixels']==active['pixels']
            assert abs((a['mse']*a['pixels']+b['mse']*b['pixels'])/active['pixels']-active['mse'])<1e-8
            if label.endswith('_patch'):
                assert row['bytes']==22+row['base_bytes']+sum(4+p['bytes'] for p in row['patches'])
                assert len(row['patches'])==2 and row['roi_rgb565_word_mismatches']==0
                for p in row['patches']:
                    assert p['bytes']==p['header_crc_bytes']+p['palette_bytes']+p['payload_bytes']
                    assert p['header_crc_bytes']==28 and p['palette_bytes']==p['colors']*2
                    expected_payload=(p['rect'][2]*p['rect'][3]*p['mode']+7)//8 if p['mode'] else 2*p['rect'][2]*p['rect'][3]
                    assert p['payload_bytes']==expected_payload
                baseline=rows[label.removesuffix('_patch')]
                assert baseline['base_packet_sha256']==row['base_packet_sha256']
                assert baseline['base_rgb_sha256']==row['base_rgb_sha256']
                assert baseline['metrics']['background']==row['metrics']['background']
                wrapped+=1;patches+=len(row['patches']);over+=row['over_48k_cap']
            else:assert row['patch_bytes']==0 and not row['patches']
            records+=1
    assert records==doc['records']==72 and wrapped==36 and patches==72 and over==36
    flat=json.loads((HERE/'flat-results.json').read_text())
    for path,expected in flat['source_sha256'].items():assert hashlib.sha256(resolve(path).read_bytes()).hexdigest()==expected,path
    assert len(flat['cases'])==2
    for i,row in enumerate(flat['cases']):
        assert row['roi_rgb565_word_mismatches']==0 and row['wrapped_bytes']<=49152 and not row['over_48k_cap']
        assert [p['mode'] for p in row['patches']]==([1,1] if i==0 else [2,1])
        assert row['wrapped_bytes']==22+row['base_bytes']+sum(4+p['bytes'] for p in row['patches'])
    print(json.dumps({'source_bindings':len(doc['source_sha256']),'source_inputs':18,'profile_records':records,
                      'wrapped_frames':wrapped,'actual_patch_encodes':patches,'all_wrapped_roi_rgb565_exact':True,
                      'wrapped_frames_over_48k':over,'flat_best_case_probes':2,'flat_source_bindings':len(flat['source_sha256']),'scope':'Stored evidence verification, not codec rerun/real-time/hardware proof'},indent=2))


if __name__=='__main__':main()
