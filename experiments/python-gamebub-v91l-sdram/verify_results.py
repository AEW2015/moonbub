#!/usr/bin/env python3
"""Independent, linear-time replay of retained controller/pin simulation evidence.

The Python oracle owns its own open-bank state and word memory. Testbench PASS
markers are checked only after command, data, and bridge receipts are replayed.
"""
from __future__ import annotations

import collections
import gzip
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'fpga/experiments/cu66-v91l-sdram'
OUT = Path(__file__).with_name('audit.json')
SCHEMA = 'cu66-v91l-sdram-independent-audit-v1'
BASELINE = '67744b3340e92ab2b188143fe3727107a7647d69'
FROZEN_CONTROLLER = 'fpga/rtl/moonshine_sdram.sv'
FROZEN_SHA = 'f1c3bfd6e41b0f2cae0a68e4bf37155a5914d2993dc27d22b9a052d3e9b0f26f'
SEEDS = (912301, 912302)
CONTROLLER = 'fpga/experiments/cu66-v91l-sdram/controller/moonshine_sdram.sv'
WIDTH_EDITS = (
    ('refresh_count<REFRESH_CYCLES', "32'(refresh_count)<REFRESH_CYCLES"),
    ('delay<=POWERUP_CYCLES', "delay<=16'(POWERUP_CYCLES)"),
    ('refresh_count>=REFRESH_CYCLES', "32'(refresh_count)>=REFRESH_CYCLES"),
    ('  WRITE_WAIT=11,REFRESH_PRE=12,REFRESH=13;', '  REFRESH_PRE=12,REFRESH=13;'),
)


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    hasher = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            hasher.update(block)
    return hasher.hexdigest()


def safe_path(parent, relative):
    path = (parent / relative).resolve()
    require(path.is_relative_to(parent.resolve()), f'path escapes evidence root: {relative}')
    return path


