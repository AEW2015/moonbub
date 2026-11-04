#!/usr/bin/env python3
"""Recheck pinned inputs, all retained canonical controls and grammar vectors."""
import json
import numpy as np
import benchmark as b
import model as m


def main():
    result = json.loads((b.HERE/'results.json').read_text())
    for name, expected in result['source_sha256'].items():
        assert b.digest((b.ROOT/name).read_bytes()) == expected, name
    early = m.load('decoder27_verify_early', m.V26/'model_early_probe.py')
    maps = frames = 0
    for row in result['records']:
        packet = b.raw(row['input'], m.V26)
        assert b.digest(packet) == row['packet_sha256'] and len(packet) == row['packet_bytes']
        old = early if row['early'] else m.frozen
        expected = old.parse(packet)
        got = m.replay_parse_gm26(packet, early=row['early'])
        b.same_meta(expected, got)
        assert expected['vectors'].tobytes() == b.raw(row['control_vectors'])
        assert b.digest(b''.join(v.astype('<i2').tobytes() for v in got['coefficients'])) == row['coefficients_sha256']
        assert got['reconstructed_tag'].hex() == row['reconstructed_tag']
        if not row['key']:
            data = b.raw(row['control_encoded_map'])
            mw, mh = got['vectors'].shape[1], got['vectors'].shape[0]
            np.testing.assert_array_equal(m.unpack_vectors(data,mw,mh),old.unpack_vectors(data,mw,mh))
            maps += 1
        frames += 1
    for row in result['negative_vectors']:
        try:
            m.unpack_vectors(b.raw(row['data']),row['mw'],row['mh'])
        except ValueError:
            pass
        else:
            raise AssertionError(row['name'])
    for row in result['expanded_language_vectors']:
        data = b.raw(row['data'])
        assert m.unpack_vectors(data,row['mw'],row['mh']).tobytes() == b.raw(row['vectors'])
        try:
            m.frozen.unpack_vectors(data,row['mw'],row['mh'])
        except ValueError:
            pass
        else:
            raise AssertionError('frozen accepted '+row['name'])
    assert frames == result['canonical_frames'] and maps == result['canonical_maps']
    print(json.dumps(dict(status='PASS',canonical_frames=frames,canonical_maps=maps,
                          coefficient_scale_map_vectors_bit_exact=True,
                          negative_vectors=len(result['negative_vectors']),
                          accepted_nonminimal_forms=len(result['expanded_language_vectors']),
                          source_pins=len(result['source_sha256']))))

if __name__ == '__main__':
    main()
