#!/usr/bin/env python3
"""Bind successful fresh focused/full/peer/parent receipts; runs no heavy jobs."""
import importlib.util
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
from contract import ROOT, sha, source_map, verify, load

AREA = ROOT/'experiments/python-gamebub-v122'


def stage(selector):
    selected = load(selector)
    receipt = ROOT/selected.get('selected_receipt', selected.get('selected_report', selected.get('path', '')))
    raw = load(receipt)
    if 'selected_receipt' in selected:
        assert raw == {k:v for k,v in selected.items() if k != 'selected_receipt'}
    else:
        assert sha(receipt) == selected.get('selected_report_sha256', selected.get('sha256'))
    assert raw['status'].startswith('PASS') and raw['actual_RTL_run'] is True
    assert raw.get('assertions_disabled_or_downgraded', False) is False
    for path, expected in raw['source_sha256'].items():
        assert sha(ROOT/path) == expected, path
    artifacts = raw.get('artifact_sha256', raw.get('artifacts_sha256', {}))
    assert artifacts
    for path, expected in artifacts.items():
        assert sha(receipt.parent/path) == expected, path
    commands = [item if isinstance(item, list) else item['argv'] for item in raw['commands']]
    compiles = [item for item in commands if 'verilator' in item and '--cc' in item]
    assert compiles and all('--assert' in item and '-Wall' in item and '-Wno-fatal' not in item for item in compiles)
    # Only the frozen v97_forward generated library has no user C++ entrypoint.
    executables = [item for item in compiles if '--exe' in item]
    libraries = [item for item in compiles if '--exe' not in item]
    assert executables and all('-CFLAGS' in item and '-Werror' in item[item.index('-CFLAGS')+1] for item in executables)
    assert all('--build' in item and '--top-module' in item and item[item.index('--top-module')+1] == 'v97_forward' for item in libraries)
    adapters = [item for item in commands if 'g++' in item]
    assert all(all(flag in item for flag in ('-std=c++17', '-O2', '-Wall', '-Wextra', '-Werror')) for item in adapters)
    if raw.get('custom_transport_status'):
        assert len(libraries) == 1 and len(adapters) == 1
    else:
        assert not libraries and not adapters
    return dict(path=str(selector.relative_to(ROOT)), sha256=sha(selector),
                receipt=dict(path=str(receipt.relative_to(ROOT)), sha256=sha(receipt))), raw


def main():
    verify()
    spec = importlib.util.spec_from_file_location('v121_selected_spatial', Path(__file__).with_name('spatial.py'))
    spatial = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(spatial)
    _, _, sources, origins, _, _, _ = spatial.prepare(True)
    source_map(sources, origins)
    pins = {}
    for name, path in [('focused','bounds'), ('spatial','integrated-study/spatial'),
                       ('peer','integrated-study/control-peer'), ('parent','integrated-study/live-guard')]:
        pin, raw = stage(AREA/path/'results.json')
        pins[name] = pin
        if name != 'focused':
            assert raw['source_origins'] == origins
        else:
            queue = 'fpga/experiments/cu66-v122-bounds/cs88_admission_v91i2a.sv'
            assert raw['source_sha256'][queue] == sha(ROOT/queue)
        if name == 'spatial':
            assert raw['status'] == 'PASS_V122_FINAL_SPATIAL_CANONICAL'
            assert raw['B_all_stdout_records_events_and_cycles_exact'] is True
        if name == 'parent':
            assert raw['status'] == 'PASS_V122_SELECTED_COMPONENT_BYTE_ROW_ACK_C2_HUD_ABSTRACT_PUBLICATION'
            assert raw['qualified_variants'] == ['byte', 'row']
            assert raw['V119_all_terminal_records_events_and_hash_cycles_exact'] is True
    result = dict(schema='v122-bounds-functional-composition-v1', status='PASS_V122_BOUNDS_FULL_FUNCTIONAL',
                  source_origins=origins, rtl_source_order=[str(path.relative_to(ROOT)) for path in sources],
                  stages=pins, all_original_oracles_retained=True, exact_B_public_cycles=True,
                  declared_public_cycle_delta=0, assertions_disabled_or_downgraded=False,
                  hardware_contact=False, full_parent_routed_timing=False)
    result['baseline_V121_index'] = dict(path='experiments/python-gamebub-v121/integration/results.json', sha256=sha(ROOT/'experiments/python-gamebub-v121/integration/results.json'))
    result['adapter_derivation'] = dict(path='scripts/cu66-v122/integration/derivation.json', sha256=sha(Path(__file__).with_name('derivation.json')))
    target = AREA/'integration/results.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(result['status'], target, sha(target))


if __name__ == '__main__':
    main()
