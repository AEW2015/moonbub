"""48 input frames: fixed-Q14 transform versus exact same recorded JPEG frames."""
import hashlib
import json
import math
from pathlib import Path
import platform
import sys
import time

import numpy as np

import fixed_codec as ft

HERE = Path(__file__).resolve().parent
CODEC = HERE.parent/'python-codec-study'
sys.path.insert(0,str(CODEC))
import corpus
import pacing

BASELINE = HERE.parent/'python-predictor-study/jpeg-results.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summary(values):
    return {key:float(value) for key,value in zip(('mean','p50','p95','max'),
            (np.mean(values),np.percentile(values,50),np.percentile(values,95),max(values)))}


def psnr(mse):
    return None if mse == 0 else 10*math.log10(65025/mse)


def main():
    baseline = json.loads(BASELINE.read_text())
    source_paths = [HERE/'fixed_codec.py',HERE/'benchmark.py',HERE/'test_fixed_codec.py',CODEC/'corpus.py',CODEC/'pacing.py']
    hashes = {str(path.relative_to(HERE.parent)):digest(path) for path in source_paths}
    scenes = []
    for scene in baseline['scenes']:
        manifest = scene['source']
        frames, selected = corpus.load_video(manifest['source'],max_frames=12,start_seconds=manifest['start_seconds'])
        if len(frames) != 12 or selected['frame_sha256'] != manifest['frame_sha256'][:12]:
            raise AssertionError('selected frames do not match JPEG baseline')
        rows = []
        for scale in (8,16,32):
            records = []
            for i,rgb in enumerate(frames):
                began = time.perf_counter_ns()
                packet = ft.encode(rgb,scale)
                encoded = time.perf_counter_ns()
                decoded = ft.decode(packet)
                completed = time.perf_counter_ns()
                golden = ft.reconstruct(rgb,scale)
                if not np.array_equal(decoded,golden):
                    raise AssertionError('packet reconstruction differs from host golden')
                display = corpus.expand565(corpus.rgb565(decoded))
                quality = corpus.metrics(rgb,display,tuple(selected['active_rects'][i]))
                records.append({'index':i,'input_sha256':selected['frame_sha256'][i],
                                'pts':selected['selected_pts'][i],
                                'time_seconds':selected['selected_times_seconds'][i],
                                'bytes':len(packet),'modeled_wire_bytes':pacing.wire_bytes(len(packet)),
                                'quality_rgb565_output':quality,
                                'quality_pre_rgb565':corpus.metrics(rgb,decoded,tuple(selected['active_rects'][i])),
                                'output_rgb565_sha256':hashlib.sha256(display.tobytes()).hexdigest(),
                                'encoder_python_wall_ms':(encoded-began)/1e6,
                                'decoder_python_wall_ms':(completed-encoded)/1e6,
                                'arithmetic':ft.stats(packet)})
            row = {'profile':f'FT01-scale{scale}','frames':len(records),
                   'packet_bytes':summary([r['bytes'] for r in records]),
                   'modeled_wire_mbps_projected_30fps':np.mean([r['modeled_wire_bytes'] for r in records])*8*30/1e6,
                   'active_rgb565_output_psnr_db':psnr(np.mean([r['quality_rgb565_output']['active']['mse'] for r in records])),
                   'over_48k_count':sum(r['bytes']>49152 for r in records),
                   'over_256k_count':sum(r['bytes']>262144 for r in records),
                   'encode_python_wall_ms':summary([r['encoder_python_wall_ms'] for r in records]),
                   'decode_python_wall_ms':summary([r['decoder_python_wall_ms'] for r in records]),
                   'records':records}
            rows.append(row)
            print(scene['name'],row['profile'],row['modeled_wire_mbps_projected_30fps'],row['active_rgb565_output_psnr_db'],flush=True)
        jpeg_rows = []
        for q,data in scene['qualities'].items():
            subset = data['frames'][:12]
            if [r['input_sha256'] for r in subset] != selected['frame_sha256']:
                raise AssertionError('JPEG comparison hashes differ')
            jpeg_rows.append({'profile':f'JPEG-q{q}','frames':len(subset),
                              'packet_bytes':summary([r['jpeg_bytes'] for r in subset]),
                              'modeled_wire_mbps_projected_30fps':np.mean([r['wire_bytes'] for r in subset])*8*30/1e6,
                              'active_rgb565_output_psnr_db':psnr(np.mean([r['active_mse'] for r in subset])),
                              'over_48k_count':sum(r['jpeg_bytes']>49152 for r in subset),
                              'records':subset})
        scenes.append({'name':scene['name'],'role':scene['role'],'selected_source':selected,
                       'transform_profiles':rows,'matched_subset_jpeg':jpeg_rows})
    absolute_l1 = int(np.abs(ft.Q14).sum(axis=1).max())
    first_accumulator = ft.MAX_COEFF*255*absolute_l1+8192
    first_rounded = first_accumulator>>14
    second_accumulator = first_rounded*absolute_l1+8192
    result = {'evidence':'Python fixed-point intra transform and matched offline frame comparison; no hardware',
              'baseline_sha256':digest(BASELINE),'source_sha256':hashes,
              'old_GBD1_arithmetic_source_sha256':ft.SOURCE_REFERENCE_SHA256,
              'basis_quant_zigzag_numeric_sha256':hashlib.sha256(b''.join(a.astype('<i8').tobytes() for a in (ft.Q14,ft.QY,ft.QC,ft.ZIGZAG))).hexdigest(),
              'python_version':platform.python_version(),'numpy_version':np.__version__,
              'wire_model':{'payload':1024,'application_header':40,'ipv4_udp':28,'excludes':'link/RF/ACK/audio/input'},
              'input_frames':sum(len(s['selected_source']['frame_sha256']) for s in scenes),
              'numeric_budget':{'blocks_720x480_yuv420':8100,'naive_macs_per_idct_frame':8294400,
                                'naive_idct_macs_per_second_30fps':248832000,
                                'naive_idct_macs_per_second_60fps':497664000,
                                'largest_basis_row_absolute_sum':absolute_l1,
                                'decoder_first_accumulator_signed_bits_bound':first_accumulator.bit_length()+1,
                                'decoder_first_intermediate_signed_bits_bound':first_rounded.bit_length()+1,
                                'decoder_second_accumulator_signed_bits_bound':second_accumulator.bit_length()+1,
                                'scope':'numeric range/operation counts only; not DSP inference, schedule, clock or fit'},
              'scenes':scenes}
    if hashes != {str(path.relative_to(HERE.parent)):digest(path) for path in source_paths}:
        raise RuntimeError('source changed during benchmark')
    (HERE/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')


if __name__ == '__main__':
    main()
