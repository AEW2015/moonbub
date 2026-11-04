#!/usr/bin/env python3
"""Actual CP25/JA25 replay and fair same-HU25 standards projections."""
from pathlib import Path
import hashlib
import importlib.util
import json
import math
import sys
import time
import numpy as np
import model as m

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
NATIVE = HERE.parent / 'python-game-native-motion-v25-study'
FINE = HERE.parent / 'python-game-fine-key-v25-study'
CAPPED = HERE.parent / 'python-game-capped-key-v25-study'
spec = importlib.util.spec_from_file_location('cp25_native_benchmark', NATIVE / 'benchmark.py')
n = importlib.util.module_from_spec(spec); sys.modules[spec.name] = n; spec.loader.exec_module(n)


def blob(data):
    # Keep one content-addressed object store for both actual inner and pairs.
    import zlib
    stored = zlib.compress(data, 9)
    path = 'objects/' + hashlib.sha256(stored).hexdigest() + '.zlib'
    (HERE / 'objects').mkdir(exist_ok=True)
    (HERE / path).write_bytes(stored)
    return dict(path=path, raw_bytes=len(data), raw_sha256=hashlib.sha256(data).hexdigest(), stored_sha256=hashlib.sha256(stored).hexdigest())


def pins():
    paths = {HERE / 'model.py', HERE / 'benchmark.py', HERE / 'verify.py'}
    for folder in (NATIVE, FINE, CAPPED):
        data = n.load(folder / 'results.json')
        paths |= {ROOT / p for p in data['source_sha256']}
        paths.add(folder / 'results.json')
        for case in data['cases']:
            for row in case['rows']:
                paths.add(folder / row['base_packet']['path'])
                for attempt in row.get('attempts', []):
                    if 'packet' in attempt: paths.add(folder / attempt['packet']['path'])
    paths |= {p for folder in ('python-game-base-motion-v25-study', 'python-game-hud-motion-v25-study')
              for p in (HERE.parent / folder).glob('*.py')}
    return {p.relative_to(ROOT).as_posix(): n.sha(p) for p in sorted(paths)}


def hud_campaign(inp, motion):
    selector = m.ui.PatchSelector(rectangles=n.RECTS)
    previous, previous_id = None, m.NO_REF
    rows = []
    for source in inp['rows']:
        fid = source['id']; key = fid % 24 == 0
        if key: previous, previous_id = None, m.NO_REF
        original = n.original(source)
        start = time.perf_counter_ns()
        full = selector.select(m.base.C.corpus.expand565(original), 98304)
        legacy_ms = (time.perf_counter_ns()-start)/1e6
        packet, work = m.encode_hud(full.patches, previous, epoch=25, frame_id=fid, reference_id=previous_id, motion=motion)
        decoded, meta = m.decode_hud(packet, previous, expected_epoch=25,
                                     expected_reference_id=None if key else previous_id)
        assert len(decoded) == 4
        for item, (x, y, w, h) in zip(decoded, n.RECTS): np.testing.assert_array_equal(item['words'], original[y:y+h, x:x+w])
        rows.append(dict(id=fid, key=key, reference_id=previous_id, packet=blob(packet), bytes=len(packet), work=work,
                         legacy_encode_ms=legacy_ms, paid_encode_ms=legacy_ms+work['encode_wall_ms'],
                         reconstructed_tag=meta['reconstructed_tag'].hex()))
        previous, previous_id = decoded, fid
    return dict(scene=inp['scene'], policy='motion' if motion else 'no_motion', rows=rows,
                summary=dict(frames=48, hud_bytes=sum(r['bytes'] for r in rows),
                             hud_Mbps_at30=sum(r['bytes'] for r in rows)*5/1e6,
                             mean_paid_encode_ms=sum(r['paid_encode_ms'] for r in rows)/48))


