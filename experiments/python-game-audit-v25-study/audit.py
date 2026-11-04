#!/usr/bin/env python3
"""Independent arithmetic, archive, and pairing checks for retained v25 rows.

The audit deliberately does not implement GM25/HD25 decoding or trust the codec
metric helper. The final integrated replay can call the retained CP25 receiver
only for ACK/state reconstruction, then compare its outputs to stored data.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import zlib

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
COMBINED = ROOT / 'experiments/python-game-combined-motion-v25-study'
NATIVE = ROOT / 'experiments/python-game-native-motion-v25-study'
HUD = ROOT / 'experiments/python-game-hud-motion-v25-study'
V24 = ROOT / 'experiments/python-game-standard-v24-study'
CAPPED = ROOT / 'experiments/python-game-capped-key-v25-study'
HUD_WORDS = 21120
CHANNELS_PER_ACTIVE_FRAME = 720 * 405 * 3
IDS_PER_SECOND = 30


def pooled_metric(rows, variant):
    """Recompute pooled MSE/PSNR from retained integer error sums."""
    sse = sum(int(r[variant]['active_squared_error']) for r in rows)
    samples = sum(int(r[variant]['active_channel_samples']) for r in rows)
    if sse < 0 or samples <= 0:
        raise ValueError('nonnegative SSE and positive sample count required')
    mse = sse / samples
    return dict(active_squared_error=sse, active_channel_samples=samples,
                active_mse=mse,
                active_psnr_db=None if mse == 0 else 10 * math.log10(65025 / mse),
                hud_word_errors=sum(int(r[variant]['hud_word_errors']) for r in rows))


def projected_mbps(complete_body_bytes, frames, ids_per_second=IDS_PER_SECOND):
    if type(complete_body_bytes) is not int or complete_body_bytes < 0 or type(frames) is not int or frames <= 0:
        raise ValueError('nonnegative bytes and positive frame count required')
    return complete_body_bytes * 8 * ids_per_second / frames / 1_000_000


def read_object(desc, base_dir):
    """Bounded descriptor verification independent of the benchmark loader."""
    p = Path(desc['path'])
    if p.is_absolute() or '..' in p.parts:
        raise ValueError('unsafe object path')
    stored = (Path(base_dir) / p).read_bytes()
    if hashlib.sha256(stored).hexdigest() != desc['stored_sha256']:
        raise ValueError('stored hash mismatch')
    raw_len = int(desc['raw_bytes'])
    if raw_len < 0 or raw_len > 2_000_000:
        raise ValueError('raw object outside audit bound')
    dec = zlib.decompressobj()
    raw = dec.decompress(stored, raw_len + 1)
    if len(raw) != raw_len or not dec.eof or dec.unused_data or dec.unconsumed_tail:
        raise ValueError('invalid bounded zlib object')
    if hashlib.sha256(raw).hexdigest() != desc['raw_sha256']:
        raise ValueError('raw hash mismatch')
    return raw


def frame_map(rows, id_key='id'):
    out = {}
    for row in rows:
        fid = row[id_key]
        if type(fid) is not int or fid in out:
            raise ValueError('frame IDs must be unique integers')
        out[fid] = row
    return out


def compare_pairing(old_rows, new_rows, *, id_key='id', reference_key='reference_id',
                    allow_reference_policy_change=False):
    """Pair only same IDs; return and disclose reference-ID differences."""
    a, b = frame_map(old_rows, id_key), frame_map(new_rows, id_key)
    if a.keys() != b.keys():
        raise ValueError('source frame ID sets differ')
    changed = []
    for fid in sorted(a):
        if a[fid].get('source_sha256') != b[fid].get('source_sha256'):
            raise ValueError(f'source identity differs at frame {fid}')
        if a[fid].get(reference_key) != b[fid].get(reference_key):
            changed.append(fid)
    if changed and not allow_reference_policy_change:
        raise ValueError('reference policy differs; comparison is confounded')
    return changed


def exact_hud_words(rectangles):
    """Count words in explicit (x,y,w,h) rectangles, rejecting overlap/invalids."""
    checked, total = [], 0
    for rect in rectangles:
        if len(rect) != 4:
            raise ValueError('rectangle arity')
        x, y, w, h = map(int, rect)
        if min(x, y) < 0 or min(w, h) <= 0:
            raise ValueError('rectangle bounds')
        if any(x < ox + ow and ox < x + w and y < oy + oh and oy < y + h for ox, oy, ow, oh in checked):
            raise ValueError('HUD rectangles overlap')
        checked.append((x, y, w, h)); total += w * h
    return total


def assert_packet_composition(row):
    """Check reported inner/outer byte totals against real complete descriptors.

    Expected final row fields are base_packet, hud_packet, complete_packet,
    base_bytes, hud_bytes, complete_bytes. Additional outer overhead can be
    named outer_overhead_bytes; complete CP25 packet length must remain exact.
    """
    names = ('base_packet', 'hud_packet', 'complete_packet')
    sizes = {key: int(row[key]['raw_bytes']) for key in names}
    if sizes['base_packet'] != int(row['base_bytes']) or sizes['hud_packet'] != int(row['hud_bytes']):
        raise ValueError('inner packet size mismatch')
    complete = int(row['complete_bytes'])
    if sizes['complete_packet'] != complete:
        raise ValueError('complete packet size mismatch')
    overhead = int(row.get('outer_overhead_bytes', complete - sizes['base_packet'] - sizes['hud_packet']))
    if overhead < 0 or sizes['base_packet'] + sizes['hud_packet'] + overhead != complete:
        raise ValueError('complete body composition mismatch')
    return dict(base_bytes=sizes['base_packet'], hud_bytes=sizes['hud_packet'],
                outer_overhead_bytes=overhead, complete_bytes=complete)


def quality_from_samples(rows, variant):
    summary = pooled_metric(rows, variant)
    if summary['active_channel_samples'] != len(rows) * CHANNELS_PER_ACTIVE_FRAME:
        raise ValueError('unexpected active sample count')
    return summary


def _load(path):
    return json.loads(Path(path).read_text())


def run_check():
    """Independently check pooled arithmetic and replay ACK/reference lineage."""
    result_path = COMBINED / 'results.json'
    if not result_path.is_file():
        raise RuntimeError('combined v25 results are not frozen/present yet')
    data = _load(result_path)
    if data.get('schema') != 'gamebub-combined-motion-v25':
        raise ValueError('unexpected combined v25 schema: ' + repr(data.get('schema')))
    import importlib.util, sys
    spec = importlib.util.spec_from_file_location('audit_cp25_model', COMBINED / 'model.py')
    model = importlib.util.module_from_spec(spec); sys.modules[spec.name] = model; spec.loader.exec_module(model)
    for p, expected in data['source_sha256'].items():
        path = ROOT / p
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('combined source pin mismatch: ' + p)
    old = _load(V24 / 'results.json')
    native = _load(NATIVE / 'results.json')
    fine_dir = ROOT / 'experiments/python-game-fine-key-v25-study'
    fine = _load(fine_dir / 'results.json')
    capped = _load(CAPPED / 'results.json')
    originals = {x['scene']: x['rows'] for x in old['inputs']}
    base_cases = {}
    for folder, artifact in ((NATIVE, native), (fine_dir, fine), (CAPPED, capped)):
        for case in artifact['cases']:
            base_cases[(folder.relative_to(ROOT).as_posix(), case['scene'], case['profile'])] = case
    hud_by_key = {}
    for hc in data['huds']:
        if len(hc['rows']) != 48 or [r['id'] for r in hc['rows']] != list(range(48)):
            raise ValueError('incomplete HU25 frame sequence')
        total = 0
        for r in hc['rows']:
            packet = read_object(r['packet'], COMBINED)
            if len(packet) != r['bytes'] or len(packet) != r['work']['packet_bytes']:
                raise ValueError('HU25 packet size mismatch')
            total += len(packet)
        if total != hc['summary']['hud_bytes'] or abs(projected_mbps(total,48)-hc['summary']['hud_Mbps_at30']) > 1e-12:
            raise ValueError('HU25 byte/rate summary mismatch')
        hud_by_key[(hc['scene'],hc['policy'])] = hc

    reports = []; rows_seen = words_seen = standards_options = 0
    for case in data['cases']:
        scene, profile, policy = case['scene'], case['profile'], case['hud_policy']
        base = base_cases[(case['base_result_directory'],scene,profile)]
        hcase = hud_by_key[(scene,policy)]
        receiver = model.Receiver(epoch=25); prior_id = None; slot = 0
        sums = {'bare':0,'hybrid':0}; body=basebytes=hudbytes=ackbytes=0
        rows=case['rows']
        if len(rows)!=48: raise ValueError('combined cohort must retain 48 frames')
        for fid,(r,br,hr,sr) in enumerate(zip(rows,base['rows'],hcase['rows'],originals[scene])):
            if [r['id'],br['id'],hr['id'],sr['id']] != [fid]*4: raise ValueError('source/frame IDs differ')
            if r['reference_id'] != br['reference_id'] or r['hud_reference_id'] != hr['reference_id']:
                raise ValueError('base/HUD reference identity mismatch')
            keyframe = fid%24==0; period=int(base['policy'].get('period',1)); publish=keyframe or fid%period==0
            if r['key']!=keyframe or r['publish']!=publish: raise ValueError('key/publish policy mismatch')
            if keyframe: want_id,want_slot=0xffffffff,255; prior_id,slot=None,0
            else: want_id,want_slot=prior_id,slot
            if r['reference_id']!=want_id or r['source_slot']!=want_slot: raise ValueError('reference was not last published bank')
            want_dest=0 if keyframe else (1-slot if publish else 255)
            if r['destination_slot']!=want_dest: raise ValueError('destination bank mismatch')
            directory=ROOT/case['base_result_directory']
            bp=read_object(r['base_packet'],directory); hp=read_object(r['hud_packet'],COMBINED)
            pair=read_object(r['packet'],COMBINED); ack=read_object(r['ack'],COMBINED)
            if len(bp)!=r['base_bytes'] or len(hp)!=r['hud_bytes']: raise ValueError('inner bytes mismatch')
            if len(pair)!=r['body_bytes'] or len(pair)!=len(bp)+len(hp)+60: raise ValueError('CP25 byte composition mismatch')
            if r['binding_bytes']!=60 or len(pair)>model.CAP or len(ack)!=65: raise ValueError('binding/cap/ACK bytes mismatch')
            if r['bare'] != br['bare'] or r['hybrid'] != br['hybrid']:
                raise ValueError('combined quality row is not bound to its native base row')
            parsed=model.parse_pair(pair)
            if parsed['base']!=bp or parsed['hud']!=hp or parsed['frame_id']!=fid: raise ValueError('pair inner bytes/ID mismatch')
            decoded_base,decoded_hud,rebuilt_ack=receiver.receive(pair)
            model.validate_ack(rebuilt_ack,pair)
            if rebuilt_ack!=ack: raise ValueError('ACK did not bind actual CP25 replay')
            # Decoder/ACK replay is intentionally shared CP25 model evidence; our
            # own aggregate math below uses only retained integer row SSE/counts.
            import numpy as np
            source=np.frombuffer(read_object(sr['original_rgb565'],V24),dtype='<u2').reshape(480,720)
            rects=((22,54,160,24),(22,82,160,24),(168,360,320,24),(168,390,240,24))
            if len(decoded_hud)!=4: raise ValueError('exactly four HUD patches required')
            for p,(x,y,w,h) in zip(decoded_hud,rects):
                if tuple(p['rect'])!=(x,y,w,h) or not np.array_equal(p['words'],source[y:y+h,x:x+w]):
                    raise ValueError('decoded HU25 did not reproduce exact source HUD')
            for variant in ('bare','hybrid'):
                sse=int(r[variant]['active_squared_error']); count=int(r[variant]['active_channel_samples'])
                if sse<0 or count!=CHANNELS_PER_ACTIVE_FRAME: raise ValueError('bad per-row SSE or channel count')
                expected_mse=sse/count
                if abs(float(r[variant]['active_mse'])-expected_mse)>1e-12:
                    raise ValueError('per-row MSE does not equal retained SSE/sample count')
                if variant=='hybrid' and r[variant]['hud_word_errors']!=0: raise ValueError('HUD mismatch')
                sums[variant]+=sse
            fragments=math.ceil(len(pair)/1008)
            expected_wire=dict(fragments=fragments,forward_data_ip_udp_bytes=len(pair)+75*fragments,
                               forward_control_ip_udp_bytes=128,reverse_fragment_ip_udp_bytes=57*fragments,
                               reverse_gate_ip_udp_bytes=192,reverse_joint_ack_ip_udp_bytes=65+28)
            if r['wire']!=expected_wire: raise ValueError('forward/control/reverse/ACK byte model mismatch')
            body+=len(pair); basebytes+=len(bp); hudbytes+=len(hp); ackbytes+=len(ack)
            rows_seen+=1; words_seen+=HUD_WORDS
            if publish: prior_id,slot=fid,want_dest
        sse=sums['hybrid']; samples=48*CHANNELS_PER_ACTIVE_FRAME; summary=case['summary']
        expected={'complete_bytes':body,'base_bytes':basebytes,'hud_bytes':hudbytes,'binding_bytes':48*60,
                  'ack_bytes':ackbytes,'active_squared_error':sse,'active_channel_samples':samples,
                  'exact_hud_words':48*HUD_WORDS,'max_complete_bytes':max(r['body_bytes'] for r in rows),
                  'cap_fit_frames':sum(r['body_bytes']<=model.CAP for r in rows)}
        for k,v in expected.items():
            if summary.get(k)!=v: raise ValueError(f'{k} summary mismatch for {profile}')
        if abs(summary['active_mse']-sse/samples)>1e-12: raise ValueError('pooled MSE mismatch')
        if abs(summary['coded_body_Mbps_at30']-projected_mbps(body,48))>1e-12: raise ValueError('body rate mismatch')
        expected_forward=sum(r['wire']['forward_data_ip_udp_bytes']+r['wire']['forward_control_ip_udp_bytes'] for r in rows)*8*30/48/1e6
        expected_reverse=sum(sum(r['wire'][k] for k in ('reverse_fragment_ip_udp_bytes','reverse_gate_ip_udp_bytes','reverse_joint_ack_ip_udp_bytes')) for r in rows)*8*30/48/1e6
        if abs(summary['hypothetical_forward_Mbps_at30']-expected_forward)>1e-12 or abs(summary['hypothetical_reverse_Mbps_at30']-expected_reverse)>1e-12:
            raise ValueError('projected forward/reverse control rate mismatch')
        # Use the actual frozen HEVC operating point, not rounded invented rate
        # or MSE thresholds. Keep the old custom-quality milestone separate.
        target = next(p['lowest_bytes_measured_at_least_target_quality']
                      for p in old['operating_points']
                      if p['scene'] == scene and p['custom_profile'] == 'adaptive_plain'
                      and p['variant'] == 'hybrid' and p['codec'] == 'libx265')
        target_rate = projected_mbps(target['bytes'], 48)
        target_mse = target['mse']
        old_custom_mse = next(c['summary']['hybrid']['active_mse']
                              for c in old['custom_baselines']
                              if c['scene'] == scene and c['profile'] == 'adaptive_plain')
        base_work = base['summary']
        retained_arrays = max(int(r['work']['analysis']['retained_analysis_array_bytes']) for r in base['rows'])
        paid_rdo_zeroed = sum(int(r['work']['rdo']['zeroed_blocks']) for r in base['rows'])
        reports.append(dict(scene=scene,profile=profile,hud_policy=policy,frames=48,body_bytes=body,
                            body_Mbps_at30=projected_mbps(body,48),base_bytes=basebytes,hud_bytes=hudbytes,
                            binding_bytes=48*60,active_sse=sse,active_samples=samples,active_mse=sse/samples,
                            base_Mbps_at30=projected_mbps(basebytes,48),
                            complete_body_rate_target_Mbps=target_rate,active_mse_target=target_mse,
                            goal_scope='Exact frozen v24 HEVC rate/MSE pair with its old HUD, not a same-HU25 or matched-quality comparison.',
                            complete_body_goal_met=projected_mbps(body,48)<=target_rate and sse/samples<=target_mse,
                            old_custom_mse_threshold=old_custom_mse,
                            meets_old_custom_mse=sse/samples<=old_custom_mse,
                            host_base_encode_mean_ms=base_work['mean_encode_ms'],
                            host_hud_encode_mean_ms=hcase['summary']['mean_paid_encode_ms'],
                            host_encoder_combined_mean_ms=base_work['mean_encode_ms']+hcase['summary']['mean_paid_encode_ms'],
                            motion_search_sample_comparisons=base_work['search_sample_comparisons'],
                            decoder_reference_sample_reads=base_work['decoder_reference_sample_reads'],
                            reconstructed_reference_write_bytes=base_work['reconstructed_reference_write_bytes'],
                            retained_analysis_array_bytes_peak=retained_arrays,
                            lossy_rdo_zeroed_coeff_blocks=paid_rdo_zeroed,
                            exact_hud_words=48*HUD_WORDS))

    # Rejected fine-key cohorts are diagnostics only. Rebuild the exact sealed
    # over-cap pair and verify that the real CP25 parser refuses each one.
    rejected_rows = rejected_packets = 0
    for rejected in data.get('rejected_cohorts', []):
        if rejected.get('timeline_accepted') is not False or not rejected.get('failed_ids'):
            raise ValueError('rejected cohort must remain unaccepted and identify its failures')
        if len(rejected['rows']) != 48:
            raise ValueError('rejected diagnostics must retain all48 accounting rows')
        failed = []
        for rr in rejected['rows']:
            rejected_rows += 1
            total = int(rr['base_bytes']) + int(rr['hud_bytes']) + int(rr['binding_bytes'])
            if total != int(rr['complete_bytes']):
                raise ValueError('rejected complete-byte arithmetic mismatch')
            if total > model.CAP:
                if not rr.get('attempted_packet'):
                    raise ValueError('over-cap row lacks retained attempted pair')
                attempted = read_object(rr['attempted_packet'], COMBINED)
                if len(attempted) != total:
                    raise ValueError('over-cap attempted pair length mismatch')
                try:
                    model.parse_pair(attempted)
                except ValueError:
                    pass
                else:
                    raise ValueError('CP25 parser accepted an over-cap pair')
                failed.append(rr['id']); rejected_packets += 1
            elif rr.get('attempted_packet'):
                raise ValueError('under-cap diagnostic unexpectedly has failed packet')
        if failed != rejected['failed_ids']:
            raise ValueError('rejected frame IDs mismatch')

    # Validate the claimed old-v24 comparison separately from actual new-HU25
    # standard projections. There is no invented same-GM25/old-HUD counterfactual.
    for comp in data['comparisons']:
        scene,profile,policy=comp['scene'],comp['profile'],comp['hud_policy']
        case=next(c for c in data['cases'] if (c['scene'],c['profile'],c['hud_policy'])==(scene,profile,policy))
        oldcustom=next(c for c in old['custom_baselines'] if c['scene']==scene and c['profile']=='adaptive_plain')['summary']['hybrid']
        if comp['old_custom_hybrid']!=oldcustom: raise ValueError('frozen v24 target mismatch')
        if abs(comp['byte_saving_vs_old_custom']-(1-case['summary']['complete_bytes']/oldcustom['complete_bytes']))>1e-12:
            raise ValueError('old custom byte comparison mismatch')
        for std in comp['standards']:
            eligible = []
            for option in std['sampled_options']:
                oldstd=next(c for c in old['cases'] if c['scene']==scene and c['codec']==std['codec'] and c['profile']==option['profile'])
                hrows=hud_by_key[(scene,policy)]['rows']
                expected=sum(x['coded_access_unit_bytes']+h['bytes']+60 for x,h in zip(oldstd['rows'],hrows))
                if option['projected_same_HU25_bytes']!=expected: raise ValueError('same-HU25 standards byte projection mismatch')
                if option['hybrid_mse']!=oldstd['summary']['hybrid']['active_mse']: raise ValueError('standard MSE association mismatch')
                if option['at_least_custom_measured_quality'] != (option['hybrid_mse'] <= case['summary']['active_mse']):
                    raise ValueError('standard selection did not use this new custom case MSE')
                if option['at_least_custom_measured_quality']: eligible.append(option)
                standards_options+=1
            selected = min(eligible, key=lambda x:x['projected_same_HU25_bytes']) if eligible else None
            if std['selected_same_HU25'] != selected:
                raise ValueError('same-HU25 standard operating-point selection mismatch')

    # Pixel/hash replay is separately retained in the campaign's verified log;
    # this audit does not duplicate its full-canvas metric pass.
    if rows_seen != data['counts']['joint_decisions'] or words_seen != data['counts']['exact_hud_words']:
        raise ValueError('campaign row/HUD word count mismatch')
    if rows_seen != 1344 or words_seen != 1344*HUD_WORDS:
        raise ValueError('accepted campaign should contain28 complete48-frame cohorts')
    own_paths=('experiments/python-game-audit-v25-study/audit.py',
               'experiments/python-game-audit-v25-study/test_audit.py',
               'experiments/python-game-audit-v25-study/AUDIT-CHECKLIST.md')
    source_pins=dict(data['source_sha256'])
    source_pins['experiments/python-game-combined-motion-v25-study/results.json'] = hashlib.sha256(result_path.read_bytes()).hexdigest()
    source_pins['experiments/python-game-combined-motion-v25-study/verify.py'] = hashlib.sha256((COMBINED/'verify.py').read_bytes()).hexdigest()
    source_pins['experiments/python-game-combined-motion-v25-study/verify.log'] = hashlib.sha256((COMBINED/'verify.log').read_bytes()).hexdigest()
    for relative in own_paths:
        source_pins[relative] = hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()
    return dict(schema='gamebub-independent-audit-v25',combined_results_sha256=hashlib.sha256(result_path.read_bytes()).hexdigest(),
                source_sha256=source_pins,
                source_pins_checked=len(data['source_sha256']),combined_rows_replayed=rows_seen,
                exact_HUD_words_rechecked=words_seen,standards_same_HU25_options_recomputed=standards_options,
                rejected_diagnostic_rows=rejected_rows,actual_overcap_packets_rejected=rejected_packets,
                cases=reports,decoder_evidence=dict(shared_CP25_receiver_rows_replayed=rows_seen,
                                                    full_RGB_plane_HUD_hash_metric_replay='separate combined/verify.py; see pinned verify.log'),
                quality_math='pooled from retained integer row SSE and RGB565 active channel counts',
                decoder_scope='Shared CP25 Receiver supplies syntax/reference/ACK replay; it is not independent RTL proof.',
                physical_30fps_proven=False,
                limitations=['Two reused precompressed windows; projected rate uses nominal 30 IDs/s.',
                             'Key period, quantizer map and lossy RDO vary by profile, confounding pure motion/entropy attribution.',
                             'Standards plus HU25 values are prospective CP25 envelope accounting.'])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true', help='run independent checks against frozen combined results')
    args = ap.parse_args()
    if not args.check:
        ap.error('use --check')
    result = run_check()
    (HERE / 'audit.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    combined = _load(COMBINED / 'results.json')
    pins = dict(schema='gamebub-audit-sourcepins-v25',
                audit_files={name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
                             for name in ('audit.py', 'test_audit.py', 'AUDIT-CHECKLIST.md')},
                combined_results_sha256=hashlib.sha256((COMBINED / 'results.json').read_bytes()).hexdigest(),
                combined_source_sha256=combined['source_sha256'])
    (HERE / 'sourcepins.json').write_text(json.dumps(pins, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