def audit_provenance(path):
    report = json.loads(path.read_text())
    attempt = path.parent
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    revision = report.get('source_revision', '')
    require(subprocess.run(['git', 'merge-base', '--is-ancestor', BASELINE, revision],
                           cwd=ROOT, capture_output=True).returncode == 0,
            'attempt revision is not descended from required baseline')
    require(subprocess.run(['git', 'merge-base', '--is-ancestor', revision, head],
                           cwd=ROOT, capture_output=True).returncode == 0,
            'attempt revision is not in current HEAD history')
    require(report.get('status', '').startswith('PASS'), f'latest attempt is not passing: {path}')
    pins = report.get('source_sha256', {})
    require(pins and FROZEN_CONTROLLER in pins, 'missing real controller source pin')
    require(pins[FROZEN_CONTROLLER] == FROZEN_SHA, 'frozen real controller differs from baseline')
    for relative, expected in pins.items():
        require(file_sha(safe_path(attempt / 'sources', relative)) == expected,
                f'snapshot differs from source pin: {relative}')
        require(file_sha(safe_path(ROOT, relative)) == expected,
                f'current source differs from pinned snapshot: {relative}')
    derived = safe_path(attempt / 'sources', FROZEN_CONTROLLER).read_text()
    for before, after in WIDTH_EDITS:
        require(derived.count(before) == 1, 'unexpected frozen-controller edit precondition')
        derived = derived.replace(before, after)
    require(CONTROLLER in pins, 'strict controller derivative missing from source pins')
    require(safe_path(attempt / 'sources', CONTROLLER).read_text() == derived,
            'controller differs from independently whitelisted strict-width derivative')
    commands = report.get('commands', [])
    require(commands and all(c.get('exit_code') == 0 for c in commands), 'failed/missing command')
    builds = [c['argv'] for c in commands if '--cc' in c.get('argv', [])
              or '--binary' in c.get('argv', [])]
    require(len(builds) == 2, 'expected tAC2/tAC7 strict Verilator builds')
    for argv in builds:
        for flag in ('--assert', '-Wall', '-DSIMULATION', '--binary', '--timing'):
            require(flag in argv, f'missing strict build flag: {flag}')
        require(not any(str(a).startswith(('-Wno-', '-Wno-fatal')) for a in argv),
                'warning suppression weakens strict build')
        cflags = argv[argv.index('-CFLAGS') + 1].split()
        for flag in ('-std=c++20', '-Wall', '-Wextra', '-Werror'):
            require(flag in cflags, f'missing strict C++ flag: {flag}')
        for name in (CONTROLLER, 'fpga/experiments/cu66-v91l-sdram/row_to_sdram.sv',
                     'fpga/experiments/cu66-v91l-sdram/sdram_pin_model.sv',
                     'fpga/experiments/cu66-v91l-sdram/tb_controller.sv'):
            require(str(safe_path(attempt / 'sources', name)) in argv,
                    f'compiled source was not the pinned snapshot: {name}')
    for relative, expected in report.get('artifacts_sha256', {}).items():
        require(file_sha(safe_path(attempt, relative)) == expected,
                f'retained artifact differs from digest: {relative}')
    require(report.get('artifacts_sha256'), 'empty artifact manifest')
    for field in ('full_live_codec_join', 'hardware_distinct_30fps_proven',
                  'full_frame_decode_under10ms_proven', 'byte_rmw_supported', 'physical_hardware_tested'):
        require(report.get(field) is False, f'unsupported claim in {field}')
    for relative, expected in report.get('inputs_sha256', {}).items():
        require(file_sha(safe_path(ROOT, relative)) == expected, 'current traffic input differs')
        require(file_sha(attempt / 'inputs' / Path(relative).name) == expected,
                'pinned traffic input differs')
    traces = {}
    for name, trace in report['compressed_artifacts'].items():
        trace_path = safe_path(attempt, trace['path'])
        packed_sha = file_sha(trace_path)
        require(packed_sha == trace['gzip_sha256'], 'compressed trace digest mismatch')
        traces[name] = {**trace, 'path': trace_path}
    return report, traces, {
        'selected_report': str(path.relative_to(ROOT)), 'report_sha256': file_sha(path),
        'source_revision': revision, 'head_at_verification': head, 'source_sha256': pins,
        'trace_sha256': {name: {'gzip': meta['gzip_sha256'], 'raw': meta['raw_sha256']}
                         for name, meta in traces.items()},
        'trace_events': {name: meta['rows'] for name, meta in traces.items()},
    }


def trace_events(trace):
    hasher, count = hashlib.sha256(), 0
    with gzip.open(trace['path'], 'rb') as stream:
        for line in stream:
            hasher.update(line)
            if line.startswith(b'{'):
                count += 1
                yield json.loads(line)
            else:
                require(not any(term in line.lower() for term in
                                (b'%error', b'assertion failed', b'fatal', b'timeout')),
                        'simulation transcript contains failure text')
    require(hasher.hexdigest() == trace['raw_sha256'], 'raw trace digest mismatch')
    require(count == trace['rows'], 'trace event count mismatch')


