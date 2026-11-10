#!/usr/bin/env python3
"""Read-only V128 packaging/evidence QA; this cannot qualify design timing."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from urllib.parse import unquote, urlsplit

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v128'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def read(p):
    return json.loads(Path(p).read_text())


def stage_closures(index_path, helper):
    expected = dict(focused='PASS', peer='PASS', spatial='PASS_V128_FINAL_SPATIAL_CANONICAL',
                    parent='PASS_V128_SELECTED_COMPONENT_BYTE_ROW_ACK_C2_HUD_ABSTRACT_PUBLICATION')
    stages = read(index_path)['stages']
    assert set(stages) == set(expected)
    rows = []
    for name, meta in stages.items():
        selector = helper.pin_result(meta['path'], meta['sha256'])
        record = meta['receipt']
        receipt = helper.pin_result(record['path'], record['sha256'])
        raw = read(ROOT / record['path'])
        sources = [helper.pin_result(p, h) for p, h in raw['source_sha256'].items()]
        artifacts = [helper.pin_result(str(Path(record['path']).parent / p), h)
                     for p, h in raw.get('artifact_sha256', raw.get('artifacts_sha256', {})).items()]
        rows.append(dict(stage=name, selector=selector, receipt=receipt,
                         source_matches=bool(sources) and all(x['matches'] for x in sources),
                         artifact_matches=bool(artifacts) and all(x['matches'] for x in artifacts),
                         receipt_qualifies=raw['status'] == expected[name] and raw['actual_RTL_run'] is True,
                         source_count=len(sources), artifact_count=len(artifacts),
                         source_mismatches=[x for x in sources if not x['matches']],
                         artifact_mismatches=[x for x in artifacts if not x['matches']]))
    return rows


def main():
    legacy_path = ROOT / 'scripts/cu66-v127/final_qa.py'
    assert sha(legacy_path) == '8b2aacd420778abc5025d52c749071755c5d5390c0f5c0dd69a70012a04cee18'
    spec = importlib.util.spec_from_file_location('v127_readonly_packaging_helpers', legacy_path)
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    checks = []

    def check(name, ok, details):
        checks.append(dict(check=name, passed=bool(ok), details=details))

    handoff = read(ROOT / 'experiments/python-gamebub-v120/handoff.json')
    origins = handoff['source_origins']
    b = []
    for alias, meta in origins.items():
        physical = meta['path']
        blob = subprocess.check_output(['git', 'show', handoff['rtl_source_commit'] + ':' + physical], cwd=ROOT)
        b.append(dict(alias=alias, path=physical,
                      matches=sha(ROOT / physical) == hashlib.sha256(blob).hexdigest() == meta['sha256']))
    check('B100_original18_physical_and_git', len(b) == 18 and all(x['matches'] for x in b), b)
    protected = read(ROOT / 'experiments/python-gamebub-v120/audit/baseline.json')['protected_files']
    markers = []
    for item in protected:
        p = ROOT / item['path']
        markers.append(dict(path=item['path'], matches=sha(p) == item['sha256'] and
                            p.stat().st_size == item['bytes'] and p.stat().st_mtime_ns == item['mtime_ns']))
    check('protected_marker_bytes_and_metadata', bool(markers) and all(x['matches'] for x in markers), markers)
    prior_path = ROOT / 'experiments/python-gamebub-v127/results.json'
    prior = read(prior_path)
    pins = old.recursive_pins(prior)
    prior_native = old.native_closure(prior)
    check('V127_frozen_parent_and_native', sha(prior_path) ==
          '5e872674c6243a3faf4aafab1a3df5cca842e23b8427ce91403130a30c6d40b9' and
          sha(ROOT / 'experiments/python-gamebub-v127/integration/results.json') ==
          'd16589645d3824399a4df4559a84405051547a48e236dc0aa0e1841812f5ce39' and
          bool(pins) and all(p['matches'] for p in pins) and prior_native['matches'],
          dict(pin_count=len(pins), mismatches=[p for p in pins if not p['matches']], native=prior_native))
    freeze = read(AREA / 'audit/functional-tooling-freeze-revision2.json')
    previous = read(AREA / 'audit/functional-tooling-freeze.json')
    current = freeze['source_sha256']
    full_freeze_path = AREA / 'audit/full-functional-tooling-freeze-revision3.json'
    assert sha(full_freeze_path) == '93049f1c3e6c8f1b437d7f8a0827aac051b6929b9da012b01554272415d63a17'
    full_freeze = read(full_freeze_path)
    full_current = full_freeze['source_sha256']
    selected_freeze_path = AREA / 'audit/full-functional-tooling-freeze-revision4.json'
    assert sha(selected_freeze_path) == '4b2180f4d201ba090bcdd4c083c99c24c92ec29f8be125ebe53e4b66850cdf8d'
    selected_freeze = read(selected_freeze_path)
    selected_current = selected_freeze['source_sha256']
    resource_repair = ROOT / selected_freeze['adapter_repair']['path']
    resource_record = read(resource_repair)
    resource_changed = {p for p in full_current if selected_current[p] != full_current[p]}
    resource_added = set(selected_current) - set(full_current)
    selected_bad = [p for p, h in selected_current.items() if sha(ROOT / p) != h]
    check('revision4_current86_and_exact_readiness_delta', len(selected_current) == 86 and not selected_bad and
          resource_changed == set(resource_record['current_inputs']) and len(resource_changed) == 4 and
          resource_added == {'scripts/cu66-v128/integration/resource_gate.py'} and
          selected_freeze['previous_freeze']['sha256'] == sha(full_freeze_path) and
          selected_freeze['resource_thresholds_or_execution_monitors_changed'] is False and
          selected_freeze['bounded_prelaunch_wait_seconds'] == 120 and
          selected_freeze['production_sources_changed_by_repairs'] is False,
          dict(count=len(selected_current), changed=sorted(resource_changed), added=sorted(resource_added), mismatches=selected_bad))
    for name in resource_changed:
        assert full_current[name] == resource_record['baseline_inputs'][name]
        assert selected_current[name] == resource_record['current_inputs'][name]
        assert any(sha(p) == full_current[name] for p in resource_repair.parent.rglob('*') if p.is_file())
    pkg_repair = ROOT / full_freeze['adapter_repair']['path']
    pkg_record = read(pkg_repair)
    expected_changes = pkg_record['current_inputs']
    mismatches = [p for p, h in full_current.items() if p not in resource_changed and sha(ROOT / p) != h]
    historical_mismatches = [p for p, h in current.items() if full_current[p] != h]
    full_changed = {p for p, h in current.items() if full_current[p] != h}
    new_paths = set(full_current) - set(current)
    check('revision3_current85_and_exact_packaging_delta', len(full_current) == 85 and not mismatches and
          full_changed == set(expected_changes) == set(historical_mismatches) and
          full_freeze['previous_freeze']['sha256'] == sha(AREA / 'audit/functional-tooling-freeze-revision2.json') and
          full_freeze['source_count'] == 85 and len(new_paths) == 2 and
          new_paths == {'fpga/experiments/cu66-v128-padding/compile-packaging.json',
                        'scripts/cu66-v128/padding/prepare_compile_packaging.py'} and
          full_freeze['production_sources_changed_by_repairs'] is False,
          dict(count=len(full_current), changed=sorted(full_changed), added=sorted(new_paths), mismatches=mismatches))
    for name in full_changed:
        assert current[name] == pkg_record['baseline_inputs'][name]
        assert full_current[name] == pkg_record['current_inputs'][name]
        assert any(sha(p) == current[name] for p in pkg_repair.parent.rglob('*') if p.is_file())
    changed = sorted(p for p in current if current[p] != previous['source_sha256'][p])
    check('revision2_historical83_with_archived_adapter_bytes', len(current) == 83 and
          changed == freeze['changed_verification_inputs'] and len(changed) == 6 and
          freeze['production_sources_changed_by_repairs'] is False and
          freeze['DUT_clock_edges_added_by_repairs'] == 0 and
          freeze['previous_freeze']['sha256'] == sha(AREA / 'audit/functional-tooling-freeze.json') ==
          '43168153ff7d751ead9bcaf100b4b171b905fdae1b8728e8a3c88b490c79d462',
          dict(source_count=len(current), changed=changed, later_archived_paths=sorted(full_changed)))
    archived = set()
    repair_pins = old.recursive_pins(freeze, 'revision2')
    for meta in freeze['repair_manifests']:
        path = ROOT / meta['path']
        record = read(path)
        if 'changes' in record:
            for item in record['changes']:
                assert sha(ROOT / item['before_archive']) == previous['source_sha256'][item['path']]
                archived.add(item['path'])
        else:
            for name in record['changed_paths']:
                expected = previous['source_sha256'][name]
                assert any(sha(p) == expected for p in path.parent.rglob('*') if p.is_file())
                archived.add(name)
    check('repaired_old_bytes_archived_and_manifests_pinned', sorted(archived) == changed and
          bool(repair_pins) and all(p['matches'] for p in repair_pins),
          dict(archived_paths=sorted(archived), pin_mismatches=[p for p in repair_pins if not p['matches']]))
    full_pins = old.recursive_pins(full_freeze, 'revision3') + old.recursive_pins(selected_freeze, 'revision4')
    check('revision3_and_4_repair_and_review_pins', bool(full_pins) and all(p['matches'] for p in full_pins),
          dict(pin_count=len(full_pins), mismatches=[p for p in full_pins if not p['matches']]))
    failed_attempts = []
    for folder in ('raw', 'padding', 'integrated-study/spatial', 'integrated-study/control-peer'):
        for rp in sorted((AREA / folder / 'attempts').glob('*/receipt.json')):
            raw = read(rp)
            if raw['status'].startswith('PASS'):
                continue
            art = raw.get('artifact_sha256', raw.get('artifacts_sha256', {}))
            bad_artifacts = [p for p, h in art.items() if sha(rp.parent / p) != h]
            bad_sources = []
            for p, h in raw['source_sha256'].items():
                candidates = [rp.parent / 'sources' / p, ROOT / p]
                if not any(x.is_file() and sha(x) == h for x in candidates):
                    # Early resource stops may precede snapshot copying. The
                    # exact reviewed old runner bytes are archived separately.
                    if not any(sha(x) == h for directory in (pkg_repair.parent, resource_repair.parent)
                               for x in directory.rglob('*') if x.is_file()):
                        bad_sources.append(p)
            failed_attempts.append(dict(path=str(rp.relative_to(ROOT)), sha256=sha(rp),
                                        bad_artifacts=bad_artifacts, bad_sources=bad_sources))
    check('retained_failed_attempt_source_and_artifact_closure', bool(failed_attempts) and
          all(not r['bad_artifacts'] and not r['bad_sources'] for r in failed_attempts), failed_attempts)
    tooling = read(AREA / 'orchestration/root-tooling-freeze.json')
    maps = {key: tooling[key] for key in ('files', 'derivations', 'core_recipe')}
    bad = [p for mapping in maps.values() for p, h in mapping.items() if sha(ROOT / p) != h]
    check('root_tooling_and_fixed_recipe', {k: len(v) for k, v in maps.items()} ==
          dict(files=9, derivations=5, core_recipe=3) and not bad,
          dict(counts={k: len(v) for k, v in maps.items()}, mismatches=bad))
    index_path = AREA / 'integration/results.json'
    stage_rows = stage_closures(index_path, old)
    check('four_selected_actual_RTL_stage_closures', len(stage_rows) == 4 and
          all(x['selector']['matches'] and x['receipt']['matches'] and x['source_matches'] and
              x['artifact_matches'] and x['receipt_qualifies'] for x in stage_rows), stage_rows)
    result = read(AREA / 'results.json')
    expected_refs = dict(functional_proof=index_path, functional_audit=AREA / 'audit/full-independent.json',
                         selected_composition=ROOT / 'fpga/experiments/cu66-v128-raw/selected-composition.json',
                         functional_input_freeze=selected_freeze_path)
    check('selected_root_schema_status_and_lineage',
          result['schema'] == 'v128-full-raw-validation-and-owned-padding-study-v1' and
          result['status'] in ('COMPONENT_125MHZ_FRESH_REPEAT_QUALIFIED',
                              'COMPLETED_BOUNDED_STUDY_125MHZ_REPEAT_FAIL',
                              'COMPLETED_BOUNDED_STUDY_125MHZ_TARGET_FAIL') and
          all(result[k] == dict(path=str(p.relative_to(ROOT)), sha256=sha(p)) for k, p in expected_refs.items()),
          dict(status=result['status'], expected_paths={k: str(p.relative_to(ROOT)) for k, p in expected_refs.items()}))
    rpins = old.recursive_pins(result, 'V128_results')
    nclosure = old.native_closure(result)
    repeat_closure = (old.native_closure(dict(candidate_native_receipt=result['repeat_native_receipt']))
                      if 'repeat_native_receipt' in result else None)
    check('current_root_pins_and_terminal_native', bool(rpins) and all(x['matches'] for x in rpins) and
          nclosure['matches'] and (repeat_closure is None or repeat_closure['matches']),
          dict(pin_count=len(rpins), mismatches=[x for x in rpins if not x['matches']],
               native=nclosure, repeat_native=repeat_closure))
    check('hardware_and_whole_system_claims_remain_open', all(result[k] is False for k in (
        'hardware_contact', 'board_bitstream_generated', 'whole_parent_routed_clock_qualified',
        'sustained_hardware_30fps_qualified', 'validated_hardware_decode_under10ms_qualified',
        'ESP32_CPU_WiFi_QSPI_physical_service_calibrated', 'full_single_timebase_custom_endpoint_harness_complete')),
        dict(component_125MHz_qualified=result['candidate_component_125MHz_qualified']))
    roots = [ROOT / 'scripts/cu66-v128', ROOT / 'docs/cu66-v128', AREA,
             ROOT / 'fpga/experiments/cu66-v128-raw', ROOT / 'fpga/experiments/cu66-v128-padding']
    files = sorted({p for root in roots for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts})
    py = [p for p in files if p.suffix == '.py']
    for p in py:
        ast.parse(p.read_text(), filename=str(p))
    oversized = [str(p.relative_to(ROOT)) for p in files if p.stat().st_size > 50 * 1024 * 1024]
    sensitive = [str(p.relative_to(ROOT)) for p in files if p.name.endswith(('.lic', '.pem', '.key', '.pairing.json'))]
    check('packaging_python_sizes_and_secret_filenames', bool(py) and not oversized and not sensitive,
          dict(python_count=len(py), file_count=len(files), oversized=oversized, sensitive_names=sensitive))
    archive_dir = ROOT / 'docs/cu66-v128/plan-history'
    archived_docs = [p for p in archive_dir.glob('*.md') if p.name != 'README.md']
    docs = [p for p in (ROOT / 'docs/cu66-v128').rglob('*.md') if p not in archived_docs] + [ROOT / x for x in (
        'docs/gamebub-application-specific-codec-plan.md', 'docs/gamebub-v121-v125-spatial-literature-review.md')]
    links = old.markdown_check(docs)
    broken = [x for x in links if x.get('exists') is False or 'error' in x]
    check('current_markdown_local_links', bool(links) and not broken,
          dict(document_count=len(docs), local_links=len(links), broken=broken))
    # These are literal historical copies, not rewritten current documents.
    # Resolve their authored links in the retained original document directory.
    archived_links = []
    for doc in archived_docs:
        for raw in old.markdown_targets(doc.read_text()):
            decoded = unquote(raw)
            target = urlsplit(decoded)
            if target.scheme or decoded.startswith(('//', '#')) or not target.path:
                continue
            dest = (ROOT / target.path.lstrip('/') if target.path.startswith('/') else
                    archive_dir.parent / target.path)
            archived_links.append(dict(archive=str(doc.relative_to(ROOT)), target=raw,
                                       authored_directory=str(archive_dir.parent.relative_to(ROOT)), exists=dest.exists()))
    check('archived_markdown_links_at_original_authored_location', bool(archived_links) and
          all(row['exists'] for row in archived_links), archived_links)
    output = dict(schema='v128-readonly-final-packaging-qa-v1',
                  status='PASS_FINAL_EVIDENCE_QA_NOT_DESIGN_TIMING' if all(c['passed'] for c in checks) else 'FAIL',
                  check_count=len(checks), passed_checks=sum(c['passed'] for c in checks), checks=checks,
                  helper_source=old.pin_result(str(legacy_path.relative_to(ROOT)), sha(legacy_path)),
                  script_sha256=sha(Path(__file__)), design_timing_qualified_by_this_QA=False)
    (AREA / 'audit/final-qa.json').write_text(json.dumps(output, indent=2, sort_keys=True) + '\n')
    print(output['status'], output['passed_checks'], '/', output['check_count'])
    raise SystemExit(0 if all(c['passed'] for c in checks) else 1)


if __name__ == '__main__':
    main()
