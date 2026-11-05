#!/usr/bin/env python3
"""Offline actual-packet, decoded-reference and source-pixel replay of v29."""
from pathlib import Path
import hashlib
import json
import numpy as np
import benchmark as b
from controller import select_group

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
m, p, n = b.m, b.p, b.n


def quiet_mask(source, reference):
    """Independent scalar-grid accounting, no adaptive search helper calls."""
    h, w = source[0].shape
    mw, mh = (w + 31) // 32, (h + 31) // 32
    costs = np.zeros(mh * mw, np.int64)
    weights = costs.copy()
    for plane, (src, ref) in enumerate(zip(source, reference)):
        bs, weight = (32, 1) if plane == 0 else (16, 2)
        y, x = np.meshgrid(np.arange(0, src.shape[0], 4), np.arange(0, src.shape[1], 4), indexing='ij')
        ids = (y // bs) * mw + x // bs
        np.add.at(costs, ids.ravel(), (weight * np.abs(src[y, x].astype(np.int64) - ref[y, x])).ravel())
        np.add.at(weights, ids.ravel(), weight)
    return (costs <= 2 * weights).reshape(mh, mw)


def scored_samples(source, active, stride):
    total = 0
    for plane, src in enumerate(source):
        bs = 32 if plane == 0 else 16
        y, x = np.meshgrid(np.arange(0, src.shape[0], stride), np.arange(0, src.shape[1], stride), indexing='ij')
        total += int(np.count_nonzero(active[y // bs, x // bs]))
    return total


def main():
    data = b.b.load(HERE / 'results.json')
    assert data['schema'] == 'gamebub-controller-v29' and len(data['cases']) == 8
    assert data['physical_30fps_proven'] is False and data['unchanged_GM27_wire'] is True
    for path, sha in data['source_sha256'].items():
        q = Path(path)
        assert not q.is_absolute() and '..' not in q.parts
        assert b.sha(ROOT / q) == sha, path
    inputs = b.b.load(n.V24 / 'results.json')['inputs']
    prior28 = b.b.load(HERE.parent / 'python-game-runtime-v28-study/results.json')['cases']
    pairs = attempts = words = baseline_pairs = adaptive_p_frames = entropy_planes = 0
    chains = []
    for case in data['cases']:
        assert case['policy'] in b.POLICIES
        inp = next(x for x in inputs if x['scene'] == case['scene'])
        previous = next(x for x in prior28 if x['scene'] == case['scene'] and x['policy'] == 'sample4_refine2')
        assert [r['id'] for r in case['rows']] == list(range(48))
        rx = p.Receiver(epoch=25)
        ref, refid, slot = None, m.NO_REF, 0
        chain = []
        for row, srcrow, old in zip(case['rows'], inp['rows'], previous['rows']):
            fid = row['id']
            key = fid % 24 == 0
            if key:
                ref, refid, slot = None, m.NO_REF, 0
            reference_tag = m.base.ZERO_TAG.hex() if key else m.C.reference_tag(ref).hex()
            assert row['reference_id'] == refid and row['reference_tag'] == reference_tag and row['key'] == key
            assert row['source_common_yuv_sha256'] == srcrow['common_yuv420_u8_sha256']
            assert row['source_slot'] == (255 if key else slot) and row['destination_slot'] == (0 if key else 1-slot)
            source, original = n.source(srcrow), n.original(srcrow)
            quiet = None
            if case['policy'].startswith('adaptive') and not key:
                quiet = quiet_mask(source, ref)
                search = row['analyses']['half32']['search']
                screen = sum(v[::4, ::4].size for v in source)
                coarse = scored_samples(source, ~quiet, 4)
                fine = scored_samples(source, ~quiet, 2)
                assert search['quiet_blocks'] == int(quiet.sum()) and search['active_blocks'] == int((~quiet).sum())
                assert search['screen_sample_operations'] == screen
                assert search['sad_sample_operations'] == screen + 81 * coarse + 25 * fine
                assert search['reference_sample_fetches'] == screen + 81 * coarse + 100 * fine
                adaptive_p_frames += 1
            chosen = None
            for bg in sorted({a['background'] for a in row['attempts']}):
                group = [a for a in row['attempts'] if a['background'] == bg]
                assert [a['kind'] for a in group] == (['zero'] if key else ['zero', 'half32'])
                before = [(a['cap_fit'], a['quality_eligible']) for a in group]
                candidate = select_group(group)
                assert before == [(a['cap_fit'], a['quality_eligible']) for a in group]
                if chosen is None and candidate is not None:
                    chosen = candidate
            assert chosen is not None and [a for a in row['attempts'] if a['selected']] == [chosen]
            for a in row['attempts']:
                base, pair = b.raw(a['base_packet']), b.raw(a['packet'])
                assert len(base) == a['base_bytes'] and len(pair) == a['complete_bytes'] == len(base) + row['hud_bytes'] + 60
                decoded, meta = m.decode(base, ref, expected_epoch=25, expected_reference_id=None if key else refid)
                assert meta['reference_tag'].hex() == reference_tag
                assert meta['reconstructed_tag'].hex() == a['reconstructed_tag']
                np.testing.assert_array_equal(meta['scale_map'], m.roi.declared_map(720, 480, n.ROIS, 8, a['background']))
                if a['kind'] == 'zero':
                    assert not np.any(meta['vectors'])
                elif quiet is not None:
                    assert not np.any(meta['vectors'][quiet])
                hybrid = n.overlay(m.C.corpus.rgb565(m.ft.planes_to_rgb(decoded)),
                                   tuple(original[y:y+h, x:x+w] for x, y, w, h in n.RECTS))
                assert n.metric(original, hybrid) == a['hybrid'] and n.digest(hybrid) == a['hybrid_rgb565_sha256']
                if key:
                    assert a['work']['decoder_reference_sample_reads'] == 0
                else:
                    _, taps = m.taps.predict_with_info(ref, meta['vectors'], 32)
                    assert taps['reference_sample_fetches'] == a['work']['decoder_reference_sample_reads']
                if case['policy'].endswith('_ec'):
                    for detail in a['work']['planes']:
                        records = detail['candidate_plans']
                        eligible = [r for r in records if r['source_yuv_sse'] <= detail['baseline_source_yuv_sse']]
                        selected = [r for r in records if r.get('selected')]
                        assert selected == [min(eligible, key=lambda r: r['bytes'])]
                        assert selected[0]['label'] == detail['selected_label']
                        assert detail['selected_bytes'] == selected[0]['bytes'] <= detail['baseline_bytes']
                        entropy_planes += 1
                attempts += 1
            packet = b.raw(row['packet'])
            parsed = p.parse_pair(packet)
            hud = b.raw(row['hud_packet'], ROOT / row['hud_packet']['directory'])
            assert parsed['base'] == b.raw(row['base_packet']) == b.raw(chosen['base_packet'])
            assert parsed['hud'] == hud and packet == b.raw(chosen['packet'])
            decoded, patches, ack = rx.receive(packet)
            assert ack == b.raw(row['ack'])
            p.validate_ack(ack, packet)
            for patch, (x, y, w, h) in zip(patches, n.RECTS):
                np.testing.assert_array_equal(patch['words'], original[y:y+h, x:x+w])
                words += w * h
            hybrid = n.overlay(m.C.corpus.rgb565(m.ft.planes_to_rgb(decoded)), tuple(v['words'] for v in patches))
            assert n.metric(original, hybrid) == row['hybrid'] and n.digest(hybrid) == row['hybrid_rgb565_sha256']
            assert m.C.reference_tag(decoded).hex() == row['reconstructed_tag'] == chosen['reconstructed_tag']
            assert len(packet) == row['body_bytes'] == row['base_bytes'] + row['hud_bytes'] + 60 <= 49152
            paid = sum(v['analysis_wall_ms'] for v in row['analyses'].values()) + sum(a['encode_ms'] for a in row['attempts'])
            service = paid + sum(a['quality_ms'] + a['bind_ms'] for a in row['attempts'])
            assert abs(paid - row['paid_base_encode_ms']) < 1e-8 and abs(service - row['base_policy_service_ms']) < 1e-8
            if case['policy'] == 'mixed_lazy':
                assert packet == b.raw(old['packet'], HERE.parent / 'python-game-runtime-v28-study')
                assert ack == b.raw(old['ack'], HERE.parent / 'python-game-runtime-v28-study')
                assert row['hybrid'] == old['hybrid']
                baseline_pairs += 1
            chain.append(dict(id=fid, reference_tag=reference_tag, decoded_tag=row['reconstructed_tag'],
                              hybrid_rgb565_sha256=n.digest(hybrid)))
            ref, refid, slot = decoded, fid, 0 if key else 1-slot
            pairs += 1
        assert b.summarize(case['rows']) == case['summary']
        chains.append(dict(scene=case['scene'], policy=case['policy'], rows=chain))
    assert pairs == 384 and words == pairs * 21120 and baseline_pairs == 96
    result = dict(schema='gamebub-v29-replay', results_sha256=b.sha(HERE / 'results.json'),
                  verifier_sha256=b.sha(Path(__file__)), accepted_pairs=pairs, candidate_attempts=attempts,
                  exact_hud_words=words, baseline_v28_exact_pairs=baseline_pairs, adaptive_p_frames=adaptive_p_frames,
                  entropy_candidate_planes=entropy_planes, chains=chains, physical_30fps_proven=False,
                  all_source_pixels_decoded_references_metrics_and_work_replayed=True)
    output = json.dumps(result, sort_keys=True, separators=(',', ':')) + '\n'
    (HERE / 'replay.json').write_text(output)
    print(json.dumps({k: v for k, v in result.items() if k != 'chains'}))


if __name__ == '__main__':
    main()
