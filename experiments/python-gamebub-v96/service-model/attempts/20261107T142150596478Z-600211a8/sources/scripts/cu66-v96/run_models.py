#!/usr/bin/env python3
"""Qualify addressed constant accounting and materialized-bank lifetimes."""
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import signal
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v96/service-model'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-' + uuid.uuid4().hex[:8]
    out = AREA / 'attempts' / stamp
    out.mkdir(parents=True)
    sources = [Path(__file__).resolve(), AREA / 'model.py', ROOT / 'experiments/python-gamebub-v82/native/data.py',
               ROOT / 'experiments/python-gamebub-v82/native/index.json']
    sources += sorted((ROOT / 'experiments/python-gamebub-v82/native/data').glob('*.gz'))
    pins = {str(path.relative_to(ROOT)): sha(path) for path in sources}
    report = dict(schema='cu66-v96-service-model-v1', status='FAIL', source_sha256=pins,
                  backend='Python behavioral constant scheduler and bank lifecycle',
                  physical_timing_proven=False, hardware_30fps_proven=False,
                  complete_under10ms_proven=False, rows=[], lifecycle_checks=[])
    started = time.monotonic()
    def expired(signum, frame):
        raise TimeoutError('service model watchdog expired')
    old = signal.signal(signal.SIGALRM, expired)
    signal.alarm(300)
    for path in sources:
        if path.suffix != '.gz':
            target = out / 'sources' / path.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())
    try:
        model = load('v96_service', AREA / 'model.py')
        data = load('v96_native_tiles', ROOT / 'experiments/python-gamebub-v82/native/data.py')
        mask_hash = None
        for frame in data.iter_frames():
            observed = hashlib.sha256(frame['hidden_mask']).hexdigest()
            if mask_hash is None:
                mask_hash = observed
            assert observed == mask_hash, 'fixed hidden profile changed'
            for width in (1, 4, 16):
                result = model.constant_scan(frame, width)
                report['rows'].append(dict(cohort=frame['cohort'], fid=frame['fid'], **result))
        assert len(report['rows']) == 457 * 3
        first = report['rows'][0]
        assert first['scheduled_line_count'] == 32400
        assert first['generated_lines'] == 1176 and first['memory_bl8_commands'] == 31224
        assert all(row['generated_bytes'] == 18816 and row['address_order_sha256'] == first['address_order_sha256'] for row in report['rows'])
        banks = model.Banks()
        def check(name, function, reject=False):
            try:
                function()
            except ValueError as error:
                assert reject, (name, str(error))
                report['lifecycle_checks'].append(dict(name=name, rejected=True, reason=str(error)))
            else:
                assert not reject, name
                report['lifecycle_checks'].append(dict(name=name, rejected=False))
        check('key_start', lambda: banks.start(0, 0, 1))
        check('write_owned', banks.issue)
        check('commit_before_write_ack', lambda: banks.commit(True), True)
        check('write_ack', banks.acknowledge)
        check('late_invalid_root', lambda: banks.commit(False), True)
        check('key_commit', lambda: banks.commit(True))
        check('presentation_without_vblank', lambda: banks.present(False), True)
        check('key_present', lambda: banks.present(True))
        check('open_key_display', banks.open_display)
        check('protected_key_destination', lambda: banks.start(0, 1, 2), True)
        check('delta_start', lambda: banks.start(1, 1, (1 << 32) + 2))
        check('delta_commit_advances_reference', lambda: banks.commit(True))
        assert banks.display == (0, 0, 1) and banks.accepted == (1, 1, (1 << 32) + 2)
        check('display_blocks_presentation', lambda: banks.present(True), True)
        check('next_candidate_other_bank', lambda: banks.start(2, 2, (1 << 32) + 3))
        check('pending_slot_not_free', lambda: banks.commit(True), True)
        check('next_write', banks.issue)
        check('cancel_next', banks.cancel)
        check('discard_before_ack', banks.discard, True)
        check('cancel_write_ack', banks.acknowledge)
        check('canceled_cannot_commit', lambda: banks.commit(True), True)
        check('discard_after_drain', banks.discard)
        check('display_terminal_busy_retains', lambda: banks.close_display(True, True, False))
        assert banks.display is not None
        check('display_response_held_retains', lambda: banks.close_display(True, False, True))
        assert banks.display is not None
        check('display_first_idle_retains', lambda: banks.close_display(True, False, False))
        assert banks.display is not None
        check('display_second_idle_releases', lambda: banks.close_display(True, False, False))
        assert banks.display is None
        check('delta_present', lambda: banks.present(True))
        check('old_bank_reuse_after_drain', lambda: banks.start(0, 2, (1 << 32) + 3))
        check('cancel_reused_bank', banks.cancel)
        check('discard_reused_bank', banks.discard)
        check('stale_fid_rejected', lambda: banks.start(0, 1, (1 << 32) + 3), True)
        check('stale_generation_rejected', lambda: banks.start(0, 3, 2), True)
        check('generation_overflow_rejected', lambda: banks.start(0, 3, 1 << 64), True)
        check('scratch_bank_rejected', lambda: banks.start(3, 3, (1 << 32) + 4), True)
        check('unowned_response_rejected', banks.acknowledge, True)
        report.update(status='PASS_BEHAVIORAL_CONSTANT_AND_LIFETIME_MODEL', frames=457,
                      constant_profile_sha256=mask_hash, lifecycle_check_count=len(report['lifecycle_checks']),
                      baseline_display_bl8_commands=32400, candidate_display_bl8_commands=31224,
                      read_command_reduction_percent=100 * 1176 / 32400,
                      extra_full_frame_payload_bytes=0, candidate_write_saving_claimed=False,
                      scope='Constant producer charges 1/4/16 bytes per clock with one 16-byte slot; existing frame and hidden mask supplied. Complete tiled line scan, not an emulation of raster RGB/controller arbitration. Materialized candidate writes, validation/HUD and visible memory latency not optimized or timed. Behavioral bank tests are directed, not RTL/formal or hardware evidence.')
        assert pins == {name: sha(ROOT / name) for name in pins}, 'inputs changed'
    except BaseException as error:
        report['failure'] = repr(error)
        raise
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)
        report['wall_seconds'] = time.monotonic() - started
        report['artifacts_sha256'] = {str(p.relative_to(out)): sha(p) for p in out.rglob('*') if p.is_file() and p.name != 'results.json'}
        (out / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
        if report['status'].startswith('PASS'):
            selected = dict(report, selected_report=str((out / 'results.json').relative_to(ROOT)))
            (AREA / 'results.json').write_text(json.dumps(selected, indent=2) + '\n')
    print(report['status'], 'frames', report['frames'], 'lifecycle', report['lifecycle_check_count'])


if __name__ == '__main__':
    main()
