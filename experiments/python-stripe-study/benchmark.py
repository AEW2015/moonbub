#!/usr/bin/env python3
"""Actual incremental CP02-stripe bytes, matched to frozen transform pixels."""
import hashlib
import json
from pathlib import Path
import platform
import sys
import time
import tracemalloc

import numpy as np

import stripe_codec as sc

HERE = Path(__file__).resolve().parent
CODEC = HERE.parent/'python-codec-study'
sys.path.insert(0, str(CODEC))
import corpus
import pacing

BASELINE = HERE.parent/'python-predictor-study/jpeg-results.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stream(packet, back, chunk):
    events = []
    def put(row, image):
        back[row:row+len(image)] = image
    decoder = sc.Decoder(put)
    for at in range(0, len(packet), chunk):
        events.extend(decoder.feed(packet[at:at+chunk]))
    if decoder.committed:
        raise AssertionError('commit preceded explicit finish')
    stats = decoder.finish()
    if events[-1]['kind'] != 'frame_validated' or not stats['committed']:
        raise AssertionError('missing complete-frame validation/commit')
    return stats


def main():
    paths = [HERE/'stripe_codec.py', HERE/'benchmark.py', HERE/'test_stripe_codec.py',
             Path(sc.ft.__file__), Path(sc.cc.__file__), CODEC/'corpus.py', CODEC/'pacing.py']
    hashes = {str(p.relative_to(HERE.parent)):digest(p) for p in paths}
    source = json.loads(BASELINE.read_text())
    baseline_sha = digest(BASELINE)
    scenes = []
    for scene in source['scenes']:
        manifest = scene['source']
        frames, chosen = corpus.load_video(manifest['source'], max_frames=12,
                                           start_seconds=manifest['start_seconds'])
        if len(frames) != 12 or chosen['frame_sha256'] != manifest['frame_sha256'][:12]:
            raise AssertionError('source mismatch')
        rows = []
        for index, rgb in enumerate(frames):
            began = time.perf_counter_ns()
            packet = sc.encode(rgb, 16)
            encoded = time.perf_counter_ns()
            golden = sc.ft.reconstruct(rgb, 16)
            back = np.empty_like(rgb)
            stats = stream(packet, back, 137)
            completed = time.perf_counter_ns()
            if not np.array_equal(back, golden):
                raise AssertionError('streaming output differs from frozen host reconstruction')
            tested_chunks = [137]
            if index == 0:
                for chunk in (1, 4096, len(packet)):
                    extra = np.empty_like(rgb)
                    stream(packet, extra, chunk)
                    if not np.array_equal(extra, golden):
                        raise AssertionError('chunk partition changed pixels')
                    tested_chunks.append(chunk)
                # Input packet and provisional output allocation are already owned
                # by the caller. This traces decoder/interpolation temporaries only.
                tracemalloc.start()
                memory_back = np.empty_like(rgb)
                # Account caller back allocation separately from decoder trace.
                tracemalloc.stop()
                tracemalloc.start()
                stream(packet, memory_back, 137)
                _, trace_peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
            else:
                trace_peak = None
            display = corpus.expand565(corpus.rgb565(back))
            rows.append({'index':index, 'pts':chosen['selected_pts'][index],
                         'time_seconds':chosen['selected_times_seconds'][index],
                         'input_sha256':chosen['frame_sha256'][index],
                         'decoded_rgb_sha256':hashlib.sha256(back.tobytes()).hexdigest(),
                         'packet_bytes':len(packet), 'wire_bytes':pacing.wire_bytes(len(packet)),
                         'over_48k':len(packet)>49152,
                         'encoder_python_wall_ms':(encoded-began)/1e6,
                         'decoder_plus_host_golden_wall_ms':(completed-encoded)/1e6,
                         'tested_feed_chunk_bytes':tested_chunks,
                         'decoder_tracemalloc_peak_excluding_caller_input_and_back':trace_peak,
                         'caller_provisional_back_rgb888_bytes':back.nbytes,
                         'hypothetical_rgb565_back_bytes':back.shape[0]*back.shape[1]*2,
                         'quality':corpus.metrics(rgb,display,tuple(chosen['active_rects'][index])),
                         'stats':stats})
        mse = np.mean([r['quality']['active']['mse'] for r in rows])
        scenes.append({'name':scene['name'], 'role':scene['role'], 'selected_source':chosen,
                       'frames':rows, 'projected_wire_mbps_30fps':np.mean([r['wire_bytes'] for r in rows])*8*30/1e6,
                       'active_rgb565_output_psnr_db':float(10*np.log10(65025/mse)) if mse else None,
                       'packet_bytes_mean':float(np.mean([r['packet_bytes'] for r in rows])),
                       'packet_bytes_max':max(r['packet_bytes'] for r in rows),
                       'over_48k_count':sum(r['over_48k'] for r in rows),
                       'peak_retained_sample_bytes':max(r['stats']['peak_retained_sample_bytes'] for r in rows)})
        print(scene['name'], scenes[-1]['projected_wire_mbps_30fps'], scenes[-1]['packet_bytes_max'], flush=True)
    if hashes != {str(p.relative_to(HERE.parent)):digest(p) for p in paths} or digest(BASELINE) != baseline_sha:
        raise RuntimeError('source/input changed during run')
    report = {'evidence':'Python actual byte-driven compressed stripes; not RTL/hardware or physical memory proof',
              'python_version':platform.python_version(), 'numpy_version':np.__version__,
              'source_sha256':hashes, 'baseline_sha256':baseline_sha, 'frames':48,
              'profile':'SS01 scale16; Cb,Cr,Y region order and CP02 coefficient helper',
              'commit_rule':'Region pixels provisional until whole-frame CRC and explicit finish; caller never exposes uncommitted BACK pixels',
              'scenes':scenes}
    (HERE/'results.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')


if __name__ == '__main__':
    main()
