#!/usr/bin/env python3
"""Actual measured-stage finite replay at the unchanged 720x480/30 target."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import sys
import time

import av
import numpy as np
import PIL
import adapter
import model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
spec = importlib.util.spec_from_file_location('execution_native_inputs', HERE.parent / 'python-game-service-study/benchmark.py')
source = importlib.util.module_from_spec(spec)
spec.loader.exec_module(source)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dependencies():
    import cache_admission
    paths = [HERE / name for name in ('model.py', 'adapter.py', 'benchmark.py', 'test_execution.py', 'verify.py')]
    paths += [Path(source.__file__), Path(cache_admission.__file__), Path(adapter.fast_codec.__file__),
              Path(model.gc.__file__), Path(model.normal_controller.__file__),
              Path(model.cheap_gate.__file__), Path(model.cheap_gate.exact.__file__),
              Path(model.transport.__file__), Path(model.corpus.__file__),
              Path(model.gc.roi.__file__), Path(model.gc.mt.__file__), Path(model.gc.ft.__file__),
              Path(model.gc.token_coeff.__file__), Path(model.gc.word_coeff.__file__),
              Path(model.gc.word_coeff.frozen_codec.__file__), Path(adapter.hybrid.__file__),
              Path(adapter.hybrid.row.__file__), Path(adapter.hybrid.hp.__file__),
              HERE.parent / 'python-coupled-study/validation.py',
              HERE.parent / 'python-game-refresh-study/model.py']
    return sorted(set(paths))


def run_case(frames, manifest, label, *, cache, fast, ui, refresh_period=30):
    cfg = model.Config(width=720, height=480, fps=30, controller='normal',
                       decoder_service='python_wall', transport_cpu=True, resize_cpu=True,
                       refresh_period=refresh_period, frame_cap=49152)
    result = model.run(frames, manifest, cfg,
                       controller_factory=adapter.make_controller(cache=cache, ui=ui),
                       receiver_factory=lambda: adapter.DecoderState(frame_cap=cfg.frame_cap, fast=fast),
                       service_tape=None)
    source.check_drained(result)
    return dict(source=label, cache=cache, fast_decoder=fast, exact_ui=ui,
                refresh_period=refresh_period, manifest=manifest, result=result)


def brief(case):
    r = case['result']; packets = r['packets']
    attempts = [a for p in packets for a in p['attempts']]
    return dict(source=case['source'], cache=case['cache'], fast_decoder=case['fast_decoder'],
                exact_ui=case['exact_ui'], captures=r['capture_count'], prepared=r['prepared'],
                strict=r['presented_strict'], eventual=r['presented_eventual'],
                diagnostic_ids_per_second=r['metrics']['steady_fps'],
                diagnostic_window_ms=r['steady_window_ms'],
                cache_hit_attempts=sum(bool(a.get('cache_hit')) for a in attempts),
                forward_calls=sum(p['forward_calls'] for p in packets),
                encode_wall_ms=sum(p['encode_wall_ms'] for p in packets),
                decode_wall_ms=sum(p.get('decode_wall_ms', 0) for p in packets),
                drops=r['drops_by_reason'], admission_wait_ms=r['encoder_admission_wait_ms'])


def summarize_pair(a, b):
    aa = {p['id']: p for p in a['result']['packets']}
    bb = {p['id']: p for p in b['result']['packets']}
    common = sorted(aa.keys() & bb.keys())
    same_ref = [i for i in common if aa[i]['acked_anchor_at_prepare'] == bb[i]['acked_anchor_at_prepare']
                and aa[i]['force_key'] == bb[i]['force_key']]
    same_packet = [i for i in common if aa[i].get('packet_sha256') is not None
                   and aa[i].get('packet_sha256') == bb[i].get('packet_sha256')]
    return dict(source=a['source'], exact_ui=a['exact_ui'], common_prepared_ids=common,
                same_anchor_and_forced_key_ids=same_ref, same_packet_ids=same_packet,
                strict_delta=b['result']['presented_strict']-a['result']['presented_strict'],
                eventual_delta=b['result']['presented_eventual']-a['result']['presented_eventual'],
                scope='Same source hashes, separately remeasured work and causal histories. Not isolated statistical timing evidence.')


def main():
    pins = {str(p): sha(p) for p in dependencies()}
    cases = []; pairs = []; started = time.perf_counter()
    media = Path(os.environ.get('GAMEBUB_MEDIA_DIR', str(HERE.parents[3] / 'media')))
    for index, clip in enumerate(('mass-effect-combat', 'mass-effect-2600')):
        frames, manifest = source.native(media / (clip + '.mp4'), n=60, start=1)
        by_profile = {}
        profiles = [(False, False), (True, False), (False, True), (True, True)]
        if index: profiles.reverse()
        for cache, fast in profiles:
            case = run_case(frames, manifest, clip, cache=cache, fast=fast, ui=True)
            cases.append(case); by_profile[cache, fast] = case
            print(json.dumps(brief(case)), flush=True)
        pairs.append(summarize_pair(by_profile[False, False], by_profile[True, True]))
        base = {}
        for enabled in ((False, True) if index == 0 else (True, False)):
            case = run_case(frames, manifest, clip, cache=enabled, fast=enabled, ui=False)
            cases.append(case); base[enabled] = case; print(json.dumps(brief(case)), flush=True)
        pairs.append(summarize_pair(base[False], base[True]))
    # Longer held-out second-source window. Native source remains ~29.88 fps;
    # scheduling at 30 IDs/s does not manufacture live 30 Hz acquisition.
    frames, manifest = source.native(media / 'mass-effect-2600.mp4', n=180, start=4)
    assert len(frames) == 180
    long_cases = {}
    for enabled in (False, True):
        case = run_case(frames, manifest, 'mass-effect-2600-heldout180',
                        cache=enabled, fast=enabled, ui=True)
        cases.append(case); long_cases[enabled] = case; print(json.dumps(brief(case)), flush=True)
    pairs.append(summarize_pair(long_cases[False], long_cases[True]))
    frames, manifest = source.stress()
    stress_cases = {}
    for enabled in (True, False):
        case = run_case(frames, manifest, 'synthetic-noise-recovery',
                        cache=enabled, fast=enabled, ui=True)
        cases.append(case); stress_cases[enabled] = case; print(json.dumps(brief(case)), flush=True)
    pairs.append(summarize_pair(stress_cases[False], stress_cases[True]))
    assert pins == {str(p): sha(p) for p in dependencies()}, 'executed sources changed'
    result = dict(evidence='Actual GM01/HG01/GF02/GA01 measured-stage finite replay; not physical target timing',
                  source_sha256=pins, cases=cases, case_count=len(cases), pairs=pairs,
                  summary=[brief(c) for c in cases], total_python_wall_seconds=time.perf_counter()-started,
                  versions=dict(python=platform.python_version(), numpy=np.__version__,
                                pillow=PIL.__version__, pyav=av.__version__),
                  service_scope='No fixed tape or assumed decode time. Every actual prepare/reject, receive, BOX and transport call pays its measured wall duration on independent virtual servers. This does not measure parallel execution on one CPU.',
                  pairing_scope='Same source hashes and policies; alternate case order between clips. Re-measured costs can alter admission, refresh and references. Direct same-packet component studies are the isolated arithmetic evidence; finite deltas remain host-load/history-confounded.',
                  memory_scope='Two sender/ingress/credits and three metadata framebuffer roles. Host source/oracle/codec arrays and cached RGB/payloads are extra, not physical memory-fit proof.',
                  transport_scope='Assumed8Mb/s forward/reverse,160Mb/sQSPI,10msfeedback,60Hzvblank; no real sockets/WiFi/DMA/CDC/scanout.',
                  resolution_scope='All performance cases720x480 at30 scheduledIDs/s. Native sources scaled to720x405active; synthetic noise uses fullcanvas. Native25/29.88fps precompressed files, not live30distinctcapture.',
                  omitted='No native/RTL codec, hardware display, host desktop acquisition or sustained physical30fps proof.')
    (HERE / 'results.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')


if __name__ == '__main__':
    main()