def wire(body):
    fragments = math.ceil(body/1008)
    return dict(fragments=fragments, forward_data_ip_udp_bytes=body+fragments*75,
                forward_control_ip_udp_bytes=128,
                reverse_fragment_ip_udp_bytes=fragments*57, reverse_gate_ip_udp_bytes=192,
                reverse_joint_ack_ip_udp_bytes=m.ACK.size+4+28)


def summarize(rows):
    total = sum(r['body_bytes'] for r in rows); count = len(rows)
    s = sum(r['hybrid']['active_squared_error'] for r in rows)
    samples = sum(r['hybrid']['active_channel_samples'] for r in rows)
    return dict(frames=count, complete_bytes=total, coded_body_Mbps_at30=total*8*30/count/1e6,
                base_bytes=sum(r['base_bytes'] for r in rows), hud_bytes=sum(r['hud_bytes'] for r in rows),
                binding_bytes=sum(r['binding_bytes'] for r in rows), max_complete_bytes=max(r['body_bytes'] for r in rows),
                cap_fit_frames=sum(r['body_bytes'] <= m.CAP for r in rows),
                active_squared_error=s, active_channel_samples=samples, active_mse=s/samples,
                active_psnr_db=10*math.log10(65025/(s/samples)),
                hud_word_errors=sum(r['hybrid']['hud_word_errors'] for r in rows),
                exact_hud_words=21120*count, ack_bytes=sum(r['ack']['raw_bytes'] for r in rows),
                hypothetical_forward_Mbps_at30=sum(r['wire']['forward_data_ip_udp_bytes']+r['wire']['forward_control_ip_udp_bytes'] for r in rows)*8*30/count/1e6,
                hypothetical_reverse_Mbps_at30=sum(sum(r['wire'][k] for k in ('reverse_fragment_ip_udp_bytes','reverse_gate_ip_udp_bytes','reverse_joint_ack_ip_udp_bytes')) for r in rows)*8*30/count/1e6,
                mean_paid_base_hud_encode_ms=sum(r['base_encode_ms']+r['hud_encode_ms'] for r in rows)/count,
                mean_joint_receive_ms=sum(r['receive_ms'] for r in rows)/count,
                mean_pair_bind_parse_ms=sum(r['bind_ms'] for r in rows)/count,
                mean_sender_ack_validation_ms=sum(r['ack_validation_ms'] for r in rows)/count)


def admission(case, folder, hud):
    """Diagnose the entire component trace before claiming an accepted timeline.

    A rejected trace cannot continue with its imagined fine-key reference. Its
    later rows remain offline component diagnostics, never accepted CP25 frames.
    """
    rows, failed = [], []
    for row, hrow in zip(case['rows'], hud['rows']):
        complete = row['base_bytes'] + hrow['bytes'] + m.PAIR.size + 4
        item = dict(id=row['id'], base_bytes=row['base_bytes'], hud_bytes=hrow['bytes'],
                    binding_bytes=m.PAIR.size+4, complete_bytes=complete, fits=complete <= m.CAP)
        if not item['fits']:
            bp = n.raw(row['base_packet'], folder); hp = n.raw(hrow['packet'], HERE)
            flags = (m.KEY if row['key'] else 0) | (m.PUBLISH if row['publish'] else 0)
            attempted = m.seal(m.PAIR.pack(b'CP25',1,flags,25,row['id'],row['source_slot'],row['destination_slot'],
                                          len(bp),len(hp),m.digest(bp),m.digest(hp))+bp+hp)
            assert len(attempted) == complete and complete > m.CAP
            try: m.parse_pair(attempted)
            except ValueError: pass
            else: raise AssertionError('overcap CP25 accepted')
            item['attempted_packet'] = blob(attempted); failed.append(row['id'])
        rows.append(item)
    if not failed: return None
    return dict(scene=case['scene'], profile=case['profile'], hud_policy=hud['policy'],
                base_result_directory=folder.relative_to(ROOT).as_posix(), rows=rows, failed_ids=failed,
                timeline_accepted=False, reason='Complete cap rejects at least one frame; later component-reference history is diagnostic only.')


