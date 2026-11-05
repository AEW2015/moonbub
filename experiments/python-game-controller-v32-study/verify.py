#!/usr/bin/env python3
"""Offline actual-packet, decoded-reference and source-pixel replay of v32."""
from pathlib import Path
import hashlib
import json
import numpy as np
import benchmark as b
from controller import select_tier

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


def block_sse(source, output):
    diff=source.astype(np.int64)-output
    h,w=diff.shape
    diff=np.pad(diff,((0,(-h)%8),(0,(-w)%8)))
    return (diff.reshape((h+7)//8,8,(w+7)//8,8).transpose(0,2,1,3).reshape(-1,64)**2).sum(axis=1)


def main():
    data = b.b.load(HERE / 'results.json')
    assert data['schema'] == 'gamebub-controller-v32' and len(data['cases']) == 6
    assert data['physical_30fps_proven'] is False and data['unchanged_GM27_wire'] is True
    for path, sha in data['source_sha256'].items():
        q = Path(path)
        assert not q.is_absolute() and '..' not in q.parts
        assert b.sha(ROOT / q) == sha, path
    inputs = b.b.load(n.V24 / 'results.json')['inputs']
    prior30 = b.b.load(HERE.parent / 'python-game-controller-v30-study/results.json')['cases']
    pairs = attempts = words = baseline_pairs = adaptive_p_frames = band_planes = band_block_checks = 0
    chains = []
    for case in data['cases']:
        assert case['policy'] in b.POLICIES
        inp = next(x for x in inputs if x['scene'] == case['scene'])
        previous = next(x for x in prior30 if x['scene'] == case['scene'] and x['policy'] == 'band_strict')
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
            if not key:
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
                kinds = ['zero'] if key else ['zero', 'half32']
                expected_kinds = kinds + [v+'_band' for v in kinds]
                if case['policy']!='band_control':expected_kinds += [v+'_shrink' for v in kinds]
                assert [a['kind'] for a in group] == expected_kinds
                before = [(a['cap_fit'], a['quality_eligible']) for a in group]
                candidate, shadow = select_tier(group, case['policy'])
                assert before == [(a['cap_fit'], a['quality_eligible']) for a in group]
                if chosen is None and candidate is not None:
                    chosen = candidate
                    assert row['baseline_kind']==shadow['kind'] and row['baseline_source_sse']==shadow['hybrid']['active_squared_error']
                    assert row['baseline_complete_bytes']==shadow['complete_bytes']
            assert chosen is not None and [a for a in row['attempts'] if a['selected']] == [chosen]
            assert chosen['complete_bytes']<=row['baseline_complete_bytes']
            assert row['quality_budget_percent']==(1 if case['policy']=='shrink_budget' else 0)
            assert 100*chosen['hybrid']['active_squared_error'] <= (100+row['quality_budget_percent'])*row['baseline_source_sse']
            decoded_attempts = {}
            for a in row['attempts']:
                base, pair = b.raw(a['base_packet']), b.raw(a['packet'])
                assert len(base) == a['base_bytes'] and len(pair) == a['complete_bytes'] == len(base) + row['hud_bytes'] + 60
                decoded, meta = m.decode(base, ref, expected_epoch=25, expected_reference_id=None if key else refid)
                assert meta['reference_tag'].hex() == reference_tag
                assert meta['reconstructed_tag'].hex() == a['reconstructed_tag']
                np.testing.assert_array_equal(meta['scale_map'], m.roi.declared_map(720, 480, n.ROIS, 8, a['background']))
                if a['kind'].startswith('zero'):
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
                if a['kind'].endswith(('_band','_shrink')):
                    old_planes, old_meta = decoded_attempts[(a['background'],a['kind'].removesuffix('_band').removesuffix('_shrink'))]
                    assert np.array_equal(meta['vectors'],old_meta['vectors'])
                    assert len(base)<=old_meta['packet_bytes']
                    changed = removed = 0
                    for plane, (coeff, oldcoeff, out, oldout, detail) in enumerate(zip(meta['coefficients'],old_meta['coefficients'],decoded,old_planes,a['work']['planes'])):
                        np.testing.assert_array_equal(coeff[:,0,0],oldcoeff[:,0,0])
                        np.testing.assert_array_equal(coeff.reshape(-1,64)[:,m.ft.ZIGZAG[:6]],oldcoeff.reshape(-1,64)[:,m.ft.ZIGZAG[:6]])
                        priority = meta['scale_map']==8
                        if plane:
                            protected=priority.copy()
                            protected[1:,:] |= priority[:-1,:]
                            protected[:,1:] |= priority[:,:-1]
                            protected[1:,1:] |= priority[:-1,:-1]
                            protected=protected.reshape(-1)
                        else:
                            protected=np.repeat(np.repeat(priority,2,axis=0),2,axis=1).reshape(-1)
                        np.testing.assert_array_equal(coeff[protected],oldcoeff[protected])
                        # AC may be removed or reduced toward zero; never amplify or flip sign.
                        assert np.all(np.abs(coeff.astype(np.int64))<=np.abs(oldcoeff.astype(np.int64)))
                        assert np.all((coeff==0)|(np.sign(coeff)==np.sign(oldcoeff)))
                        old_sse=block_sse(source[plane],oldout);new_sse=block_sse(source[plane],out)
                        allowed=np.minimum(old_sse//100,64) if a['kind'].endswith('_shrink') and case['policy']=='shrink_budget' else np.zeros_like(old_sse)
                        allowed[protected]=0
                        assert np.all(new_sse<=old_sse+allowed)
                        assert int(old_sse.sum())==detail['baseline_source_yuv_sse']
                        assert int(new_sse.sum())==detail['selected_source_yuv_sse']
                        assert int(allowed.sum())==detail['allowed_extra_source_yuv_sse']
                        c=int(np.any(coeff!=oldcoeff,axis=(1,2)).sum());r=int(np.count_nonzero(oldcoeff)-np.count_nonzero(coeff))
                        assert c==detail['changed_blocks'] and r==detail['removed_coefficients']
                        assert int(protected.sum())==detail['protected_blocks']
                        records=detail['candidate_plans'];selected=min(records,key=lambda v:v['bytes'])
                        assert selected['label']==detail['selected_label']
                        assert selected['bytes']==detail['selected_bytes']==meta['plane_lengths'][plane]<=detail['baseline_bytes']
                        changed+=c;removed+=r;band_planes+=1;band_block_checks+=len(coeff)
                    assert changed==a['work']['changed_blocks'] and removed==a['work']['removed_coefficients']
                meta['packet_bytes']=len(base)
                decoded_attempts[(a['background'],a['kind'])]=(decoded,meta)
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
            if case['policy'] == 'band_control':
                assert packet == b.raw(old['packet'], HERE.parent / 'python-game-controller-v30-study')
                assert ack == b.raw(old['ack'], HERE.parent / 'python-game-controller-v30-study')
                assert row['hybrid'] == old['hybrid']
                baseline_pairs += 1
            chain.append(dict(id=fid, reference_tag=reference_tag, decoded_tag=row['reconstructed_tag'],
                              hybrid_rgb565_sha256=n.digest(hybrid)))
            ref, refid, slot = decoded, fid, 0 if key else 1-slot
            pairs += 1
        assert b.summarize(case['rows']) == case['summary']
        chains.append(dict(scene=case['scene'], policy=case['policy'], rows=chain))
    assert pairs == 288 and attempts==1504 and words == pairs * 21120 and baseline_pairs == 96
    result = dict(schema='gamebub-v32-replay', results_sha256=b.sha(HERE / 'results.json'),
                  verifier_sha256=b.sha(Path(__file__)), accepted_pairs=pairs, candidate_attempts=attempts,
                  exact_hud_words=words, baseline_v30_exact_pairs=baseline_pairs, adaptive_p_frames=adaptive_p_frames,
                  band_candidate_planes=band_planes, band_block_checks=band_block_checks, chains=chains, physical_30fps_proven=False,
                  band_and_shrink_dc_roi_magnitude_perblock_rgb_guards_replayed=True,
                  all_source_pixels_decoded_references_metrics_and_work_replayed=True)
    output = json.dumps(result, sort_keys=True, separators=(',', ':')) + '\n'
    (HERE / 'replay.json').write_text(output)
    print(json.dumps({k: v for k, v in result.items() if k != 'chains'}))


if __name__ == '__main__':
    main()
