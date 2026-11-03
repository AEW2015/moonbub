#!/usr/bin/env python3
"""Primary720x480@30 causal packets under fixed declared CPU-stage tables."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import time

import av
import numpy as np
import PIL

import adapter
import model
from replay import BASELINE, RefreshPolicy, baseline_tape, sha

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('refresh_native_inputs', HERE.parent / 'python-game-service-study/benchmark.py')
source = importlib.util.module_from_spec(spec); spec.loader.exec_module(source)


def synthetic(n=60):
    rng = np.random.default_rng(20261103)
    yy, xx = np.indices((480, 720))
    before = np.stack(((xx // 5) % 160 + 20, (yy // 4) % 120 + 30,
                       np.full_like(xx, 50)), axis=-1).astype(np.uint8)
    after = np.stack((np.full_like(xx, 190), (xx // 6) % 120,
                      (yy // 3) % 120 + 100), axis=-1).astype(np.uint8)
    frames = []
    for i in range(n):
        if 42 <= i < 48:
            image = rng.integers(0, 256, (480, 720, 3), dtype=np.uint8)
        else:
            image = (before if i < 31 else after).copy()
            image[48:80, 24:200] = [230, 240, 250] if i % 2 else [20, 20, 30]
        frames.append(image)
    return frames, dict(source='synthetic:seed20261103-cut31-noise42to47', synthetic=True,
                        frame_count=n, frame_sha256=[hashlib.sha256(f.tobytes()).hexdigest() for f in frames],
                        source_fps=None, input_scope='declared synthetic cuts and noise; no capture measurement')


def dependencies():
    paths = [HERE / f for f in ('model.py', 'adapter.py', 'replay.py', 'benchmark.py', 'copy-origin.json',
                                'verify.py', 'test_refresh.py')]
    paths += [BASELINE, HERE.parent / 'python-game-hybrid-link-study/model.py',
              HERE.parent / 'python-game-hybrid-link-study/adapter.py', Path(source.__file__),
              Path(adapter.hybrid.__file__), Path(adapter.hybrid.row.__file__), Path(adapter.hybrid.hp.__file__),
              Path(model.gc.__file__), Path(model.normal_controller.__file__), Path(model.cheap_gate.__file__),
              Path(model.cheap_gate.exact.__file__), Path(model.transport.__file__), Path(model.corpus.__file__),
              Path(model.gc.roi.__file__), Path(model.gc.mt.__file__), Path(model.gc.ft.__file__),
              Path(model.gc.token_coeff.__file__), Path(model.gc.word_coeff.__file__),
              Path(model.gc.word_coeff.frozen_codec.__file__), HERE.parent / 'python-coupled-study/validation.py']
    return sorted(set(paths))


def run_case(frames, manifest, clip, mode, policy, *, table_clip=None, scale=1.0):
    tape = baseline_tape(table_clip or clip, mode, scale=scale)
    factory = adapter.make_controller(patch_policy='adaptive_row', rectangles=adapter.hybrid.COMPACT,
                                     max_attempts=0 if mode == 'gm_only' else 4, use_gate=True)
    cfg = model.Config(width=720, height=480, fps=30, rectangles=adapter.hybrid.BROAD,
                       controller='gate', decoder_service='python_wall', refresh_period=0,
                       frame_cap=49152, frame_deadline_ms=150)
    result = model.run(frames, manifest, cfg, controller_factory=factory,
                       receiver_factory=lambda: adapter.DecoderState(frame_cap=cfg.frame_cap),
                       service_tape=tape, key_policy=RefreshPolicy(policy))
    source.check_drained(result)
    return dict(source=clip, mode=mode, policy=policy, service_scale=scale,
                table_source_clip=table_clip or clip, manifest=manifest, result=result)


def brief(case):
    r = case['result']; packets = r['packets']
    return dict(source=case['source'], mode=case['mode'], policy=case['policy'],
                scale=case['service_scale'], table_sha256=r['service_tape']['table_sha256'],
                strict=r['presented_strict'], eventual=r['presented_eventual'],
                diagnostic_ids_per_second=r['metrics']['steady_fps'],
                diagnostic_window_ms=r['steady_window_ms'],
                key_ids=[p['id'] for p in packets if p.get('key')],
                rejected_ids=[p['id'] for p in packets if not p['admitted']],
                drops=r['drops_by_reason'], admission_wait_ms=r['encoder_admission_wait_ms'],
                actual_encode_wall_ms=sum(p['encode_wall_ms'] for p in packets),
                charged_encode_service_ms=sum(p['encode_service_ms'] for p in packets),
                encode_calls_observed_above_declared_service=sum(p['encode_wall_ms'] > p['encode_service_ms'] for p in packets),
                rejected_calls_observed_above_declared_service=[p['id'] for p in packets
                    if not p['admitted'] and p['encode_wall_ms'] > p['encode_service_ms']],
                max_encode_wall_ms=max((p['encode_wall_ms'] for p in packets), default=None),
                actual_decode_wall_ms=sum(p.get('decode_wall_ms', 0) for p in packets),
                charged_decode_service_ms=sum(p.get('decode_service_ms', 0) for p in packets),
                decode_calls_observed_above_declared_service=sum(p.get('decode_wall_ms', 0) > p.get('decode_service_ms', 0) for p in packets),
                actual_resize_transport_wall_ms=sum(p['wall_ms'] for p in r['resize_services'] + r['cpu_services']),
                charged_resize_transport_service_ms=sum(p['service_ms'] for p in r['resize_services'] + r['cpu_services']),
                python_run_wall_seconds=r['python_wall_seconds'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-frames', type=int, default=60)
    parser.add_argument('--fast-ablation', action='store_true', help='add two explicitly declared half-CPU-service cases')
    parser.add_argument('--skip-synthetic', action='store_true')
    args = parser.parse_args()
    if args.native_frames < 60:
        parser.error('primary benchmark requires at least60 native source frames')
    pins = {str(p): sha(p) for p in dependencies()}
    cases = []; started = time.perf_counter()
    media = Path(os.environ.get('GAMEBUB_MEDIA_DIR', str(HERE.parents[3] / 'media')))
    for clip in ('mass-effect-combat', 'mass-effect-2600'):
        frames, manifest = source.native(media / (clip + '.mp4'), n=args.native_frames)
        if len(frames) != args.native_frames:
            raise ValueError('requested native source length not available')
        for mode in ('gm_only', 'adaptive_ui'):
            for policy in ('periodic30', 'periodic60', 'initial_only'):
                case = run_case(frames, manifest, clip, mode, policy)
                cases.append(case); print(json.dumps(brief(case)), flush=True)
        if args.fast_ablation and clip == 'mass-effect-2600':
            for policy in ('periodic30', 'initial_only'):
                case = run_case(frames, manifest, clip, 'adaptive_ui', policy, scale=0.5)
                cases.append(case); print(json.dumps(brief(case)), flush=True)
    if not args.skip_synthetic:
        frames, manifest = synthetic()
        for policy in ('periodic30', 'initial_only', 'bounded_scene'):
            case = run_case(frames, manifest, 'synthetic-cut-noise', 'adaptive_ui', policy,
                            table_clip='mass-effect-2600')
            cases.append(case); print(json.dumps(brief(case)), flush=True)
    assert pins == {str(p): sha(p) for p in dependencies()}, 'executed source changed during run'
    data = dict(evidence='actual causal HG01/GM01/GF02/GA01 at720x480@30 with fixed declared CPU-stage means',
                source_sha256=pins, versions=dict(python=platform.python_version(), numpy=np.__version__,
                                                  pillow=PIL.__version__, pyav=av.__version__),
                cases=cases, case_count=len(cases), summary=[brief(c) for c in cases],
                total_python_wall_seconds=time.perf_counter() - started,
                pairing_scope='same immutable table per source+UI mode+scale across policies; actual calls reexecuted and wall measured separately. Newly encoded packets follow current ACKed reference and capture/drop decisions. No perpacket cost equivalence claimed.',
                reject_scope='v11 main720traces had no rejects. Every rejected preparation pays declared120ms times service_scale, including all attempts; actual entire call wall is separately recorded and can exceed scenario cost.',
                cpu_scope='each stage is an independent serialized virtual server. Conditional costs and halfcost ablation are assumptions, not measured accelerated execution or sharedCPU/hardware30fps.',
                source_scope='native60frames decoded offline from precompressed25/29.88fps clips and hypothetically scheduled30IDs/s. No new native30Hz acquisition claim; repeated frames and short windows remain limitations.',
                policy_scope='periodic60 equals initialonly for a clean60capture window; no second60period refresh observed. Scene policy only source thumbnails, minimum30gap and maximum120gap; cut/noise case tests one heuristic, not scene accuracy.',
                ownership_scope='48KiB outer-packet cap, two sender/ingress payload slots, two GM credits,150ms frame age,actualGF02/GA01,reader pins and three framebuffer metadata roles retained. LateACK after requested expiry rejected in new copy; frozenv11 issue remains preserved.',
                omitted='no desktopcapture,targetfirmware,RTL,HLS,sockets,RF,SDRAM/DMA/CDC,sharedCPU,physicalRGBbuffer fit or panel qualification')
    (HERE / 'results.json').write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')


if __name__ == '__main__':
    main()