def combine(case, folder, hud, inp):
    receiver = m.Receiver(epoch=25)
    rows = []
    for src, row, hrow in zip(inp['rows'], case['rows'], hud['rows']):
        fid = row['id']; assert fid == src['id'] == hrow['id']
        base = n.raw(row['base_packet'], folder); hp = n.raw(hrow['packet'], HERE)
        start = time.perf_counter_ns()
        pair = m.encode_pair(base, hp, epoch=25, frame_id=fid, source_slot=row['source_slot'],
                             destination_slot=row['destination_slot'], publish=row['publish'], key=row['key'])
        bind_ms = (time.perf_counter_ns()-start)/1e6
        start = time.perf_counter_ns(); decoded, patches, ack = receiver.receive(pair)
        receive_ms = (time.perf_counter_ns()-start)/1e6
        start = time.perf_counter_ns(); ack_meta = m.validate_ack(ack, pair)
        ack_ms = (time.perf_counter_ns()-start)/1e6
        bare = m.base.C.corpus.rgb565(m.base.ft.planes_to_rgb(decoded))
        hybrid = n.overlay(bare, tuple(p['words'] for p in patches))
        assert n.digest(bare) == row['bare_rgb565_sha256']
        assert n.digest(hybrid) == row['hybrid_rgb565_sha256']
        original = n.original(src); quality = n.metric(original, hybrid)
        assert quality == row['hybrid'] and quality['hud_word_errors'] == 0
        rows.append(dict(id=fid, key=row['key'], publish=row['publish'], reference_id=row['reference_id'],
                         hud_reference_id=hrow['reference_id'], source_slot=row['source_slot'], destination_slot=row['destination_slot'],
                         base_packet=dict(directory=folder.relative_to(ROOT).as_posix(), **row['base_packet']),
                         hud_packet=hrow['packet'], packet=blob(pair), ack=blob(ack), ack_meta=ack_meta,
                         base_bytes=len(base), hud_bytes=len(hp), binding_bytes=m.PAIR.size+4, body_bytes=len(pair),
                         base_encode_ms=row['work']['encoder_wall_ms'], hud_encode_ms=hrow['paid_encode_ms'], bind_ms=bind_ms,
                         receive_ms=receive_ms, ack_validation_ms=ack_ms, wire=wire(len(pair)), bare=row['bare'], hybrid=quality,
                         reconstructed_yuv_tag=row['reconstructed_yuv_tag'], bare_rgb565_sha256=n.digest(bare), hybrid_rgb565_sha256=n.digest(hybrid)))
    return dict(scene=case['scene'], profile=case['profile'], hud_policy=hud['policy'], policy=case['policy'],
                base_result_directory=folder.relative_to(ROOT).as_posix(), rows=rows, summary=summarize(rows))


def comparisons(cases, huds, old):
    out = []
    for case in cases:
        scene, policy, summary = case['scene'], case['hud_policy'], case['summary']
        oldcustom = next(c for c in old['custom_baselines'] if c['scene'] == scene and c['profile'] == 'adaptive_plain')['summary']['hybrid']
        hud = next(h for h in huds if h['scene'] == scene and h['policy'] == policy)
        standards = []
        for codec in ('libx265', 'libsvtav1'):
            options = []
            for standard in old['cases']:
                if standard['scene'] != scene or standard['codec'] != codec: continue
                body = sum(r['coded_access_unit_bytes']+h['bytes']+m.PAIR.size+4 for r, h in zip(standard['rows'], hud['rows']))
                options.append(dict(profile=standard['profile'], native_base_bytes=standard['summary']['bare']['complete_bytes'],
                                    projected_same_HU25_bytes=body, projected_same_HU25_Mbps_at30=body*5/1e6,
                                    hybrid_mse=standard['summary']['hybrid']['active_mse'],
                                    at_least_custom_measured_quality=standard['summary']['hybrid']['active_mse'] <= summary['active_mse']))
            passing = [o for o in options if o['at_least_custom_measured_quality']]
            selected = min(passing, key=lambda o:o['projected_same_HU25_bytes']) if passing else None
            oldpoint = next(o for o in old['operating_points'] if o['scene'] == scene and o['custom_profile'] == 'adaptive_plain' and o['variant'] == 'hybrid' and o['codec'] == codec)['lowest_bytes_measured_at_least_target_quality']
            standards.append(dict(codec=codec, sampled_options=options, selected_same_HU25=selected,
                                  custom_to_selected_same_HU25_body_ratio=None if selected is None else summary['complete_bytes']/selected['projected_same_HU25_bytes'],
                                  frozen_v24_target=oldpoint,
                                  meets_frozen_v24_rate_and_its_quality=summary['complete_bytes'] <= oldpoint['bytes'] and summary['active_mse'] <= oldpoint['mse']))
        out.append(dict(scene=scene, profile=case['profile'], hud_policy=policy, old_custom_hybrid=oldcustom,
                        byte_saving_vs_old_custom=1-summary['complete_bytes']/oldcustom['complete_bytes'],
                        meets_old_custom_measured_quality=summary['active_mse'] <= oldcustom['active_mse'], standards=standards))
    return out


