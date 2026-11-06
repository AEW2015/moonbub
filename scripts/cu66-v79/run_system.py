#!/usr/bin/env python3
"""V79 continuous monitor campaign over the unchanged V78 actual system RTL."""
import argparse, hashlib, json, re, subprocess, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'fpga/experiments/cu66-v79/system'
NATIVE = ROOT / 'experiments/cu66-native-v69'
SPEC = ROOT / 'fpga/experiments/cu66-v78/system/sources.json'
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
    parser.add_argument('--skip-build', action='store_true', help='Require the previously built, identically pinned binary for this TAC; safe for parallel read-only runs.')
    args = parser.parse_args()
    index_rows = [line.split('\t') for line in (NATIVE / 'index.tsv').read_text().splitlines()]
    selected = [row for row in index_rows if int(row[0]) == args.cohort]
    count = len(selected) if args.frames == 'full' else int(args.frames)
    assert count <= len(selected)
    out = AREA / f'cohort{args.cohort}-frames{count}-{args.mode}-tac{args.tac}'
    out.mkdir(parents=True, exist_ok=True)
    assert not (out / 'results.json').exists(), f'Archive existing results before rerunning {out}'
    spec = json.loads(SPEC.read_text())
    paths = [ROOT / p for p in spec['rtl_sources']] + [SPEC, AREA / 'tb_system.cpp', AREA / 'monitor.hpp', Path(__file__).resolve(), NATIVE / 'index.tsv', ROOT / 'fpga/experiments/cu66-v69/hud-partition/hud_gate.hpp', ROOT / 'fpga/experiments/cu66-v70/memory/cu70_memory_map.svh', ROOT / 'fpga/experiments/cu66-v70/memory/memory_map.hpp', ROOT / 'fpga/experiments/cu66-v69/packet/cu66_profile.svh', ROOT / 'fpga/experiments/cu66-v69/inverse/cu66_quant_rom.svh', *NATIVE.glob('*.hpp')]
    # Pin the complete finite fixture pool, so all cohorts share one build identity.
    paths += [NATIVE / row[2] for row in index_rows]
    pins = {str(path.relative_to(ROOT)): sha(path) for path in sorted(set(paths))}
    commands = []
    started = time.monotonic()
    def run(argv, name, timeout):
        begin = time.monotonic()
        exit_code = None
        timed_out = False
        try:
            with (out / name).open('w') as stream:
                result = subprocess.run(argv, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, timeout=timeout)
            exit_code = result.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
        commands.append(dict(argv=argv, log=str((out / name).relative_to(ROOT)), exit_code=exit_code, timed_out=timed_out, timeout_seconds=timeout, wall_seconds=time.monotonic()-begin, sha256=sha(out / name)))
        if timed_out or exit_code:
            raise RuntimeError(f'{name}: exit={exit_code}, timed_out={timed_out}; retained log')
        return (out / name).read_text()
    mdir = f'/build/v79-system-tac{args.tac}'
    binary = mdir + '/Vcu78_system_sim'
    build_record = AREA / f'build-tac{args.tac}.json'
    report = dict(schema='cu79-continuous-monitor-system-v1', status='FAIL_FUNCTIONAL', cohort=args.cohort, requested_frames=count, cohort_available_frames=len(selected), arrival_mode=args.mode, tac_ns=args.tac, source_sha256=pins, commands=commands)
    try:
        if not args.skip_build:
            assert not build_record.exists(), f'Existing build identity {build_record}; use --skip-build or archive it before rebuilding'
            run(['docker', 'exec', CONTAINER, 'verilator', '--cc', '--exe', '--build', '-j', '1', *spec['verilator_options'], '-DSIMULATION', f'-GTAC_NS={args.tac}.0', '--top-module', spec['top'], '--Mdir', mdir, '-CFLAGS', '-O2 -std=c++17', *['-I'+str(ROOT/p) for p in spec['include_dirs']], *[str(ROOT/p) for p in spec['rtl_sources']], str(AREA/'tb_system.cpp')], 'build.log', 1200)
            binary_sha = run(['docker', 'exec', CONTAINER, 'sha256sum', binary], 'binary.log', 30).split()[0]
            build_record.write_text(json.dumps(dict(source_sha256=pins, binary=binary, binary_sha256=binary_sha, commands=list(commands)), indent=2)+'\n')
        build = json.loads(build_record.read_text())
        assert build['source_sha256'] == pins, 'built sources differ; archive old build identity and rebuild before qualification'
        current_binary_sha = run(['docker', 'exec', CONTAINER, 'sha256sum', binary], 'binary-check.log', 30).split()[0]
        assert current_binary_sha == build['binary_sha256'], 'qualified executable changed'
        report['build_provenance'] = build
        # Bounded wall-clock timeout scales with finite cohort size; no unbounded subprocess waits.
        runtime_timeout = 600+count*120
        log = run(['docker', 'exec', CONTAINER, 'timeout', '--signal=TERM', '--kill-after=10s', str(runtime_timeout)+'s', binary, str(NATIVE/'index.tsv'), str(count), args.mode, str(args.cohort)], 'run.log', runtime_timeout+30)
        terminal = re.findall(r'^SYSTEM_PASS (.+)$', log, re.M)
        assert len(terminal) == 1 and 'FAIL' not in log, 'missing unique terminal SYSTEM_PASS or failure in log'
        summary = fields(terminal[0])
        rows = [fields(line) for line in log.splitlines() if line.startswith('SYSTEM_FRAME_PASS ')]
        timings = [fields(line) for line in log.splitlines() if line.startswith('SYSTEM_TIMING ')]
        deadlines = [fields(line) for line in log.splitlines() if line.startswith('SYSTEM_RASTER_DEADLINE ')]
        assert len(rows) == len(timings) == len(deadlines) == count
        assert summary['complete_frames'] == summary['distinct_complete_presentations'] == count
        assert summary['cohort'] == args.cohort
        assert all(summary[key] == 0 for key in ('black_lines', 'total_underruns', 'lcd_memory_errors', 'sticky_lcd_error', 'sticky_memory_error', 'sticky_underrun', 'RGB_DDR_words_written_per_frame'))
        assert all(sum(row[f'base{base}_tile{tile}_aux{aux}_cycles'] for base in range(2) for tile in range(2) for aux in range(2)) == row['cycles'] and sum(row[f'stage{stage}_cycles'] for stage in range(16)) == row['cycles'] for row in rows)
        assert all(row['actual_writes'] == 280320 and row['actual_write_commands'] == 35040 and row['actual_write_bus_beats'] == 280320 and row['hud_write_requests'] == row['hud_read_requests'] == 2640 for row in rows)
        assert len({row['fid'] for row in rows}) == count and {row['fid'] for row in rows} == {row['fid'] for row in timings}
        assert all(t['packet_complete_cycle'] <= t['admission_cycle'] < t['validated_ready_cycle'] <= t['commit_ack_cycle'] and t['complete_rasters'] > 0 and t['first_complete_raster_end_ps'] > t['first_complete_raster_start_ps'] > 0 and t['first_complete_raster_end_ps'] <= (t['commit_ack_cycle']+summary['raster_deadline_cycles'])*10000 for t in timings)
        assert rows[1]['processor_commit_calls'] >= 2
        assert pins == {path: sha(ROOT/path) for path in pins}, 'qualified sources changed during run'
        report.update(status='PASS_ACTUAL_DECODE_CANONICAL_AND_NATIVE_DISPLAY', frames=rows, timings=timings, raster_deadlines=deadlines, summary=summary, clocks=dict(memory_period_ps=10000, read_phase_degrees=279, pixel_half_period_ps=17029), performance=dict(status='PASS' if all(t['met_serial_30fps_budget'] and t['met_validated_under10ms'] for t in timings) else 'FAIL', serial_30fps_all_pass=all(t['met_serial_30fps_budget'] for t in timings), validated_under10ms_all_pass=all(t['met_validated_under10ms'] for t in timings), validated_model_ms=[t['validated_decode_model_cycles']*1e-5 for t in timings], origin_to_ack_model_ms=[(t['commit_ack_cycle']-t['packet_complete_cycle'])*1e-5 for t in timings]), scope='Unchanged V78 actual packet/parser/qmap/inverse/hash FPGA decode, stored canonical references, semantic native HUD through actual SDRAM transfer/readback, CPU ACK retry, continuous direct native LCD raster; V79 changes only verification.', limitations=['Native HUD CPU/hash/control execution uses zero simulation time.', 'Finite native fixture replay; no live ESP32 Wi-Fi/QSPI or 60/600-second stream qualification.', '100ms ACK-to-full-raster deadline is a conservative functional liveness bound, not a performance gate.', 'Fixed30 releases come from the finite immutable schedule; queue occupancy is modeled, not target queue-capacity proof.', 'No physical 30fps, target validated-under10ms, Fmax/fit/CDC/electrical proof.'])
    except Exception as error:
        report['failure'] = str(error)
        raise
    finally:
        report['wall_seconds'] = time.monotonic()-started
        (out/'results.json').write_text(json.dumps(report, indent=2)+'\n')
    print(f'V79_SYSTEM_PASS cohort={args.cohort} frames={count} mode={args.mode} performance={report["performance"]["status"]} wall_seconds={report["wall_seconds"]:.3f}')
if __name__ == '__main__':
    main()
