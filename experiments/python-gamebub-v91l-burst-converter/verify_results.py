#!/usr/bin/env python3
"""Independent streaming audit of the static scalar/direct-line-hit RGB join.

Prior immutable line/gather and timed SDRAM pin oracles retain their original
contracts. This auditor additionally reconstructs every consumed canonical byte
from accepted external leases or observed direct-hit consumption. No hardware
frequency, shared live decoder, or complete frame latency is inferred.
"""
import argparse
import collections
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
AREA = ROOT / 'fpga/experiments/cu66-v91l-burst-converter'
BASELINE = 'd57c0e47fba91032e2c94a78a09ed22a46679c46'
HELPERS = {
    'experiments/python-gamebub-v91l-readbridge/verify_converter.py':
        '8e04b1d6b8eb3b2bdbe1f5d1c1fe7724093e3c13b714c23247c1c114866aba05',
    'experiments/python-gamebub-v91l-readbridge/verify_timed_pins.py':
        'dbeceff8eb74e373dbec22df9e7710cc69c75c0e094bfef03de9d89705041817',
    'experiments/python-gamebub-v91l-readbridge/verify_readbridge.py':
        '8fa8d4a666549a68174b6778b7c2fa93f52be53b5db0e86aaa1a7c1a6c91b590',
    'experiments/python-gamebub-v91l-tiled/verify_rowpair.py':
        '8e40414864dbe0a28d2e522b51fa65ac20e8ca8aabc14fe5c17dd306cfcf7454',
    'experiments/python-gamebub-v91l-writepipe/verify_results.py':
        '0a2d293add938e48f2a726481a90e197fb53b5bce293c5800212b027bfda3004',
    'experiments/python-gamebub-v91l-sdram/verify_results.py':
        'c3452197f0a080482b47a1167c450f2d021f0cb10a76dc3be05b27f064ea79d3',
}
FIXED_INPUTS = {
    'fpga/experiments/cu66-v91k-lines/comparison-attempts/20261106T223415479309Z-7a2603de/inputs/canonical_actual.tsv.gz':
        '03fab04d4273388cb1477c6db11c19486d7f0ad1ebc2e39b18fe6cc3508c0192',
    'fpga/experiments/cu66-v91k-lines/comparison-attempts/20261106T223415479309Z-7a2603de/inputs/rgb_goldens.tsv.gz':
        'abe85556017a634b43711306763af93d39cbf3207b9547842edd0064c3e6547b',
    'experiments/python-gamebub-v91k/vectors/rgb_goldens.tsv.gz':
        'abe85556017a634b43711306763af93d39cbf3207b9547842edd0064c3e6547b',
    'fpga/experiments/cu66-v91l-readbridge/preload.hex.gz':
        '328550d7def90b12334b86b7721cb1cd0156046dfe872b8841c55e7fa73c48a8',
    'experiments/python-gamebub-v91l-tiled/vectors/prefill-lines.hex.gz':
        'dcf721977ebc03b445ff221efcc4349037c07840ce26bdfa717a023e270db14e',
}
EXTRA_KINDS = {'byte_req', 'byte_rsp', 'direct_byte', 'probe_check'}
FROZEN_SOURCES = (
    'fpga/experiments/cu66-v91k-cache/canonical_rgb565_cached.sv',
    'fpga/experiments/cu66-v91k-lines/canonical_line_reader.sv',
    'fpga/experiments/cu66-v91k-lines/canonical_rgb565_lines.sv',
    'fpga/experiments/cu66-v91l-rowpair/tile_rowpair_reader.sv',
    'fpga/experiments/cu66-v91l-readbridge/bl8_read_bridge.sv',
    'fpga/experiments/cu66-v91l-writepipe/controller/moonshine_sdram.sv',
    'fpga/experiments/cu66-v91l-writepipe/sdram_pin_model.sv',
    'fpga/experiments/cu66-v91l-converter/canonical_rgb565_tiled.sv',
    'fpga/experiments/cu66-v91l-converter/canonical_rgb565_timed.sv',
)
# Filled only after independent source review; these are not learned from a
# runner report. A changed derivative must be reviewed before audit publication.
REVIEWED_SOURCE_SHA256 = {
    'fpga/experiments/cu66-v91l-burst-converter/canonical_line_reader.sv':
        '30e2b59acd864d200a256523957307d215bb9f12f69dcd631693514d4c8cb4dc',
    'fpga/experiments/cu66-v91l-burst-converter/canonical_rgb565_cached.sv':
        'ac4cfcffe3bd2afb6ffce41a635f9c2f038bfb2142e37a8fc3010361b167b904',
    'fpga/experiments/cu66-v91l-burst-converter/canonical_rgb565_lines.sv':
        '2e91f40e19f8773e0400dc7720e669d2972a489188622fef1e1a8881683ce07a',
    'fpga/experiments/cu66-v91l-burst-converter/canonical_rgb565_tiled.sv':
        'bdfd6d1b90e406bf3a9f496a30fe6dcec26ea31df537a1604432cb5de77c75f7',
    'fpga/experiments/cu66-v91l-burst-converter/scalar/canonical_rgb565_timed.sv':
        '2d90ff4010eb75a3aa7c0ba2aeb064220b3a539b5706e15d3637e2f87562d829',
    'fpga/experiments/cu66-v91l-burst-converter/burst/canonical_rgb565_timed.sv':
        '325e7eeac818804d6ed59953c61ca744d89d35c360bd53ff009e00d1827b0301',
    'fpga/experiments/cu66-v91l-burst-converter/generate_converter.py':
        'f916f5c3740b73d141dd84d4db74b2b6978fd27b42bbc888cb575f3aed15bf56',
    'fpga/experiments/cu66-v91l-burst-converter/derivations.json':
        '15b7033a89dd906064d6dc9660641cb9240203bfe9789f32ff3f99441c416a17',
    'fpga/experiments/cu66-v91l-burst-converter/tb_timed.cpp':
        '72339bc63125640ff09adc157b1a6460176d4951e79fd9742e16193ab0efbbd7',
    'fpga/experiments/cu66-v91l-burst-converter/INTERFACE.md':
        '3a0908a594e7bcd9db7dfc1f8b4ef088b60b33ccfa5263e1e28505a144b6d5a4',
    'scripts/cu66-v91l-burst-converter/run_comparison.py':
        '93073d2b324797436a6cff5c4fca5a1d02f5c2fc5444e1af318583bd292d1baa',
}
PROBE_SOURCE_SHA256 = {
    'fpga/experiments/cu66-v91l-burst-converter/canonical_line_reader.sv':
        '30e2b59acd864d200a256523957307d215bb9f12f69dcd631693514d4c8cb4dc',
    'fpga/experiments/cu66-v91l-burst-probe/tb_probe.cpp':
        'afa0dbefe637cfc29e7f264877765431288783dff37bd4a578153094abf9a4df',
    'scripts/cu66-v91l-burst-probe/run_test.py':
        'a1d0bc67d31b6bcc693a31d38fc00054b0d00a8a278b40f0533c4faffb376cd8',
}


