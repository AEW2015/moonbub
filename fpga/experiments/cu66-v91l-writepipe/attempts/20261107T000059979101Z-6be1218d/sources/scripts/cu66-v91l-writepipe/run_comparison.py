#!/usr/bin/env python3
"""Matched frozen-control versus four-word write pipeline at real SDRAM pins."""
import argparse
import datetime
import gzip
import hashlib
import json
import shutil
import subprocess
import time
import uuid
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'fpga/experiments/cu66-v91l-writepipe'
PRIOR = ROOT / 'fpga/experiments/cu66-v91l-sdram'
MODEL = ROOT / 'experiments/python-gamebub-v91l-sdram'
CONTAINER = 'gamebub-cu66-v69-build'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect_trace(path):
    """Independent signal boundary checks; full logical oracle is separate audit."""
    pending, commands = deque(), deque()
    checks, frames, verdicts = [], {}, []
    native = False
    accepted = retired = written = max_pending = consecutive = 0
    previous_write_cycle = None
    native_start = native_end = None
    with path.open() as stream:
        for line in stream:
            if not line.startswith('{'):
                continue
            event = json.loads(line)
            kind = event['type']
            if kind == 'controller_req':
                owner = dict(event, issued=False)
                pending.append(owner)
                commands.append(owner)
                max_pending = max(max_pending, len(pending))
                assert len(pending) <= 4, 'more than four controller credits'
                accepted += 1
            elif kind == 'pin' and event['command'] in (4, 5):
                assert commands, 'physical command without accepted request'
                owner = commands.popleft()
                address = (event['bank'] << 22) | (event['row'] << 9) | (event['address'] & 511)
                assert address == owner['address'], 'physical address differs from accepted request'
                assert event['command'] == (4 if owner['write'] else 5), 'physical command differs'
                if owner['write']:
                    assert event['dq'] == owner['data'], 'physical DQ differs from accepted request'
                    if previous_write_cycle is not None:
                        gap = event['cycle'] - previous_write_cycle
                        assert gap >= 1, 'write spacing below tCCD'
                        consecutive += gap == 1
                    previous_write_cycle = event['cycle']
                    written += 1
                owner['issued'] = True
                owner['pin_time_ps'] = event['time_ps']
            elif kind == 'controller_done':
                assert pending, 'retirement without ownership'
                owner = pending.popleft()
                assert all(event[k] == owner[k] for k in ('write', 'address', 'data'))
                assert owner['issued'] and event['time_ps'] > owner['pin_time_ps'], 'retirement before physical command'
                retired += 1
            elif kind == 'native_begin':
                native = True
                native_start = event['cycle']
            elif kind == 'native_end':
                native = False
                native_end = event['cycle']
            elif native and kind in ('bridge_req', 'bridge_rsp'):
                key = str(event['epoch']) + ':' + str(event['bank'])
                frame = frames.setdefault(key, dict(epoch=event['epoch'], bank=event['bank'], rows=0))
                if kind == 'bridge_req':
                    frame.setdefault('first_request_cycle', event['cycle'])
                else:
                    frame['last_response_cycle'] = event['cycle']
                    frame['rows'] += 1
            elif kind == 'check':
                assert event['status'] == 'PASS'
                checks.append(event['name'])
            elif kind == 'verdict':
                verdicts.append(event)
    assert len(verdicts) == 1 and verdicts[0]['status'] == 'TEST_PASS'
    assert not pending and not commands and accepted == retired
    assert verdicts[0]['checks'] == len(checks)
    assert verdicts[0]['word_writes'] == written
    for frame in frames.values():
        frame['cycles'] = frame['last_response_cycle'] - frame['first_request_cycle']
        frame['modeled_ms_at100mhz'] = frame['cycles'] / 100000
    return dict(verdict=verdicts[0], checks=checks, frames=list(frames.values()),
                pin_oracle=dict(accepts=accepted, retires=retired, writes=written,
                                max_pending=max_pending, consecutive_write_pairs=consecutive),
                native_cycles=None if native_start is None else native_end-native_start)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, choices=(912301, 912302), action='append')
    parser.add_argument('--unit-only', action='store_true')
    args = parser.parse_args()
    seeds = args.seed or [912301, 912302]
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-' + uuid.uuid4().hex[:8]
    out = AREA / 'attempts' / stamp
    out.mkdir(parents=True)
    variants = {
        'control': [PRIOR/'controller/moonshine_sdram.sv', PRIOR/'row_to_sdram.sv'],
        'writepipe': [AREA/'controller/moonshine_sdram.sv', AREA/'row_to_sdram.sv'],
    }
    common = [AREA/'sdram_pin_model.sv', AREA/'tb_controller.sv']
    sources = list(dict.fromkeys([p for pair in variants.values() for p in pair] + common + [Path(__file__).resolve()]))
    inputs = [] if args.unit_only else [MODEL/'vectors/native-rows.hex.gz', MODEL/'traffic-results.json']
    report = dict(schema='cu66-v91l-writepipe-comparison-v1', status='FAIL', source_revision=subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(),
                  source_sha256={str(p.relative_to(ROOT)):sha(p) for p in sources},
                  inputs_sha256={str(p.relative_to(ROOT)):sha(p) for p in inputs}, commands=[], modes=[],
                  seeds=seeds, native_replay=not args.unit_only,
                  physical_hardware_tested=False, full_live_codec_join=False,
                  hardware_distinct_30fps_proven=False, full_frame_decode_under10ms_proven=False,
                  scope='Matched actual frozen controller/bridge versus same-row write pipeline, single-write MRS0x233. Candidate-memory native replay only. No shared traffic, live decode, route/PVT or physical hardware validation.')
    plain = None
    started = time.monotonic()
    def command(argv, log, timeout):
        entry = dict(argv=argv, log=log, exit_code=None)
        report['commands'].append(entry)
        with (out/log).open('w') as stream:
            result = subprocess.run(argv, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, timeout=timeout)
        entry['exit_code'] = result.returncode
        if result.returncode:
            raise RuntimeError(f'command exit {result.returncode}: {out/log}')
    try:
        for path in sources:
            dest = out/'sources'/path.relative_to(ROOT)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, dest)
        for path in inputs:
            dest = out/'inputs'/path.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, dest)
        if not args.unit_only:
            plain = out/'native-rows.hex'
            plain.write_bytes(gzip.decompress((out/'inputs/native-rows.hex.gz').read_bytes()))
            assert len(plain.read_bytes().splitlines()) == 140160
            report['native_expansion'] = dict(raw_sha256=sha(plain), rows=140160)
        command(['docker','exec',CONTAINER,'verilator','--version'], 'tool-version.log', 30)
        command(['docker','exec',CONTAINER,'g++','--version'], 'compiler-version.log', 30)
        for variant, pair in variants.items():
            for tac in (2, 7):
                build = '/build/v91l-writepipe-'+stamp+'-'+variant+'-tac'+str(tac)
                snapshot = [str(out/'sources'/p.relative_to(ROOT)) for p in pair+common]
                command(['docker','exec',CONTAINER,'verilator','--binary','--timing','--assert','-Wall','-DSIMULATION','-j','2','--top-module','tb_controller','-GT_AC_NS='+str(tac)+'.0','--Mdir',build,'-CFLAGS','-std=c++20 -O2 -Wall -Wextra -Werror',*snapshot], 'compile-'+variant+'-tac'+str(tac)+'.log', 600)
                for seed in seeds:
                    name = f'simulation-{variant}-{seed}-tac{tac}.jsonl'
                    mode = dict(variant=variant, seed=seed, t_ac_ns=tac, status='FAIL', log=name+'.gz', native_rows=140160 if plain and tac==2 else 0)
                    report['modes'].append(mode)
                    argv = ['docker','exec',CONTAINER,build+'/Vtb_controller','+SEED='+str(seed)]
                    if mode['native_rows']:
                        argv += ['+NATIVE_ROWS='+str(plain),'+NATIVE_COUNT=140160']
                    command(argv, name, 1200)
                    mode.update(inspect_trace(out/name))
                    assert mode['verdict']['seed'] == seed and mode['verdict']['t_ac_ns'] == tac and mode['verdict']['native_rows'] == mode['native_rows']
                    mode['status'] = 'PASS_PIN_COMMAND_DATA_AND_PHYSICAL_DRAIN'
        assert report['source_sha256'] == {str(p.relative_to(ROOT)):sha(p) for p in sources}
        assert report['inputs_sha256'] == {str(p.relative_to(ROOT)):sha(p) for p in inputs}
        if plain:
            comparisons = []
            for seed in seeds:
                control = next(m for m in report['modes'] if m['variant']=='control' and m['seed']==seed and m['t_ac_ns']==2)
                fast = next(m for m in report['modes'] if m['variant']=='writepipe' and m['seed']==seed and m['t_ac_ns']==2)
                assert len(control['frames']) == len(fast['frames']) == 2
                for previous, current in zip(control['frames'],fast['frames']):
                    assert previous['rows']==current['rows']==70080
                    comparisons.append(dict(seed=seed, epoch=current['epoch'], bank=current['bank'], rows=70080, control_cycles=previous['cycles'], writepipe_cycles=current['cycles'], modeled_control_ms=previous['modeled_ms_at100mhz'], modeled_writepipe_ms=current['modeled_ms_at100mhz'], speedup=previous['cycles']/current['cycles']))
            report['comparisons'] = comparisons
        report['status'] = 'PASS_MATCHED_REAL_CONTROLLER_WRITEPIPE'
    except BaseException as error:
        report.update(error_class=type(error).__name__, error=str(error))
        raise
    finally:
        if plain and plain.exists():
            plain.unlink()
        report['compressed_artifacts'] = {}
        for path in out.glob('simulation-*.jsonl'):
            raw = path.read_bytes()
            target = path.with_suffix('.jsonl.gz')
            target.write_bytes(gzip.compress(raw, mtime=0))
            assert gzip.decompress(target.read_bytes()) == raw
            report['compressed_artifacts'][path.name] = dict(path=target.name, gzip_sha256=sha(target), raw_sha256=hashlib.sha256(raw).hexdigest(), rows=sum(x.startswith(b'{') for x in raw.splitlines()))
            path.unlink()
        report['wall_seconds'] = time.monotonic()-started
        report['artifacts_sha256'] = {str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
        (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
        (AREA/'results.json').write_text(json.dumps(dict(report,selected_report=str((out/'results.json').relative_to(ROOT))),indent=2)+'\n')
        print('WRITEPIPE_COMPARISON', report['status'], out, flush=True)


if __name__ == '__main__':
    main()
