#!/usr/bin/env python3
"""Freeze matched write scheduling and independently cross-check all layout addresses."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v91l-writepipe'
FPGA = ROOT / 'fpga/experiments/cu66-v91l-writepipe'
SHARED = ['docs/gamebub-application-specific-codec-plan.md',
          'docs/gamebub-v91-v110-development-plan.md',
          'docs/literature-review-2026-11-06/README.md']


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read(p):
    return json.loads(p.read_text())


def source_pins(report):
    for name, h in report['source_sha256'].items():
        assert sha(ROOT / name) == h, name


def mapped(name, logical):
    assert 0 <= logical < 560640
    if name == 'raster':
        return logical
    if logical >= 518400:
        return (522240 if name == 'micro16x8' else 518400) + logical - 518400
    plane = 0 if logical < 345600 else 1 if logical < 432000 else 2
    base, width = ((0, 720), (345600, 360), (432000, 360))[plane]
    row, column = divmod(logical - base, width)
    if name == 'tile8x8':
        return base + ((row // 8) * (width // 8) + column // 8) * 64 + (row % 8) * 8 + column % 8
    assert name == 'micro16x8'
    return (0, 345600, 433920)[plane] + ((row // 8) * ((width + 15) // 16) + column // 16) * 128 + (row % 8) * 16 + column % 16


def model_check():
    model = read(AREA / 'layout-read-results.json')
    cache = read(AREA / 'rowpair-cache-results.json')
    source_pins(model)
    source_pins(cache)
    assert model['status'] == 'PASS_EXACT_GATHER_BOUNDED_WORKLOAD_MODEL'
    assert cache['status'] == 'PASS_PYTHON_EXACT_ROWPAIR_GATHER'
    fixture = ROOT / 'experiments/python-gamebub-v91l-sdram/vectors/native-rows.hex.gz'
    with gzip.open(fixture, 'rt') as f:
        rows = [int(line, 16) for line in f]
    assert len(rows) == 140160
    logical_banks = [bytearray(560640), bytearray(560640)]
    seen = [bytearray(560640), bytearray(560640)]
    for n in rows:
        logical = (n >> 64) & ((1 << 20) - 1)
        bank = (n >> 84) & 3
        assert bank in (0, 1) and logical % 8 == 0 and logical <= 560632
        assert not any(seen[bank][logical:logical+8])
        logical_banks[bank][logical:logical+8] = (n & ((1 << 64) - 1)).to_bytes(8, 'little')
        seen[bank][logical:logical+8] = b'\1' * 8
    assert all(all(bitmap) for bitmap in seen)
    traffic = read(ROOT / 'experiments/python-gamebub-v91l-sdram/traffic-results.json')
    for bank, frame in zip(logical_banks, traffic['frames']):
        assert hashlib.sha256(bank).hexdigest() == frame['accepted_bank_sha256']
    refs = []
    with gzip.open(ROOT / 'fpga/experiments/cu66-v91l-rows/comparison-attempts/20261106T231139409747Z-2dd7b637/events-rows.jsonl.gz', 'rt') as f:
        for line in f:
            d = json.loads(line)
            if d.get('type') == 'reference_request' and d.get('id') == 'actual_006' and d.get('memory_profile') == 0:
                refs.append((d['plane'], d['tile']))
    assert len(refs) == 7806
    output = []
    for item in model['layouts']:
        name = item['layout']
        extent = 564480 if name == 'micro16x8' else 560640
        assert item['allocation_bytes'] == extent
        memories = [bytearray(extent), bytearray(extent)]
        bitmap = bytearray(extent)
        for logical in range(560640):
            address = mapped(name, logical)
            assert not bitmap[address]
            bitmap[address] = 1
            for bank in (0, 1):
                memories[bank][address] = logical_banks[bank][logical]
        assert sum(bitmap) == 560640
        # Full canonical AND semantic HUD bytes, including microtile padding holes.
        for bank in (0, 1):
            inverse = bytes(memories[bank][mapped(name, logical)] for logical in range(560640))
            assert inverse == logical_banks[bank]
        state = {}
        def phase(name, addresses, useful, writes=0, requests=None):
            act = conflict = hit = count = 0
            banks = set()
            for bank, address in addresses:
                banks.add(bank)
                row = address // 1024
                count += 1
                if bank not in state:
                    act += 1
                elif state[bank] != row:
                    act += 1
                    conflict += 1
                else:
                    hit += 1
                state[bank] = row
            expected = dict(logical_requests=requests or count,
                            physical_request_or_burst_count=count,
                            read_bl8_bursts=0 if writes else count,
                            useful_bytes=useful, physical_read_bytes=0 if writes else count * 16,
                            overfetch_bytes=0 if writes else count * 16 - useful,
                            eight_byte_write_rows=writes, x16_write_words=writes * 4,
                            row_activations=act, row_conflicts=conflict, row_hits=hit,
                            banks_touched=sorted(banks))
            assert item['row_transitions'][name] == expected, (item['layout'], name, expected)
            return expected
        def writes():
            for n in rows:
                logical = (n >> 64) & ((1 << 20) - 1)
                bank = (n >> 84) & 3
                physical = mapped(name, logical)
                assert physical % 8 == 0
                assert [mapped(name, logical + j) for j in range(8)] == list(range(physical, physical+8))
                yield bank, physical
        wp = phase('candidate_writes_two_frame_fixture', writes(), 1121280, writes=140160)
        def reference():
            for plane, tile in refs:
                base, width, height = ((0,720,480), (345600,360,240), (432000,360,240))[plane]
                assert 0 <= tile < width * height // 64
                y, x = divmod(tile, width // 8)
                logical = [base + (y*8+j)*width+x*8+k for j in range(8) for k in range(8)]
                addresses = [mapped(name, v) for v in logical]
                bursts = sorted({a & ~15 for a in addresses})
                gathered = {a: memories[0][a:a+16] for a in bursts}
                assert bytes(gathered[a & ~15][a & 15] for a in addresses) == bytes(logical_banks[0][v] for v in logical)
                yield from ((0, a) for a in bursts)
        rp = phase('delta_reference_tiles_one_frame', reference(), 7806*64, requests=7806)
        def converter():
            for start in range(0, 518400, 16):
                addresses = [mapped(name, v) for v in range(start, start+16)]
                bursts = sorted({a & ~15 for a in addresses})
                assert len(bursts) <= 2
                data = {a: memories[1][a:a+16] for a in bursts}
                assert bytes(data[a & ~15][a & 15] for a in addresses) == logical_banks[1][start:start+16]
                yield from ((1, a) for a in bursts)
        cp = phase('canonical_converter_fullframe_one_frame', converter(), 518400, requests=32400)
        output.append(dict(layout=name, native_rows=140160, inverse_exact_banks=2,
                           reference_tiles=7806, converter_requests=32400,
                           write_activations=wp['row_activations'], reference_bl8=rp['read_bl8_bursts'],
                           converter_bl8=cp['read_bl8_bursts'], total_read_bl8=rp['read_bl8_bursts']+cp['read_bl8_bursts']))
    assert len(output) == 3
    for key, frame in zip(('actual_001', 'actual_006'), logical_banks):
        item = cache['frames'][key]
        assert item['sha256'] == hashlib.sha256(frame[:518400]).hexdigest()
        assert item['physical_bl8_bursts'] == 32400 and item['overfetch_bytes'] == 0
        assert item['maximum_pending_data_bytes'] == 728
    result = dict(status='PASS_ROOT_INDEPENDENT_LAYOUT_MAPPING_PAYLOAD_AND_PHASE_CHECK',
                  source_sha256={str(p.relative_to(ROOT)):sha(p) for p in (Path(__file__).resolve(), AREA/'layout-read-results.json', AREA/'rowpair-cache-results.json')},
                  fixture_sha256=sha(fixture), layouts=output,
                  exact_complete_canonical_plus_hud_bank_checks=6,
                  total_native_request_address_checks=420480,
                  total_reference_tile_checks=23418, total_converter_request_checks=97200,
                  scope='Independent address/payload/phase-count model cross-check. Cache own byte-exact script separately rerun; no timed read-controller or hardware claim.')
    (AREA / 'model-crosscheck.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--models-only', action='store_true')
    args = parser.parse_args()
    models = model_check()
    if args.models_only:
        print(models['status'])
        return
    audit = read(AREA / 'audit.json')
    # Final report/audit bindings are checked below after the independent campaign.
    assert audit['status'] == 'PASS_TWO_SEED_MATCHED_WRITEPIPE_PIN_AUDIT'
    assert audit['verifier_sha256'] == sha(AREA / 'verify_results.py')
    alias = read(FPGA / 'results.json')
    selected = ROOT / alias['selected_report']
    run = read(selected)
    assert run['status'] == 'PASS_MATCHED_REAL_CONTROLLER_WRITEPIPE' and run['native_replay']
    assert audit['selected_report'] == str(selected.relative_to(ROOT))
    assert audit['report_sha256'] == sha(selected)
    source_pins(run)
    assert len(audit['modes']) == 8
    assert len(audit['checker_negative_controls']) == 32
    assert all(n['rejected'] for n in audit['checker_negative_controls'])
    for name,h in run['source_sha256'].items():
        assert sha(selected.parent / 'sources' / name) == h
    for name,h in run['inputs_sha256'].items():
        assert sha(ROOT / name) == h
        assert sha(selected.parent / 'inputs' / Path(name).name) == h
    assert all(c['exit_code'] == 0 for c in run['commands'])
    for name,h in run['artifacts_sha256'].items():
        assert sha(selected.parent / name) == h
    assert len(run['modes']) == 8 and set(run['seeds']) == {912301, 912302}
    comparisons = run['comparisons']
    assert len(comparisons) == 4
    for checked, reported in zip(audit['comparisons'], comparisons):
        for key in ('seed', 'bank', 'control_cycles', 'writepipe_cycles', 'speedup'):
            assert checked[key] == reported[key]
    totals = dict(check_entries=0, checked_read_words=0, native_frame_replays=0, native_rows=0, native_pin_word_writes=0)
    for mode in audit['modes']:
        verdict = mode['verdict']
        totals['check_entries'] += verdict['checks']
        totals['checked_read_words'] += verdict['read_words']
        totals['native_frame_replays'] += len(mode['native_frames'])
        totals['native_rows'] += mode['native_rows']
        totals['native_pin_word_writes'] += mode['native_rows'] * 4
    assert totals == dict(check_entries=204, checked_read_words=256, native_frame_replays=8, native_rows=560640, native_pin_word_writes=2242560)
    result = dict(schema='cu66-v91l-writepipe-qualified-v1', status='PASS_MATCHED_WRITEPIPE_AND_PYTHON_LAYOUT_MODELS',
                  run=dict(path=str(selected.relative_to(ROOT)), sha256=sha(selected)),
                  comparisons=comparisons, totals=totals,
                  integrity={name:sha(AREA / name) for name in ('audit.json','verify_results.py','layout_reads.py','layout-read-results.json','rowpair_cache.py','rowpair-cache-results.json','model-crosscheck.json')},
                  read_layouts=models['layouts'],
                  timing_scope='First actual accepted native row to last matching physical-drained response. Replay of already decoded candidate data; excludes live entropy/transform/HUD/hash/publication and shared reference/conversion/scanout service.',
                  nominal_clock_period_ns=10,
                  physical_hardware_tested=False, full_live_codec_join=False, shared_service_complete=False,
                  hardware_distinct_30fps_proven=False, full_frame_decode_under10ms_proven=False,
                  layout_mapping_implemented_in_rtl=False, rowpair_cache_implemented_in_rtl=False,
                  next='Implement timed tile8x8 address mapping and bounded row retention as static comparisons, then join live decode and all clients on one physical service. Keep V100-V110 physical timing/hardware gates.')
    (AREA/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    paths=[]
    for directory in (AREA, FPGA, ROOT/'scripts/cu66-v91l-writepipe', ROOT/'docs/cu66-v91l-writepipe'):
        paths.extend(p for p in directory.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='bundle-manifest.json')
    paths.extend(ROOT/name for name in SHARED)
    manifest = dict(schema='cu66-v91l-writepipe-bundle-v1', files={str(p.relative_to(ROOT)):sha(p) for p in sorted(paths)})
    (AREA/'bundle-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(result['status'], len(paths), 'manifest files')


if __name__ == '__main__':
    main()
