#!/usr/bin/env python3
"""Independent streaming replay of the matched controller write-pipeline gate.

This checker owns a FIFO of every accepted word, a separate SDR command/memory
oracle, logical leases, and native accepted-bank goldens. It reuses the frozen
prior gate's SDR pin decoder and source-backed native fixture decoder, not DUT
state or testbench-derived expected values.
"""
from __future__ import annotations
import collections
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'fpga/experiments/cu66-v91l-writepipe'
OUT = Path(__file__).with_name('audit.json')
LIB = ROOT / 'experiments/python-gamebub-v91l-sdram/verify_results.py'
LIB_SHA = 'c3452197f0a080482b47a1167c450f2d021f0cb10a76dc3be05b27f064ea79d3'
assert hashlib.sha256(LIB.read_bytes()).hexdigest() == LIB_SHA, 'prior oracle changed'
spec = importlib.util.spec_from_file_location('frozen_v91l_sdram_oracle', LIB)
legacy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy)
require, digest, file_sha, safe_path = legacy.require, legacy.digest, legacy.file_sha, legacy.safe_path
trace_events, decode_native_fixture = legacy.trace_events, legacy.decode_native_fixture

class PinOracle(legacy.PinOracle):
    def __init__(self):
        super().__init__()
        self.previous_activate = -100
        self.previous_write = -100
        self.refresh_cycles = []

    def command(self, event):
        cycle, command, bank = (event[k] for k in ('cycle', 'command', 'bank'))
        if command == 3:
            require(cycle - self.last_act[bank] >= 6, 'ACTIVATE violates -6 tRC60ns')
            require(cycle - self.previous_activate >= 2, 'ACTIVATE violates tRRD2cycles')
            self.previous_activate = cycle
        elif command == 4:
            require(self.mode == 0x233, 'WRITE before BL8/CAS3/write-single MRS')
            require(cycle - self.previous_write >= 1, 'WRITE violates tCCD1cycle')
            self.previous_write = cycle
        elif command == 1:
            self.refresh_cycles.append(cycle)
        super().command(event)

REQUIRED_CHECKS = {
    'four_bank_single_writes_and_exact_bl8_reads', 'row_hit_exact_four_word_writes',
    'row_miss_precharge_activate', 'three_candidate_bank_aperture_edges',
    'seeded_distinct_row_payloads', 'periodic_refresh_and_post_refresh_row',
    'reset_held_success_response_stable', 'cancel_held_success_response_stable',
    'invalid_bank_alignment_and_aperture_reject', 'clean_retry_after_cancel_and_reject',
    'cancel_after_prefix_already_physically_drained',
    'write_follow_refuses_read_bank_and_row_changes',
    'refresh_budget_blocks_follow_writes_and_recovers',
    'reset_held_error_response_stable', 'cancel_held_error_response_stable',
} | {f'{kind}_after_word_{index}' for kind in ('cancel', 'reset') for index in range(-1, 4)}