class PinOracle:
    """SDR command decoder independent of the SV RAM and DUT implementation."""

    def __init__(self):
        self.memory = {}
        self.open_rows = {}
        self.last_act = collections.defaultdict(lambda: -100)
        self.last_pre = collections.defaultdict(lambda: -100)
        self.last_write = collections.defaultdict(lambda: -100)
        self.last_refresh = -100
        self.reads = collections.deque()
        self.controller_reads = collections.deque()
        self.counts = collections.Counter()
        self.last_command_cycle = -1
        self.mode = None

    def value(self, address):
        return self.memory.get(address, (address & 65535) ^ 0x5a3c)

    def command(self, event):
        cycle, command, bank, address = (event[k] for k in ('cycle', 'command', 'bank', 'address'))
        require(cycle > self.last_command_cycle, 'two commands or reordered SDR command edges')
        self.last_command_cycle = cycle
        require(command in range(8) and bank in range(4) and address in range(8192),
                'invalid SDR command width')
        require(command == 7 or cycle - self.last_refresh >= 8,
                'SDR command before tRFC recovery')
        self.counts[command] += 1
        if command == 3:  # ACTIVATE
            require(bank not in self.open_rows, 'ACTIVATE into an open bank')
            require(cycle - self.last_pre[bank] >= 2, 'ACTIVATE violates tRP')
            self.open_rows[bank] = address
            self.last_act[bank] = cycle
        elif command == 2:  # PRECHARGE
            banks = range(4) if address & 1024 else (bank,)
            for b in banks:
                if b in self.open_rows:
                    require(cycle - self.last_act[b] >= 5, 'PRECHARGE violates tRAS')
                require(cycle - self.last_write[b] >= 2, 'PRECHARGE violates tWR')
                self.open_rows.pop(b, None)
                self.last_pre[b] = cycle
        elif command in (4, 5):  # WRITE / READ
            require(bank in self.open_rows, 'column command to closed bank')
            require(cycle - self.last_act[bank] >= 2, 'column command violates tRCD')
            require(address & ~511 == 0, 'unexpected column flags/auto precharge')
            word = (bank << 22) | (self.open_rows[bank] << 9) | address
            if 'row' in event:
                require(event['row'] == self.open_rows[bank], 'trace row disagrees with ACTIVATE')
            if command == 4:
                data = event['dq']
                require(data in range(65536), 'invalid write DQ')
                self.memory[word] = data
                self.last_write[bank] = cycle
            else:
                require(address % 8 == 0, 'BL8 read not aligned')
                require(self.mode == 0x233, 'READ before BL8/CAS3/single-write mode set')
                for beat in range(8):
                    self.reads.append((cycle + 3 + beat, word + beat, self.value(word + beat)))
                    self.controller_reads.append((word + beat, self.value(word + beat),
                                                  event['time_ps'] + 61000 + beat * 10000))
        elif command == 1:  # AUTO REFRESH
            require(not self.open_rows, 'AUTO REFRESH with open bank')
            require(all(cycle - self.last_pre[b] >= 2 for b in range(4)),
                    'AUTO REFRESH violates precharge recovery')
            self.last_refresh = cycle
        elif command == 0:  # LOAD MODE REGISTER
            require(address == 0x233 and bank == 0, 'wrong BL8/CAS3/single-write mode')
            self.mode = address
        else:
            require(command == 7, 'unexpected BURST TERMINATE/reserved command')

    def read(self, event):
        require(self.reads, 'unsolicited SDR read data')
        expected_cycle, expected_address, expected_data = self.reads.popleft()
        require((event['cycle'], event['address'], event['data']) ==
                (expected_cycle, expected_address, expected_data),
                f'SDR BL8 beat differs from independent memory oracle: {event}')
        self.counts['read_beats'] += 1

    def controller_read(self, event):
        require(self.controller_reads, 'unsolicited controller read response')
        address, data, time_ps = self.controller_reads.popleft()
        require(event['data'] == data, '279-degree capture/retime/consume data mismatch')
        require(event['time_ps'] == time_ps, 'controller read capture/retime/consume timing mismatch')
        if 'address' in event:
            require(event['address'] == address, 'controller read response address mismatch')
        self.counts['controller_read_beats'] += 1


