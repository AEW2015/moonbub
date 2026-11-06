#!/usr/bin/env python3
"""V80 integrated prefetch qualification with the frozen V79 observer."""
import argparse
import datetime
import hashlib
import gzip
import shutil
import json
import re
import subprocess
import tarfile
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'fpga/experiments/cu66-v80/system'
NATIVE = ROOT / 'experiments/cu66-native-v69'
SPEC = AREA / 'sources.json'
CONTAINER = 'gamebub-cu66-v69-build'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fields(line):
    return {key: int(value) for key, value in re.findall(r'(\w+)=(\d+)', line)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--frames', choices=('2', '4', '30', 'full'), default='2')
    parser.add_argument('--cohort', type=int, choices=range(4), default=0)
    parser.add_argument('--mode', choices=('paced', 'fixed30'), default='paced')
    parser.add_argument('--tac', type=int, choices=(2, 7), default=2)
    variant = parser.add_mutually_exclusive_group()
    variant.add_argument('--prefetch', type=int, choices=(0, 1, 2))
    variant.add_argument('--variant', choices=('baseline', 'prefetch', 'overlap'))
    parser.add_argument('--trace', action='store_true', help='Bounded event CSV for all requested sources (requires at most four).')
    parser.add_argument('--trace-frame', action='append', type=int, default=[], help='Zero-based source ordinal to trace, repeat for up to four sources.')
    parser.add_argument('--skip-build', action='store_true', help='Verify and use the immutable binary for this variant/TAC; never rebuild.')
    args = parser.parse_args()
    variant_modes = {'baseline': 0, 'prefetch': 1, 'overlap': 2}
    prefetch = args.prefetch if args.prefetch is not None else variant_modes[args.variant or 'prefetch']
    # Allocate evidence before checking source/build identity. Failed attempts remain immutable.
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA / f'cohort{args.cohort}-frames{args.frames}-{args.mode}-prefetch{prefetch}-tac{args.tac}' / f'attempt-{stamp}-{uuid.uuid4().hex[:8]}'
    out.mkdir(parents=True, exist_ok=False)
    commands = []
    report = dict(schema='cu80-integrated-prefetch-system-v1', status='FAIL_FUNCTIONAL', cohort=args.cohort, arrival_mode=args.mode, tac_ns=args.tac, prefetch=prefetch, variant={mode: name for name, mode in variant_modes.items()}[prefetch], arguments=vars(args), commands=commands)
    started = time.monotonic()
    held_lock = None

    def run(argv, name, timeout):
        begin = time.monotonic()
        entry = dict(argv=argv, log=str((out / name).relative_to(ROOT)), exit_code=None, timed_out=False, timeout_seconds=timeout)
        commands.append(entry)
        try:
            with (out / name).open('w') as stream:
                result = subprocess.run(argv, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, timeout=timeout)
            entry['exit_code'] = result.returncode
        except subprocess.TimeoutExpired:
            entry['timed_out'] = True
        finally:
            entry['wall_seconds'] = time.monotonic()-begin
            if (out / name).exists():
                entry['sha256'] = sha(out / name)
            (out / 'results.json').write_text(json.dumps(report, indent=2)+'\n')
        if entry['timed_out'] or entry['exit_code']:
            raise RuntimeError(f'{name}: exit={entry["exit_code"]}, timed_out={entry["timed_out"]}; retained log')
        return (out / name).read_text()

    try:
        index_rows = [line.split('\t') for line in (NATIVE / 'index.tsv').read_text().splitlines()]
        selected = [row for row in index_rows if int(row[0]) == args.cohort]
        count = len(selected) if args.frames == 'full' else int(args.frames)
        report.update(requested_frames=count, cohort_available_frames=len(selected))
        spec = json.loads(SPEC.read_text())
        paths = [ROOT / p for p in spec['rtl_sources']] + [SPEC, AREA / 'tb_system.cpp', AREA / 'monitor.hpp', Path(__file__).resolve(), NATIVE / 'index.tsv', ROOT / 'fpga/experiments/cu66-v69/hud-partition/hud_gate.hpp', ROOT / 'fpga/experiments/cu66-v70/memory/cu70_memory_map.svh', ROOT / 'fpga/experiments/cu66-v70/memory/memory_map.hpp', ROOT / 'fpga/experiments/cu66-v69/packet/cu66_profile.svh', ROOT / 'fpga/experiments/cu66-v69/inverse/cu66_quant_rom.svh', *NATIVE.glob('*.hpp')]
        paths += [NATIVE / row[2] for row in index_rows]
        paths = sorted(set(paths))
        pins = {str(path.relative_to(ROOT)): sha(path) for path in paths}
        report['source_sha256'] = pins
        (out / 'source-manifest.json').write_text(json.dumps(pins, indent=2)+'\n')
        with tarfile.open(out / 'sources.tar.gz', 'w:gz') as archive:
            for path in paths:
                if 'cu66-v80' in path.parts:
                    archive.add(path, arcname=str(path.relative_to(ROOT)), recursive=False)
        report['source_snapshot'] = dict(scope='Mutable V80 code/script/source-list bytes; immutable baseline and fixtures resolved by source_sha256 from unchanged repository.', path=str((out / 'sources.tar.gz').relative_to(ROOT)), sha256=sha(out / 'sources.tar.gz'))
        assert pins == {path: sha(ROOT/path) for path in pins}, 'sources changed while snapshotting'
        assert count <= len(selected), 'requested count outside finite cohort'
        assert spec['top'] == 'cu80_system_sim', 'unexpected simulation top'
        trace_frames = sorted(set(args.trace_frame) | (set(range(count)) if args.trace else set()))
        assert len(trace_frames) <= 4 and all(0 <= n < count for n in trace_frames), 'trace selects one to four in-range sources'
        trace_args = [str(out/'trace.csv'), ','.join(str(n+1) for n in trace_frames)] if trace_frames else ['-', '-']
        report['trace_source_ordinals'] = trace_frames
        mdir = f'/build/v80-system-prefetch{prefetch}-tac{args.tac}'
        binary = mdir + '/Vcu80_system_sim'
        build_record = AREA / f'build-prefetch{prefetch}-tac{args.tac}.json'
        if not args.skip_build:
            assert not build_record.exists(), f'Existing immutable build identity {build_record}; use --skip-build or explicitly archive it before rebuilding'
            lock = AREA / f'.build-prefetch{prefetch}-tac{args.tac}.lock'
            with lock.open('x') as stream:
                stream.write(str(out.relative_to(ROOT))+'\n')
            held_lock = lock
            run(['docker', 'exec', CONTAINER, 'verilator', '--cc', '--exe', '--build', '-j', '1', *spec['verilator_options'], '-DSIMULATION', f'-GTAC_NS={args.tac}.0', f'-GPREFETCH_ENABLE={prefetch}', '--top-module', spec['top'], '--Mdir', mdir, '-CFLAGS', '-O2 -std=c++17', *['-I'+str(ROOT/p) for p in spec['include_dirs']], *[str(ROOT/p) for p in spec['rtl_sources']], str(AREA/'tb_system.cpp')], 'build.log', 1200)
            binary_sha = run(['docker', 'exec', CONTAINER, 'sha256sum', binary], 'binary.log', 30).split()[0]
            assert pins == {path: sha(ROOT/path) for path in pins}, 'sources changed during build'
            with build_record.open('x') as stream:
                json.dump(dict(source_sha256=pins, binary=binary, binary_sha256=binary_sha, prefetch=prefetch, tac_ns=args.tac, source_snapshot=report['source_snapshot'], commands=list(commands)), stream, indent=2)
                stream.write('\n')
        build = json.loads(build_record.read_text())
        assert build['source_sha256'] == pins, 'built sources differ; archive old build identity and rebuild before qualification'
        assert build['binary'] == binary and build['prefetch'] == prefetch and build['tac_ns'] == args.tac, 'build variant mismatch'
        current_binary_sha = run(['docker', 'exec', CONTAINER, 'sha256sum', binary], 'binary-check.log', 30).split()[0]
        assert current_binary_sha == build['binary_sha256'], 'qualified executable changed'
        report['build_provenance'] = build
        runtime_timeout = 600+count*120
        log = run(['docker', 'exec', CONTAINER, 'timeout', '--signal=TERM', '--kill-after=10s', str(runtime_timeout)+'s', binary, str(NATIVE/'index.tsv'), str(count), args.mode, str(args.cohort), str(prefetch), *trace_args], 'run.log', runtime_timeout+30)
        terminal = re.findall(r'^SYSTEM_PASS (.+)$', log, re.M)
        assert len(terminal) == 1 and 'FAIL' not in log, 'missing unique terminal SYSTEM_PASS or failure in log'
        summary = fields(terminal[0])
        rows = [fields(line) for line in log.splitlines() if line.startswith('SYSTEM_FRAME_PASS ')]
        timings = [fields(line) for line in log.splitlines() if line.startswith('SYSTEM_TIMING ')]
        deadlines = [fields(line) for line in log.splitlines() if line.startswith('SYSTEM_RASTER_DEADLINE ')]
        prefetch_rows = [fields(line) for line in log.splitlines() if line.startswith('SYSTEM_PREFETCH ')]
        command_rows = [fields(line) for line in log.splitlines() if line.startswith('SYSTEM_COMMANDS ')]
        stream_rows = [fields(line) for line in log.splitlines() if line.startswith('SYSTEM_STREAM ')]
        assert len(rows) == len(timings) == len(deadlines) == len(prefetch_rows) == len(command_rows) == len(stream_rows) == count
        assert summary['complete_frames'] == summary['distinct_complete_presentations'] == count
        assert summary['cohort'] == args.cohort
        assert all(summary[key] == 0 for key in ('black_lines', 'total_underruns', 'lcd_memory_errors', 'sticky_lcd_error', 'sticky_memory_error', 'sticky_underrun', 'RGB_DDR_words_written_per_frame'))
        assert all(sum(row[f'base{base}_tile{tile}_aux{aux}_cycles'] for base in range(2) for tile in range(2) for aux in range(2)) == row['cycles'] and sum(row[f'stage{stage}_cycles'] for stage in range(16)) == row['cycles'] for row in rows)
        assert all(row['actual_writes'] == 280320 and row['actual_write_commands'] == 35040 and row['actual_write_bus_beats'] == 280320 and row['hud_write_requests'] == row['hud_read_requests'] == 2640 for row in rows)
        assert len({row['fid'] for row in rows}) == count and {row['fid'] for row in rows} == {row['fid'] for row in timings}
        assert all(t['packet_complete_cycle'] <= t['admission_cycle'] < t['validated_ready_cycle'] <= t['commit_ack_cycle'] and t['complete_rasters'] > 0 and t['first_complete_raster_end_ps'] > t['first_complete_raster_start_ps'] > 0 and t['first_complete_raster_end_ps'] <= (t['commit_ack_cycle']+summary['raster_deadline_cycles'])*10000 for t in timings)
        assert rows[1]['processor_commit_calls'] >= 2
        assert all(p['enabled'] == int(prefetch > 0) and p['fault'] == 0 and p['busy'] == 0 for p in prefetch_rows)
        previous_epoch = 0
        for p, frame in zip(prefetch_rows, rows):
            assert p['fid'] == frame['fid'] and p['generation'] == frame['generation'] and p['key'] == frame['key']
            if not prefetch:
                assert all(p[k] == 0 for k in ('epoch_generation', 'epoch_done_events', 'epoch_aborted_events', 'epoch_done_cycle', 'epoch_aborted_cycle', 'epoch_done_level', 'epoch_aborted_level', 'read_commands', 'read_beats', 'tiles_filled', 'lookups', 'tiles_retired', 'unused_retired', 'new_epoch'))
            elif p['key']:
                assert p['epoch_generation'] == previous_epoch and p['new_epoch'] == 0
            else:
                assert p['epoch_generation'] == p['generation'] and p['epoch_done_events'] == 1 and p['epoch_aborted_events'] == 0 and p['new_epoch'] == 1
                assert 0 < p['epoch_done_cycle'] < next(t['commit_ack_cycle'] for t in timings if t['generation'] == p['generation']) and p['epoch_aborted_cycle'] == 0
                assert (p['read_commands'], p['read_beats'], p['tiles_filled'], p['lookups'], p['tiles_retired'], p['unused_retired']) == (32400, 259200, 8100, 7806, 8100, 294)
            previous_epoch = p['epoch_generation']
        for c, frame in zip(command_rows, rows):
            assert c['generation'] == frame['generation'] and c['fid'] == frame['fid']
            assert c['ref_requests'] == c['ref_responses'] == (0 if frame['key'] else 7806)
            assert c['tile_write_requests'] == c['tile_write_done'] == 8100
            assert sum(c[f'client{i}_writes'] for i in range(4)) == 35040
            assert c['client3_reads'] <= (32400 if prefetch and not frame['key'] else 0)
            assert c['prefetch_fill_events'] == (8100 if prefetch and not frame['key'] else 0)
        for stream, frame in zip(stream_rows, rows):
            assert stream['generation'] == frame['generation'] and stream['fid'] == frame['fid'] and stream['mode'] == prefetch
            if prefetch == 0:
                assert all(stream[key] == 0 for key in ('candidate_wait_cycles', 'idle_candidate_wait_cycles', 'write_accepts'))
        assert pins == {path: sha(ROOT/path) for path in pins}, 'qualified sources changed during run'
        report.update(status='PASS_ACTUAL_DECODE_CANONICAL_AND_NATIVE_DISPLAY', frames=rows, timings=timings, raster_deadlines=deadlines, prefetch_frames=prefetch_rows, command_frames=command_rows, stream_frames=stream_rows, summary=summary, clocks=dict(memory_period_ps=10000, read_phase_degrees=279, pixel_half_period_ps=17029), performance=dict(status='PASS' if all(t['met_serial_30fps_budget'] and t['met_validated_under10ms'] for t in timings) else 'FAIL', serial_30fps_all_pass=all(t['met_serial_30fps_budget'] for t in timings), validated_under10ms_all_pass=all(t['met_validated_under10ms'] for t in timings), validated_model_ms=[t['validated_decode_model_cycles']*1e-5 for t in timings], origin_to_ack_model_ms=[(t['commit_ack_cycle']-t['packet_complete_cycle'])*1e-5 for t in timings]), scope='V80 actual integrated decode and reference-prefetch variant, stored canonical reference verification, semantic native HUD through actual SDRAM transfer/readback, CPU ACK retry, continuous full native LCD raster; frozen V79 observer.', limitations=['Native HUD CPU/hash/control execution uses zero simulation time.', 'Finite native fixture replay; no live ESP32 Wi-Fi/QSPI or 60/600-second stream qualification.', '100ms ACK-to-full-raster deadline is a conservative functional liveness bound, independent of strict latency and serial ACK budgets.', 'Fixed30 releases preserve original 108-cycle origin and finite immutable schedule; queue occupancy is modeled, not target queue-capacity proof.', 'No physical 30fps, target validated-under10ms, Fmax/fit/CDC/electrical proof.'])
    except Exception as error:
        report['failure'] = str(error)
        raise
    finally:
        if held_lock is not None:
            held_lock.unlink()
        raw_trace = out/'trace.csv'
        if raw_trace.exists():
            raw_size, raw_sha = raw_trace.stat().st_size, sha(raw_trace)
            with raw_trace.open('rb') as source, (out/'trace.csv.gz').open('wb') as target:
                with gzip.GzipFile(filename='', fileobj=target, mode='wb', mtime=0) as compressed:
                    shutil.copyfileobj(source, compressed)
            report['trace'] = dict(path=str((out/'trace.csv.gz').relative_to(ROOT)), sha256=sha(out/'trace.csv.gz'), raw_sha256=raw_sha, raw_bytes=raw_size, event_counts={})
            with raw_trace.open() as stream:
                next(stream, None)
                for line in stream:
                    parts = line.split(',')
                    event = parts[3] if len(parts) == 11 else 'incomplete_record'
                    counts = report['trace']['event_counts']
                    counts[event] = counts.get(event, 0)+1
            raw_trace.unlink()
        report['wall_seconds'] = time.monotonic()-started
        (out/'results.json').write_text(json.dumps(report, indent=2)+'\n')
        print(json.dumps(dict(status='V80_SYSTEM_PASS' if report['status'] == 'PASS_ACTUAL_DECODE_CANONICAL_AND_NATIVE_DISPLAY' else report['status'], cohort=args.cohort, frames=report.get('requested_frames'), mode=args.mode, prefetch=prefetch, performance=report.get('performance', {}).get('status'), wall_seconds=report['wall_seconds'], results_path=str(out/'results.json'))), flush=True)


if __name__ == '__main__':
    main()
