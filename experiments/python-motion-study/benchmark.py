#!/usr/bin/env python3
"""MT02 actual-packet compression/commit study; ACK timing is not simulated."""
import hashlib
import json
from pathlib import Path
import time

import numpy as np

import corpus_support as support
import motion_codec as mc

HERE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def distribution(values):
    return {name: float(value) for name, value in zip(('mean', 'p50', 'p95', 'max'),
            (np.mean(values), *np.percentile(values, [50, 95]), max(values)))}


def run_profile(scene, scale, mode, epoch, faults=False):
    if not scene['frames']:
        raise ValueError('empty scene')
    enc, dec = mc.Encoder(epoch), mc.Receiver(epoch)
    records = []
    failure_events = []
    for index, source in enumerate(scene['frames']):
        start = time.perf_counter_ns()
        packet = enc.prepare(source, index, quant_scale=scale,
                             mode='zero' if mode == 'intra' else mode,
                             force_key=mode == 'intra' or index % 30 == 0)
        encoded = time.perf_counter_ns()
        expected = enc.prepared_rgb()
        fields = mc.HEADER.unpack_from(packet)
        row = {'index': index, 'input_sha256': scene['manifest']['frame_sha256'][index],
               'bytes': len(packet), 'wire_bytes': support.pacing.wire_bytes(len(packet)),
               'key': fields[4] == mc.NO_REF, 'reference_id': None if fields[4] == mc.NO_REF else fields[4],
               'dx': fields[8], 'dy': fields[9], 'encode_ms_python': (encoded-start)/1e6,
               'delivered': False, 'receiver_committed': False}
        if faults and index == 7:
            enc.abort()
            failure_events.append({'frame': index, 'fault': 'data_loss', 'action': 'timeout; next independent'})
        else:
            damaged = packet
            if faults and index == 23:
                damaged = packet[:-1]+bytes([packet[-1]^1])
            before = dec.reference_id
            try:
                begin_decode = time.perf_counter_ns()
                actual, info = dec.receive(damaged)
                decoded = time.perf_counter_ns()
            except ValueError:
                if not (faults and index == 23):
                    raise
                if dec.reference_id != before:
                    raise AssertionError('failed packet changed receiver reference')
                enc.abort()
                failure_events.append({'frame': index, 'fault': 'CRC_corruption', 'action': 'reject; next independent'})
            else:
                if not np.array_equal(actual, expected):
                    raise AssertionError('encoder and receiver references drifted')
                row.update(delivered=True, receiver_committed=True, accounting=info,
                           decode_ms_python=(decoded-begin_decode)/1e6,
                           output_rgb565_sha256=hashlib.sha256(support.corpus.rgb565(actual).astype('<u2').tobytes()).hexdigest(),
                           quality=support.corpus.metrics(source, support.corpus.expand565(support.corpus.rgb565(actual)),
                                                         tuple(scene['manifest']['active_rects'][index])))
                if faults and index == 17:
                    enc.abort()
                    failure_events.append({'frame': index, 'fault': 'ACK_loss_after_commit', 'action': 'timeout; next independent'})
                else:
                    enc.ack(info['frame_id'], epoch=info['epoch'])
        records.append(row)
    sizes = [x['bytes'] for x in records]
    wire = [x['wire_bytes'] for x in records]
    valid = [x for x in records if x['receiver_committed']]
    mse = float(np.mean([x['quality']['active']['mse'] for x in valid]))
    psnr = None if mse == 0 else float(10*np.log10(65025/mse))
    candidates = [(quality, row) for quality, row in scene['jpeg'].items()
                  if row['pooled_active_psnr_db'] is not None]
    nearest = min(candidates, key=lambda x: abs(x[1]['pooled_active_psnr_db']-psnr)) if psnr is not None and candidates else None
    return {'profile': f'MT02-{mode}-q{scale}'+('-faults' if faults else ''),
            'frames_attempted': len(records), 'receiver_committed': len(valid),
            'keyframes': sum(x['key'] for x in records),
            'nonzero_vectors': sum(bool(x['dx'] or x['dy']) for x in records),
            'packet_bytes': distribution(sizes), 'wire_mbps_projected_30fps': float(np.mean(wire)*8*30/1e6),
            'over_48k': sum(x > 49152 for x in sizes), 'over_256k': sum(x > 262144 for x in sizes),
            'pooled_active_psnr_db_committed_frames': psnr, 'exact_committed_frames': mse == 0,
            'nearest_jpeg_quality_by_psnr': int(nearest[0]) if nearest is not None and not faults else None,
            'nearest_jpeg_psnr_difference_db': None if faults or nearest is None else psnr-nearest[1]['pooled_active_psnr_db'],
            'faults': failure_events, 'records': records,
            'last_receiver_frame': dec.reference_id,
            'scope': 'Sequential actual packet/reference correctness with immediate ACK; no real-time delivery or cap enforcement'}


def main():
    paths = [HERE/'benchmark.py', HERE/'motion_codec.py', HERE/'corpus_support.py',
             Path(mc.cc.__file__), Path(mc.ft.__file__), Path(support.corpus.__file__), Path(support.pacing.__file__),
             support.SUNSHINE/'msv1.py', support.SUNSHINE/'host.py']
    hashes = {str(p): digest(p) for p in paths}
    scenes = support.load_scenes(30)
    reference = {'evidence': 'offline native consecutive frames and exact receiver JPEG; no FPS measurement',
                 'source_hashes': hashes,
                 'scenes': [{k: v for k, v in s.items() if k != 'frames'} for s in scenes]}
    (HERE/'jpeg-reference.json').write_text(json.dumps(reference, indent=2, allow_nan=False)+'\n')
    output = []
    for si, scene in enumerate(scenes):
        rows = []
        for qi, scale in enumerate((8, 16, 32)):
            for mi, mode in enumerate(('intra', 'zero', 'global')):
                row = run_profile(scene, scale, mode, 1+si*20+qi*3+mi)
                rows.append(row)
                print(scene['name'], row['profile'], round(row['wire_mbps_projected_30fps'], 4),
                      round(row['pooled_active_psnr_db_committed_frames'], 3), row['over_48k'], flush=True)
        rows.append(run_profile(scene, 16, 'global', 100+si, faults=True))
        output.append({'name': scene['name'], 'role': scene['role'], 'manifest': scene['manifest'],
                       'jpeg': scene['jpeg'], 'profiles': rows})
    if hashes != {str(p): digest(p) for p in paths}:
        raise RuntimeError('executed source changed during benchmark')
    report = {'evidence': 'Python global motion/residual transform correctness and actual packet sizes; no hardware/FPS',
              'source_sha256': hashes, 'source_hashes_unchanged': True,
              'jpeg_reference_sha256': digest(HERE/'jpeg-reference.json'),
              'capture_limit': 'native compressed sources at25/29.88fps, projected30 is size accounting only',
              'ACK_policy': 'One outstanding, ACK immediately after complete reconstructed commit; timeouts force key. No feedback delay in codec benchmark.',
              'scenes': output}
    (HERE/'results.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')


if __name__ == '__main__':
    main()
