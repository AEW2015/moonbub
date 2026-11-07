#!/usr/bin/env python3
"""Finite native exact PIXEL campaign, independently verify every retained variant.

Native generation uses provided predecoded canonical targets. Target capture,
transform and target generation are excluded; no complete host 30fps claim.
"""
import argparse
import datetime
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import signal
import statistics
import struct
import subprocess
import time
import uuid
ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v95/native'
CONTAINER = 'gamebub-cu66-v69-build'

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--timeout', type=int, default=3600)
    args = parser.parse_args()
    assert 60 <= args.timeout <= 7200
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA / 'attempts' / (stamp + '-' + uuid.uuid4().hex[:8])
    out.mkdir(parents=True)
    paths = [Path(__file__).resolve()] + [AREA / name for name in ('codec.hpp', 'collect.cpp', 'data.py', 'test_codec.cpp')]
    paths += [ROOT / name for name in ('experiments/python-gamebub-v95/python/codec.py', 'experiments/python-gamebub-v92/native/codec.hpp', 'experiments/python-gamebub-v92/python/codec.py', 'experiments/python-gamebub-v85/residual/encode.hpp', 'experiments/python-gamebub-v88/entropy/codec.hpp', 'experiments/python-gamebub-v88/entropy/codec.py', 'experiments/python-gamebub-v88/entropy/data.py', 'experiments/python-gamebub-v88/entropy/index.json', 'experiments/python-gamebub-v85/residual/data.py', 'experiments/python-gamebub-v85/residual/index.json', 'experiments/python-gamebub-v82/native/data.py', 'experiments/python-gamebub-v82/native/index.json')]
    paths += sorted((ROOT / 'experiments/cu66-native-v69').glob('*.hpp'))
    pins = {str(p.relative_to(ROOT)): sha(p) for p in paths}
    for path in paths:
        dest = out / 'sources' / path.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(path.read_bytes())
    report = dict(schema='cu66-v95-exact-palettes-v1', status='FAIL', source_sha256=pins, commands=[], profiles=['control','P2','P4','P8','E8','W8'], physical_timing_proven=False,
        qualification='Software exact canonical PIXEL palette and residual components only; no FPGA/ESP32 timing or full host encoder 30fps claim.',
        timing_scope='generation_ns includes frozen AB decode + all six palette histogram/DP/reuse searches + all actual filtered AB/BR prepare/assemblies, including discarded profiles; native and Python validation separate. Predecoded V82 canonical targets supplied: capture/DCT/target generation excluded. No cross-frame palette state.',
        bounds=dict(max_record_bytes=138, max_plane_tiles=5400, profiles=6, shard_raw_bytes=25165824))
    started = time.monotonic()
    process = stderr = None
    archive = None
    prior = signal.getsignal(signal.SIGALRM)
    def expired(_signum, _frame):
        raise TimeoutError('finite PA95 campaign watchdog')
    signal.signal(signal.SIGALRM, expired)
    signal.alarm(args.timeout)
    try:
        def command(argv, name, timeout=120):
            result = subprocess.run(argv, capture_output=True, timeout=timeout)
            (out / name).write_bytes(result.stdout + result.stderr)
            report['commands'].append(dict(argv=argv, exit_code=result.returncode))
            assert result.returncode == 0, name
        command(['docker','exec',CONTAINER,'g++','--version'], 'compiler.log',30)
        binary = '/build/v95-palettes-' + stamp
        common = ['docker','exec',CONTAINER,'g++','-std=c++17','-O2','-Wall','-Wextra','-Werror']
        snapshot = out / 'sources' / AREA.relative_to(ROOT)
        command(common + [str(snapshot / 'collect.cpp'), '-o', binary], 'compile.log')
        command(common + [str(snapshot / 'test_codec.cpp'), '-o', binary + '-test'], 'compile-tests.log')
        command(['docker','exec',CONTAINER,binary+'-test',str(out/'fixtures')], 'native-tests.json')
        command(['docker','cp',CONTAINER+':'+binary,str(out/'collector.bin')], 'copy-binary.log')
        codec = load('pa95_independent', ROOT/'experiments/python-gamebub-v95/python/codec.py')
        ec92 = load('pa95_ec92', ROOT/'experiments/python-gamebub-v92/python/codec.py')
        br88 = load('pa95_br88', ROOT/'experiments/python-gamebub-v88/entropy/codec.py')
        frozen = load('pa95_input', ROOT/'experiments/python-gamebub-v88/entropy/data.py')
        target_data = load('pa95_pixels', ROOT/'experiments/python-gamebub-v82/native/data.py')
        stderr = (out/'collector.stderr').open('wb')
        argv = ['docker','exec','-i',CONTAINER,'timeout',str(args.timeout),binary]
        process = subprocess.Popen(argv,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=stderr)
        report['commands'].append(dict(argv=argv))
        def take(n):
            value = process.stdout.read(n)
            assert len(value) == n, ('helper truncation', process.poll())
            return value
        shards, frames, frame_generations = [], [], []
        totals = [dict(bytes=0,avoided_tiles=0,residual_blocks=0,search_ns=0,encode_ns=0,validate_ns=0,record_kind_counts=[0]*5,ab_decisions=0,ab_renorm=0,br_bits=0) for _ in range(6)]
        source_decode_total = python_verify_ns = planes = palette_records = 0
        shard_cohort = None
        shard_raw_bytes = 0
        def close_shard():
            nonlocal archive
            if archive is not None:
                archive.close()
                path = out / shard_name
                assert path.stat().st_size < 50*1024*1024
                shards.append(dict(path=str(path.relative_to(AREA)),cohort=shard_cohort,frames=shard_frames,raw_bytes=shard_raw_bytes,raw_sha256=shard_sha.hexdigest(),gzip_sha256=sha(path)))
                archive = None
        for frame, target in zip(frozen.iter_frames(),target_data.iter_frames(),strict=True):
            for key in ('cohort','ordinal','fid','key'):
                assert frame[key] == target[key]
            meta = {k:frame[k] for k in ('cohort','ordinal','fid','key','canonical_coefficients_sha256')}
            meta['canonical_sha256'] = target['canonical_sha256']
            meta['planes'] = []
            payloads = []
            frame_generation = 0
            for axis,(a,b) in enumerate(((0,5400),(5400,6750),(6750,8100))):
                chunks = frame['variants']['65536'][axis]
                assert len(chunks) == 1
                chunk = chunks[0]
                active = [i-a for i in range(a,b) if not target['hidden_mask'][i] and (target['key'] or not target['zero_coeff_mask'][i])]
                assert len(active) == chunk['blocks']
                request = struct.pack('<III',chunk['blocks'],len(chunk['data']),b-a) + chunk['data']
                request += b''.join(struct.pack('<H',pos) + target['tiles'][a+pos] for pos in active)
                process.stdin.write(request)
                process.stdin.flush()
                line = process.stdout.readline()
                assert line and len(line) <= 2097152
                stats = json.loads(line)
                assert stats['blocks'] == chunk['blocks'] and stats['old_bytes'] == len(chunk['data'])
                source_decode_total += stats['source_decode_ns']
                frame_generation += stats['source_decode_ns']
                verify_start = time.monotonic_ns()
                original = br88.decode(chunk['br88'],chunk['blocks'])
                for profile in range(6):
                    length, = struct.unpack('<I', take(4))
                    assert 12 <= length <= 48 + 146*(b-a)
                    packet = take(length)
                    observation = stats['profiles'][profile]
                    assert observation['bytes'] == length and observation['sha256'] == hashlib.sha256(packet).hexdigest()
                    parsed = codec.parse_plane(packet,active)
                    positions = [entry['position'] for entry in parsed['palettes']]
                    assert positions == observation['pal_positions']
                    selected = set(positions)
                    for entry in parsed['palettes']:
                        assert entry['pixels'] == target['tiles'][a+entry['position']], 'independent canonical PIXEL mismatch'
                    remaining = tuple(v for i,pos in enumerate(active) if pos not in selected for v in original[i*64:(i+1)*64])
                    decoded = ec92.decode(parsed['entropy'],parsed['residual_blocks']) if parsed['residual_blocks'] else ()
                    assert tuple(decoded) == remaining, 'independent residual complement mismatch'
                    packed = struct.pack('<'+'h'*len(remaining),*remaining)
                    assert hashlib.sha256(packed).hexdigest() == observation['residual_coeff_sha256']
                    pixels = b''.join(entry['pixels'] for entry in parsed['palettes'])
                    assert hashlib.sha256(pixels).hexdigest() == observation['palette_pixel_sha256']
                    assert len(positions) == observation['avoided_tiles']
                    assert parsed['residual_blocks'] == observation['residual_blocks']
                    t = totals[profile]
                    for key in ('bytes','avoided_tiles','residual_blocks','search_ns','encode_ns','validate_ns'):
                        t[key] += observation[key]
                    for key in ('ab_decisions','ab_renorm','br_bits'):
                        t[key] += sum(observation[key])
                    for kind,count in enumerate(observation['record_kind_counts']):
                        t['record_kind_counts'][kind] += count
                    palette_records += len(positions)
                    frame_generation += observation['search_ns'] + observation['encode_ns']
                    payloads.append(packet)
                python_verify_ns += time.monotonic_ns()-verify_start
                meta['planes'].append(stats)
                planes += 1
            encoded = json.dumps(meta,separators=(',',':')).encode()
            record = struct.pack('<I',len(encoded))+encoded+b''.join(struct.pack('<I',len(packet))+packet for packet in payloads)
            if shard_cohort != frame['cohort'] or (archive is not None and shard_raw_bytes+len(record)>24*1024*1024):
                close_shard()
            if archive is None:
                shard_cohort = frame['cohort']
                shard_name = 'data-cohort'+str(shard_cohort)+'-'+str(len(shards)).zfill(3)+'.bin.gz'
                archive = gzip.open(out/shard_name,'wb',compresslevel=6)
                shard_sha, shard_raw_bytes, shard_frames = hashlib.sha256(), 0, 0
            archive.write(record)
            shard_sha.update(record)
            shard_raw_bytes += len(record)
            shard_frames += 1
            frames.append({key:meta[key] for key in ('cohort','ordinal','fid','key','canonical_sha256','canonical_coefficients_sha256')})
            frame_generations.append(frame_generation)
            if len(frames)==1 or len(frames)%25==0:
                print('PA95_PROGRESS',len(frames),planes,'elapsed',round(time.monotonic()-started,1),flush=True)
        close_shard()
        process.stdin.close()
        report['native_exit_code'] = process.wait(timeout=30)
        assert report['native_exit_code'] == 0
        stderr.close()
        assert len(frames)==457 and planes==1371
        assert pins == {name:sha(ROOT/name) for name in pins}, 'source mutation during campaign'
        rss = next(int(line.split()[-1]) for line in (out/'collector.stderr').read_text().splitlines() if line.startswith('PA95_NATIVE_PEAK_RSS_KIB '))
        report.update(status='PASS_NATIVE_AND_INDEPENDENT_PYTHON_ALL_RECORDS',native_sources=len(frames),planes=planes,actual_variants=planes*6,palette_records=palette_records,totals=totals,source_decode_ns=source_decode_total,python_verify_ns=python_verify_ns,native_peak_rss_kib=rss,shards=shards,frames=frames,
            generation_ns=sum(frame_generations),frame_generation_ns=dict(min=min(frame_generations),median=statistics.median(frame_generations),p95=sorted(frame_generations)[int(.95*(len(frame_generations)-1))],max=max(frame_generations)))
    except BaseException as error:
        report['failure'] = repr(error)
        raise
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM,prior)
        if archive is not None:
            archive.close()
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
        if stderr is not None and not stderr.closed:
            stderr.close()
        if process is not None and process.poll() is not None and report['status']=='FAIL':
            (out/'helper-stdout-tail.bin').write_bytes(process.stdout.read(1048576))
        report['wall_seconds'] = time.monotonic()-started
        report['artifacts_sha256'] = {str(path.relative_to(out)):sha(path) for path in out.rglob('*') if path.is_file()}
        (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
        print('PA95_REPORT',out/'results.json',report['status'],flush=True)
    (AREA/'index.json').write_text(json.dumps(dict(report,selected_report=str((out/'results.json').relative_to(ROOT))),indent=2)+'\n')
if __name__=='__main__':
    main()