def replay(events, seed, variant):
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
            require(event['seed'] == seed and event['t_ac_ns'] in (2.0, 7.0), 'unexpected seed/tAC')
            require(event['clock_flight_ns'] == 4 and event['read_phase_ns'] == 7.75,
                    'unexpected source-compatible pin/read clock timing')
            require(event['initial_memory'] == '(word_address & 65535) ^ 23100',
                    'unexpected initial RAM contents')
            require(event['row_bytes'] == 8 and event['bank_mapping'] == '(bank<<22)|(byteaddr>>1)',
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
            require(len(physical) < (1 if variant == 'control' else 4), 'accepted owner credit overflow')
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
            base = (bank << 22) | (addr >> 1)
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
                                          'physical_writes_before': oracle.counts[4]}
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
                            bank_bytes.extend(oracle.value((frame['bank'] << 22) | word).to_bytes(2, 'little'))
                        actual_hash = digest(bank_bytes)
                        require(actual_hash == frame['accepted_bank_sha256'],
                                'independently reconstructed native SDRAM bank differs from accepted golden')
                        physical_writes = oracle.counts[4] - native_frame_start['physical_writes_before']
                        require(physical_writes == 280320, 'native frame did not perform exactly 280320 physical writes')
                        native_frames.append({'id': frame['id'], 'bank': frame['bank'],
                                              'epoch': frame['epoch'], 'rows': 70080,
                                              'physical_writes': physical_writes,
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
    require(oracle.counts[5] == 4 and counts['controller_read'] == counts['read'] == 32,
            'four physical banks require exact BL8 probes')
    require(oracle.counts[0] == 1 and oracle.counts[1] >= 4, 'initialization/refresh recovery evidence missing')
    require(max_pending == (1 if variant == 'control' else 4), 'bounded write credit path not exercised')
    require(minimum_write_gap >= (6 if variant == 'control' else 1), 'physical WRITE spacing violates controller/memory contract')
    if variant == 'writepipe':
        require(consecutive_writes >= 100, 'consecutive WRITE path unexercised')
    return {
        'variant': variant, 'max_pending_accepted_words': max_pending,
        'minimum_pin_write_spacing_cycles': minimum_write_gap,
        'consecutive_pin_write_pairs': consecutive_writes,
        'seed': seed, 't_ac_ns': config['t_ac_ns'], 'event_counts': dict(counts),
        'command_counts': {str(k): v for k, v in oracle.counts.items()},
        'checks': sorted(checks), 'native_frames': native_frames,
        'native_rows': native_rows, 'verdict': verdict,
        'receipt_algorithm': 'Single-pass FIFO/controller ownership correlation; no per-response rescans',
    }


def negative_controls(trace, seed, variant):
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
            replay(modified(), seed, variant)
        except AssertionError as error:
            require(changed, 'negative control did not exercise a trace mutation')
            rejected.append({'mutation': name, 'variant': variant, 'rejected': True, 'reason': str(error)})
        else:
            raise AssertionError(f'independent checker accepted negative control {name}')
    return rejected

BASELINE_REVISION = '78162802af92f3a99773683aaf4929159e50a63b'
CONTROL = 'fpga/experiments/cu66-v91l-sdram'
FAST = 'fpga/experiments/cu66-v91l-writepipe'
FIXED_SOURCES = {
    'fpga/rtl/moonshine_sdram.sv': legacy.FROZEN_SHA,
    CONTROL + '/controller/moonshine_sdram.sv': '9ecadf0e42bd0c35267e09d4c3b6df632d663d2096f93a80805b78528d2c6d4f',
    CONTROL + '/row_to_sdram.sv': 'f5d887dae1937e057999c9280a66674a7debbce86d191dd9f398949a2f24186c',
}
CONTROLLER_EDITS = (
    (" assign request_ready=state==IDLE && 32'(refresh_count)<REFRESH_CYCLES;",
     """ // Accept one next same-open-row write while issuing the current word.
 // All command/data pins use the OLD address/wdata at this clock edge.
 // No queue crosses rows, banks, a read, or the refresh budget.
 wire write_follow=state==RW_CMD && is_write && request_write &&
  request_address[23:9]==address[23:9];
 assign request_ready=(state==IDLE || write_follow) && !reset && 32'(refresh_count)<REFRESH_CYCLES;"""),
    ('     if(is_write)begin sdram_we_n<=0;wait_cycles(3,IDLE);end',
     '''     if(is_write)begin
      sdram_we_n<=0;
      if(request_valid&&request_ready)begin
       address<=request_address;wdata<=request_data;is_write<=1;state<=RW_CMD;
      end else wait_cycles(3,IDLE);
     end'''),
)


def audit_provenance(path):
    report = json.loads(path.read_text())
    attempt = path.parent
    require(report.get('status', '').startswith('PASS'), 'selected comparison is not passing')
    revision = report['source_revision']
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    for ancestor, descendant in ((BASELINE_REVISION, revision), (revision, head)):
        require(subprocess.run(['git', 'merge-base', '--is-ancestor', ancestor, descendant],
                               cwd=ROOT, capture_output=True).returncode == 0,
                'comparison source revision does not descend from frozen baseline/current HEAD')
    pins = report['source_sha256']
    require(pins, 'missing source pins')
    for relative, expected in pins.items():
        require(file_sha(safe_path(ROOT, relative)) == expected, 'current source differs from snapshot: ' + relative)
        require(file_sha(safe_path(attempt / 'sources', relative)) == expected, 'snapshot source differs: ' + relative)
    for relative, expected in FIXED_SOURCES.items():
        require(pins.get(relative) == expected, 'frozen control source changed: ' + relative)
    for relative in pins:
        if relative.startswith(CONTROL + '/') or relative == legacy.FROZEN_CONTROLLER:
            frozen_bytes = subprocess.check_output(['git', 'show', BASELINE_REVISION + ':' + relative], cwd=ROOT)
            require(safe_path(attempt / 'sources', relative).read_bytes() == frozen_bytes,
                    'control/generator metadata differs from baseline commit: ' + relative)
    original_derived = safe_path(attempt / 'sources', legacy.FROZEN_CONTROLLER).read_text()
    for before, after in legacy.WIDTH_EDITS:
        require(original_derived.count(before) == 1, 'unexpected original-to-strict width edit precondition')
        original_derived = original_derived.replace(before, after)
    require(original_derived == safe_path(attempt / 'sources', CONTROL + '/controller/moonshine_sdram.sv').read_text(),
            'strict control is not the frozen original with whitelisted width-only edits')
    derived = safe_path(attempt / 'sources', CONTROL + '/controller/moonshine_sdram.sv').read_text()
    for before, after in CONTROLLER_EDITS:
        require(derived.count(before) == 1, 'unexpected controller scheduling edit precondition')
        derived = derived.replace(before, after)
    require(safe_path(attempt / 'sources', FAST + '/controller/moonshine_sdram.sv').read_text() == derived,
            'fast controller differs from independent two-edit scheduling whitelist')
    prior_pin = ROOT / (CONTROL + '/sdram_pin_model.sv')
    require(file_sha(prior_pin) == '0bb096806aebeefaa75a4275a5c0b6846f4705805ed10d8caaa6ae019ad02bae',
            'prior timed SDR pin model changed')
    expected_pin = prior_pin.read_text()
    pin_edits = (
        (' integer latency=0,left=0,readaddr=0,cycle=0;',
         ' integer latency=0,left=0,readaddr=0,cycle=0,lastcolumn=-100;'),
        ('     mem[{ba,rows[ba],a[8:0]}]=dq;',
         '     assert(cycle-lastcolumn>=1)else $fatal(1,\"WRITE tCCD below one clock\");lastcolumn=cycle;\n     mem[{ba,rows[ba],a[8:0]}]=dq;'),
        ("     readaddr=int'({ba,rows[ba],a[8:0]});latency=3;",
         "     assert(cycle-lastcolumn>=1)else $fatal(1,\"READ tCCD below one clock\");lastcolumn=cycle;\n     readaddr=int'({ba,rows[ba],a[8:0]});latency=3;"),
    )
    for before, after in pin_edits:
        require(expected_pin.count(before) == 1, 'unexpected timed-model edit precondition')
        expected_pin = expected_pin.replace(before, after)
    require(safe_path(attempt / 'sources', FAST + '/sdram_pin_model.sv').read_text() == expected_pin,
            'timed pin model differs from independent tCCD assertion whitelist')
    commands = report['commands']
    require(commands and all(command.get('exit_code') == 0 for command in commands), 'failed comparison command')
    builds = [c['argv'] for c in commands if '--binary' in c['argv']]
    require(len(builds) == 4, 'expected matched control/writepipe x tAC2/7 builds')
    configurations = set()
    for argv in builds:
        for flag in ('--binary', '--timing', '--assert', '-Wall', '-DSIMULATION'):
            require(flag in argv, 'missing strict build flag: ' + flag)
        require(not any(str(a).startswith('-Wno-') for a in argv), 'warning suppression weakens build')
        cflags = argv[argv.index('-CFLAGS') + 1].split()
        require({'-std=c++20', '-Wall', '-Wextra', '-Werror'} <= set(cflags), 'weak C++ flags')
        controller_sources = [variant for variant, area in (('control', CONTROL), ('writepipe', FAST))
                              if str(safe_path(attempt / 'sources', area + '/controller/moonshine_sdram.sv')) in argv]
        require(len(controller_sources) == 1, 'compiled controller source not uniquely pinned')
        variant = controller_sources[0]
        selected = CONTROL if variant == 'control' else FAST
        for relative in (selected + '/controller/moonshine_sdram.sv', selected + '/row_to_sdram.sv',
                         FAST + '/sdram_pin_model.sv', FAST + '/tb_controller.sv'):
            require(str(safe_path(attempt / 'sources', relative)) in argv, 'compiled source is not matched pinned snapshot')
        tac = next((str(a).split('=')[1] for a in argv if str(a).startswith('-GT_AC_NS=')), None)
        configurations.add((variant, float(tac) if tac is not None else None))
    require(configurations == {(variant, tac) for variant in ('control', 'writepipe') for tac in (2, 7)},
            'missing matched strict build configuration')
    for relative, expected in report['artifacts_sha256'].items():
        require(file_sha(safe_path(attempt, relative)) == expected, 'retained artifact digest differs: ' + relative)
    require(report['artifacts_sha256'], 'empty artifact manifest')
    for relative, expected in report['inputs_sha256'].items():
        require(file_sha(safe_path(ROOT, relative)) == expected, 'current traffic input differs')
        require(file_sha(attempt / 'inputs' / Path(relative).name) == expected, 'snapshot traffic input differs')
    for field in ('full_live_codec_join', 'physical_hardware_tested', 'hardware_distinct_30fps_proven',
                  'full_frame_decode_under10ms_proven'):
        require(report.get(field) is False, 'unsupported claim: ' + field)
    traces = {}
    for name, metadata in report['compressed_artifacts'].items():
        trace_path = safe_path(attempt, metadata['path'])
        require(file_sha(trace_path) == metadata['gzip_sha256'], 'compressed trace digest mismatch')
        traces[name] = {**metadata, 'path': trace_path}
    return report, traces, {
        'selected_report': str(path.relative_to(ROOT)), 'report_sha256': file_sha(path),
        'source_revision': revision, 'head_at_verification': head,
        'source_sha256': pins,
        'trace_sha256': {name: {key: metadata[key] for key in ('gzip_sha256', 'raw_sha256', 'rows')}
                         for name, metadata in traces.items()},
    }


def main():
    selected = json.loads((AREA / 'results.json').read_text())
    path = safe_path(ROOT, selected['selected_report'])
    require(path.parent.parent == AREA / 'attempts', 'selected report outside writepipe attempt roots')
    report, traces, result = audit_provenance(path)
    require({key: value for key, value in selected.items() if key != 'selected_report'} == report,
            'selected report pointer fields differ from retained report')
    require(report['schema'] == 'cu66-v91l-writepipe-comparison-v1', 'unexpected comparison schema')
    require(report['seeds'] == [912301, 912302] and report['native_replay'] is True,
            'final qualification requires both seeds and native traffic')
    expected_modes = {(variant, seed, tac) for variant in ('control', 'writepipe')
                      for seed in (912301, 912302) for tac in (2, 7)}
    actual_modes = {(mode['variant'], mode['seed'], mode['t_ac_ns']) for mode in report['modes']}
    require(actual_modes == expected_modes and len(report['modes']) == 8, 'incomplete/duplicate matched mode matrix')
    audited_modes, mutations = [], []
    for mode in report['modes']:
        require(mode['status'].startswith('PASS'), 'failed comparison mode')
        trace_name = mode['log'].removesuffix('.gz')
        require(trace_name in traces, 'missing retained comparison trace')
        output = replay(trace_events(traces[trace_name]), mode['seed'], mode['variant'])
        require(output['verdict'] == mode['verdict'], 'reported verdict differs from replay')
        require(output['t_ac_ns'] == mode['t_ac_ns'], 'timing corner differs from mode label')
        require(output['native_rows'] == mode['native_rows'] == (140160 if mode['t_ac_ns'] == 2 else 0),
                'native replay scope differs from declared matrix')
        require(output['checks'] == sorted(name.strip() for name in mode['checks']), 'check list differs from receipts')
        pin = mode['pin_oracle']
        for field, expected in (('accepts', output['event_counts']['controller_req']),
                                ('retires', output['event_counts']['controller_done']),
                                ('writes', output['command_counts']['4']),
                                ('max_pending', output['max_pending_accepted_words']),
                                ('consecutive_write_pairs', output['consecutive_pin_write_pairs'])):
            require(pin[field] == expected, 'runner pin summary differs from independent replay: ' + field)
        for frame in output['native_frames']:
            cycles = frame['last_matching_response_cycle'] - frame['first_accepted_row_cycle']
            time_ps = frame['last_matching_response_time_ps'] - frame['first_accepted_row_time_ps']
            require(time_ps == cycles * 10000, 'physical simulated times differ from 10ns cycle count')
            frame.update(cycles=cycles, modeled_ms_at_100mhz=cycles/100000)
        require(len(output['native_frames']) == len(mode['frames']), 'native frame summary missing')
        for replayed, summarized in zip(output['native_frames'], mode['frames']):
            require(replayed['cycles'] == summarized['cycles'] and replayed['epoch'] == summarized['epoch']
                    and replayed['bank'] == summarized['bank'] and replayed['rows'] == summarized['rows'],
                    'runner native frame timing differs from independent receipts')
        if mode['t_ac_ns'] == 7:
            mutations.extend(negative_controls(traces[trace_name], mode['seed'], mode['variant']))
        audited_modes.append(output)
        print('AUDITED', mode['variant'], mode['seed'], mode['t_ac_ns'], flush=True)
    comparisons = []
    for seed in (912301, 912302):
        control = next(mode for mode in audited_modes if mode['variant'] == 'control' and mode['seed'] == seed and mode['t_ac_ns'] == 2)
        fast = next(mode for mode in audited_modes if mode['variant'] == 'writepipe' and mode['seed'] == seed and mode['t_ac_ns'] == 2)
        for old, new in zip(control['native_frames'], fast['native_frames']):
            require(old['sha256'] == new['sha256'] and old['id'] == new['id'] and old['bytes'] == new['bytes'],
                    'matched experiment changed native accepted-bank bytes')
            require(new['cycles'] < old['cycles'], 'write pipeline did not improve native write-only replay')
            comparisons.append({'seed': seed, 'frame': new['id'], 'bank': new['bank'],
                                'control_cycles': old['cycles'], 'writepipe_cycles': new['cycles'],
                                'control_ms_at100mhz': old['cycles']/100000,
                                'writepipe_ms_at100mhz': new['cycles']/100000,
                                'speedup': old['cycles']/new['cycles'],
                                'cycle_reduction_percent': (old['cycles']-new['cycles'])/old['cycles']*100,
                                'identical_accepted_bank_sha256': new['sha256']})
    for checked, summarized in zip(comparisons, report['comparisons']):
        for field in ('seed', 'bank', 'control_cycles', 'writepipe_cycles', 'speedup'):
            require(checked[field] == summarized[field], 'runner speedup differs from independent comparison')
    result.update(schema='cu66-v91l-writepipe-independent-audit-v1',
                  status='PASS_TWO_SEED_MATCHED_WRITEPIPE_PIN_AUDIT',
                  verifier=str(Path(__file__).relative_to(ROOT)), verifier_sha256=file_sha(Path(__file__)),
                  frozen_oracle_library=str(LIB.relative_to(ROOT)), frozen_oracle_library_sha256=LIB_SHA,
                  baseline_revision=BASELINE_REVISION,
                  modes=audited_modes, comparisons=comparisons, checker_negative_controls=mutations,
                  assertions={
                      'current_sources_equal_retained_snapshots': True,
                      'original_and_strict_control_unchanged': True,
                      'fast_controller_only_two_independently_whitelisted_scheduling_edits': True,
                      'strict_verilator_and_cpp_warning_flags': True,
                      'accepted_word_to_pin_command_to_idle_drain_bijection': True,
                      'credit_limit_control1_writepipe4': True,
                      'all_successful_rows_four_little_endian_word_writes': True,
                      'all_acks_after_all_accepted_words_physically_drained': True,
                      'cancel_retains_only_exact_accepted_prefix': True,
                      'held_success_and_error_response_identity_immutable': True,
                      'sdram_tRP_tRCD_tRAS_tRC_tRRD_tCCD_tWR_tRFC_checked': True,
                      'tAC2_and7_BL8_capture_values_and_timestamps': True,
                      'native_two_frame_accepted_bank_goldens_reconstructed_from_all_pin_writes': True,
                      'live_codec_or_shared_service_qualified': False,
                      'achieved_fpga_frequency_or_route_timing_qualified': False,
                      'sustained_hardware_30fps_proven': False,
                      'validated_full_frame_decode_under10ms_proven': False,
                  },
                  limits=[
                      '10ns source clock,4ns forwarded-clock flight,279degree read phase and tAC2/7 are simulation assumptions, not hardware or I/O/PVT timing qualification.',
                      'Write-only traffic replays earlier live candidate requests and their accepted bank goldens; current decode, hash/seal, publication, shared reference/RGB traffic and scanout are not joined.',
                      'Cancel leaves already accepted physical writes in memory; the caller must assign only provisional destination banks and discard canceled epochs.',
                      'Controller has no physical write error acknowledgement; bridge errors cover invalid or canceled requests only.',
                      'Pin model checks selected manufacturer command timing; it is not a complete vendor SDRAM model or formal equivalence proof.',
                  ])
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'status': result['status'], 'modes': len(audited_modes),
                      'negative_controls_rejected': len(mutations), 'comparisons': comparisons,
                      'audit': str(OUT.relative_to(ROOT))}, indent=2))


if __name__ == '__main__':
    main()