def need(ok, why):
    if not ok:
        raise AssertionError(why)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def load_helper(name, module_name):
    path = ROOT / name
    need(sha(path) == HELPERS[name], 'frozen independent oracle changed: ' + name)
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rgb_oracle = load_helper(next(iter(HELPERS)), 'burst_frozen_rgb_oracle')
pin_oracle = load_helper(list(HELPERS)[1], 'burst_frozen_pin_oracle')


def events(path, metadata=None):
    digest = hashlib.sha256()
    count = 0
    with gzip.open(path, 'rb') as stream:
        for raw in stream:
            digest.update(raw)
            count += 1
            yield json.loads(raw)
    if metadata is not None:
        need(count == metadata['rows'] and digest.hexdigest() == metadata['raw_sha256'],
             'raw event hash/row receipt differs')


def legacy_events(stream):
    for event in stream:
        if event['type'] not in EXTRA_KINDS:
            yield event


def consumed_addresses():
    """Derive the scalar chroma-fill/luma schedule independently of the RTL.

    Fill Cb then Cr for each new chroma row; hold two rows for interpolation.
    The final chroma row is replicated rather than refilled. Each native luma
    pixel is read exactly once. This yields 172800 chroma +345600 luma bytes.
    """
    for y in range(480):
        fills = (0, 1) if y == 0 else ((y // 2 + 1,) if y % 2 == 0 and y <= 476 else ())
        for row in fills:
            for base in (345600, 432000):
                yield from range(base + row * 360, base + (row + 1) * 360)
        yield from range(y * 720, (y + 1) * 720)


BYTE_SCHEDULE = tuple(consumed_addresses())
need(len(BYTE_SCHEDULE) == 518400, 'independent canonical byte schedule extent differs')


def byte_replay(stream, variant, images, terminal=True):
    """O(n) lease, cache tag, direct byte, and source-order replay."""
    session = pending = None
    slots = {}
    frames = []
    counts = collections.Counter()
    checks = []
    last_cycle = -1

    def consume(event, direct):
        need(session is not None and session['active'], 'canonical consume without active descriptor')
        index = session['consumed']
        need(index < len(BYTE_SCHEDULE), 'too many canonical consumed bytes')
        address = BYTE_SCHEDULE[index]
        need(event['address'] == address, 'canonical consumed byte order differs')
        need(event['epoch'] == session['epoch'], 'canonical consumed byte epoch differs')
        need(event['data'] == images[session['image']][address], 'canonical consumed byte data differs')
        session['consumed'] += 1
        if direct:
            session['direct'] += 1

    for event in stream:
        kind = event['type']
        cycle = event.get('cycle', event.get('closed_cycle', last_cycle))
        need(cycle >= last_cycle, 'byte receipts move backward in time')
        last_cycle = cycle
        counts[kind] += 1
        if kind == 'start':
            need(pending is None, 'new descriptor overwrites external byte owner')
            slots.clear()
            session = dict(event, active=event['bank'] < 3 and event['epoch'] != 0 and event['generation'] != 0,
                           consumed=0, direct=0, requests=0, responses=0, hits=0, misses=0)
        elif kind == 'kill':
            need(session is not None, 'byte kill lacks descriptor')
            session['active'] = False
            session['kill_cycle'] = cycle
            slots.clear()
        elif kind == 'line_rsp':
            if not event['error'] and session is not None and session['active']:
                need(event['epoch'] == session['epoch'] and event['generation'] == session['generation']
                     and event['bank'] == session['bank'], 'cache publication descriptor differs')
                address = event['address']
                need(address % 16 == 0, 'cache publication not line aligned')
                plane = 0 if address < 345600 else 1 if address < 432000 else 2
                data = bytes.fromhex(event['data'])
                need(data == images[session['image']][address:address + 16], 'cache publication bytes differ')
                slots[plane] = dict(address=address, epoch=event['epoch'], data=data, cycle=cycle)
        elif kind == 'byte_req':
            need(session is not None and session['active'] and pending is None,
                 'external byte request lacks free active lease')
            need(event['epoch'] == session['epoch'], 'external byte request epoch differs')
            index = session['consumed']
            need(index < len(BYTE_SCHEDULE) and event['address'] == BYTE_SCHEDULE[index],
                 'external byte request source order differs')
            address = event['address']
            plane = 0 if address < 345600 else 1 if address < 432000 else 2
            slot = slots.get(plane)
            hit = slot is not None and slot['address'] == address & ~15 and slot['epoch'] == event['epoch']
            need(variant != 'burst' or not hit, 'direct-hit variant issued redundant external hit lease')
            session['hits' if hit else 'misses'] += 1
            session['requests'] += 1
            pending = dict(event)
        elif kind == 'byte_rsp':
            need(pending is not None and session is not None, 'external byte response lacks owner')
            need(event['address'] == pending['address'] and event['epoch'] == pending['epoch'],
                 'external byte response identity differs')
            if not event['error']:
                need(event['data'] == images[session['image']][event['address']],
                     'external byte response data differs')
                if session['active']:
                    address = event['address']
                    plane = 0 if address < 345600 else 1 if address < 432000 else 2
                    slot = slots.get(plane)
                    need(slot is not None and slot['address'] == address & ~15 and
                         slot['epoch'] == event['epoch'] and slot['cycle'] < cycle,
                         'external byte response precedes owned matching line publication')
                    need(slot['data'][address & 15] == event['data'], 'external byte response differs from owned line')
                    consume(event, False)
                else:
                    need(cycle == session.get('kill_cycle'), 'canceled descriptor consumed late success')
            session['responses'] += 1
            pending = None
        elif kind == 'direct_byte':
            need(variant == 'burst' and pending is None, 'direct hit overlaps external byte owner or scalar mode')
            need(session is not None and session['active'], 'direct hit after cancel/invalidation')
            address = event['address']
            plane = 0 if address < 345600 else 1 if address < 432000 else 2
            slot = slots.get(plane)
            need(slot is not None and slot['address'] == address & ~15 and slot['epoch'] == event['epoch']
                 and slot['cycle'] < cycle, 'direct hit without previously published matching line')
            need(slot['data'][address & 15] == event['data'], 'direct hit differs from owned line byte')
            consume(event, True)
        elif kind == 'probe_check':
            need(event['status'] == 'PASS', 'failed directed direct-probe check')
            checks.append(event)
        elif kind == 'frame':
            need(session is not None and session['active'] and pending is None,
                 'byte frame closes without drained descriptor')
            expected_reads = 32400 if variant == 'burst' else 518400
            expected_direct = 486000 if variant == 'burst' else 0
            need(session['consumed'] == 518400 and session['direct'] == expected_direct,
                 'canonical consumed/direct split differs')
            need(session['requests'] == session['responses'] == expected_reads,
                 'actual external byte lease request/response count differs')
            need(session['misses'] == 32400 and session['hits'] == (0 if variant == 'burst' else 486000),
                 'independent external byte cache hit/miss split differs')
            for field, value in (('canonical_consumed', session['consumed']), ('direct_consumes', session['direct']),
                                 ('external_byte_leases', session['requests']), ('external_byte_returns', session['responses']),
                                 ('adapter_hits', session['hits']), ('adapter_misses', session['misses'])):
                need(event[field] == value, 'RTL counter differs from independent byte receipts: ' + field)
            frames.append(dict(name=session['image'], external_byte_requests=session['requests'],
                               external_byte_responses=session['responses'], external_hits=session['hits'],
                               external_misses=session['misses'], direct_consumes=session['direct'],
                               canonical_consumed=session['consumed']))
            session['active'] = False
            slots.clear()
    if terminal:
        need(pending is None and len(frames) == 2, 'external byte owner or native frame remains unclosed')
    return dict(variant=variant, frames=frames, event_counts=dict(counts), probe_checks=checks)


def frame_negative_controls(stream, seed, images, tiles, forward, schedule, rgb):
    """Reuse existing mutations against the unchanged legacy receipt contract."""
    prefix = []
    for event in legacy_events(stream):
        prefix.append(event)
        if event['type'] == 'pixel_row':
            break
    need(prefix and prefix[-1]['type'] == 'pixel_row', 'no first RGB row for mutation controls')
    first = lambda kind, pred=lambda e: True: next(i for i, e in enumerate(prefix) if e['type'] == kind and pred(e))
    fliphex = lambda value: f'{int(value[:2], 16) ^ 1:02x}' + value[2:]
    phys = first('phys_rsp', lambda e: not e['error'])
    line = first('line_rsp', lambda e: not e['error'])
    beat = first('controller_read')
    fence = first('bridge_fence')
    done = first('controller_done')
    holds = [i for i, e in enumerate(prefix) if e['type'] == 'pixel_hold']
    need(len(holds) >= 2, 'missing repeated held pixels for negative control')
    controls = (
        ('controller_data', beat, 'data', prefix[beat]['data'] ^ 1, 'controller beat bytes differ'),
        ('controller_drain', done, None, None, 'physical response before capture/drain/idle fence'),
        ('bridge_fence', fence, 'pending', 0, 'bridge fence ownership differs'),
        ('bridge_payload', phys, 'data', fliphex(prefix[phys]['data']), 'bridge response packing differs'),
        ('canonical_payload', line, 'data', fliphex(prefix[line]['data']), 'canonical line bytes differ'),
        ('row_hash', len(prefix) - 1, 'hash_fnv64', prefix[-1]['hash_fnv64'] ^ 1, 'RGB row digest differs'),
        ('held_pixel', holds[1], 'word', prefix[holds[1]]['word'] ^ 1, 'held pixel identity/data changed'),
        ('physical_response_removed', phys, None, None, 'physical read without a free live line owner'),
    )
    rejected = []
    for name, index, field, value, reason in controls:
        def mutated():
            for i, event in enumerate(prefix):
                if i != index:
                    yield event
                elif field is not None:
                    yield {**event, field: value}
        try:
            rgb_oracle.replay(mutated(), seed, 1, images, tiles, forward, schedule, rgb, timed=True)
        except AssertionError as error:
            need(reason in str(error), 'RGB negative rejected for unrelated reason: ' + name + ': ' + str(error))
            rejected.append(dict(mutation=name, rejected=True, reason=str(error),
                                 prefix_filter='legacy_event_kinds_through_first_pixel_row',
                                 prefix_event_index=index, original_event=prefix[index],
                                 corrupted_event=None if field is None else {**prefix[index], field: value}))
        else:
            raise AssertionError('corrupted RGB receipt accepted: ' + name)
    return rejected


def byte_negative_controls(stream, variant, images):
    prefix = []
    for event in stream:
        prefix.append(event)
        if event['type'] == 'pixel_row':
            break
    controls = []
    for kind, field, transform, cause in (
        ('byte_req', 'address', lambda v: v ^ 1, 'external byte request source order differs'),
        ('byte_rsp', 'data', lambda v: v ^ 1, 'external byte response data differs'),
        ('byte_rsp', 'epoch', lambda v: v ^ 1, 'external byte response identity differs'),
    ):
        index = next(i for i, e in enumerate(prefix) if e['type'] == kind and not e.get('error', 0))
        controls.append((kind + '_' + field, index, field, transform(prefix[index][field]), cause))
    if variant == 'burst':
        index = next(i for i, e in enumerate(prefix) if e['type'] == 'direct_byte')
        controls.extend((
            ('direct_data', index, 'data', prefix[index]['data'] ^ 1, 'direct hit differs from owned line byte'),
            ('direct_epoch', index, 'epoch', prefix[index]['epoch'] ^ 1, 'direct hit without previously published matching line'),
            ('direct_address', index, 'address', prefix[index]['address'] + 16, 'direct hit without previously published matching line'),
        ))
    result = []
    for name, index, field, value, cause in controls:
        mutated = ({**e, field: value} if i == index else e for i, e in enumerate(prefix))
        try:
            byte_replay(mutated, variant, images, terminal=False)
        except AssertionError as error:
            need(cause in str(error), 'byte negative rejected for unrelated reason: ' + name + ': ' + str(error))
            result.append(dict(mutation=name, rejected=True, reason=str(error),
                               prefix_filter='all_events_through_first_pixel_row',
                               prefix_event_index=index, original_event=prefix[index],
                               corrupted_event={**prefix[index], field: value}))
        else:
            raise AssertionError('corrupted byte receipt accepted: ' + name)
    return result


def pin_negative_controls(stream, seed, tac, tiles):
    prefix = []
    for event in stream:
        prefix.append(event)
        if len(prefix) == 12000:
            break
    first = lambda kind, pred=lambda e: True: next(i for i, e in enumerate(prefix) if e['type'] == kind and pred(e))
    pin, read, capture = first('pin', lambda e: e['command'] == 5), first('read'), first('controller_read')
    fence, response = first('bridge_fence'), first('phys_rsp', lambda e: not e['error'])
    controls = (
        ('pin_address', pin, 'address', prefix[pin]['address'] ^ 8, 'pin READ address differs'),
        ('scheduled_read_data', read, 'data', prefix[read]['data'] ^ 1, 'SDR BL8 beat differs'),
        ('captured_read_data', capture, 'data', prefix[capture]['data'] ^ 1, 'capture/retime/consume data mismatch'),
        ('captured_read_time', capture, 'time_ps', prefix[capture]['time_ps'] + 1, 'capture/retime/consume timing mismatch'),
        ('idle_fence', fence, 'ctrl_idle', 0, 'physical response precedes two consecutive idle'),
        ('response_generation', response, 'generation', prefix[response]['generation'] ^ 1, 'tagged physical response differs'),
        ('response_payload', response, 'data', f"{int(prefix[response]['data'][:2], 16) ^ 1:02x}" + prefix[response]['data'][2:], 'physical response bytes differ'),
    )
    rejected = []
    for name, index, field, value, cause in controls:
        mutated = ({**event, field: value} if i == index else event for i, event in enumerate(prefix))
        try:
            pin_oracle.replay(mutated, seed, tac, tiles, terminal=False)
        except AssertionError as error:
            need(cause in str(error), 'pin negative rejected for unrelated reason: ' + name + ': ' + str(error))
            rejected.append(dict(mutation=name, rejected=True, reason=str(error),
                                 prefix_filter='time_merged_pin_and_controller_first_12000_events',
                                 prefix_event_index=index, original_event=prefix[index],
                                 corrupted_event={**prefix[index], field: value}))
        else:
            raise AssertionError('corrupted pin receipt accepted: ' + name)
    return rejected


def provenance(path):
    report = json.loads(path.read_text())
    attempt = path.parent
    need(report['schema'] == 'cu66-v91l-burst-comparison-v1' and
         report['status'] == 'PASS_MATCHED_BURST_NATIVE_RGB565_ACTUAL_TIMED_SDRAM', 'selected comparison did not pass')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    for older, newer in ((BASELINE, report['source_revision']), (report['source_revision'], head)):
        need(subprocess.run(['git', 'merge-base', '--is-ancestor', older, newer], cwd=ROOT,
                            capture_output=True).returncode == 0, 'source ancestry differs')
    for name, digest in report['source_sha256'].items():
        need(sha(ROOT / name) == sha(attempt / 'sources' / name) == digest, 'source snapshot differs: ' + name)
    for name, digest in report['inputs_sha256'].items():
        need(sha(ROOT / name) == sha(attempt / 'inputs' / Path(name).name) == digest, 'input snapshot differs: ' + name)
    for name, digest in FIXED_INPUTS.items():
        need(sha(ROOT / name) == digest, 'frozen native input changed: ' + name)
    for expansion in report['input_expansions']:
        packed = attempt / expansion['compressed_path']
        need(sha(packed) == expansion['compressed_sha256'], 'expanded input compressed identity differs')
        need(hashlib.sha256(gzip.decompress(packed.read_bytes())).hexdigest() == expansion['raw_sha256'],
             'expanded input raw identity differs')
    for name, digest in report['artifacts_sha256'].items():
        need(sha(attempt / name) == digest, 'retained artifact differs: ' + name)
    for name in FROZEN_SOURCES:
        original = subprocess.check_output(['git', 'show', BASELINE + ':' + name], cwd=ROOT)
        need(sha(ROOT / name) == hashlib.sha256(original).hexdigest(), 'frozen source changed: ' + name)
    need(REVIEWED_SOURCE_SHA256, 'new derivative source review not finalized')
    for name, digest in REVIEWED_SOURCE_SHA256.items():
        need(report['source_sha256'].get(name) == digest, 'reviewed derivative differs: ' + name)
    need(all(command['exit_code'] == 0 for command in report['commands']), 'failed campaign command')
    need('5.020' in (attempt / 'tool-version.log').read_text()
         and '13.3.0' in (attempt / 'compiler-version.log').read_text(), 'tool versions differ')
    builds = [command['argv'] for command in report['commands'] if '--build' in command['argv']]
    need(len(builds) == 4, 'missing two static variants times two tAC builds')
    common = {'fpga/experiments/cu66-v91l-rowpair/tile_rowpair_reader.sv',
              'fpga/experiments/cu66-v91l-readbridge/bl8_read_bridge.sv',
              'fpga/experiments/cu66-v91l-writepipe/controller/moonshine_sdram.sv',
              'fpga/experiments/cu66-v91l-writepipe/sdram_pin_model.sv',
              'fpga/experiments/cu66-v91l-burst-converter/tb_timed.cpp'}
    expected_sources = {
        'scalar': common | {'fpga/experiments/cu66-v91k-cache/canonical_rgb565_cached.sv',
                            'fpga/experiments/cu66-v91k-lines/canonical_line_reader.sv',
                            'fpga/experiments/cu66-v91k-lines/canonical_rgb565_lines.sv',
                            'fpga/experiments/cu66-v91l-converter/canonical_rgb565_tiled.sv',
                            'fpga/experiments/cu66-v91l-burst-converter/scalar/canonical_rgb565_timed.sv'},
        'burst': common | {str(AREA.relative_to(ROOT) / name) for name in
                           ('canonical_rgb565_cached.sv', 'canonical_line_reader.sv', 'canonical_rgb565_lines.sv',
                            'canonical_rgb565_tiled.sv', 'burst/canonical_rgb565_timed.sv')},
    }
    build_directories = {}
    for argv in builds:
        need({'--timing', '--assert', '-Wall', '-DSIMULATION', '--cc', '--exe', '--build'} <= set(argv), 'weak RTL build flags')
        need(not any(str(value).startswith('-Wno-') for value in argv), 'design warning waived')
        need({'-std=c++20', '-Wall', '-Wextra', '-Werror'} <= set(argv[argv.index('-CFLAGS') + 1].split()), 'weak C++ flags')
        need("-GRETAIN_ROWS=1'b1" in argv, 'static retention mode changed')
        compiled = [Path(value) for value in argv if str(value).endswith(('.sv', '.cpp'))]
        need(compiled and all(value.is_relative_to(attempt / 'sources') for value in compiled), 'compiled source outside exact snapshot')
        for value in compiled:
            need(str(value.relative_to(attempt / 'sources')) in report['source_sha256'], 'compiled source absent from manifest')
        source_set = {str(value.relative_to(attempt / 'sources')) for value in compiled}
        variants = [name for name, source in expected_sources.items() if source_set == source]
        need(len(variants) == 1, 'compiled static variant sources differ from reviewed set')
        tac = float(next(value.split('=')[1] for value in argv if value.startswith('-GT_AC_NS=')))
        key = variants[0], tac
        need(key not in build_directories, 'duplicate static timing-corner build')
        build_directories[key] = argv[argv.index('--Mdir') + 1]
    need(set(build_directories) == {(variant, tac) for variant in ('scalar', 'burst') for tac in (2, 7)},
         'compiled static/timing-corner grid differs')
    runs = [command['argv'] for command in report['commands']
            if any(str(value).endswith('/Vcanonical_rgb565_timed') for value in command['argv'])]
    need(len(runs) == len(report['modes']) == 8, 'missing full-native executions')
    for mode in report['modes']:
        binary = build_directories[mode['variant'], mode['t_ac_ns']] + '/Vcanonical_rgb565_timed'
        expected_event = str(attempt / mode['event_log'].removesuffix('.gz'))
        matching = [argv for argv in runs if binary in argv and expected_event in argv]
        need(len(matching) == 1, 'mode not bound to exact static corner and output path')
        argv = matching[0]
        tail = argv[argv.index(binary) + 1:]
        need(tail == [str(attempt / 'canonical_actual.tsv'), str(attempt / 'rgb_goldens.tsv'),
                      expected_event, str((attempt / mode['event_log']).parent), str(mode['seed']), '1',
                      '+PRELOAD=' + str(attempt / 'preload.hex'), str(int(mode['variant'] == 'burst'))],
             'mode executable arguments differ from pinned inputs/static observers')
    need(report['actual_converter_rtl_join'] is True and report['physical_sdram_controller_join'] is True,
         'actual RTL/controller join absent')
    for key in ('shared_service_complete', 'physical_hardware_tested', 'sustained_hardware_30fps_proven',
                'validated_full_frame_decode_under10ms_proven'):
        need(report[key] is False, 'unsupported hardware/full-decoder claim: ' + key)
    return report


def probe_audit():
    """Bind the separately authored, independently reviewed adapter lifecycle test."""
    alias_path = ROOT / 'fpga/experiments/cu66-v91l-burst-probe/results.json'
    alias = json.loads(alias_path.read_text())
    path = ROOT / alias['selected_report']
    report = json.loads(path.read_text())
    need({k: v for k, v in alias.items() if k != 'selected_report'} == report, 'probe alias differs')
    need(report['schema'] == 'cu66-v91l-direct-probe-contract-v1'
         and report['status'] == 'PASS_DIRECT_PROBE_OWNERSHIP' and report['hardware_tested'] is False,
         'standalone probe contract did not pass')
    need(report['source_sha256'] == PROBE_SOURCE_SHA256, 'reviewed standalone probe sources differ')
    for name, digest in PROBE_SOURCE_SHA256.items():
        need(sha(ROOT / name) == sha(path.parent / 'sources' / name) == digest, 'probe source snapshot differs: ' + name)
    for name, digest in report['artifacts_sha256'].items():
        need(sha(path.parent / name) == digest, 'probe retained artifact differs: ' + name)
    need(all(command['exit_code'] == 0 for command in report['commands']), 'failed standalone probe command')
    builds = [command['argv'] for command in report['commands'] if '--build' in command['argv']]
    need(len(builds) == 1, 'standalone probe build count differs')
    argv = builds[0]
    need({'--timing', '--assert', '-Wall', '--cc', '--exe', '--build'} <= set(argv), 'weak standalone probe build flags')
    need(not any(str(value).startswith('-Wno-') for value in argv), 'standalone probe warning waived')
    need({'-std=c++20', '-Wall', '-Wextra', '-Werror'} <= set(argv[argv.index('-CFLAGS') + 1].split()),
         'weak standalone probe C++ flags')
    compiled = {str(Path(value).relative_to(path.parent / 'sources')) for value in argv if str(value).endswith(('.sv', '.cpp'))}
    need(compiled == set(PROBE_SOURCE_SHA256) - {'scripts/cu66-v91l-burst-probe/run_test.py'},
         'standalone probe compiled source set differs')
    runs = [command['argv'] for command in report['commands']
            if any(str(value).endswith('/Vcanonical_line_reader') for value in command['argv'])]
    need(len(runs) == 1 and argv[argv.index('--Mdir') + 1] + '/Vcanonical_line_reader' in runs[0],
         'standalone probe run binary differs')
    verdict = json.loads((path.parent / 'run.log').read_text())
    need(verdict == report['verdict'] == dict(status='PASS_DIRECT_PROBE_OWNERSHIP', checks=255, clocks=88),
         'standalone probe explicit verdict differs')
    return dict(selected_report=str(path.relative_to(ROOT)), report_sha256=sha(path),
                source_sha256=PROBE_SOURCE_SHA256, verdict=verdict,
                scope='Source-reviewed standalone directed RTL contract: three plane slots, chroma row shared line, '
                      'epoch/range/tag gates, preACK/held-byte ownership, start/finish/reset/cancel invalidation, '
                      'wrong-epoch return cannot release physical owner, cancel/reset matching physical drain, '
                      'matching bus-error ACK invalidates slots and drains held error before fresh-epoch retry. '
                      'Not formal/exhaustive, native data, timed physical pins, full decoder or hardware.')


def source_contract():
    old_core = (ROOT / 'fpga/experiments/cu66-v91k-cache/canonical_rgb565_cached.sv').read_text()
    new_core = (AREA / 'canonical_rgb565_cached.sv').read_text()
    old_reader = (ROOT / 'fpga/experiments/cu66-v91k-lines/canonical_line_reader.sv').read_text()
    new_reader = (AREA / 'canonical_line_reader.sv').read_text()
    arithmetic = lambda text: text[text.index('    always_comb begin'):text.index('    always_ff @(posedge clk)begin', text.index('    always_comb begin'))]
    need(arithmetic(old_core) == arithmetic(new_core), 'native interpolation/conversion arithmetic changed')
    arrays = lambda text: re.findall(r'^\s*logic \[[^\n]+\] \w+ \[0:\d+\];$', text, re.MULTILINE)
    need(arrays(old_core) == arrays(new_core), 'chroma payload array layout changed')
    need(arrays(old_reader) == arrays(new_reader), 'canonical line payload array layout changed')
    readwrite = lambda text: text[text.index('    // Each bank has one registered read port.'):text.index('    always_comb begin')]
    new_ram = readwrite(new_core).replace('if(fill_write)begin',
        'if(pending&&mem_rsp_valid&&mem_rsp_epoch==epoch&&running&&\n                state==FILL_WAIT&&!mem_rsp_error&&!kill)begin').replace('<=fill_data;', '<=mem_rsp_data;')
    need(new_ram == readwrite(old_core), 'RAM registered-read/byte-enable write structure changed')
    suffix = lambda text: text[text.index('    always_ff @(posedge clk)begin'):]
    need(suffix(old_reader) == suffix(new_reader), 'adapter ownership/publication/cancel state machine changed')
    need('assign direct_consume=probe_valid&&probe_hit;' in new_core and
         'assign mem_req_valid=probe_valid&&!probe_hit;' in new_core and
         'state==FILL_WAIT&&!mem_rsp_error&&!kill)||(direct_consume&&state==FILL_REQ);' in new_core,
         'direct versus external consume exclusion differs')
    return dict(native_arithmetic_unchanged=True, chroma_RAM_layout_and_ports_unchanged=True,
                line_reader_sequential_ownership_state_machine_unchanged=True,
                direct_and_external_RAM_write_conditions_mutually_exclusive=True,
                payload_bytes_added=0, existing_canonical_cache_payload_bytes=48,
                existing_chroma_RAM_payload_bytes=1440, added_diagnostic_counter_bits=128,
                note='Structural source comparison and reviewed hashes; no physical mapping, routed timing or formal proof.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    alias = None
    if args.report is None:
        alias = json.loads((AREA / 'timed-results.json').read_text())
        path = ROOT / alias['selected_report']
    else:
        path = args.report.resolve()
    report = provenance(path)
    probe_result = probe_audit()
    structural_result = source_contract()
    report_digest = sha(path)
    if alias is not None:
        need({k: v for k, v in alias.items() if k != 'selected_report'} == report, 'selected alias differs')
    images, tiles, forward, schedule, rgb = rgb_oracle.load_inputs()
    modes = []
    negatives = []
    for mode in report['modes']:
        variant = mode['variant']
        need(variant in ('scalar', 'burst') and mode['retain'] == 1, 'unknown static variant/retention')
        cppmeta = report['compressed_artifacts'][mode['event_log'].removesuffix('.gz')]
        pinmeta = report['compressed_artifacts'][mode['pin_log'].removesuffix('.gz')]
        cpppath, pinpath = path.parent / cppmeta['path'], path.parent / pinmeta['path']
        need(sha(cpppath) == cppmeta['gzip_sha256'] and sha(pinpath) == pinmeta['gzip_sha256'], 'compressed receipt differs')
        line_result = rgb_oracle.replay(legacy_events(events(cpppath, cppmeta)), mode['seed'], 1,
                                       images, tiles, forward, schedule, rgb, cpppath.parent, timed=True)
        byte_result = byte_replay(events(cpppath, cppmeta), variant, images)
        physical_result = pin_oracle.replay(pin_oracle.merged(pinpath, pinmeta, cpppath, cppmeta),
                                           mode['seed'], mode['t_ac_ns'], tiles)
        need(line_result['verdict'] == physical_result['verdict'] == mode['verdict'], 'runner terminal verdict differs')
        need(line_result['checks'] == physical_result['checks'] == sorted(mode['checks']), 'runner directed check set differs')
        need(len(line_result['frames']) == len(mode['frames']) == 2, 'runner native frame count differs')
        for actual, summarized in zip(line_result['frames'], mode['frames']):
            for field, value in actual.items():
                if field != 'sha256':
                    need(summarized[field] == value, 'runner frame summary differs: ' + field)
            need(summarized['output_sha256'] == actual['sha256'], 'runner native RGB file hash differs')
        tag = dict(variant=variant, seed=mode['seed'], t_ac_ns=mode['t_ac_ns'])
        negative = frame_negative_controls(events(cpppath), mode['seed'], images, tiles, forward, schedule, rgb)
        negative += byte_negative_controls(events(cpppath), variant, images)
        negative += pin_negative_controls(pin_oracle.merged(pinpath, pinmeta, cpppath, cppmeta),
                                          mode['seed'], mode['t_ac_ns'], tiles)
        negatives.extend({**tag, **row} for row in negative)
        modes.append(dict(**tag, rgb=line_result, canonical_bytes=byte_result, physical_pins=physical_result))
        print('AUDITED_BURST_CONVERTER', variant, mode['seed'], mode['t_ac_ns'], flush=True)
    expected = {(v, s, t) for v in ('scalar', 'burst') for s in (912701, 912702) for t in (2, 7)}
    need(len(modes) == len(expected) and {(m['variant'], m['seed'], m['t_ac_ns']) for m in modes} == expected,
         'missing/duplicate variant/seed/tAC mode')
    comparisons = []
    for seed in (912701, 912702):
        for tac in (2, 7):
            selected = {m['variant']: m for m in modes if m['seed'] == seed and m['t_ac_ns'] == tac}
            for scalar, burst in zip(selected['scalar']['rgb']['frames'], selected['burst']['rgb']['frames']):
                need(scalar['name'] == burst['name'] and scalar['sha256'] == burst['sha256'], 'static variants RGB identity differs')
                need(scalar['logical_reads'] == burst['logical_reads'] == scalar['physical_reads'] == burst['physical_reads'] == 32400,
                     'static variant changed line/physical read counts')
                saved = scalar['start_to_closed'] - burst['start_to_closed']
                need(saved > 0, 'independent matched comparison did not improve component closure')
                comparisons.append(dict(seed=seed, t_ac_ns=tac, name=scalar['name'],
                                        scalar_cycles=scalar['start_to_closed'], burst_cycles=burst['start_to_closed'],
                                        cycles_saved=saved, speedup=scalar['start_to_closed'] / burst['start_to_closed'],
                                        assumed_100mhz_component_30hz_budget_met=burst['start_to_closed'] * 30 <= 100000000))
    reported_comparison = {(row['seed'], row['t_ac_ns'], row['name']): row for row in report['comparison']}
    need(len(reported_comparison) == len(report['comparison']) == len(comparisons), 'matched runner comparison count differs')
    for row in comparisons:
        summarized = reported_comparison[row['seed'], row['t_ac_ns'], row['name']]
        for field in ('scalar_cycles', 'burst_cycles', 'speedup'):
            need(summarized[field] == row[field], 'matched runner comparison arithmetic differs: ' + field)
        need(summarized['saved_cycles'] == row['cycles_saved'], 'matched runner cycle saving differs')
    for name, digest in report['source_sha256'].items():
        need(sha(ROOT / name) == digest, 'source changed during long audit: ' + name)
    for name, digest in HELPERS.items():
        need(sha(ROOT / name) == digest, 'independent helper changed during audit: ' + name)
    for name, digest in FIXED_INPUTS.items():
        need(sha(ROOT / name) == digest, 'frozen native input changed during audit: ' + name)
    need(sha(path) == report_digest, 'selected report changed during audit')
    need(probe_audit() == probe_result, 'standalone probe changed during long audit')
    if alias is not None:
        need(json.loads((AREA / 'timed-results.json').read_text()) == alias, 'selected alias changed during audit')
    result = dict(schema='cu66-v91l-burst-converter-independent-audit-v1',
                  status='PASS_INDEPENDENT_NATIVE_RGB_CANONICAL_BYTES_AND_TIMED_SDRAM_PINS',
                  selected_report=str(path.relative_to(ROOT)), report_sha256=report_digest,
                  verifier_sha256=sha(Path(__file__)), helper_sha256=HELPERS,
                  frozen_native_input_sha256=FIXED_INPUTS,
                  reviewed_source_sha256=REVIEWED_SOURCE_SHA256,
                  standalone_direct_probe=probe_result,
                  structural_source_review=structural_result,
                  modes=modes, matched_comparisons=comparisons, checker_negative_controls=negatives,
                  assertions=dict(all_canonical_byte_consumes_in_independent_source_order=True,
                                  external_byte_leases_distinct_from_direct_hits=True,
                                  exact_native_RGB_rows_and_complete_files=True,
                                  independent_gather_line_and_physical_order=True,
                                  actual_pin_commands_capture_times_and_word_values=True,
                                  cancel_reset_drain_and_held_output_checks=True,
                                  frozen_sources_exact_and_new_derivatives_reviewed=True,
                                  hardware_or_full_decoder_proven=False),
                  scope='Two native base RGB frames, two static converters, two seeds, tAC 2/7 ns. '
                        'Canonical memory is preloaded outside fences. Constant-pass streaming independent RTL receipt audit; '
                        'no live entropy/reconstruction, shared writer, HUD/publication, routed frequency, electrical timing, '
                        'sustained hardware 30 fps or validated full FPGA decode under 10 ms.')
    (HERE / 'audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(result['status'], flush=True)


if __name__ == '__main__':
    main()
