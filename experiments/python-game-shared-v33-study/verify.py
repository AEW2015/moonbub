#!/usr/bin/env python3
"""Independent retained packet/source/causal-history and exact pair replay."""
import argparse
import json
import numpy as np
import helpers as h


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--archives-only',action='store_true',help='Skip expensive re-encoding; still decode every actual packet.')
    args = parser.parse_args()
    data = h.load(h.HERE/'results.json')
    assert data['schema'] == 'gamebub-shared-v33'
    assert data['physical_30fps_proven'] is False and data['unchanged_GM27_wire'] is True
    for path, digest in data['source_sha256'].items(): assert h.sha(h.ROOT/path) == digest, path
    checked = inputs = 0
    for case, inp in h.cases():
        ref = None
        for prior, src in zip(case['rows'][:12],inp['rows'][:12]):
            source = h.n.source(src)
            assert h.digest(b''.join(a.astype('u1').tobytes() for a in source)) == src['common_yuv420_u8_sha256']
            preparations = {}
            matches = [r for r in data['rows'] if r['scene'] == case['scene'] and r['frame_id'] == prior['id']]
            expected = {(a['kind'],a['background']) for a in prior['attempts'] if not a['kind'].endswith('_band')}
            assert {(r['motion_kind'],r['background']) for r in matches} == expected
            assert len(matches) == len(expected)
            for row in matches:
                assert row['source_sha256'] == src['common_yuv420_u8_sha256']
                assert row['reference_tag'] == prior['reference_tag']
                kind, bg = row['motion_kind'],row['background']
                if not args.archives_only:
                    if kind not in preparations: preparations[kind] = h.prepare(source,ref,prior,kind)
                    prepared = preparations[kind]
                    q = h.m.roi.declared_map(720,480,h.n.ROIS,8,bg)
                    old = h.old_pair(prepared,q)
                    new = h.shared.encode_pair(h.m,prepared,q)
                for i, record in enumerate(row['records']):
                    packet = h.raw(record['packet'])
                    signature = record['signature']
                    assert h.digest(packet) == signature['packet_sha256']
                    assert [h.digest(p) for p in h.packet_planes(packet)] == signature['plane_packet_sha256']
                    attempt = next(a for a in prior['attempts'] if a['kind'] == kind+('_band' if i else '') and a['background'] == bg)
                    assert packet == h.raw(attempt['base_packet'],h.V32)
                    decoded, _ = h.m.decode(packet,ref,expected_epoch=25,expected_reference_id=None if prior['key'] else prior['reference_id'])
                    assert [h.digest(a.astype('<i2').tobytes()) for a in decoded] == signature['output_plane_sha256']
                    if not args.archives_only:
                        assert packet == old[i][0] == new[i][0]
                        for a,b,c in zip(decoded,old[i][1],new[i][1]):
                            np.testing.assert_array_equal(a,b);np.testing.assert_array_equal(a,c)
                        assert new[i][2]['rdo'] == record['work']['rdo']
                        assert new[i][2]['planes'] == record['work']['planes']
                    checked += 1
            ref,_ = h.m.decode(h.raw(prior['base_packet'],h.V32),ref,expected_epoch=25,
                expected_reference_id=None if prior['key'] else prior['reference_id'])
            inputs += 1
    assert inputs == 24 and checked == data['summary']['output_packets']
    assert len(data['rows']) == data['summary']['pairs']
    print(json.dumps(dict(verified_source_frames=inputs,verified_packets=checked,reran_exact_pair=not args.archives_only)))


if __name__ == '__main__': main()
