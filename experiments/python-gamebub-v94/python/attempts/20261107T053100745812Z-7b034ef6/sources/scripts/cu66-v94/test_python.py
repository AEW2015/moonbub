#!/usr/bin/env python3
"""Independent EC94 strict-reader tests, immutable attempts, pins and watchdog.

The tiny mathematical fixture builder below belongs only to this test. The
production reader imports no encoder, native implementation or fixture builder.
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import signal
import struct
import time
import uuid
import zlib

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v94/python'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def crc(body):
    return body + struct.pack('<I', zlib.crc32(body))


def bitbytes(bits):
    return bytes(sum(int(v) << (7-j) for j, v in enumerate(bits[i:i+8]))
                 for i in range(0, len(bits), 8))


def rans_fixture(values, context=0, lanes=2, scale=8, k0=0, k1=255, frequencies=None):
    """Direct inverse formula for self-contained synthetic grammar fixtures."""
    count = 1 if context == 0 else 2
    qs, literal = [], ''
    for index, value in enumerate(values):
        level = context and index % 2
        k, escape = (k1, 12) if level else (k0, 24 if context else 14)
        q = min(value >> k, 15)
        qs.append(q)
        width = escape if q == 15 else k
        if width:
            literal += format(value if q == 15 else value & ((1 << k)-1), '0%db' % width)
    if frequencies is None:
        frequencies = [[(1 << scale) // 16] * 16 for _ in range(count)]
    cdfs = [[sum(freq[:q]) for q in range(16)] for freq in frequencies]
    states, renorm = [1 << 23] * lanes, []
    for index in reversed(range(len(qs))):
        model = index % 2 if context else 0
        q, lane = qs[index], index % lanes
        freq, cdf = frequencies[model][q], cdfs[model][q]
        assert freq
        state = states[lane]
        while state >= (((1 << 23) >> scale) << 8) * freq:
            renorm.append(state & 255)
            state >>= 8
        states[lane] = ((state // freq) << scale) + state % freq + cdf
    tables = b''.join(struct.pack('<16H', *freq) for freq in frequencies)
    extent = struct.pack('<' + 'I' * lanes, *states) + bytes(reversed(renorm))
    return (struct.pack('<BBBBIIII', k0, k1, scale, 0, zlib.crc32(tables),
                        len(extent), len(literal), len(values)) + tables + extent + bitbytes(literal))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fixtures', type=Path,
                        default=ROOT / 'experiments/python-gamebub-v94/native/fixtures/manifest.json')
    parser.add_argument('--timeout', type=int, default=180)
    args = parser.parse_args()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA / 'attempts' / (stamp + '-' + uuid.uuid4().hex[:8])
    out.mkdir(parents=True)
    pins, checks, synthetic = {}, [], []
    def pin(path):
        name = str(path.resolve().relative_to(ROOT))
        digest = sha(path)
        if name in pins:
            assert pins[name] == digest, 'input changed'
        pins[name] = digest
        dest = out / 'sources' / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(path.read_bytes())
    pin(Path(__file__).resolve()); pin(AREA / 'codec.py')
    report = dict(schema='cu66-v94-independent-python-tests-v1', status='FAIL',
                  watchdog_seconds=args.timeout, physical_timing_proven=False,
                  source_sha256=pins, checks=checks, synthetic=synthetic)
    started = time.monotonic()
    def timeout(signum, frame):
        raise TimeoutError('EC94 independent Python watchdog expired')
    signal.signal(signal.SIGALRM, timeout); signal.alarm(args.timeout)
    try:
        spec = importlib.util.spec_from_file_location('ec94_independent_test', AREA / 'codec.py')
        codec = importlib.util.module_from_spec(spec); spec.loader.exec_module(codec)
        def packet(streams, selector=85, blocks=1, counts=(0,0,0), flags=0):
            return crc(codec.FRAME.pack(b'EC94', 1, flags, selector, 0, blocks, 1, 0,
                                        *map(len, streams), *counts) + b''.join(streams))
        def check(name, call, expected=None, accepted=True):
            try:
                result = call()
            except ValueError:
                assert not accepted, ('unexpected rejection', name)
            else:
                assert accepted, ('unexpected acceptance', name)
                if expected is not None:
                    assert result == expected, ('mismatch', name)
            checks.append(dict(name=name, accepted=accepted))
        def context(name, stream, context=0, blocks=1, count=1, method=2, expected=None):
            path = out / 'fixtures' / (name + '.context')
            path.parent.mkdir(exist_ok=True); path.write_bytes(stream)
            check(name, lambda: codec.decode_context(stream, context, count, blocks, method), expected)
            trace = codec.inspect_rans(stream, context, method)
            synthetic.append(dict(name=name, path=str(path.relative_to(ROOT)),
                                  context=context, blocks=blocks, count=count, method=method,
                                  sha256=sha(path), symbols=trace['symbol_count'],
                                  renorm_counts=sorted(set(f['renorm_count'] for f in trace['fields']))))
            return trace
        dc_br = struct.pack('<BBI', 0, 255, 1) + b'\x80'
        ac_br = struct.pack('<BBI', 0, 0, 0)
        dc_ab = struct.pack('<BBI', 0, 255, 19) + bytes.fromhex('a00000')
        ac_ab = struct.pack('<BBI', 0, 0, 18) + bytes.fromhex('400000')
        check('AB_primitives', lambda: codec.decode(packet([dc_ab]+[ac_ab]*3, 0), 1), [0]*64)
        base = packet([dc_br]+[ac_br]*3)
        check('BR_primitives', lambda: codec.decode(base, 1), [0]*64)
        raw = packet([struct.pack('<64h', *([-2048,2048]*32)),b'',b'',b''], 0, flags=1)
        check('RAW_boundaries', lambda: codec.decode(raw, 1), [-2048,2048]*32)
        for lanes in (2,4):
            method = 2 if lanes == 2 else 3
            for scale in (8,9,10):
                uniform = [[(1 << scale)//16]*16]
                singleton = [[1 << scale]+[0]*15]
                context('singleton_n%d_s%d' % (lanes,scale),
                        rans_fixture([0]*65, lanes=lanes, scale=scale, frequencies=singleton),
                        blocks=65, count=65, method=method, expected=[0]*65)
                context('empty_n%d_s%d' % (lanes,scale),
                        rans_fixture([], 1, lanes, scale, k1=0),
                        context=1, count=0, method=method, expected=[0]*5)
                vals = [0,1,14,15,4095,4096]*20
                context('uniform_n%d_s%d' % (lanes,scale), rans_fixture(vals, lanes=lanes,scale=scale),
                        blocks=len(vals), count=len(vals), method=method,
                        expected=[codec.signed(v) for v in vals])
                rare = [[1, (1 << scale)-1]+[0]*14]
                context('rare_n%d_s%d' % (lanes,scale),
                        rans_fixture([0]*96, lanes=lanes,scale=scale, frequencies=rare),
                        blocks=96, count=96, method=method, expected=[0]*96)
                for band in (1,2,3):
                    width=(5,15,43)[band-1]
                    values = [width-1,4095]
                    expected=[0]*width; expected[-1]=2048
                    context('AC_boundary_c%d_n%d_s%d' % (band,lanes,scale),
                            rans_fixture(values, band,lanes,scale,k1=0), band,
                            method=method, expected=expected)
        good = rans_fixture([0], frequencies=[[256]+[0]*15])
        def bad(name, data, context_id=0, count=1, blocks=1, method=2):
            check('reject_'+name, lambda: codec.decode_context(data, context_id,count,blocks,method), accepted=False)
        def replace(data, offset, value):
            return data[:offset] + value + data[offset+len(value):]
        for name, offset, value in (
            ('scale',2,b'\x07'), ('cached_model',3,b'\x01'), ('unknown_model_mode',3,b'\x02'),
            ('model_crc',4,b'\0'*4), ('rans_extent',8,struct.pack('<I',7)),
            ('literal_extent',12,struct.pack('<I',1)), ('symbol_count',16,struct.pack('<I',2)),
            ('state_low',52,struct.pack('<I',(1<<23)-1)), ('state_high',52,struct.pack('<I',1<<31)),
            ('nonterminal_state',52,struct.pack('<I',(1<<23)+256)), ('k0',0,b'\x0e'),('k1',1,b'\0')):
            bad(name, replace(good,offset,value))
        for length in range(len(good)):
            bad('truncation_%d'%length,good[:length])
        bad('trailing',good+b'\0')
        broken = bytearray(good); broken[20:22]=struct.pack('<H',255)
        broken[4:8]=struct.pack('<I',zlib.crc32(broken[20:52])); bad('model_sum',bytes(broken))
        literal = rans_fixture([1], k0=1, frequencies=[[256]+[0]*15])
        bad('literal_padding',literal[:-1]+bytes([literal[-1]|1]))
        bad('unused_literal',replace(good,12,struct.pack('<I',1))+b'\0')
        bad('missing_literal',replace(literal,12,struct.pack('<I',0))[:-1])
        extra = replace(good,8,struct.pack('<I',9))+b'\0'; bad('unused_renorm',extra)
        bad('DC_range',rans_fixture([4098]))
        bad('AC_run',rans_fixture([5,0],1,k1=0),1)
        for offset,value in ((0,b'BAD!'),(4,b'\2'),(5,b'\2'),(7,b'\1'),
                             (8,struct.pack('<I',2)),(12,b'\2\0'),(14,b'\1\0'),
                             (16,struct.pack('<I',0)),(32,struct.pack('<I',6))):
            mutated=crc(replace(base[:-4],offset,value))
            check('reject_header_%d'%offset,lambda d=mutated:codec.decode(d,1),accepted=False)
        for name,data,blocks,bw in [('CRC',base[:-1]+bytes([base[-1]^1]),1,1),
                ('trailing_packet',base+b'\0',1,1),('zero_blocks',base,0,1),
                ('bool_blocks',base,True,1),('large_blocks',base,65537,1),('bw',base,1,2),
                ('raw_selector',crc(replace(raw[:-4],6,b'\1')),1,1),
                ('raw_range',crc(replace(raw[:-4],44,struct.pack('<h',2049))),1,1),
                ('coded_requires_raw',crc(replace(raw[:-4],5,b'\0')),1,1)]:
            check('reject_'+name,lambda d=data,b=blocks,w=bw:codec.decode(d,b,w),accepted=False)
        native_count, selectors = 0,set()
        if args.fixtures.exists():
            pin(args.fixtures)
            manifest=json.loads(args.fixtures.read_text())
            for fixture in manifest['fixtures']:
                path=args.fixtures.parent/fixture['path']; pin(path)
                data=path.read_bytes(); values=codec.decode(data,fixture['blocks'])
                packed=struct.pack('<'+'h'*len(values),*values)
                assert hashlib.sha256(packed).hexdigest()==fixture['coefficient_sha256'], path
                if not data[5]: selectors.add(data[6])
                native_count+=1
            assert selectors==set(range(256)), 'native 256-selector coverage required'
            for fixture in manifest.get('context_fixtures',[]):
                path=args.fixtures.parent/fixture['path'];pin(path)
                trace=codec.inspect_rans(path.read_bytes(),fixture['context'],fixture['method'],fixture['symbol_count'])
                assert trace['values']==fixture['fields'], 'native unsigned field parity'
                checks.append(dict(name='native_context_'+fixture['name'],accepted=True,
                                   symbols=trace['symbol_count'],source_sha256=sha(path)))
        assert pins=={name:sha(ROOT/name) for name in pins}, 'pinned inputs changed'
        report.update(status='PASS_INDEPENDENT_EC94_STRICT_GRAMMAR',checks_count=len(checks),
                      native_fixtures=native_count,native_selector_count=len(selectors),
                      scope='EC94 coefficient syntax and independent traces; no frame/pixel/hardware claim.')
    except BaseException as error:
        report['error']=repr(error)
        raise
    finally:
        signal.alarm(0); report['wall_seconds']=time.monotonic()-started
        report['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()}
        (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
        print(report['status'],out/'results.json',flush=True)
    (AREA/'index.json').write_text(json.dumps(dict(report,selected_report=str((out/'results.json').relative_to(ROOT))),indent=2)+'\n')


if __name__=='__main__':
    main()