def decode_native_fixture():
    meta = json.loads(Path(__file__).with_name('traffic-results.json').read_text())
    fixture = safe_path(ROOT, meta['fixture']['path'])
    require(file_sha(fixture) == meta['fixture']['gzip_sha256'], 'native fixture digest differs')
    require(file_sha(safe_path(ROOT, meta['source_report'])) == meta['source_report_sha256'],
            'native traffic source report differs')
    require(meta['source_report_sha256'] == '73286b38fb62dc667213d143005a4315a9cf661c96b19677e02310dccf261704',
            'native replay no longer uses the independently selected earlier live report')
    source_path = safe_path(ROOT, meta['source_report'])
    source = json.loads(source_path.read_text())
    source_mode = next(mode for mode in source['modes'] if mode['name'] == 'rows')
    actual_meta = source_mode['compressed_artifacts']['actual-rows.tsv']
    actual_path = safe_path(source_path.parent, actual_meta['path'])
    require(file_sha(actual_path) == actual_meta['gzip_sha256'], 'earlier actual bank artifact differs')
    actual_raw = gzip.decompress(actual_path.read_bytes())
    require(digest(actual_raw) == actual_meta['raw_sha256'], 'earlier actual bank bytes differ')
    accepted = {}
    for line in actual_raw.decode().splitlines():
        name, profile, data = line.split('\t')
        if profile == '0' and name.startswith('accepted_'):
            accepted[name.removeprefix('accepted_')] = bytes.fromhex(data)
    source_frames = {row['fid']: row for row in source_mode['live_rows'] if row['profile'] == 0}
    for frame in meta['frames']:
        row = source_frames[frame['fid']]
        bank = accepted[row['pipeline_id']]
        require(len(bank) == 560640 and digest(bank) == frame['accepted_bank_sha256'],
                'native golden is not the earlier actual accepted bank')
        require(frame['bank'] == row['accepted_bank'] and frame['epoch'] == row['epoch'],
                'native bank/epoch differs from earlier live acceptance')
    raw_hash, count = hashlib.sha256(), 0
    with gzip.open(fixture, 'rb') as stream:
        for line in stream:
            raw_hash.update(line)
            value = int(line, 16)
            require(value >> 150 == 0, 'native fixture reserved bits nonzero')
            count += 1
            yield {'epoch': (value >> 118) & 0xffffffff,
                   'token': (value >> 86) & 0xffffffff,
                   'bank': (value >> 84) & 3,
                   'addr': (value >> 64) & 0xfffff,
                   'data': value & 0xffffffffffffffff}
    require(raw_hash.hexdigest() == meta['fixture']['raw_sha256'], 'native raw fixture differs')
    require(count == meta['fixture']['rows'], 'native fixture row count differs')


REQUIRED_CHECKS = {
    'four_bank_single_writes_and_exact_bl8_reads', 'row_hit_exact_four_word_writes',
    'row_miss_precharge_activate', 'three_candidate_bank_aperture_edges',
    'seeded_distinct_row_payloads', 'periodic_refresh_and_post_refresh_row',
    'reset_held_success_response_stable', 'cancel_held_success_response_stable',
    'invalid_bank_alignment_and_aperture_reject', 'clean_retry_after_cancel_and_reject',
} | {f'{kind}_after_word_{index}' for kind in ('cancel', 'reset') for index in range(-1, 4)}


