#!/usr/bin/env python3
"""Independent timed-pin/ownership/layout audit; frozen prior pin oracle reused."""
import collections
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'fpga/experiments/cu66-v91l-tiled'
OUT = Path(__file__).with_name('audit-tiled.json')
LIB = ROOT / 'experiments/python-gamebub-v91l-writepipe/verify_results.py'
LIB_SHA = '0a2d293add938e48f2a726481a90e197fb53b5bce293c5800212b027bfda3004'
assert hashlib.sha256(LIB.read_bytes()).hexdigest() == LIB_SHA
spec = importlib.util.spec_from_file_location('frozen_writepipe_audit', LIB)
parent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parent)
PinOracle, require, digest = parent.PinOracle, parent.require, parent.digest
file_sha, trace_events, safe_path = parent.file_sha, parent.trace_events, parent.safe_path
decode_native_fixture = parent.decode_native_fixture
REQUIRED_CHECKS = set(parent.REQUIRED_CHECKS) | {'plane_tile_chroma_and_hud_mapping_edges', 'mapped_adjacent_physical_tile_rows_exact_bl8'}


def physical_byte(layout, logical):
    if layout == 'raster' or logical >= 518400:
        return logical
    require(layout == 'tile8x8', 'unsupported layout')
    plane = 0 if logical < 345600 else 1 if logical < 432000 else 2
    base, width = ((0,720), (345600,360), (432000,360))[plane]
    y, x = divmod(logical - base, width)
    return base + ((y // 8) * (width // 8) + x // 8) * 64 + (y % 8) * 8 + x % 8


def replay(events, seed, layout):
    oracle = PinOracle()
    active = None
    physical = collections.deque()
    max_pending = 0
    minimum_write_gap = 1 << 60
    consecutive_writes = 0
    last_pin_write = None
    config = verdict = None
    counts = collections.Counter()
    checks, kills, offers = set(), collections.Counter(), 0
    last_done = None
    native = False
    native_rows = native_responses = 0
    fixture = None
    native_frames = []
    native_frame_start = None
    native_meta = None
    last_time = -1
    for event in events:
        kind = event['type']
        counts[kind] += 1
        if 'time_ps' in event:
            require(event['time_ps'] >= last_time, 'simulation events reordered in time')
            last_time = event['time_ps']
        if kind == 'config':
            require(config is None, 'duplicate simulation config')
            config = event
            require(event['layout'].strip() == layout, 'layout differs from static build')
            require(event['seed'] == seed and event['t_ac_ns'] in (2.0, 7.0), 'unexpected seed/tAC')
            require(event['clock_flight_ns'] == 4 and event['read_phase_ns'] == 7.75,
                    'unexpected source-compatible pin/read clock timing')
            require(event['initial_memory'] == '(word_address & 65535) ^ 23100',
                    'unexpected initial RAM contents')
            require(event['row_bytes'] == 8 and event['bank_mapping'] == '(bank<<22)|(physical_byte>>1)',
                    'unexpected bridge address contract')
        elif kind == 'pin':
            oracle.command(event)
            if event['command'] in (4, 5):
                owner = next((entry for entry in physical if not entry['pin_seen']), None)
                require(owner is not None, 'pin column command has no unique accepted request')
                word = ((event['bank'] << 22) | (oracle.open_rows[event['bank']] << 9)
                        | event['address'])
                require(word == owner['address'] and
                        (event['command'] == 4) == bool(owner['write']),
                        'pin command differs from accepted controller request')
                if owner['write']:
                    require(event['dq'] == owner['data'], 'pin DQ differs from controller write data')
                owner['pin_seen'] = True
                owner['pin_time'] = event['time_ps']
                require(event['time_ps'] > owner['time_ps'], 'pin command precedes request acceptance')
                if owner['write']:
                    if last_pin_write is not None:
                        gap = event['cycle'] - last_pin_write
                        minimum_write_gap = min(minimum_write_gap, gap)
                        consecutive_writes += gap == 1
                    last_pin_write = event['cycle']
        elif kind == 'read':
            oracle.read(event)
        elif kind == 'controller_read':
            oracle.controller_read(event)
        elif kind == 'controller_req':
            require(len(physical) < 4, 'accepted owner credit overflow')
            logical = active is not None
            if logical:
                require(active['valid'] and not active['killed'] and active['offered'] is None,
                        'controller accepted a word for invalid/canceled/responded row')
                index = active['accepted']
                require(index < 4, 'more than four words accepted for an 8B row')
                require(event['write'] == 1 and event['address'] == active['base'] + index and
                        event['data'] == ((active['data'] >> (index * 16)) & 65535),
                        'row did not issue four ordered little-endian x16 words')
                active['accepted'] += 1
            physical.append(dict(event, logical=logical, pin_seen=False))
            max_pending = max(max_pending, len(physical))
        elif kind == 'controller_done':
            owner = physical[0] if physical else None
            require(owner is not None and owner['pin_seen'],
                    'controller retired without an actual pin command')
            for field in ('write', 'address', 'data'):
                require(event[field] == owner[field], 'controller owner identity changed before drain')
            minimum = 41000 if owner['write'] else 131000
            require(event['time_ps'] - owner['pin_time'] >= minimum,
                    'controller retired before its real command/data recovery completed')
            if owner['logical']:
                require(active is not None, 'logical owner lost before physical drain')
                active['retired'] += 1
            last_done = dict(event, logical=owner['logical'])
            physical.popleft()
        elif kind == 'bridge_req':
            require(active is None and not physical, 'logical row accepted over owned physical/response lease')
            addr, bank = event['address'], event['bank']
            valid = event['epoch'] != 0 and bank < 3 and addr % 8 == 0 and addr <= 560632
            base = (bank << 22) | (physical_byte(layout, addr) >> 1)
            active = dict(event, valid=valid, base=base, accepted=0, retired=0,
                          killed=False, offered=None,
                          before=[oracle.value(base + j) for j in range(4)], native=native)
            if native:
                expected = next(fixture)
                expected['address'] = expected.pop('addr')
                require(all(event[k] == v for k, v in expected.items()),
                        f'native request {native_rows} differs from source-backed fixture')
                if native_rows % 70080 == 0:
                    native_frame_start = {'first_accepted_row_cycle': event['cycle'],
                                          'first_accepted_row_time_ps': event['time_ps'],
                                          'physical_writes_before': oracle.counts[4],
                                          'activates_before': oracle.counts[3], 'refreshes_before': oracle.counts[1]}
                native_rows += 1
        elif kind == 'kill':
            require(event['reset'] or event['cancel'], 'kill event without kill input')
            kills['reset' if event['reset'] else 'cancel'] += 1
            if active is not None and active['offered'] is None:
                active['killed'] = True
            if event['word_pending']:
                require(any(entry['logical'] for entry in physical) or
                        (active is not None and active['accepted'] > 0 and
                         active['retired'] == active['accepted']),
                        'warm kill reports pending word with no retained physical owner')
        elif kind in ('bridge_offer', 'bridge_rsp'):
            require(active is not None, 'response has no logical owner')
            payload = tuple(event[k] for k in ('epoch', 'token', 'bank', 'address', 'error'))
            require(payload[:4] == tuple(active[k] for k in ('epoch', 'token', 'bank', 'address')),
                    'response tag/address identity differs from accepted row')
            require(not physical and active['retired'] == active['accepted'],
                    'logical ACK precedes physical word completion')
            expected_error = int(not active['valid'] or active['killed'])
            if active['offered'] is None:
                require(event['error'] == expected_error, 'wrong logical completion status')
                active['offered'] = payload
            require(active['offered'] == payload, 'held response changed under backpressure or warm kill')
            require(event['error'] or active['accepted'] == 4, 'success ACK before four actual word writes')
            require(active['valid'] or active['accepted'] == 0, 'invalid row produced physical side effects')
            for j in range(4):
                expected = ((active['data'] >> (16*j)) & 65535) if j < active['accepted'] else active['before'][j]
                require(oracle.value(active['base'] + j) == expected,
                        'partial-row side effects differ from exact accepted-word prefix')
            if kind == 'bridge_offer':
                offers += 1
            else:
                if active['native']:
                    native_responses += 1
                    if native_responses % 70080 == 0:
                        frame = native_meta['frames'][native_responses // 70080 - 1]
                        bank_bytes = bytearray()
                        for word in range(280320):
                            bank_bytes.extend(oracle.value((frame['bank'] << 22) | (physical_byte(layout, word * 2) >> 1)).to_bytes(2, 'little'))
                        actual_hash = digest(bank_bytes)
                        require(actual_hash == frame['accepted_bank_sha256'],
                                'independently reconstructed native SDRAM bank differs from accepted golden')
                        physical_writes = oracle.counts[4] - native_frame_start['physical_writes_before']
                        require(physical_writes == 280320, 'native frame did not perform exactly 280320 physical writes')
                        native_frames.append({'id': frame['id'], 'bank': frame['bank'],
                                              'epoch': frame['epoch'], 'rows': 70080,
                                              'physical_writes': physical_writes,
                                              'activate_commands': oracle.counts[3] - native_frame_start['activates_before'],
                                              'refresh_commands': oracle.counts[1] - native_frame_start['refreshes_before'],
                                              'first_accepted_row_cycle': native_frame_start['first_accepted_row_cycle'],
                                              'first_accepted_row_time_ps': native_frame_start['first_accepted_row_time_ps'],
                                              'last_matching_response_cycle': event['cycle'],
                                              'last_matching_response_time_ps': event['time_ps'],
                                              'bytes': len(bank_bytes), 'sha256': actual_hash,
                                              'expected_sha256': frame['accepted_bank_sha256'],
                                              'complete_bank_matches_accepted_golden': True})
                active = None
        elif kind == 'native_begin':
            require(not native and active is None and not physical, 'native replay starts with owned lease')
            native = True
            fixture = iter(decode_native_fixture())
            native_meta = json.loads((ROOT / 'experiments/python-gamebub-v91l-sdram/traffic-results.json').read_text())
        elif kind == 'native_end':
            require(native and active is None and not physical, 'native replay ends before drain')
            require(native_rows == native_responses == event['rows'] == 140160, 'incomplete native traffic replay')
            require(next(fixture, None) is None, 'native fixture not consumed exactly')
            native = False
        elif kind == 'check':
            name = event['name'].strip()  # SV packed string ternary pads "reset" to width of "cancel".
            require(event['status'] == 'PASS' and name not in checks, 'failed/duplicate directed check')
            checks.add(name)
        elif kind == 'verdict':
            require(verdict is None, 'duplicate terminal verdict')
            verdict = event
        else:
            raise AssertionError(f'unrecognized event type: {kind}')
    require(config is not None and verdict is not None, 'missing config/terminal verdict')
    require(verdict['status'] == 'TEST_PASS' and verdict['seed'] == seed, 'terminal verdict mismatch')
    require(active is None and not physical and not native, 'undrained logical/physical lease at end')
    require(not oracle.reads and not oracle.controller_reads, 'incomplete BL8 model/controller reads')
    require(REQUIRED_CHECKS <= checks, f'missing directed checks: {sorted(REQUIRED_CHECKS-checks)}')
    require(kills['reset'] >= 5 and kills['cancel'] >= 5, 'warm reset/cancel stimulus missing')
    require(offers > counts['bridge_rsp'], 'no response backpressure evidence')
    for field, actual in (
        ('checks', len(checks)), ('rows', counts['bridge_req']),
        ('logical_responses', counts['bridge_rsp']), ('word_writes', oracle.counts[4]),
        ('read_words', counts['controller_read']), ('controller_accepts', counts['controller_req']),
        ('controller_retires', counts['controller_done']), ('refreshes', oracle.counts[1]),
        ('activates', oracle.counts[3]), ('precharges', oracle.counts[2]), ('native_rows', native_rows),
    ):
        require(verdict[field] == actual, f'verdict {field} differs from replayed receipts')
    require(counts['controller_req'] == counts['controller_done'] == oracle.counts[4]+oracle.counts[5],
            'controller receipts do not bijectively match real pin column commands')
    require(oracle.counts[5] >= 4 and counts['controller_read'] == counts['read'] == oracle.counts[5] * 8,
            'four physical banks require exact BL8 probes')
    require(oracle.counts[0] == 1 and oracle.counts[1] >= 4, 'initialization/refresh recovery evidence missing')
    require(max_pending == 4, 'bounded write credit path not exercised')
    require(minimum_write_gap >= 1, 'physical WRITE spacing violates controller/memory contract')
    require(consecutive_writes >= 100, 'consecutive WRITE path unexercised')
    return {
        'layout': layout, 'max_pending_accepted_words': max_pending,
        'minimum_pin_write_spacing_cycles': minimum_write_gap,
        'consecutive_pin_write_pairs': consecutive_writes,
        'seed': seed, 't_ac_ns': config['t_ac_ns'], 'event_counts': dict(counts),
        'command_counts': {str(k): v for k, v in oracle.counts.items()},
        'checks': sorted(checks), 'native_frames': native_frames,
        'native_rows': native_rows, 'verdict': verdict,
        'receipt_algorithm': 'Single-pass FIFO/controller ownership correlation; no per-response rescans',
    }



def negative_controls(trace, seed, layout):
    events = list(trace_events(trace))
    seen_offers = set()
    held_event = None
    for event in events:
        if event['type'] == 'bridge_offer':
            identity = tuple(event[key] for key in ('epoch', 'token', 'bank', 'address'))
            if identity in seen_offers and event['ready'] == 0:
                held_event = event
                break
            seen_offers.add(identity)
    require(held_event is not None, 'no repeated held response for checker mutation')
    controls = (
        ('corrupt_write_pin_dq', 'pin', 'dq', lambda e: e['command'] == 4),
        ('corrupt_bl8_scheduled_data', 'read', 'data', lambda e: True),
        ('corrupt_controller_capture_data', 'controller_read', 'data', lambda e: True),
        ('corrupt_response_identity', 'bridge_rsp', 'token', lambda e: True),
        ('false_response_error', 'bridge_offer', 'error', lambda e: True),
        ('corrupt_physical_drain_identity', 'controller_done', 'address', lambda e: True),
        ('corrupt_accepted_word_data', 'controller_req', 'data', lambda e: e['write'] == 1),
        ('change_held_response_error', 'bridge_offer', 'error', lambda e: e is held_event),
    )
    rejected = []
    for name, kind, field, predicate in controls:
        changed = False
        def modified():
            nonlocal changed
            for event in events:
                if not changed and event['type'] == kind and predicate(event):
                    changed = True
                    yield {**event, field: event[field] ^ 1}
                else:
                    yield event
        try:
            replay(modified(), seed, layout)
        except AssertionError as error:
            require(changed, 'negative control did not exercise a trace mutation')
            rejected.append({'mutation': name, 'layout': layout, 'rejected': True, 'reason': str(error)})
        else:
            raise AssertionError(f'independent checker accepted negative control {name}')
    return rejected


def provenance(path):
    report = json.loads(path.read_text())
    attempt = path.parent
    require(report['status'] == 'PASS_MATCHED_REAL_CONTROLLER_TILED', 'nonpassing selected campaign')
    baseline_revision = '438dbb2e8d5ccfa2fa38ad34706dc3c2fd904080'
    head = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    for ancestor,descendant in ((baseline_revision,report['source_revision']),(report['source_revision'],head)):
        require(subprocess.run(['git','merge-base','--is-ancestor',ancestor,descendant],cwd=ROOT).returncode==0,'unexpected source ancestry')
    for name, h in report['source_sha256'].items():
        require(file_sha(ROOT / name) == file_sha(attempt / 'sources' / name) == h, 'source changed: '+name)
    frozen = ['fpga/rtl/moonshine_sdram.sv', 'fpga/experiments/cu66-v91l-writepipe/controller/moonshine_sdram.sv',
              'fpga/experiments/cu66-v91l-writepipe/row_to_sdram.sv', 'fpga/experiments/cu66-v91l-writepipe/sdram_pin_model.sv']
    for name in frozen:
        expected = digest(subprocess.check_output(['git','show',baseline_revision+':'+name],cwd=ROOT))
        require(report['source_sha256'].get(name) == expected, 'frozen source not pinned: '+name)
    derivation = json.loads((attempt / 'sources/fpga/experiments/cu66-v91l-tiled/bridge-derivation.json').read_text())
    baseline = (ROOT / derivation['baseline']).read_text()
    require(file_sha(ROOT / derivation['baseline']) == derivation['baseline_sha256'], 'wrong bridge baseline')
    require(len(derivation['replacements']) == 3, 'unexpected mapping edit count')
    for change in derivation['replacements']:
        require(baseline.count(change['old']) == 1, 'derivation precondition differs')
        baseline = baseline.replace(change['old'], change['new'])
    require(baseline.encode() == (ROOT / derivation['derived']).read_bytes(), 'unrecorded bridge edits')
    require(file_sha(ROOT / derivation['derived']) == derivation['derived_sha256'], 'mapped bridge digest differs')
    for name, h in report['inputs_sha256'].items():
        require(file_sha(ROOT/name) == file_sha(attempt/'inputs'/Path(name).name) == h, 'input differs')
    for name, h in report['artifacts_sha256'].items():
        require(file_sha(attempt/name) == h, 'artifact differs: '+name)
    require(all(c['exit_code'] == 0 for c in report['commands']), 'failed command')
    builds = [c['argv'] for c in report['commands'] if '--binary' in c['argv']]
    require(len(builds) == 4, 'missing matched builds')
    variants = set()
    for argv in builds:
        require({'--timing','--assert','-Wall','-DSIMULATION'} <= set(argv), 'weak RTL flags')
        require(not any(a.startswith('-Wno-') for a in argv), 'waived warning')
        require({'-std=c++20','-Wall','-Wextra','-Werror'} <= set(argv[argv.index('-CFLAGS')+1].split()), 'weak C++ flags')
        layout = 'tile8x8' if '-GTILED=1' in argv else 'raster'
        tac = float(next(a.split('=')[1] for a in argv if a.startswith('-GT_AC_NS=')))
        variants.add((layout,tac))
        relative = 'fpga/experiments/cu66-v91l-tiled/row_to_sdram.sv' if layout == 'tile8x8' else 'fpga/experiments/cu66-v91l-writepipe/row_to_sdram.sv'
        require(str(attempt/'sources'/relative) in argv, 'wrong static bridge source')
    require(variants == {(v,t) for v in ('raster','tile8x8') for t in (2,7)}, 'build matrix differs')
    for name in ('physical_hardware_tested','full_live_codec_join','hardware_distinct_30fps_proven','full_frame_decode_under10ms_proven'):
        require(report[name] is False, 'unsupported scope claim')
    return report


def main():
    alias = json.loads((AREA/'results.json').read_text())
    path = safe_path(ROOT, alias['selected_report'])
    report = provenance(path)
    require({k:v for k,v in alias.items() if k!='selected_report'} == report, 'alias differs')
    require(report['native_replay'] and report['seeds'] == [912301,912302], 'incomplete native seeds')
    modes, controls = [], []
    for mode in report['modes']:
        meta = report['compressed_artifacts'][mode['log'].removesuffix('.gz')]
        trace = {**meta, 'path':path.parent / meta['path']}
        require(file_sha(trace['path']) == trace['gzip_sha256'], 'trace digest differs')
        audited = replay(trace_events(trace), mode['seed'], mode['variant'])
        require(audited['verdict'] == mode['verdict'], 'verdict summary differs')
        require(audited['t_ac_ns'] == mode['t_ac_ns'], 'wrong timing corner')
        require(audited['native_rows'] == mode['native_rows'] == (140160 if mode['t_ac_ns']==2 else 0), 'native coverage differs')
        for exact, measured in zip(audited['native_frames'], mode['frames']):
            exact['cycles'] = exact['last_matching_response_cycle'] - exact['first_accepted_row_cycle']
            require(exact['last_matching_response_time_ps']-exact['first_accepted_row_time_ps'] == exact['cycles']*10000, 'time fence differs')
            require(exact['cycles'] == measured['cycles'] and exact['sha256'] == measured['inverse_sha256'], 'native frame fence/golden differs')
            require(exact['activate_commands'] == measured['activates'], 'ACT count differs')
        if mode['t_ac_ns'] == 7:
            controls.extend(negative_controls(trace, mode['seed'], mode['variant']))
        modes.append(audited)
        print('AUDITED_TILED',mode['variant'],mode['seed'],mode['t_ac_ns'],flush=True)
    require(len(modes) == 8 and {(m['layout'],m['seed'],m['t_ac_ns']) for m in modes} == {(v,s,t) for v in ('raster','tile8x8') for s in (912301,912302) for t in (2,7)}, 'missing modes')
    comparisons=[]
    for seed in (912301,912302):
        a=next(m for m in modes if m['layout']=='raster' and m['seed']==seed and m['t_ac_ns']==2)
        b=next(m for m in modes if m['layout']=='tile8x8' and m['seed']==seed and m['t_ac_ns']==2)
        for old,new in zip(a['native_frames'],b['native_frames']):
            require(old['sha256']==new['sha256'] and new['cycles']<old['cycles'], 'nonexact or slower tiled frame')
            comparisons.append(dict(seed=seed,id=new['id'],raster_cycles=old['cycles'],tile8x8_cycles=new['cycles'],raster_activates=old['activate_commands'],tile8x8_activates=new['activate_commands'],sha256=new['sha256']))
    result=dict(status='PASS_INDEPENDENT_TWO_SEED_TILED_PIN_AUDIT',schema='cu66-v91l-tiled-audit-v1',
                selected_report=str(path.relative_to(ROOT)),report_sha256=file_sha(path),
                verifier_sha256=file_sha(Path(__file__)),oracle_library_sha256=LIB_SHA,
                modes=modes,comparisons=comparisons,checker_negative_controls=controls,
                physical_hardware_tested=False,full_live_codec_join=False,validated_full_decode_under10ms=False,
                scope='Static raster/tile8x8 candidate writes through actual frozen controller and timed functional SDRAM pins. Full inverse native bank contents, ownership, command timing, drain, response stability, 2/7ns BL8 units; not live decoding/shared service or hardware proof.')
    OUT.write_text(json.dumps(result,indent=2)+'\n')
    print(result['status'])


if __name__=='__main__':
    main()
