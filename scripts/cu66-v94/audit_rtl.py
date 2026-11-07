#!/usr/bin/env python3
"""Independent RV94 math replay and deliberately corrupted-oracle checks."""
import datetime
import gzip
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT/'fpga/experiments/cu66-v94-rans'
CONTAINER = 'gamebub-cu66-v69-build'
LOWER = 1 << 23


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    selected = json.loads((AREA/'results.json').read_text())
    report_path = ROOT/selected['selected_report']
    qualified = json.loads(report_path.read_text())
    assert qualified['status'] == 'PASS_RTL_RANS_SYMBOL_KERNEL'
    for name, digest in qualified['source_sha256'].items():
        assert sha(ROOT/name) == digest, ('stale source', name)
    for name, digest in qualified['artifacts_sha256'].items():
        assert sha(report_path.parent/name) == digest, ('changed artifact', name)
    vector_report = ROOT/qualified['vector_report']
    provenance = json.loads(vector_report.read_text())
    vectors = vector_report.with_name('vectors.bin')
    data = vectors.read_bytes()
    assert hashlib.sha256(data).hexdigest() == provenance['vectors_sha256']
    assert data[:4] == b'RV94'
    count, = struct.unpack_from('<I', data, 4)
    at = 8
    first_field = None
    symbol_count = 0
    histogram = [0, 0, 0]
    for _ in range(count):
        scale, lanes, models, symbols, nrbytes = struct.unpack_from('<5I', data, at)
        at += 20
        states = list(struct.unpack_from('<4I', data, at))[:lanes]
        at += 16
        frequencies = [struct.unpack_from('<16H', data, at+32*m) for m in range(models)]
        at += 64
        assert scale in (8, 9, 10) and lanes in (2, 4) and models in (1, 2)
        assert all(LOWER <= s < (1 << 31) for s in states)
        assert all(sum(f) == 1 << scale for f in frequencies)
        renorm = data[at:at+nrbytes]
        at += nrbytes
        cursor = 0
        if first_field is None and symbols:
            first_field = at
        for i in range(symbols):
            q, lane, expected_state, expected_cursor = struct.unpack_from('<4I', data, at)
            at += 16
            assert lane == i % lanes and q < 16
            f = frequencies[i % 2 if models == 2 else 0]
            cumulative = sum(f[:q])
            slot = states[lane] & ((1 << scale)-1)
            assert f[q] and cumulative <= slot < cumulative+f[q]
            quotient = states[lane] >> scale
            assert quotient < 1 << 24 and f[q] <= 1024
            product = f[q]*quotient
            assert product < 1 << 32
            value = product+slot-cumulative
            nbytes = 0
            while value < LOWER:
                assert cursor < nrbytes and nbytes < 2
                value = value*256+renorm[cursor]
                cursor += 1
                nbytes += 1
            assert value < 1 << 31
            assert (value, cursor) == (expected_state, expected_cursor)
            states[lane] = value
            histogram[nbytes] += 1
            symbol_count += 1
        assert cursor == nrbytes and all(s == LOWER for s in states)
    assert at == len(data) and count == provenance['case_count'] and symbol_count == provenance['total_symbols']
    assert first_field is not None and all(histogram)
    out = AREA/'audit-attempts'/(datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+uuid.uuid4().hex[:8])
    out.mkdir(parents=True)
    paths = [Path(__file__).resolve(), report_path, vector_report, vectors, report_path.parent/'simulation.bin']
    pins = {str(p.relative_to(ROOT)): sha(p) for p in paths}
    for p in paths:
        dest = out/'sources'/p.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(p.read_bytes())
    result = dict(schema='cu66-v94-rtl-independent-audit-v1', status='FAIL', source_sha256=pins,
                  native_rtl_report=str(report_path.relative_to(ROOT)), symbols_replayed=symbol_count,
                  refill_histogram=histogram, controls=[], physical_timing_proven=False)
    started = time.monotonic()
    try:
        for field, offset in (('symbol', 0), ('state', 8), ('cursor', 12)):
            bad = bytearray(data)
            value, = struct.unpack_from('<I', bad, first_field+offset)
            struct.pack_into('<I', bad, first_field+offset, value ^ 1)
            path = out/(field+'-corrupted.bin')
            path.write_bytes(bad)
            command = ['docker', 'exec', CONTAINER, 'timeout', '30', str(report_path.parent/'simulation.bin'), str(path), str(out/field)]
            observed = subprocess.run(command, capture_output=True, text=True, timeout=45)
            (out/(field+'.log')).write_text(observed.stdout+observed.stderr)
            assert observed.returncode == 1 and 'RTL_TEST_FAIL RTL field/state/cursor mismatch' in observed.stderr
            result['controls'].append(dict(field=field, argv=command, observed_exit_code=observed.returncode,
                                           rejected=True, input_sha256=sha(path)))
        for wave in out.glob('*.vcd'):
            wave.with_suffix('.vcd.gz').write_bytes(gzip.compress(wave.read_bytes(), mtime=0))
            wave.unlink()
        assert pins == {p: sha(ROOT/p) for p in pins}
        result['status'] = 'PASS_INDEPENDENT_RANS_MATH_AND_CHECKER_CONTROLS'
    finally:
        result['wall_seconds'] = time.monotonic()-started
        result['artifacts_sha256'] = {str(p.relative_to(out)): sha(p) for p in out.rglob('*') if p.is_file()}
        (out/'results.json').write_text(json.dumps(result, indent=2)+'\n')
        (AREA/'audit.json').write_text(json.dumps(dict(result, selected_report=str((out/'results.json').relative_to(ROOT))), indent=2)+'\n')
    print(result['status'], symbol_count, 'symbols;', len(result['controls']), 'checker controls')


if __name__ == '__main__':
    main()