def replay(events, seed):
    oracle = PinOracle()
    active = physical = None
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
                require(physical is not None and not physical['pin_seen'],
                        'pin column command has no unique controller request')
                word = ((event['bank'] << 22) | (oracle.open_rows[event['bank']] << 9)
                        | event['address'])
                require(word == physical['address'] and
                        (event['command'] == 4) == bool(physical['write']),
                        'pin command differs from accepted controller request')
                if physical['write']:
                    require(event['dq'] == physical['data'], 'pin DQ differs from controller write data')
                physical['pin_seen'] = True
                physical['pin_time'] = event['time_ps']
        elif kind == 'read':
            oracle.read(event)
        elif kind == 'controller_read':
            oracle.controller_read(event)
        elif kind == 'controller_req':
            require(physical is None, 'controller accepted two physical owners')
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
            physical = dict(event, logical=logical, pin_seen=False)
        elif kind == 'controller_done':
            require(physical is not None and physical['pin_seen'],
                    'controller retired without an actual pin command')
            for field in ('write', 'address', 'data'):
                require(event[field] == physical[field], 'controller owner identity changed before drain')
            minimum = 41000 if physical['write'] else 131000
            require(event['time_ps'] - physical['pin_time'] >= minimum,
                    'controller retired before its real command/data recovery completed')
            if physical['logical']:
                require(active is not None, 'logical owner lost before physical drain')
                active['retired'] += 1
            last_done = dict(event, logical=physical['logical'])
            physical = None
        elif kind == 'bridge_req':
            require(active is None and physical is None, 'logical row accepted over owned physical/response lease')
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
            if active is not None and active['offered'] is None and event['state'] != 4:
                active['killed'] = True
            if event['word_pending']:
                require((physical is not None and physical['logical']) or
                        (last_done is not None and last_done['logical'] and
                         last_done['time_ps'] == event['time_ps']),
                        'warm kill reports pending word with no retained physical owner')
        elif kind in ('bridge_offer', 'bridge_rsp'):
            require(active is not None, 'response has no logical owner')
            payload = tuple(event[k] for k in ('epoch', 'token', 'bank', 'address', 'error'))
            require(payload[:4] == tuple(active[k] for k in ('epoch', 'token', 'bank', 'address')),
                    'response tag/address identity differs from accepted row')
            require(physical is None and active['retired'] == active['accepted'],
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
            require(not native and active is None and physical is None, 'native replay starts with owned lease')
            native = True
            fixture = iter(decode_native_fixture())
            native_meta = json.loads(Path(__file__).with_name('traffic-results.json').read_text())
        elif kind == 'native_end':
            require(native and active is None and physical is None, 'native replay ends before drain')
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
    require(active is None and physical is None and not native, 'undrained logical/physical lease at end')
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
    return {
        'seed': seed, 't_ac_ns': config['t_ac_ns'], 'event_counts': dict(counts),
        'command_counts': {str(k): v for k, v in oracle.counts.items()},
        'checks': sorted(checks), 'native_frames': native_frames,
        'native_rows': native_rows, 'verdict': verdict,
        'receipt_algorithm': 'Single-pass FIFO/controller ownership correlation; no per-response rescans',
    }


def audit_attempt(path):
    report, traces, output = audit_provenance(path)
    require(report['schema'] == 'cu66-v91l-real-sdram-bridge-v1', 'wrong real-controller report schema')
    require(report['seed'] in SEEDS, 'unexpected seed')
    require({m['name'] for m in report['modes']} == {'tac2', 'tac7'}, 'missing tAC mode')
    modes = []
    for mode in report['modes']:
        require(mode['status'].startswith('PASS'), 'failed tAC mode')
        trace_name = f"simulation-{mode['name']}.jsonl"
        require(trace_name in traces, 'missing tAC trace')
        result = replay(trace_events(traces[trace_name]), report['seed'])
        require(result['verdict'] == mode['verdict'], 'mode verdict differs from trace')
        require(result['t_ac_ns'] == mode['t_ac_ns'], 'tAC mode label mismatch')
        require(result['native_rows'] == mode['native_rows'], 'native replay mode mismatch')
        require(result['checks'] == sorted(name.strip() for name in mode['checks']),
                'reported directed case list differs from replayed trace')
        modes.append(result)
    output.update(seed=report['seed'], modes=modes, native_replay=report['native_replay'])
    return output


def negative_controls(path):
    report = json.loads(path.read_text())
    metadata = report['compressed_artifacts']['simulation-tac7.jsonl']
    events = list(trace_events({**metadata, 'path': path.parent / metadata['path']}))
    controls = (
        ('corrupt_write_pin_dq', 'pin', 'dq', lambda e: e['command'] == 4),
        ('corrupt_bl8_scheduled_data', 'read', 'data', lambda e: True),
        ('corrupt_controller_capture_data', 'controller_read', 'data', lambda e: True),
        ('corrupt_response_identity', 'bridge_rsp', 'token', lambda e: True),
        ('false_response_error', 'bridge_offer', 'error', lambda e: True),
        ('corrupt_physical_drain_identity', 'controller_done', 'address', lambda e: True),
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
            replay(modified(), report['seed'])
        except AssertionError as error:
            require(changed, 'negative control did not exercise a trace mutation')
            rejected.append({'mutation': name, 'rejected': True, 'reason': str(error)})
        else:
            raise AssertionError(f'independent checker accepted negative control {name}')
    return rejected


def main():
    selected = json.loads((AREA / 'controller-results.json').read_text())
    latest = {}
    for path in sorted((AREA / 'controller-attempts').glob('*/results.json')):
        report = json.loads(path.read_text())
        if report.get('seed') in SEEDS:
            latest[report['seed']] = path
    require(set(latest) == set(SEEDS), f'missing required seeds: {sorted(latest)}')
    audits = [audit_attempt(latest[seed]) for seed in SEEDS]
    require(audits[0]['source_sha256'] == audits[1]['source_sha256'],
            'required seeds used different source bytes')
    require(selected['selected_report'] in {a['selected_report'] for a in audits},
            'selected report is not one of the latest independently audited attempts')
    require(all(a['native_replay'] == audits[0]['native_replay'] for a in audits),
            'required seeds used different native replay scope')
    result = {
        'schema': SCHEMA, 'status': 'PASS_TWO_SEED_REAL_CONTROLLER_ROW_PIN_AUDIT',
        'verifier': str(Path(__file__).resolve().relative_to(ROOT)),
        'verifier_sha256': file_sha(Path(__file__).resolve()),
        'baseline_revision': BASELINE, 'frozen_controller_sha256': FROZEN_SHA,
        'controller_derivative': 'Only three explicit width casts and one unused constant removal; independently reconstructed from frozen original',
        'attempts': audits,
        'checker_negative_controls': negative_controls(latest[SEEDS[0]]),
        'assertions': {
            'seeds': list(SEEDS), 't_ac_ns': [2, 7],
            'current_source_bytes_equal_both_source_snapshots': True,
            'strict_assert_and_warning_flags': True,
            'all_pin_column_commands_matched_to_accepted_controller_requests': True,
            'pin_write_data_and_bl8_read_data_independently_replayed': True,
            'four_ordered_little_endian_word_writes_per_successful_row': True,
            'ack_after_actual_controller_idle_recovery': True,
            'warm_cancel_reset_exact_prefix_side_effects': True,
            'immutable_response_identity_under_backpressure_and_late_kill': True,
            'native_candidate_traffic_replay_qualified': audits[0]['native_replay'],
            'byte_rmw_implemented': False, 'byte_rmw_qualified': False,
            'physical_byte_vs_row_comparison_qualified': False,
            'current_live_codec_controller_join_qualified': False,
            'shared_service_complete': False,
            'hardware_or_frequency_qualified': False,
        },
        'scope': 'Independent source and pin-trace audit of the standalone real SDRAM-controller row bridge, source-compatible timing model, and optional replay of earlier native candidate writes.',
        'limitations': [
            'The 10ns clock period, 4ns forwarded-clock flight, 279-degree read capture, and tAC2/7ns are simulation assumptions; clock counts are not achieved FPGA frequency or hardware timing signoff.',
            'Warm reset/cancel preserves already accepted physical writes; it cannot roll back a partially written row. Only the exact accepted-word prefix may change.',
            'The standalone bridge checks bank 0..2 and aperture bounds but has no accepted/reference/front bank role inputs; caller must choose a provisional destination and discard canceled logical completions.',
            'An already offered completion remains immutable through later reset/cancel, and may be consumed on that same edge after physical ownership has drained.',
            'No byte-control RTL RMW, shared concurrent SDRAM clients, current decoder/hash/publication join, 30fps hardware result, or under-10ms decode result is qualified.',
            'Native replay, when present, is preserved earlier live candidate-memory traffic with accepted-bank goldens, not current live cryptographic commit/publication integration.',
            'count_cancels in RTL counts asserted kill cycles while active, not necessarily distinct canceled rows.',
        ],
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'status': result['status'], 'seeds': list(SEEDS),
                      'native_replay': audits[0]['native_replay'],
                      'audit': str(OUT.relative_to(ROOT))}, indent=2))


if __name__ == '__main__':
    main()
