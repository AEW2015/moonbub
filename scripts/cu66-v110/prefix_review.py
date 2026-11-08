#!/usr/bin/env python3
"""Independent bounded Rice-prefix arithmetic/source audit; no tool flow runs."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / 'experiments/python-gamebub-v110/prefix-expert-review.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def focused_source_audit():
    directory = ROOT / 'fpga/experiments/cu66-v110-prefix'
    recipe_path = directory / 'edit-recipe.json'
    recipe = json.loads(recipe_path.read_text())
    entry = recipe['production']['br88_rice_elastic.sv']
    old_path, candidate_path = (ROOT / entry[key] for key in ('original', 'candidate'))
    assert sha(old_path) == entry['original_sha256']
    assert sha(candidate_path) == entry['candidate_sha256']
    original, candidate = old_path.read_text(), candidate_path.read_text()
    forward = original
    assert len(entry['edits']) == 3  # two operational edits plus additive assertions
    for edit in entry['edits']:
        assert forward.count(edit['before']) == 1
        forward = forward.replace(edit['before'], edit['after'], 1)
    assert forward == candidate
    for edit in reversed(entry['edits']):
        assert forward.count(edit['after']) == 1
        forward = forward.replace(edit['after'], edit['before'], 1)
    assert forward == original
    assert original.split('`ifndef SYNTHESIS', 1)[1].rsplit('endmodule', 1)[0] in candidate
    assert 'zeros=window<6\'(prefix_rank)?5\'(window):5\'(prefix_rank);' in candidate
    assert '!(req_valid&&req_ready)&&!(in_valid&&in_ready)&&failed==0&&!prefix_empty&&can_step&&' in candidate
    fixtures = {}
    for name in ('rice_probe.sv', 'tb_rice.cpp', 'historical_rice.cpp'):
        old = old_path.parent / 'verification' / name
        new = directory / 'verification' / name
        assert old.read_bytes() == new.read_bytes()
        fixtures[name] = sha(new)
    adapters_path = directory / 'verification/adapters.json'
    adapters = json.loads(adapters_path.read_text())
    for adapter in adapters['adapters']:
        source, target = (ROOT / adapter[key] for key in ('source', 'path'))
        assert sha(source) == adapter['source_sha256'] and sha(target) == adapter['sha256']
        body = source.read_text()
        for before, after in adapter['renames']:
            assert body.count(before) == 1
            body = body.replace(before, after, 1)
        assert body == target.read_text()
    fixture_path = directory / 'verification/fixture-adapter.json'
    fixture = json.loads(fixture_path.read_text())
    wrapper = ROOT / fixture['original']
    assert sha(wrapper) == fixture['sha256']
    wrapper_body = wrapper.read_text()
    for edit in fixture['edits']:
        assert wrapper_body.count(edit['before']) == 1
        wrapper_body = wrapper_body.replace(edit['before'], edit['after'], 1)
    assert wrapper_body == (directory / 'verification/tb_prefix.cpp').read_text()
    assert 'require(OLD(prefix_rank)==NEW(prefix_rank),' in wrapper_body
    assert 'if(independently_masked_rank!=NEW(prefix_rank))' in wrapper_body
    summary_path = ROOT / 'experiments/python-gamebub-v110/prefix/results.json'
    summary = json.loads(summary_path.read_text())
    focused_path = ROOT / summary['selected_report']
    assert sha(focused_path) == summary['selected_report_sha256']
    focused = json.loads(focused_path.read_text())
    assert focused['status'] == 'PASS' and focused['actual_RTL_run'] is True
    assert focused['strict_warnings'] is True and focused['warning_suppression'] is False
    assert focused['assertions_disabled_or_downgraded'] is False and focused['added_public_cycles'] == 0
    for name, expected in focused['source_sha256'].items():
        assert sha(ROOT / name) == sha(focused_path.parent / 'sources' / name) == expected
    for name, expected in focused['artifacts_sha256'].items():
        assert sha(focused_path.parent / name) == expected
    assert '%Warning-' not in (focused_path.parent / 'compile.log').read_text()
    assert len(focused['runs']) == 2
    for command in focused['commands']:
        assert command['exit_code'] == 0 and command['stop_reason'] is None
    for run in focused['runs']:
        assert run['focused']['status'] == run['historical']['status'] == run['unowned']['status'] == 'TEST_PASS'
        assert run['focused']['parameter_cases'] == 6096 and run['focused']['prepared_clocks'] == 189105
        assert run['historical']['cases'] == 1520 and run['historical']['configurations'] == 8
        assert run['historical']['requests_per_configuration'] == 173061
        assert run['historical']['directed_checks'] == 104 and run['unowned']['cases'] == 8320
    return dict(status='PASS_INDEPENDENT_SOURCE_ASSERTION_HARNESS_AND_ACTUAL_FOCUSED_AUDIT',
                original_path=entry['original'], original_sha256=sha(old_path),
                candidate_path=entry['candidate'], candidate_sha256=sha(candidate_path),
                recipe_path=str(recipe_path.relative_to(ROOT)), recipe_sha256=sha(recipe_path),
                adapters_sha256=sha(adapters_path), additive_fixture_adapter_sha256=sha(fixture_path),
                byte_identical_original_fixtures=fixtures, original_assertion_tail_byte_identical=True,
                original_zeros_reference_retained=True, original_guards_and_write_edges_unchanged=True,
                additive_fixture_binding='Both actual parsers now unmasked: stronger old/new raw-rank equality added. Independent masked-linear reference supplies intentional-unused-rank coverage count; every original public/raw/oracle check retained.',
                focused_summary_path=str(summary_path.relative_to(ROOT)), focused_summary_sha256=sha(summary_path),
                focused_receipt_path=str(focused_path.relative_to(ROOT)), focused_receipt_sha256=sha(focused_path),
                source_snapshot_hashes_verified=len(focused['source_sha256']),
                retained_artifact_hashes_verified=len(focused['artifacts_sha256']),
                runs=focused['runs'])


def main():
    rows = loads = 0
    for window in range(16):
        for rank in range(16):
            zeros = min(window, rank)
            found = rank < window
            original_take = 15 if zeros == 15 else zeros + 1 if found else window
            direct_take = rank + 1 if found else window
            assert original_take == direct_take
            for available in range(65):
                rows += 1
                consumer = window != 0 and available >= window
                nontruncated = found or window == 15
                if consumer and nontruncated:
                    assert zeros == rank
                    assert (zeros == 15) == (rank == 15)
                    loads += 1
    native = ROOT / 'experiments/python-gamebub-v110/native/20261108T141714174050Z'
    receipt = json.loads((native / 'receipt.json').read_text())
    path_report = native / 'reports/route-setup-paths.rpt'
    assert sha(path_report) == receipt['retained_artifact_sha256']['reports/route-setup-paths.rpt']
    origins = receipt['source_origins']
    source_evidence = {}
    for alias in ('fpga/experiments/cu66-v91/br88_rice_elastic.sv',
                  'fpga/experiments/cu66-v91h/br88_pipeline_v91h.sv',
                  'fpga/experiments/cu66-v91h/br88_packet_ingress_sync_v91h.sv',
                  'fpga/experiments/cu66-v91b/br88_context.sv'):
        entry = origins[alias]
        path = ROOT / entry['path']
        assert sha(path) == entry['sha256']
        source_evidence[alias] = entry
    result = dict(status='PASS_INDEPENDENT_BOUNDED_PARALLEL_PREFIX_ARITHMETIC',
                  script_sha256=sha(Path(__file__)), arithmetic_rows=rows,
                  consuming_nontruncated_rows=loads, window_domain=[0, 15],
                  prefix_rank_domain=[0, 15], available_domain=[0, 64],
                  remaining_coverage='Every unsigned32 remaining value maps exactly to window=min(remaining,15); all16 equivalence classes are covered.',
                  parallel_take_identity='found_one ? prefix_rank+1 : window equals original zeros==15 ? 15 : found_one ? zeros+1 : window for every parallel window/rank pair.',
                  guarded_load_identity='After actual parallel nontruncation guard (found_one || window==15), zeros==prefix_rank and zeros==15 iff prefix_rank==15.',
                  source_evidence=source_evidence,
                  native_receipt_path=str((native / 'receipt.json').relative_to(ROOT)),
                  native_receipt_sha256=sha(native / 'receipt.json'),
                  native_path_report_sha256=sha(path_report),
                  measured_path=receipt['result']['worst_setup_path'],
                  serial_candidate='Generic serialPREFIX fixed-bit rewrite is exact, but actual pipeline ties serial_mode=0 through ingress/context. Optimized serial_reg_2 LUT alias does not establish an operational serial branch; no native gain claim supported by that rewrite.',
                  structural_effect='Parallel direct-rank load/take removes remaining-derived zeros clamp from selected quotient/suffix data and take arithmetic. Required window/can_step/truncation/priority enables still depend on remaining.',
                  physical_limit='Actual worst endpoint is quotient CE, launch fanout4, 17levels and74.751%route. Source factoring may change shared CE/data logic but does not prove removal of every required remaining-to-CE dependency or timing recovery.',
                  source_and_focused_audit=focused_source_audit(),
                  no_RTL_simulation_synthesis_implementation_or_hardware_executed=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(result['status'], rows, loads, sha(OUTPUT))


if __name__ == '__main__':
    main()