def main():
    before = pins(); old = n.load(n.V24/'results.json')
    huds = [hud_campaign(inp, motion) for inp in old['inputs'] for motion in (False, True)]
    cases, rejected = [], []
    for folder in (NATIVE, FINE, CAPPED):
        for base in n.load(folder/'results.json')['cases']:
            inp = next(x for x in old['inputs'] if x['scene'] == base['scene'])
            for hud in huds:
                if hud['scene'] != base['scene']: continue
                # All base policies get the strongest HUD; one fine-key control
                # also exposes the cheaper no-motion HUD implementation.
                if hud['policy'] == 'no_motion' and base['profile'] not in ('finekey_zero','capped_key_zero'): continue
                failure = admission(base, folder, hud)
                if failure is not None:
                    rejected.append(failure)
                    print(json.dumps(dict(rejected_scene=base['scene'],profile=base['profile'],hud_policy=hud['policy'],failed_ids=failure['failed_ids'])),flush=True)
                    continue
                case = combine(base, folder, hud, inp); cases.append(case)
                print(json.dumps(dict(scene=case['scene'], profile=case['profile'], hud_policy=case['hud_policy'], summary=case['summary'])), flush=True)
    assert before == pins(), 'frozen dependency changed'
    result = dict(schema='gamebub-combined-motion-v25', source_sha256=before, huds=huds, cases=cases, rejected_cohorts=rejected,
                  comparisons=comparisons(cases,huds,old),
                  counts=dict(native_source_frames=96, joint_decisions=sum(len(c['rows']) for c in cases),
                              exact_hud_words=sum(c['summary']['exact_hud_words'] for c in cases)),
                  scope=['All actual CP25/HU25/JA25 bytes retained; keys0/24 have independent HUD; receiver rebuilt solely from bytes and reconstructed banks.',
                         'Native GM25 encoding was paid in prior retained campaign; joint replay reuses exact bytes and their measured work, not retimed capture or encode.',
                         'Per-decision source analyzed only once in each fixedpolicy; codec controls reuse96 distinct sourceimages, not independent new captures.',
                         'Standards+sameHU25 is prospective complete-envelope accounting, not a standards-compatible CP25 decoder.',
                         'Complete49,152B cap is validated for every actual pair; rates are nominal30IDs/s projections, not measured throughput.',
                         'Nonadmissible fine-key component traces are retained as rejected_cohorts; no accepted timeline or rate claim follows for their downstream references.',
                         'Wire budget reuses GF03/token/PC18/FG19 arithmetic but no CP25 transport implementation exists. JA25 actual65B replaces JA23actual134B.',
                         'Write-drain/vblank are synchronous trusted modelinputs. Bankpublication/ACK validation are functional, not hardware memory/CDC/timing evidence.'])
    (HERE/'results.json').write_text(json.dumps(result,separators=(',', ':'),allow_nan=False)+'\n')


if __name__ == '__main__': main()
