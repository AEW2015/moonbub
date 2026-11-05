#!/usr/bin/env python3
"""Read-only, independent audit of frozen CU66 v69 leaf-component evidence.

Does not run producer audit scripts, simulate, re-encode, or repin their results.
Integration is intentionally excluded. Newly observed hashes in this audit are
not represented as historical producer pins. Requires only the Python standard
library; run from any working directory.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import struct
import sys
import zlib

ROOT = Path(__file__).resolve().parents[2]
FPGA = ROOT / 'fpga/experiments/cu66-v69'
NATIVE = ROOT / 'experiments/cu66-native-v69'
OLD = ROOT / 'experiments/python-game-binary-qual-v40-study'
HEX64 = re.compile(r'^[0-9a-f]{64}$')
AB = struct.Struct('<4sBBIHH4I3I')
OUTER = struct.Struct('<4sBBHIIHH16s16s16sII')
INNER = struct.Struct('<4sBBIIIHHBB16sIIIII')


class Audit:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.checked = Counter()
        self.observed = {}
        self.pin_assertions = []
        self.components = {}

    def label(self, path):
        path = Path(path).resolve()
        try:
            return path.relative_to(ROOT).as_posix()
        except ValueError:
            return str(path)

    def need(self, condition, context, **details):
        self.checked['assertions'] += 1
        if not condition:
            self.errors.append(dict(context=context, **details))
        return bool(condition)

    def sha(self, path):
        path = Path(path).resolve()
        key = self.label(path)
        if key not in self.observed:
            digest = hashlib.sha256()
            with path.open('rb') as stream:
                for data in iter(lambda: stream.read(1024 * 1024), b''):
                    digest.update(data)
            self.observed[key] = dict(sha256=digest.hexdigest(), bytes=path.stat().st_size)
        return self.observed[key]['sha256']

    def pin(self, path, expected, context, size=None):
        path = Path(path).resolve()
        record = dict(context=context, path=self.label(path), expected=expected)
        self.pin_assertions.append(record)
        self.checked['declared_hash_assertions'] += 1
        if not self.need(path.is_file(), context, path=self.label(path), error='missing file'):
            return
        actual = self.sha(path)
        self.need(actual == expected, context, path=self.label(path), expected=expected, actual=actual)
        if size is not None:
            self.need(path.stat().st_size == size, context + ': byte length', path=self.label(path), expected=size, actual=path.stat().st_size)

    def json(self, path, schema=None):
        self.sha(path)
        result = json.loads(Path(path).read_text())
        if schema:
            self.need(result.get('schema') == schema, self.label(path) + ': schema', expected=schema, actual=result.get('schema'))
        return result

    def resolve(self, key, base, aliases=None):
        if aliases and key in aliases:
            return aliases[key]
        path = Path(key)
        if path.is_absolute():
            return path
        if path.parts[0] in ('experiments', 'fpga', 'scripts', 'docs'):
            return ROOT / path
        return base / path

    def pinmaps(self, document, base, aliases=None):
        for field in ('source_sha256', 'source_sha256_after', 'producer_source_sha256', 'artifacts_sha256', 'logs_sha256'):
            value = document.get(field)
            if isinstance(value, dict):
                for key, expected in value.items():
                    if not isinstance(expected, str) or not HEX64.fullmatch(expected):
                        self.need(False, field + ': unsupported pin schema', key=key)
                        continue
                    self.pin(self.resolve(key, base, aliases), expected, field)
        if 'source_sha256_after' in document:
            self.need(document['source_sha256'] == document['source_sha256_after'], str(base) + ': before/after source agreement')

    def descriptor(self, value, base, context='fixture'):
        """Check all declared stored/raw hashes, using bounded zlib inflation."""
        path = self.resolve(value['path'], base)
        expected = value.get('sha256', value.get('stored_sha256'))
        if expected is None:
            self.need(False, context + ': descriptor lacks stored hash', path=self.label(path))
            return b''
        self.pin(path, expected, context, value.get('bytes'))
        if not path.is_file():
            return b''
        stored = path.read_bytes()
        if 'raw_bytes' in value:
            data = self.inflate(stored, value['raw_bytes'], context)
            self.need(hashlib.sha256(data).hexdigest() == value['raw_sha256'], context + ': inflated hash', path=self.label(path))
            return data
        return stored

    def inflate(self, stored, expected_length, context):
        self.need(0 <= expected_length <= 4_000_000, context + ': bounded inflated length', bytes=expected_length)
        if not 0 <= expected_length <= 4_000_000:
            return b''
        decoder = zlib.decompressobj()
        raw = decoder.decompress(stored, expected_length + 1)
        self.need(len(raw) == expected_length and decoder.eof and not decoder.unused_data and not decoder.unconsumed_tail,
                  context + ': exact zlib termination/length', expected=expected_length, actual=len(raw))
        self.checked['inflated_fixtures'] += 1
        return raw

    def walk_descriptors(self, value, base, context):
        if isinstance(value, dict):
            if 'path' in value and any(k in value for k in ('sha256', 'stored_sha256')):
                self.descriptor(value, base, context)
            else:
                for key, child in value.items():
                    self.walk_descriptors(child, OLD if key == 'source_old_packet' else base, context + '/' + key)
        elif isinstance(value, list):
            for i, child in enumerate(value):
                self.walk_descriptors(child, base, context + '/' + str(i))

    def text(self, path):
        self.sha(path)
        return Path(path).read_text()

    def kv_records(self, path, prefix='CASE_PASS '):
        text = self.text(path)
        self.need('TEST_FAIL' not in text and 'Assertion failed' not in text and '%Error' not in text,
                  self.label(path) + ': failure markers absent')
        rows = []
        for line in text.splitlines():
            if line.startswith(prefix):
                rows.append({k: int(v) if re.fullmatch(r'-?\d+', v) else v for k, v in re.findall(r'(\w+)=([^ ]+)', line)})
        return rows, text

    def section(self, name, action):
        before = len(self.errors)
        try:
            result = action()
        except Exception as exc:
            self.errors.append(dict(context=name, exception=type(exc).__name__, detail=str(exc)))
            result = {}
        self.components[name] = dict(status='PASS' if len(self.errors) == before else 'FAIL', **(result or {}))
        print(json.dumps(dict(component=name, **self.components[name])), flush=True)


def crc_ok(data):
    return len(data) >= 4 and zlib.crc32(data[:-4]) == struct.unpack_from('<I', data, len(data) - 4)[0]


def json_lines(text):
    return [json.loads(line) for line in text.splitlines() if line.startswith('{')]


def check_native(a):
    manifest = a.json(NATIVE / 'manifest.json', 'cu66-native-v69-fixtures')
    qualification = a.json(NATIVE / 'qualification.json', 'cu66-native-v69-qualification')
    result = a.json(NATIVE / 'results.json', 'cu66-native-v69-paired')
    for doc in (manifest, qualification, result):
        a.pinmaps(doc, NATIVE)
    a.pin(NATIVE / 'manifest.json', result['manifest_sha256'], 'native timing manifest')
    fixture_rows = [(c['scene'], r) for c in manifest['cases'] for r in c['rows']]
    a.need(len(fixture_rows) == 457 and sum(r['key'] for _, r in fixture_rows) == 20, 'native frame/key counts')
    tiles = 0
    for scene, row in fixture_rows:
        a.walk_descriptors(row, NATIVE, f'native/{scene}/{row["id"]}')
        packet = (NATIVE / row['packet']['path']).read_bytes()
        a.need(crc_ok(packet) and packet[:4] == b'CU66', 'native outer CRC/profile', scene=scene, id=row['id'])
        fields = OUTER.unpack_from(packet)
        nb, nh = fields[-2:]
        a.need(len(packet) == OUTER.size + nb + nh + 4 and bool(fields[2] & 1) == row['key'] and fields[4] == row['id'], 'native envelope lengths/identity')
        a.need(fields[10].hex() == row['canonical_tag'], 'native canonical tag descriptor')
        inner = packet[OUTER.size:OUTER.size + nb]
        a.need(crc_ok(inner) and inner[:4] == b'GU66', 'native inner CRC/profile')
        old = a.descriptor(row['source_old_packet'], OLD, 'native source packet')
        a.need(len(packet) == len(old) - 16, 'native canonical-only wire saving')
        for plane in row['planes']:
            tiles += plane['blocks']
            ab = (NATIVE / plane['packet']['path']).read_bytes()
            h = AB.unpack_from(ab)
            a.need(crc_ok(ab) and h[:2] == (b'AB38', 1) and h[3:5] == (plane['blocks'], plane['blocks_w']) and len(ab) == AB.size + 4 + sum(h[6:10]), 'native AB38 headers/CRC')
            coefficient = a.inflate((NATIVE / plane['expected_coefficients']['path']).read_bytes(), plane['blocks'] * 128, 'native coefficients')
            a.need(hashlib.sha256(coefficient).hexdigest() == plane['expected_coefficients_raw_sha256'], 'native raw coefficient digest')
            mask = (NATIVE / plane['safe_hidden_mask']['path']).read_bytes()
            a.need(len(mask) == plane['full_blocks'] and set(mask) <= {0, 1}, 'native safe mask domain')
            want = plane['full_blocks'] if plane['dispatch'] == 5 else len(mask) - sum(mask)
            a.need(plane['dispatch'] in (5, 6) and want == plane['blocks'], 'native full/compact geometry')
    a.need(tiles == qualification['checks']['coefficient_tiles'] == 3_586_687, 'native coefficient tile total')
    all_timing = []
    for case, fixture in zip(result['cases'], manifest['cases'], strict=True):
        a.need(case['scene'] == fixture['scene'], 'native paired scene')
        for row, expected in zip(case['rows'], fixture['rows'], strict=True):
            for key in ('id', 'key', 'canonical_tag', 'canonical_yuv_u8_sha256', 'hud_words_u16le_sha256', 'display_rgb565_u16le_sha256'):
                a.need(row[key] == expected[key], 'native timing golden binding: ' + key)
            a.need(row['packet_sha256'] == expected['packet']['sha256'], 'native timing packet binding')
            for role in ('python', 'native'):
                times = row['complete_presentation_ms'][role]
                a.need(len(times) == 3 and all(math.isfinite(t) and t > 0 for t in times), 'native positive paired samples')
                a.need(statistics.median(times) == row['median_ms'][role], 'native paired median')
            a.need(row['paired_order'] == [(['python', 'native'] if (row['id'] + rep) % 2 == 0 else ['native', 'python']) for rep in range(3)], 'native alternating order')
            all_timing.append(row)
        for role in ('python', 'native'):
            a.need(math.isclose(statistics.mean(r['median_ms'][role] for r in case['rows']), case['summary']['mean_paired_median_complete_presentation_ms'][role], rel_tol=1e-12), 'native per-case mean')
    for role in ('python', 'native'):
        a.need(math.isclose(statistics.mean(r['median_ms'][role] for r in all_timing), result['summary']['mean_paired_median_complete_presentation_ms'][role], rel_tol=1e-12), 'native aggregate mean')
    for name, count in (('negative_manifest.json', 28), ('entropy-directed.json', 31), ('hud-directed.json', 32)):
        d = a.json(NATIVE / name)
        a.pinmaps(d, NATIVE)
        a.walk_descriptors(d, NATIVE, name)
        a.need(len(d['cases']) == count, 'native directed count: ' + name)
    full = json_lines(a.text(NATIVE / 'full-sanitized.log'))
    a.need(len(full[:-1]) == 457 and full[-1]['frames'] == 457 and full[-1]['keys'] == 20, 'native sanitized full frame evidence')
    index = [line.split('\t') for line in (NATIVE / 'index.tsv').read_text().splitlines()]
    a.need(len(index) == 457, 'native executable fixture index length')
    by_case = {c['scene']: i for i, c in enumerate(manifest['cases'])}
    for (scene, row), fields, observed in zip(fixture_rows, index, full[:-1], strict=True):
        expected = [str(by_case[scene]), str(row['id']), row['packet']['path'], row['canonical_yuv_u8_sha256'], row['hud_words_u16le_sha256'], row['display_rgb565_u16le_sha256']]
        a.need(fields == expected and observed['case'] == by_case[scene] and observed['id'] == row['id'], 'native sanitized executable index/manifest/frame binding')
    for log in ('tests-sanitized.log', 'fuzz-sanitized.log', 'full-sanitized.log'):
        text = a.text(NATIVE / log)
        a.need(not any(term in text for term in ('ERROR:', 'runtime error:', 'AddressSanitizer')), 'native sanitizer failure markers absent: ' + log)
    coefficients = json_lines(a.text(NATIVE / 'ab38-check.log'))[-1]
    a.need(coefficients['arithmetic_planes'] == 1371 and coefficients['exact_coefficient_tiles'] == tiles, 'native exact coefficient transcript coverage')
    directed = json_lines(a.text(NATIVE / 'entropy-directed.log'))[-1]
    a.need(directed['directed_valid_entropy_packets'] == 6 and directed['directed_rejected_entropy_packets'] == 25, 'native actual directed entropy outcomes')
    negative = json_lines(a.text(NATIVE / 'tests-sanitized.log'))
    a.need(len(negative[:-1]) == negative[-1]['malformed_or_unsupported_packets_rejected'] == 28 and all(r['published_state_unchanged'] for r in negative[:-1]), 'native actual malformed failure/publication evidence')
    fuzz = json_lines(a.text(NATIVE / 'fuzz-sanitized.log'))[-1]
    a.need(fuzz['mutation_trials'] == 512 and fuzz['rejected'] == 507 and fuzz['accepted_bound_identical'] == 5, 'native seeded mutation evidence')
    hud = json_lines(a.text(NATIVE / 'hud-directed.log'))
    a.need(hud[-1]['native_directed_HUD_cases'] == len(hud) - 1 == 32, 'native HUD transcript count')
    return dict(frames=len(fixture_rows), keys=20, arithmetic_planes=3 * len(fixture_rows), coefficient_tiles=tiles, actual_paired_samples=6 * len(all_timing))


def check_entropy(a):
    base = FPGA / 'entropy'
    result = a.json(base / 'results.json', 'cu66-ab38-entropy-rtl-v69')
    a.pinmaps(result, base)
    a.pinmaps(a.json(base / 'fixture-evidence.json'), base)
    native = a.json(NATIVE / 'manifest.json')
    old = a.json(OLD / 'results.json')
    expected = {}
    for nc, oc in zip(native['cases'], old['cases'], strict=True):
        for nr, row in zip(nc['rows'], oc['rows'], strict=True):
            for axis, (plane, attempt) in enumerate(zip(nr['planes'], row['attempts'], strict=True)):
                trial = attempt['trials'][attempt['selected'] - 1]
                packet = (NATIVE / plane['packet']['path']).read_bytes()
                raw = packet[5] == 1
                a.need(hashlib.sha256(packet).hexdigest() == trial['packet']['raw_sha256'], 'entropy selected frozen packet')
                expected[f'{nc["scene"]}_{row["id"]}_{axis}'] = dict(tiles=plane['blocks'], decisions=0 if raw else trial['work']['probability_products'], renorm=0 if raw else trial['work']['renorm_steps'], reads=2 * len(packet) - (46 if raw else 42))
    for kind in ('actual', 'directed', 'stress'):
        fixture = [line.split('\t') for line in (base / (kind + '.tsv')).read_text().splitlines()]
        for fields in fixture:
            for index in (1, 2):
                if fields[index] == '-':
                    a.need(index == 2 and fields[6] == '1', 'entropy absent coefficient oracle only for rejected fixture')
                    continue
                p = (base / fields[index]).resolve()
                digest = p.name.split('.')[0]
                a.pin(p, digest, f'entropy/{kind} content addressed fixture')
            if fields[6] == '0':
                a.inflate((base / fields[2]).read_bytes(), int(fields[3]) * 128, 'entropy expected coefficients')
        seeds = (6901, 6902) if kind == 'actual' else (6901, 6902, 6903)
        for seed in seeds:
            rows, text = a.kv_records(base / f'{kind}-seed{seed}.log')
            final_line = text.rstrip().splitlines()[-1]
            a.need(final_line.startswith('TEST_PASS '), 'entropy terminal PASS')
            final = {k: int(v) if v.isdigit() else v for k, v in re.findall(r'(\w+)=([^ ]+)', final_line)}
            a.need(len(rows) == len(fixture) == final['cases'], 'entropy actual case count')
            a.need(final['valid'] == sum(r['error'] == 0 for r in rows) and final['rejected'] == sum(r['error'] != 0 for r in rows), 'entropy valid/reject totals')
            for outkey, rowkey in (('cycles', 'cycles'), ('decisions', 'decisions'), ('renorm', 'renorm'), ('external_reads', 'reads'), ('output_stalls', 'stalls')):
                a.need(final[outkey] == sum(r[rowkey] for r in rows), 'entropy aggregate ' + outkey)
            for fields, row in zip(fixture, rows, strict=True):
                a.need(row['name'] == fields[0] and row['seed'] == seed and (row['error'] != 0) == (fields[6] == '1'), 'entropy fixture/transcript binding')
                if kind == 'actual':
                    for key, want in expected[row['name']].items():
                        a.need(row[key] == want, 'entropy frozen work parity: ' + key)
            entry = next(r for r in result['runs'] if r['seed'] == seed and r.get('kind', 'actual') == kind)
            a.need(entry['clock_counts'] == final, 'entropy saved clock evidence')
            if kind != 'actual':
                a.need('ABORT_RESET_PASS' in text, 'entropy abort/reset transcript')
    a.need(result['actual_coefficient_tiles_per_seed'] == sum(v['tiles'] for v in expected.values()), 'entropy saved tile total')
    return dict(actual_planes_per_seed=len(expected), actual_seeds=2, directed_seeds=3, stress_seeds=3)


def message_fixtures(a, base, length=None):
    result = []
    for line in (base / 'fixtures.tsv').read_text().splitlines():
        name, filename, size, expected = line.split('\t')
        path = base / filename
        a.pin(path, path.name.split('.')[0], 'message stored fixture')
        data = a.inflate(path.read_bytes(), int(size), 'message fixture')
        a.need(hashlib.sha256(data).hexdigest() == expected, 'message fixture SHA256')
        if length is not None:
            a.need(len(data) == length and data[:4] == bytes.fromhex('d002e001'), 'canonical geometry prefix')
        result.append((name, len(data)))
    return result


def check_hash(a):
    base = FPGA / 'hash'
    result = a.json(base / 'results.json', 'cu66-sha256-rtl-v69')
    a.pinmaps(result, base)
    a.pinmaps(a.json(base / 'fixture-evidence.json'), base)
    fixtures = message_fixtures(a, base)
    a.need(len(fixtures) == 98, 'SHA fixture count')
    for entry in result['runs']:
        banks, mode = entry['buffer_blocks'], entry['mode']
        rows, text = a.kv_records(base / f'banks{banks}-{mode}.log')
        a.need(text.rstrip().splitlines()[-1].startswith('TEST_PASS ') and 'CONTROL_PASS ' in text, 'SHA terminal/control evidence')
        a.need(len(rows) == 106, 'SHA complete fixture/retry count')
        for row, (name, size) in zip(rows[:98], fixtures, strict=True):
            blocks = (size + 9 + 63) // 64
            a.need((row['name'], row['bytes'], row['blocks'], row['rounds'], row['padding']) == (name, size, blocks, blocks * 64, blocks * 64 - size), 'SHA fixture identity/active work')
            a.need(row['result_accept'] == row['cycles'] and row['result_first'] < row['cycles'], 'SHA result timing')
            if mode == 'ideal':
                expected = 130 * blocks + 2 if banks == 1 else (132 if blocks == 1 else 66 * blocks + 65)
                a.need(row['result_first'] == expected, 'SHA ideal actual clock count')
        a.need(entry['canonical_messages'] == [r for r in rows[:98] if r['name'].startswith('canonical_')], 'SHA saved canonical clocks')
    return dict(fixture_messages=98, runs=len(result['runs']), main_digest_checks=98 * len(result['runs']))


def check_rows(a):
    base = FPGA / 'rows'
    result = a.json(base / 'results.json', 'cu66-canonical-rows-sha-rtl-v69')
    a.pinmaps(result, base)
    a.pinmaps(a.json(base / 'fixture-evidence.json'), base)
    fixtures = message_fixtures(a, base, 518404)
    a.need(len(fixtures) == 7, 'rows fixture count')
    for entry in result['runs']:
        strips, hashes = entry['strip_banks'], entry['hash_banks']
        label = f'rows{strips}' if not hashes else f'combined{strips}{hashes}'
        rows, text = a.kv_records(base / f'{label}-{entry["mode"]}.log')
        a.need(text.rstrip().splitlines()[-1].startswith('TEST_PASS ') and 'CONTROL_PASS ' in text, 'rows terminal/control evidence')
        a.need(len(rows) == 19 and [r['mode'] for r in rows] == [0] * 7 + list(range(1, 9)) + [0] * 4, 'rows success/malformed/retry sequence')
        for row in rows:
            if row['mode'] == 0:
                a.need((row['error'], row['bytes'], row['tiles'], row['writes'], row['reads']) == (0, 518404, 8100, 64800, 64800), 'rows actual byte/tile/RAM counts')
                a.need(row['first_result'] >= row['last_byte'] if hashes else row['first_result'] == 0, 'rows SHA result boundary')
            else:
                a.need(row['error'] in (2, 3) and row['first_result'] == 0, 'rows malformed no published hash')
        a.need(entry['frames'] == rows[:7], 'rows saved per-frame evidence')
    memory = a.json(base / 'memory-evidence.json', 'cu66-rows-generic-memory-v69')
    a.pinmaps(memory, base)
    for entry in memory['cases']:
        banks = entry['strip_banks']
        path = base / f'yosys-rows{banks}.json.zlib'
        a.pin(path, entry['netlist_sha256'], 'rows collected netlist')
        netlist = json.loads(zlib.decompress(path.read_bytes()))
        cell = netlist['modules']['cu66_tile_rows']['cells']['strip']
        parameters = {k: int(cell['parameters'][k], 2) for k in ('WIDTH', 'SIZE', 'RD_PORTS', 'WR_PORTS', 'RD_CLK_ENABLE', 'WR_CLK_ENABLE')}
        a.need(cell['type'] == '$mem_v2' and parameters == entry['parameters'] == dict(WIDTH=64, SIZE=720 * banks, RD_PORTS=1, WR_PORTS=1, RD_CLK_ENABLE=1, WR_CLK_ENABLE=1), 'rows actual collected RAM ports')
        a.need(entry['logical_payload_bytes'] == parameters['WIDTH'] * parameters['SIZE'] // 8, 'rows logical RAM storage')
    return dict(runs=len(result['runs']), main_stream_checks=7 * len(result['runs']), main_bytes=7 * len(result['runs']) * 518404, generic_sync_RAM_configs=2)


def marker_counts(a, path, marker):
    text = a.text(path)
    matches = [line for line in text.splitlines() if line.startswith(marker + ' ')]
    a.need(len(matches) == 1 and not re.search(r'TEST_FAIL|\bFATAL\b|%Error|Assertion failed', text), a.label(path) + ': unique success/no failure')
    return {k: int(v) for k, v in re.findall(r'(\w+)=(\d+)', matches[0])} if matches else {}


def check_inverse(a):
    base = FPGA / 'inverse'
    result = a.json(base / 'results/results.json', 'cu66-idct-v69-dual-simulator-regression-v1')
    a.pinmaps(result, base / 'results')
    fixture = a.json(base / 'fixtures.json', 'cu66-idct-v69-fixtures')
    a.pinmaps(fixture, base)
    a.pin(base / 'tiles.hex', fixture['fixture_sha256'], 'IDCT vector fixture')
    a.need(len((base / 'tiles.hex').read_text().splitlines()) == fixture['tiles'] == 3471, 'IDCT fixture line count')
    for command in result['commands']:
        path = base / 'results' / command['log']
        a.need(command['exit_code'] == 0, 'IDCT command exit')
        a.sha(path)
        if '-seed-' in command['log']:
            backend, seed = command['log'].split('-seed-')
            parsed = marker_counts(a, path, 'CU66_IDCT_TEST_PASS')
            a.need(parsed == result['results'][backend][seed.removesuffix('.log')], 'IDCT actual transcript/saved counts')
    a.need(result['results']['iverilog'] == result['results']['verilator'], 'IDCT independent backend cycle agreement')
    a.warnings.append(dict(component='inverse', gap='Original result declares no expected transcript hashes. Current transcript hashes are observed by this audit, not retroactively attributed to the producer.', logs=[str(c['log']) for c in result['commands']]))
    return dict(backends=2, seeds=len(result['seeds']), tiles_per_run=3471, historical_log_hash_binding=False)


def check_math(a):
    base = FPGA / 'inverse'
    result = a.json(base / 'math-results/results.json', 'cu66-math-v69-regression')
    a.pinmaps(result, base / 'math-results')
    fixture = a.json(base / 'math-fixtures.json')
    a.pinmaps(fixture, base)
    for name, expected in fixture['files'].items():
        a.pin(base / name, expected, 'math fixture')
        a.need(len((base / name).read_text().splitlines()) == fixture['dequant_cases' if name == 'dequant.hex' else 'reconstruct_cases'], 'math fixture line count')
    for run in result['runs']:
        path = base / 'math-results' / (run['name'] + '.log')
        a.pin(path, run['log_sha256'], 'math transcript')
        a.need(run['returncode'] == 0, 'math command exit')
        if run['terminal_PASS_required']:
            a.need(marker_counts(a, path, 'CU66_MATH_TEST_PASS') == dict(dequant=1536, reconstruct=1536), 'math transcript counts')
    return dict(backends=2, dequant_cases_per_backend=1536, reconstruct_cases_per_backend=1536)


def check_expand(a):
    base = FPGA / 'inverse/expand'
    result = a.json(base / 'results/results.json', 'cu66-expand-tiles-v69-test-evidence-v1')
    masks = a.json(base / 'masks.json', 'cu66-expand-independent-mask-v1')
    aliases = dict(DUT=base.parent / 'cu66_expand_tiles.sv', testbench=base / 'tb_expand_tiles.sv', mask_exporter=base / 'export_masks.py', runner=base / 'run_regression.py', mask_manifest=base / 'masks.json', native_manifest=NATIVE / 'manifest.json')
    for plane, entry in masks['plane_masks'].items():
        aliases['mask_' + plane] = base / f'mask_{plane}.hex'
        aliases['native_mask_' + plane] = NATIVE / entry['source_path']
        a.pin(aliases['native_mask_' + plane], entry['source_sha256'], 'expand native mask', entry['bytes'])
        native = aliases['native_mask_' + plane].read_bytes()
        own = bytes(int(v, 16) for v in aliases['mask_' + plane].read_text().split())
        a.need(own == native and sum(own) == entry['hidden_blocks'] and len(own) - sum(own) == entry['visible_blocks'], 'expand independently exported mask agreement')
    a.pin(NATIVE / 'manifest.json', masks['source_manifest_sha256'], 'expand source manifest')
    a.pinmaps(result, base / 'results', aliases)
    for name, descriptor in result['logs'].items():
        a.pin(base / 'results' / name, descriptor['sha256'], 'expand transcript', descriptor['bytes'])
    for backend, entries in result['results'].items():
        for seed, expected in entries.items():
            parsed = marker_counts(a, base / 'results' / f'{backend}-seed-{seed}.log', 'CU66_EXPAND_TILES_PASS')
            a.need(parsed == expected, 'expand actual transcript counts')
    a.need(result['results']['iverilog'] == result['results']['verilator'], 'expand backend agreement')
    return dict(backends=2, seeds=len(result['seeds']), outputs_per_run=16833)


def check_banks(a):
    base = FPGA / 'banks'
    result = a.json(base / 'results.json', 'cu66-bank-v69-sim-evidence-v1')
    vectors = a.json(base / 'vectors.json')
    a.pinmaps(result, base)
    a.pinmaps(vectors, base)
    a.pin(base / 'vectors.txt', vectors['vectors_sha256'], 'bank vectors')
    a.need(len((base / 'vectors.txt').read_text().splitlines()) == vectors['cycles'] == result['vector_cycles'] == 427, 'banks vector cycle count')
    for name, descriptor in result['logs'].items():
        a.pin(base / name, descriptor['sha256'], 'bank transcript', descriptor['bytes'])
    for backend, expected in result['backend_summaries'].items():
        a.need(marker_counts(a, base / f'{backend}-run.log', 'CU66_BANK_CONTROL_PASS') == expected, 'banks transcript count agreement')
    a.need(result['backend_summaries']['iverilog'] == result['backend_summaries']['verilator'], 'banks backend agreement')
    return dict(vector_cycles=427, backends=2)


def check_layout(a):
    base = FPGA / 'layout'
    result = a.json(base / 'results.json', 'cu66-v69-portrait-layout-proof-v1')
    a.pinmaps(result, base)
    geometry = result['geometry']
    a.need(geometry['physical_rgb565_stream_shape'] == [800, 480] and geometry['physical_stream_bytes_each'] == 800 * 480 * 2, 'layout physical geometry')
    a.pin(NATIVE / result['fixture']['packet_path'], result['fixture']['packet_sha256'], 'layout source packet')
    for filename, entry in geometry['stream_artifacts'].items():
        path = base / filename
        a.pin(path, entry['sha256'], 'layout retained physical stream', entry['bytes'])
        data = path.read_bytes()
        a.need(data[:40 * 480 * 2] == bytes(40 * 480 * 2) and data[760 * 480 * 2:] == bytes(40 * 480 * 2), 'layout exact black bars')
        # Recover coded raster from the stored portrait stream without importing
        # the producer's layout/address routines.
        coded = bytearray(720 * 480 * 2)
        for u in range(720):
            for v in range(480):
                out = 2 * (v * 720 + u)
                src = 2 * ((u + 40) * 480 + v)
                coded[out:out + 2] = data[src:src + 2]
        expected = result['fixture']['identity_rgb565_sha256' if 'identity' in filename else 'strong_rgb565_sha256']
        a.need(hashlib.sha256(coded).hexdigest() == expected, 'layout all-pixel inverse portrait mapping')
    storage = result['plane_storage']
    a.need(sum(p['width'] * p['height'] for p in storage['planes']) == storage['total_full_frame_yuv_u8_bytes'] == 518400, 'layout sample storage arithmetic')
    a.need(storage['one_P_reference_read_plus_new_reference_write_bytes'] == 2 * 518400, 'layout reference traffic arithmetic')
    return dict(physical_streams=2, inverse_mapping_pixels_checked=2 * 720 * 480, physical_hardware_fit=False)


def check_packet(a):
    base = FPGA / 'packet'
    result = a.json(base / 'results.json', 'cu66-packet-control-v69')
    manifest = a.json(base / 'manifest.json')
    a.pinmaps(result, base)
    a.pinmaps(manifest, base)
    a.pin(base / 'manifest.json', result['manifest_sha256'], 'packet manifest')
    a.pin(base / 'regression.log', result['regression_log_sha256'], 'packet regression transcript')
    a.walk_descriptors(manifest, base, 'packet fixtures')
    counts = Counter(c['mode'] for c in manifest['cases'])
    a.need(counts == {0: 23, 1: 457, 2: 5} and len(manifest['cases']) == 485, 'packet exact fixture class counts', counts=dict(counts))
    for run in result['runs']:
        path = base / f'seed{run["seed"]}.log'
        text = a.text(path)
        final = text.rstrip().splitlines()[-1]
        a.need(final.startswith('TEST_PASS '), 'packet terminal PASS')
        parsed = json.loads(final.removeprefix('TEST_PASS '))
        a.need(parsed == run, 'packet saved/actual counters')
        # Qmap is also checked on five deferred-semantic cases and one valid
        # parse deliberately aborted by the directed control test.
        a.need(run['valid_frames'] == 457 and run['structural_rejections'] == 23 and run['semantic_deferred_and_aborted'] == 5 and run['qmap_values_checked'] == (457 + 5 + 1) * 1350 and run['abort_tests'] == 3, 'packet numerical coverage')
        # Seed logs are not directly pinned in results; the pinned combined
        # regression transcript must contain their exact output in order.
        a.need(text in (base / 'regression.log').read_text(), 'packet seed log bound by pinned regression transcript')
    return dict(valid_metadata_frames_per_seed=457, seeds=2, structural_rejections_per_seed=23, semantic_cases_deferred_per_seed=5, full_semantic_decoder_proven=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'docs/cu66-v69/component-audit.json')
    args = parser.parse_args()
    # Audit may only write its own review artifacts.
    output = args.output.resolve()
    if output.parent != ROOT / 'docs/cu66-v69':
        parser.error('output must be directly within docs/cu66-v69')
    a = Audit()
    for name, action in (('native', check_native), ('entropy', check_entropy), ('hash', check_hash), ('rows', check_rows), ('inverse', check_inverse), ('math', check_math), ('expand', check_expand), ('banks', check_banks), ('layout', check_layout), ('packet', check_packet)):
        a.section(name, lambda action=action: action(a))
    result = dict(schema='cu66-v69-independent-component-audit-v1', status='FAIL' if a.errors else 'PASS',
                  generated_utc=datetime.now(timezone.utc).isoformat(), verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  scope='Read-only frozen leaf-component provenance, fixtures, numerical transcript and result reconciliation. No new simulation or codec execution.',
                  integration_excluded=True, excluded_moving_components=['integration', 'hud-partition'], components=a.components, checked=dict(a.checked), errors=a.errors, warnings=a.warnings,
                  observed_files=a.observed, declared_hash_assertions=a.pin_assertions,
                  limitations=['No target fit, Fmax, physical RAM mapping, physical 30fps, RF/ESP32 service rate or end-to-end CU66 hardware decode is established by this audit.',
                               'Matching stored hashes and detailed transcripts binds retained evidence; it is not a fresh rerun or formal verification.',
                               'Packet control defers canonical output and HUD semantic validation; native/RTL leaf evidence is not a complete integrated receiver.'])
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(status=result['status'], components=len(a.components), errors=len(a.errors), warnings=len(a.warnings), observed_files=len(a.observed), output=str(output))), flush=True)
    return 1 if a.errors else 0


if __name__ == '__main__':
    sys.exit(main())
