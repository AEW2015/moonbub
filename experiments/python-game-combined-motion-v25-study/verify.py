#!/usr/bin/env python3
"""Offline retained CP25 replay, source metrics and complete-byte accounting.

No encoder, benchmark rerun, media fetch, standard codec or hardware required.
This independently replays the frozen Python receiver, not an RTL decoder.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import struct
import zlib
import numpy as np
import model as m

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
V24 = HERE.parent / 'python-game-standard-v24-study'
RECTS = ((22, 54, 160, 24), (22, 82, 160, 24), (168, 360, 320, 24), (168, 390, 240, 24))
SAMPLES = 720 * 405 * 3


def check(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def safe_path(directory, value):
    check(type(value) is str, 'path string')
    relative = Path(value)
    check(not relative.is_absolute() and '..' not in relative.parts, 'relative bounded path')
    actual = (directory / relative).resolve()
    check(actual.is_relative_to(directory.resolve()), 'path escapes retained directory')
    return actual


def raw(desc, directory=HERE, maximum=1_000_000):
    check(type(desc) is dict and type(desc.get('raw_bytes')) is int
          and 0 < desc['raw_bytes'] <= maximum, 'descriptor bounded raw size')
    path = safe_path(directory, desc['path'])
    check(path.stat().st_size <= maximum + 65536, 'stored object size bound')
    stored = path.read_bytes()
    check(sha(stored) == desc['stored_sha256'], 'stored object SHA256')
    decoder = zlib.decompressobj()
    output = decoder.decompress(stored, desc['raw_bytes'] + 1)
    check(decoder.eof and not decoder.unused_data and not decoder.unconsumed_tail,
          'one complete bounded zlib stream')
    check(len(output) == desc['raw_bytes'] and sha(output) == desc['raw_sha256'],
          'raw object length/SHA256')
    return output


def pins(data):
    check(type(data.get('source_sha256')) is dict and bool(data['source_sha256']), 'source snapshot map')
    for relative, digest in data['source_sha256'].items():
        check(sha(safe_path(ROOT, relative).read_bytes()) == digest, 'source snapshot changed: ' + relative)
    return len(data['source_sha256'])


def words_digest(words):
    return sha(np.ascontiguousarray(words).tobytes())


def metric(original, decoded):
    error = (m.base.C.corpus.expand565(original).astype(np.int64)
             - m.base.C.corpus.expand565(decoded).astype(np.int64)) ** 2
    squared = int(error[37:442].sum())
    return dict(active_squared_error=squared, active_channel_samples=SAMPLES,
                active_mse=squared / SAMPLES,
                active_psnr_db=None if not squared else 10 * math.log10(65025 / (squared / SAMPLES)),
                hud_word_errors=sum(int(np.count_nonzero(original[y:y+h, x:x+w]
                                                         != decoded[y:y+h, x:x+w]))
                                    for x, y, w, h in RECTS))


def wire(body):
    fragments = math.ceil(body / 1008)
    return dict(fragments=fragments, forward_data_ip_udp_bytes=body + fragments * 75,
                forward_control_ip_udp_bytes=128, reverse_fragment_ip_udp_bytes=fragments * 57,
                reverse_gate_ip_udp_bytes=192, reverse_joint_ack_ip_udp_bytes=65 + 28)


def summary(rows):
    count = len(rows)
    total = sum(r['body_bytes'] for r in rows)
    s = sum(r['hybrid']['active_squared_error'] for r in rows)
    samples = sum(r['hybrid']['active_channel_samples'] for r in rows)
    return dict(frames=count, complete_bytes=total, coded_body_Mbps_at30=total*8*30/count/1e6,
                base_bytes=sum(r['base_bytes'] for r in rows), hud_bytes=sum(r['hud_bytes'] for r in rows),
                binding_bytes=sum(r['binding_bytes'] for r in rows), max_complete_bytes=max(r['body_bytes'] for r in rows),
                cap_fit_frames=sum(r['body_bytes'] <= m.CAP for r in rows),
                active_squared_error=s, active_channel_samples=samples, active_mse=s/samples,
                active_psnr_db=10*math.log10(65025/(s/samples)),
                hud_word_errors=sum(r['hybrid']['hud_word_errors'] for r in rows), exact_hud_words=21120*count,
                ack_bytes=sum(r['ack']['raw_bytes'] for r in rows),
                hypothetical_forward_Mbps_at30=sum(r['wire']['forward_data_ip_udp_bytes']+r['wire']['forward_control_ip_udp_bytes'] for r in rows)*8*30/count/1e6,
                hypothetical_reverse_Mbps_at30=sum(sum(r['wire'][k] for k in ('reverse_fragment_ip_udp_bytes','reverse_gate_ip_udp_bytes','reverse_joint_ack_ip_udp_bytes')) for r in rows)*8*30/count/1e6,
                mean_paid_base_hud_encode_ms=sum(r['base_encode_ms']+r['hud_encode_ms'] for r in rows)/count,
                mean_joint_receive_ms=sum(r['receive_ms'] for r in rows)/count,
                mean_pair_bind_parse_ms=sum(r['bind_ms'] for r in rows)/count,
                mean_sender_ack_validation_ms=sum(r['ack_validation_ms'] for r in rows)/count)


def exact_hud(decoded, original):
    check(tuple(tuple(p['rect']) for p in decoded) == RECTS, 'exact four HUD rectangles/order')
    for patch, (x, y, w, h) in zip(decoded, RECTS):
        np.testing.assert_array_equal(patch['words'], original[y:y+h, x:x+w])


def verify(path):
    data = load(path)
    check(data['schema'] == 'gamebub-combined-motion-v25', 'combined schema')
    pin_count = pins(data)
    old = load(V24 / 'results.json'); pins(old)
    check(len(old['inputs']) == 2, 'two retained native windows')
    originals, input_rows = {}, {}
    for inp in old['inputs']:
        check([r['id'] for r in inp['rows']] == list(range(48)), '48 retained source IDs')
        for row in inp['rows']:
            original = raw(row['original_rgb565'], V24)
            common = raw(row['common_yuv420_u8'], V24)
            check(len(original) == 691200 and len(common) == 518400, 'native source geometry')
            check(sha(common) == row['common_yuv420_u8_sha256'], 'common source binding')
            key = inp['scene'], row['id']
            originals[key] = np.frombuffer(original, '<u2').reshape(480, 720)
            input_rows[key] = row

    base_cases = {}
    capped_attempts = capped_rejected_attempts = 0
    source_pin_count = 0
    for directory in ('python-game-native-motion-v25-study', 'python-game-fine-key-v25-study',
                      'python-game-capped-key-v25-study'):
        folder = HERE.parent / directory; source = load(folder / 'results.json')
        source_pin_count += pins(source)
        for case in source['cases']:
            key = folder.relative_to(ROOT).as_posix(), case['scene'], case['profile']
            check(key not in base_cases, 'unique source base cohort')
            base_cases[key] = case
            if directory == 'python-game-capped-key-v25-study':
                for row in case['rows']:
                    attempts = row['attempts']
                    check(type(attempts) is list and 1 <= len(attempts) <= 2, 'bounded causal capped attempts')
                    check(attempts[0]['background'] == 16 and attempts[-1]['admitted'] is True,
                          'fine-first attempt and an admitted last candidate')
                    if len(attempts) == 2:
                        check(row['key'] and attempts[0]['admitted'] is False and attempts[1]['background'] == 32,
                              'coarse key fallback only after actual fine-key rejection')
                    check(row['base_packet'] == attempts[-1]['packet']
                          and row['selected_background'] == attempts[-1]['background'], 'selected last admitted base packet')
                    hp = raw(row['hud_packet'], folder, maximum=m.CAP)
                    for attempt in attempts:
                        packet = raw(attempt['packet'], folder, maximum=2*m.CAP)
                        total = len(packet) + len(hp) + 60
                        fits = total <= m.CAP
                        check(attempt['base_bytes'] == len(packet) and attempt['hud_bytes'] == len(hp)
                              and attempt['binding_bytes'] == 60 and attempt['complete_bytes'] == total
                              and attempt['admitted'] is fits, 'actual causal candidate complete cap')
                        check(attempt['rejection_reason'] == (None if fits else 'complete_CP25_exceeds_49152'),
                              'candidate rejection reason')
                        meta = m.base.parse(packet, expected_epoch=25)
                        check(meta['frame_id'] == row['id'] and meta['key'] == row['key']
                              and meta['reference_id'] == row['reference_id'], 'attempt packet actual source/reference identity')
                        check(attempt['work']['forward_plane_calls'] == 0
                              and attempt['work']['analysis_paid_separately'] is True,
                              'all candidate maps share the paid causal analysis')
                        capped_attempts += 1
                        capped_rejected_attempts += int(not fits)
                    check(row['work']['encoder_wall_ms'] == row['analysis_wall_ms']
                          + sum(a['encode_wall_ms'] for a in attempts), 'all capped attempts and analysis paid')
    check(capped_attempts == 194 and capped_rejected_attempts == 2, '192 capped selections plus2 paid rejected fine-key attempts')
    check(len(base_cases) == 28, 'all18 native,6 fine-key and4 capped-key base cohorts')
    all_cases = {(directory, scene, profile, 'motion') for directory, scene, profile in base_cases}
    all_cases |= {(directory, scene, profile, 'no_motion') for directory, scene, profile in base_cases
                  if profile in ('finekey_zero', 'capped_key_zero')}

    hud_lookup = {}
    hud_frames = 0
    for hud in data['huds']:
        key = hud['scene'], hud['policy']
        check(key not in hud_lookup and hud['policy'] in ('motion', 'no_motion'), 'unique HUD cohort')
        check([r['id'] for r in hud['rows']] == list(range(48)), 'HUD IDs')
        previous, previous_id = None, m.NO_REF
        for row in hud['rows']:
            fid = row['id']; independent = fid in (0, 24)
            if independent: previous, previous_id = None, m.NO_REF
            packet = raw(row['packet'], maximum=m.CAP)
            decoded, meta = m.decode_hud(packet, previous, expected_epoch=25,
                                          expected_reference_id=None if independent else previous_id)
            check(row['key'] == independent and row['reference_id'] == previous_id, 'HUD reference lineage')
            check(meta['frame_id'] == fid and meta['reference_id'] == previous_id, 'HU25 actual frame lineage')
            check(meta['reconstructed_tag'].hex() == row['reconstructed_tag'], 'retained HUD tag')
            check(len(packet) == row['bytes'] == row['work']['packet_bytes'], 'retained HUD byte sizes')
            check(row['paid_encode_ms'] == row['legacy_encode_ms'] + row['work']['encode_wall_ms'], 'paid HUD work arithmetic')
            exact_hud(decoded, originals[(hud['scene'], fid)])
            previous, previous_id = decoded, fid; hud_frames += 1
        expected = dict(frames=48, hud_bytes=sum(r['bytes'] for r in hud['rows']),
                        hud_Mbps_at30=sum(r['bytes'] for r in hud['rows'])*5/1e6,
                        mean_paid_encode_ms=sum(r['paid_encode_ms'] for r in hud['rows'])/48)
        check(expected == hud['summary'], 'HUD summary arithmetic')
        hud_lookup[key] = hud
    check(set(hud_lookup) == {(scene, policy) for scene in {k[0] for k in originals} for policy in ('motion', 'no_motion')}, 'all four HUD cohorts')

    expected_cases, expected_rejected = set(), set()
    for identity in all_cases:
        source_case = base_cases[identity[:3]]
        hud = hud_lookup[(identity[1], identity[3])]
        fits = all(b['base_bytes'] + h['bytes'] + 60 <= m.CAP
                   for b, h in zip(source_case['rows'], hud['rows']))
        (expected_cases if fits else expected_rejected).add(identity)
    check(len(all_cases) == 32 and len(expected_cases) == 28 and len(expected_rejected) == 4,
          'actual complete-cap classification:28 accepted and4 rejected whole cohorts')

    pairs = ack_bytes = complete_bytes = all_hud_words = 0
    seen_cases = set()
    for case in data['cases']:
        identity = case['base_result_directory'], case['scene'], case['profile'], case['hud_policy']
        check(identity in expected_cases and identity not in seen_cases, 'combined cohort coverage')
        seen_cases.add(identity)
        source_case = base_cases[identity[:3]]
        check(case['policy'] == source_case['policy'], 'base policy binding')
        check([r['id'] for r in case['rows']] == list(range(48)), 'combined IDs')
        hud_rows = hud_lookup[(case['scene'], case['hud_policy'])]['rows']
        receiver = m.Receiver(epoch=25)
        folder = safe_path(ROOT, case['base_result_directory'])
        for row, original_base, original_hud in zip(case['rows'], source_case['rows'], hud_rows):
            fid = row['id']; source = input_rows[(case['scene'], fid)]
            for field in ('id', 'key', 'publish', 'reference_id', 'source_slot', 'destination_slot',
                          'bare', 'hybrid', 'reconstructed_yuv_tag', 'bare_rgb565_sha256', 'hybrid_rgb565_sha256'):
                check(row[field] == original_base[field], 'base row source binding: ' + field)
            for field, source_field in (('source_input_sha256', 'input_rgb_sha256'),
                                        ('source_common_yuv_sha256', 'common_yuv420_u8_sha256')):
                if field in original_base:
                    check(original_base[field] == source[source_field], 'original source hash binding')
            check(row['hud_reference_id'] == original_hud['reference_id'], 'HUD row reference binding')
            check(row['base_packet']['directory'] == case['base_result_directory'], 'base object directory')
            for field in ('path', 'raw_bytes', 'raw_sha256', 'stored_sha256'):
                check(row['base_packet'][field] == original_base['base_packet'][field], 'base descriptor binding')
            check(row['hud_packet'] == original_hud['packet'], 'HUD descriptor binding')
            pair = raw(row['packet'], maximum=m.CAP)
            retained_ack = raw(row['ack'], maximum=65)
            base_packet = raw(row['base_packet'], folder, maximum=m.CAP)
            hud_packet = raw(row['hud_packet'], maximum=m.CAP)
            parsed = m.parse_pair(pair)
            check(parsed['base'] == base_packet and parsed['hud'] == hud_packet, 'actual pair inner bytes')
            check(parsed['frame_id'] == fid and parsed['epoch'] == 25, 'actual pair identity')
            bare_yuv, decoded_hud, rebuilt_ack = receiver.receive(pair)
            check(rebuilt_ack == retained_ack, 'actual ACK exact reconstruction')
            check(m.validate_ack(retained_ack, pair) == row['ack_meta'], 'ACK metadata binding')
            check(m.base.C.reference_tag(bare_yuv).hex() == row['reconstructed_yuv_tag'], 'replayed YUV content tag')
            bare = m.base.C.corpus.rgb565(m.base.ft.planes_to_rgb(bare_yuv))
            original = originals[(case['scene'], fid)]
            exact_hud(decoded_hud, original)
            hybrid = bare.copy()
            for patch in decoded_hud:
                x, y, w, h = patch['rect']; hybrid[y:y+h, x:x+w] = patch['words']
            check(words_digest(bare) == row['bare_rgb565_sha256'], 'bare RGB565 hash')
            check(words_digest(hybrid) == row['hybrid_rgb565_sha256'], 'hybrid RGB565 hash')
            check(metric(original, bare) == row['bare'] and metric(original, hybrid) == row['hybrid'], 'frozen original-word RGB quality')
            check(row['hybrid']['hud_word_errors'] == 0, 'exact HUD word error count')
            check(row['base_bytes'] == len(base_packet) and row['hud_bytes'] == len(hud_packet)
                  and row['binding_bytes'] == 60 and row['body_bytes'] == len(pair)
                  and len(pair) == len(base_packet)+len(hud_packet)+60 <= m.CAP, 'actual complete cap/byte decomposition')
            check(row['wire'] == wire(len(pair)), 'hypothetical transport arithmetic')
            check(row['base_encode_ms'] == original_base['work']['encoder_wall_ms']
                  and row['hud_encode_ms'] == original_hud['paid_encode_ms'], 'retained measured work binding')
            pairs += 1; ack_bytes += len(retained_ack); complete_bytes += len(pair); all_hud_words += 21120
        check(summary(case['rows']) == case['summary'], 'complete cohort summary arithmetic')
    check(seen_cases == expected_cases and len(seen_cases) == 28, 'all28 admitted combined cohorts')
    check(pairs == 1344 and data['counts'] == dict(native_source_frames=96, joint_decisions=pairs,
                                                  exact_hud_words=all_hud_words), 'combined retained counts')

    rejected_rows = overcap_packets = 0
    seen_rejected = set()
    for case in data['rejected_cohorts']:
        identity = case['base_result_directory'], case['scene'], case['profile'], case['hud_policy']
        check(identity in expected_rejected and identity not in seen_rejected, 'rejected cohort coverage')
        seen_rejected.add(identity)
        check(case['timeline_accepted'] is False and bool(case['reason']), 'no accepted rejected timeline')
        check([r['id'] for r in case['rows']] == list(range(48)), '48 diagnostic component rows')
        source_case = base_cases[identity[:3]]
        hud_rows = hud_lookup[(case['scene'], case['hud_policy'])]['rows']
        folder = safe_path(ROOT, case['base_result_directory'])
        failed, diagnostic_banks = [], [None, None]
        receiver = m.Receiver(epoch=25)
        for row, component, hud in zip(case['rows'], source_case['rows'], hud_rows):
            fid = row['id']; check(fid == component['id'] == hud['id'], 'diagnostic IDs')
            bp = raw(component['base_packet'], folder, maximum=m.CAP)
            hp = raw(hud['packet'], maximum=m.CAP)
            body_bytes = len(bp) + len(hp) + 60
            fits = body_bytes <= m.CAP
            check(row['base_bytes'] == component['base_bytes'] == len(bp)
                  and row['hud_bytes'] == hud['bytes'] == len(hp)
                  and row['binding_bytes'] == 60 and row['complete_bytes'] == body_bytes
                  and row['fits'] is fits, 'diagnostic actual complete byte decomposition')
            # Component replay is explicitly diagnostic. These reconstructed
            # banks never populate the CP25 receiver or establish acceptance.
            if component['key']:
                diagnostic_banks = [None, None]
                reference, reference_id = None, None
            else:
                bank = diagnostic_banks[component['source_slot']]
                check(bank is not None and bank[0] == component['reference_id'], 'diagnostic component reference lineage')
                reference_id, reference = bank
            output, meta = m.base.decode(bp, reference, expected_epoch=25,
                                         expected_reference_id=reference_id)
            check(meta['frame_id'] == fid and meta['key'] == component['key']
                  and meta['reference_id'] == component['reference_id'], 'diagnostic actual GM25 identities')
            check(meta['reconstructed_tag'].hex() == component['reconstructed_yuv_tag'], 'diagnostic reconstructed YUV tag')
            original = originals[(case['scene'], fid)]
            bare = m.base.C.corpus.rgb565(m.base.ft.planes_to_rgb(output))
            hybrid = bare.copy()
            for x, y, w, h in RECTS: hybrid[y:y+h, x:x+w] = original[y:y+h, x:x+w]
            check(words_digest(bare) == component['bare_rgb565_sha256']
                  and words_digest(hybrid) == component['hybrid_rgb565_sha256'], 'diagnostic decoded RGB565 hashes')
            check(metric(original, bare) == component['bare'] and metric(original, hybrid) == component['hybrid'],
                  'diagnostic component original-word RGB metrics')
            if component['publish']:
                diagnostic_banks[component['destination_slot']] = fid, output
            if not fits:
                failed.append(fid)
                attempted = raw(row['attempted_packet'], maximum=2*m.CAP)
                check(len(attempted) == body_bytes and len(attempted) > m.CAP, 'retained actual overcap pair')
                check(zlib.crc32(attempted[:-4]) == struct.unpack('<I', attempted[-4:])[0], 'overcap pair real CRC')
                fields = m.PAIR.unpack_from(attempted)
                flags = (m.KEY if component['key'] else 0) | (m.PUBLISH if component['publish'] else 0)
                check(fields == (b'CP25', 1, flags, 25, fid, component['source_slot'],
                                 component['destination_slot'], len(bp), len(hp), m.digest(bp), m.digest(hp)),
                      'overcap pair complete header bindings')
                check(attempted[m.PAIR.size:-4] == bp + hp, 'overcap actual GM25/HU25 payload bytes')
                before = (receiver.banks, receiver.hud, receiver.hud_id, receiver.hud_tag,
                          receiver.last_frame_id, receiver.last_ack)
                for operation in (m.parse_pair, receiver.receive):
                    try:
                        operation(attempted)
                    except ValueError:
                        pass
                    else:
                        raise ValueError('overcap packet unexpectedly accepted')
                check(before == (receiver.banks, receiver.hud, receiver.hud_id, receiver.hud_tag,
                                  receiver.last_frame_id, receiver.last_ack), 'overcap failure mutated receiver')
                overcap_packets += 1
            else:
                check('attempted_packet' not in row, 'fitting diagnostic row has no failed-packet artifact')
            rejected_rows += 1
        check(failed == case['failed_ids'] and bool(failed), 'actual rejected frame IDs')
        check(receiver.last_frame_id == -1 and receiver.last_ack is None,
              'rejected cohort never advances accepted receiver history')
    check(seen_rejected == expected_rejected and rejected_rows == 192, 'all4 rejected cohorts/192 diagnostic rows')
    return dict(verified_source_pins=pin_count, verified_upstream_pin_bindings=source_pin_count,
                retained_native_sources=len(originals), replayed_HU25_packets=hud_frames,
                replayed_CP25_pairs=pairs, exact_JA25_acks=pairs, replayed_cases=len(seen_cases),
                complete_pair_bytes=complete_bytes, reverse_ack_bytes=ack_bytes,
                exact_hud_words=all_hud_words, verified_decoded_coded_pixels=pairs*720*480,
                rejected_cohorts=len(seen_rejected), rejected_component_rows=rejected_rows,
                rejected_actual_overcap_CP25_packets=overcap_packets,
                verified_capped_base_attempts=capped_attempts,
                verified_capped_rejected_fine_key_attempts=capped_rejected_attempts,
                reconstructed_from_retained_packets_only=True, hardware_fps_proven=False,
                independent_RTL_decoder=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--results', type=Path, default=HERE / 'results.json')
    args = parser.parse_args()
    print(json.dumps(verify(args.results), indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
