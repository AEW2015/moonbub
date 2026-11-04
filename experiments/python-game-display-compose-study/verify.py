#!/usr/bin/env python3
"""Read-only retained pair replay and independently recomputed budget checks."""
from pathlib import Path
import hashlib
import json
import benchmark as b
import model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def main():
    data = b.read_json(HERE / 'results.json')
    assert data['schema'] == 'gamebub-display-compose-v21'
    for path, digest in data['source_sha256'].items():
        assert b.sha(ROOT / path) == digest, path
    old = {c['scene']: c for c in b.read_json(b.OLD / 'results.json')['cases'] if c['policy'] == 'mandatory'}
    receivers = {name: model.cache.Receiver() for name in old}
    words = samples = negatives = fits = 0
    for vector in data['vectors']:
        fixture = old[vector['scene']]['vectors'][vector['fixture_index']]
        packet = b.raw(vector['packet'], HERE)
        base, hud = model.unbind(packet, enforce_frame_cap=False)
        assert base == model.strip_patches(b.raw(fixture['packet']))
        assert len(packet) == vector['complete_bytes'] == len(base) + len(hud) + model.OVERHEAD
        assert (len(packet) <= model.FRAME_CAP) == vector['complete_cap_fits']
        if vector['complete_cap_fits']:
            model.unbind(packet)
            fits += 1
        else:
            try:
                model.unbind(packet)
            except ValueError:
                pass
            else:
                raise AssertionError('oversized container admitted')
        bad = bytearray(packet)
        bad[model.HEADER.size] ^= 1
        # A repaired outer CRC cannot bypass each component's digest binding.
        bad = model.cache.seal(bytes(bad[:-4]))
        rx = receivers[vector['scene']]
        before = (rx.last_frame, rx.last_generation, rx.last_bodytag)
        try:
            model.unbind(bad, enforce_frame_cap=False)
        except ValueError:
            pass
        else:
            raise AssertionError('altered component accepted')
        assert before == (rx.last_frame, rx.last_generation, rx.last_bodytag)
        negatives += 1
        _, w, s = b.replay_vector(packet, fixture, rx)
        words += w
        samples += s
    assert len(data['vectors']) == 10
    assert words == data['exact_display_words'] == 3456000
    assert samples == data['exact_yuv_samples'] == 5184000
    expected = b.budget(b.read_json(b.CACHE / 'results.json')['cases'])
    assert expected == data['budgets']
    print(json.dumps(dict(golden_pairs=10, full_display_exact_words=words,
                          unchanged_yuv_samples=samples, repaired_outer_crc_negatives=negatives,
                          admitted_golden_pairs_under_cap=fits, native_budget_decisions=96,
                          joint_publication_implemented=False, physical_30fps_proven=False), indent=2))


if __name__ == '__main__':
    main()
