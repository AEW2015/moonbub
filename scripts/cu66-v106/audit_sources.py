#!/usr/bin/env python3
"""Offline V106 source provenance and component-functional evidence audit.

The audit checks exact source recipes and selected compositions, pins focused
component evidence, and verifies the frozen paired regression matrix. It never
launches compilers or vendor flows. Missing planned matrix evidence is PENDING;
malformed or contradictory evidence is FAIL.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BASELINE = 'eececf35da97c9b14230d464ecde7576cb7840db'
PROFILE = 'experiments/python-gamebub-v99/profile.json'
PROFILE_SHA = '8e17b24afbefe32ca00b2606ee80a3a70dd06e9050e76d50c9698fd524e735be'
MANIFEST = 'fpga/experiments/cu66-v100-baseline/frozen-inputs.json'
REGRESS = 'scripts/cu66-v106/regress.py'
COMPOSITION = 'experiments/python-gamebub-v106/composition.json'
MATH_SUMMARY = 'experiments/python-gamebub-v106/math/results.json'
LOCALITY_SUMMARY = 'experiments/python-gamebub-v106/locality/probe-results.json'
OUT = ROOT / 'experiments/python-gamebub-v106/source-audit.json'
DOC = ROOT / 'docs/cu66-v106/source-audit.md'

ADMISSION = 'fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv'
RECONSTRUCT = 'fpga/experiments/cu66-v91k/cu66_reconstruct_stream_v91k.sv'
INVERSE = 'fpga/experiments/cu66-v91j/cu66_inverse_stream_v91j.sv'
PRODUCER = 'fpga/experiments/cu66-v91k/cs88_coefficients_v91k.sv'
FRESH_PRODUCER = 'fpga/experiments/cu66-v91i2b/cs88_pipeline_v91i2b.sv'
V105_ADMISSION = 'fpga/experiments/cu66-v105-admission/cs88_admission_v91i2a.sv'
V105_COMPOSED_ADMISSION = 'fpga/experiments/cu66-v105-composed/cs88_admission_v91i2a.sv'
V104_CONTROL = 'fpga/experiments/cu66-v104-control/cu66_reconstruct_stream_v91k.sv'
LOCALITY_CANDIDATE = 'fpga/experiments/cu66-v106-locality/cu66_inverse_stream_v91j.sv'
MATH_ROOT = 'fpga/experiments/cu66-v106-math'
COMPOSED_LUT_STORAGE = 'fpga/experiments/cu66-v106-composed/lut-storage/cu66_inverse_stream_v91j.sv'
PLAN_CANDIDATE = 'fpga/experiments/cu66-v106-plan/packed_scratch_v91g2.sv'
PLAN_ORIGINAL = 'fpga/experiments/cu66-v91g2/packed_scratch_v91g2.sv'
SCRATCH_CANDIDATE = 'fpga/experiments/cu66-v106-scratch/packed_scratch_v91g2.sv'
CONTEXT_CANDIDATE = 'fpga/experiments/cu66-v106-context/br88_context.sv'
CONTEXT_ORIGINAL = 'fpga/experiments/cu66-v91b/br88_context.sv'
RICE_CANDIDATE = 'fpga/experiments/cu66-v106-rice/br88_rice_elastic.sv'
RICE_ORIGINAL = 'fpga/experiments/cu66-v91/br88_rice_elastic.sv'
PREFIX_CANDIDATE = 'fpga/experiments/cu66-v106-prefix/br88_rice_elastic.sv'
SUFFIX_CANDIDATE = 'fpga/experiments/cu66-v106-suffix/br88_rice_elastic.sv'
SUFFIX24_CANDIDATE = 'fpga/experiments/cu66-v106-suffix24/br88_rice_elastic.sv'
TELEMETRY_CANDIDATE = 'fpga/experiments/cu66-v106-telemetry/br88_pipeline_v91h.sv'
TELEMETRY_ORIGINAL = 'fpga/experiments/cu66-v91h/br88_pipeline_v91h.sv'
IDCT_ORIGINAL = 'fpga/experiments/cu66-v69/inverse/cu66_idct8x8.sv'
IDCT_CANDIDATE = 'fpga/experiments/cu66-v106-idct/cu66_idct8x8.sv'
IDCT_AREA_CANDIDATE = 'fpga/experiments/cu66-v106-idct-area/cu66_idct8x8.sv'
INGRESS_SYNC_ORIGINAL = 'fpga/experiments/cu66-v91h/br88_packet_ingress_sync_v91h.sv'
INGRESS_SYNC_CANDIDATE = 'fpga/experiments/cu66-v106-ingress/br88_packet_ingress_sync_v91h.sv'
PRODUCER_CACHE_ROOT = 'fpga/experiments/cu66-v106-producer-cache'
PRODUCER_CACHE_SUMMARY = 'experiments/python-gamebub-v106/producer-cache/results.json'
PRODUCER_CACHE_TRACE = 'experiments/python-gamebub-v106/producer-cache/transitions.tsv.gz'

BASELINE_OVERRIDES = {ADMISSION: V105_ADMISSION, RECONSTRUCT: V104_CONTROL}

def math_candidates(kind: str) -> dict[str, str]:
    root = f'{MATH_ROOT}/{kind}/'
    return {INVERSE: root + 'cu66_inverse_stream_v91j.sv',
            PRODUCER: root + 'cs88_coefficients_v91k.sv',
            FRESH_PRODUCER: root + 'cs88_pipeline_v91i2b.sv'}

LANES: dict[str, tuple[str, str, int, int]] = {}
for _variant in ('narrow', 'lut', 'storage', 'lut-storage', 'lut-storage-memory', 'memory'):
    for _mode in ('fresh', 'canonical'):
        LANES[f'{_variant}_{_mode}'] = (_variant, _mode, (6 if _mode == 'fresh' else 22) * 4,
                                        (13 if _mode == 'fresh' else 21) * 4)
for _variant in ('lut-plan', 'lut-storage-plan', 'lut-storage-plan-context', 'closure', 'closure-prefix-telemetry',
                 'local-guards-scratch-area'):
    for _mode in ('fresh', 'canonical'):
        LANES[f'{_variant}_{_mode}'] = (_variant, _mode, (6 if _mode == 'fresh' else 22) * 4,
                                        (13 if _mode == 'fresh' else 21) * 4)

def expected_candidates(variant: str) -> dict[str, str]:
    if variant in ('narrow', 'lut'):
        return math_candidates(variant)
    if variant == 'storage':
        return {INVERSE: LOCALITY_CANDIDATE}
    if variant == 'lut-storage':
        result = math_candidates('lut')
        result[INVERSE] = COMPOSED_LUT_STORAGE
        return result
    if variant == 'lut-storage-memory':
        result = expected_candidates('lut-storage')
        result[ADMISSION] = V105_COMPOSED_ADMISSION
        return result
    if variant == 'memory':
        return {ADMISSION: V105_COMPOSED_ADMISSION}
    if variant == 'lut-plan':
        result = math_candidates('lut')
        result['fpga/experiments/cu66-v91g2/packed_scratch_v91g2.sv'] = PLAN_CANDIDATE
        return result
    if variant == 'lut-storage-plan':
        result = expected_candidates('lut-storage')
        result['fpga/experiments/cu66-v91g2/packed_scratch_v91g2.sv'] = PLAN_CANDIDATE
        return result
    if variant == 'lut-storage-plan-context':
        result = expected_candidates('lut-storage-plan')
        result[CONTEXT_ORIGINAL] = CONTEXT_CANDIDATE
        return result
    if variant == 'closure':
        result = expected_candidates('lut-storage-plan-context')
        result[RICE_ORIGINAL] = RICE_CANDIDATE
        return result
    if variant == 'closure-prefix-telemetry':
        result = expected_candidates('closure')
        result[RICE_ORIGINAL] = PREFIX_CANDIDATE
        result[TELEMETRY_ORIGINAL] = TELEMETRY_CANDIDATE
        return result
    if variant == 'guarded-suffix-idct-cache':
        result = expected_candidates('closure-prefix-telemetry')
        result[RICE_ORIGINAL] = SUFFIX_CANDIDATE
        result[IDCT_ORIGINAL] = IDCT_CANDIDATE
        result[PRODUCER] = f'{PRODUCER_CACHE_ROOT}/cs88_coefficients_v91k.sv'
        result[FRESH_PRODUCER] = f'{PRODUCER_CACHE_ROOT}/cs88_pipeline_v91i2b.sv'
        return result
    if variant == 'local-guards-scratch-area':
        result = expected_candidates('guarded-suffix-idct-cache')
        result[RICE_ORIGINAL] = SUFFIX24_CANDIDATE
        result[IDCT_ORIGINAL] = IDCT_AREA_CANDIDATE
        result[INGRESS_SYNC_ORIGINAL] = INGRESS_SYNC_CANDIDATE
        result[PLAN_ORIGINAL] = SCRATCH_CANDIDATE
        return result
    raise ValueError(f'unknown V106 matrix variant: {variant}')

checks: list[dict[str, Any]] = []
errors: list[str] = []
pending: list[str] = []
inputs: dict[str, str] = {}

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def record(path: str, data: bytes) -> bytes:
    inputs[path] = sha(data)
    return data

def read(path: str) -> bytes:
    return record(path, (ROOT / path).read_bytes())

def read_json(path: str) -> Any:
    return json.loads(read(path))

def check(name: str, ok: bool, detail: Any = None) -> None:
    checks.append({'name': name, 'status': 'PASS' if ok else 'FAIL', 'detail': detail})
    if not ok:
        errors.append(name)

def need(name: str, detail: Any = None) -> None:
    checks.append({'name': name, 'status': 'PENDING', 'detail': detail})
    pending.append(name)

def git_blob(rev: str, path: str) -> bytes | None:
    p = subprocess.run(['git', '-C', str(ROOT), 'show', f'{rev}:{path}'],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if p.returncode:
        return None
    return record(f'git/{rev}/{path}', p.stdout)

def git_ok(*args: str) -> bool:
    return subprocess.run(['git', '-C', str(ROOT), *args], stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL, check=False).returncode == 0

def module_header(src: bytes, module: str) -> bytes:
    pos = src.find(('module ' + module).encode())
    end = src.find(b');', pos)
    if pos < 0 or end < 0:
        raise ValueError(f'module header missing: {module}')
    return src[pos:end + 2]

def apply_recipe(source: bytes, recipe: dict[str, Any]) -> tuple[bytes, list[dict[str, Any]]]:
    out = source
    ledger = []
    for index, row in enumerate(recipe.get('edits', [])):
        before, after = row['before'].encode(), row['after'].encode()
        expected = row.get('expected_occurrences', 1)
        actual = out.count(before)
        if actual != expected:
            raise ValueError(f'edit {index}/{row.get("name")} count {actual}!={expected}')
        out = out.replace(before, after, expected)
        ledger.append({'name': row.get('name'), 'expected_occurrences': expected,
                       'actual_occurrences': actual})
    return out, ledger

def audit_baseline() -> None:
    exists = git_ok('cat-file', '-e', f'{BASELINE}^{{commit}}')
    ancestor = exists and git_ok('merge-base', '--is-ancestor', BASELINE, 'HEAD')
    check('baseline_exists_and_is_ancestor', exists and ancestor,
          {'baseline': BASELINE, 'exists': exists, 'ancestor_of_HEAD': ancestor})
    try:
        audit = read_json('experiments/python-gamebub-v106/baseline-audit.json')
        route = audit.get('selected_geometry_route', {})
        qual = audit.get('qualification', {})
        rows = audit.get('checks', [])
        expected_resources = {'total_LUT': 46115, 'logic_LUT': 43397, 'LUTRAM': 2718, 'FF': 34760,
                              'RAMB36': 32, 'RAMB18': 0, 'DSP': 27}
        timing = route.get('timing', {})
        net_counts = route.get('routing_legality', {}).get('reported_net_counts', {})
        resources = route.get('resources', {})
        route_ok = (route.get('variant') == 'geometry' and timing.get('WNS_ns') == -13.124
                    and timing.get('WHS_ns') == 0.028 and net_counts.get('of fully routed nets') == 69998
                    and net_counts.get('of routable nets') == 69998
                    and net_counts.get('of nets with routing errors') == 0
                    and all(resources.get(k) == v for k, v in expected_resources.items()))
        goals_open = (qual.get('component_100MHz_internal_timing_target_met') is False
                      and qual.get('complete_custom_path_integrated') is False
                      and qual.get('parent_clock_boundary_IO_qualified') is False
                      and qual.get('methodology_DRC_CDC_signed_off') is False
                      and qual.get('whole_device_memory_service_qualified') is False
                      and qual.get('hardware_30fps_validated') is False
                      and qual.get('hardware_test_performed') is False
                      and qual.get('complete_FPGA_decode_under10ms_validated') is False)
        baseline_audit_ok = (audit.get('schema') == 'v106-baseline-audit-v1'
                             and audit.get('task_baseline_revision') == BASELINE
                             and audit.get('status') == 'PASS_EVIDENCE'
                             and len(rows) == 9 and all(row.get('status') == 'PASS' for row in rows)
                             and audit.get('frozen_profile', {}).get('resolution') == [720, 480]
                             and audit.get('frozen_profile', {}).get('packet_cap_bytes') == 49152
                             and route_ok and goals_open)
        check('retained_v106_baseline_audit_and_open_qualification_limits', baseline_audit_ok,
              {'status': audit.get('status'), 'checks_passed': sum(r.get('status') == 'PASS' for r in rows),
               'checks_total': len(rows), 'route_metrics_match': route_ok,
               'all_full_system_goals_open': goals_open})
    except Exception as exc:
        check('retained_v106_baseline_audit_and_open_qualification_limits', False, {'error': str(exc)})
    try:
        raw = read(PROFILE)
        profile = json.loads(raw)
        blob = git_blob(BASELINE, PROFILE)
        geometry = profile.get('geometry', {})
        cap = profile.get('parameters', {}).get('complete_packet_cap_bytes_including_outer_CRC')
        ok = (sha(raw) == PROFILE_SHA and raw == blob and geometry.get('coded_width') == 720
              and geometry.get('coded_height') == 480 and cap == 49152)
        check('frozen_720x480_profile_and_49152_byte_cap', ok,
              {'sha256': sha(raw), 'expected_sha256': PROFILE_SHA, 'baseline_blob_equal': raw == blob,
               'coded_width': geometry.get('coded_width'), 'coded_height': geometry.get('coded_height'),
               'packet_cap_bytes': cap})
    except Exception as exc:
        check('frozen_720x480_profile_and_49152_byte_cap', False, {'error': str(exc)})
    try:
        manifest = read_json(MANIFEST)
        mismatches, missing, baseline_diffs = [], [], []
        for path, expected in manifest.get('baseline_rtl_sha256', {}).items():
            try:
                data = read(path)
            except Exception:
                missing.append(path)
                continue
            if sha(data) != expected:
                mismatches.append(path)
            if data != git_blob(BASELINE, path):
                baseline_diffs.append(path)
        check('frozen_baseline_rtl_inventory', bool(manifest.get('baseline_rtl_sha256')) and
              not (mismatches or missing or baseline_diffs),
              {'count': len(manifest.get('baseline_rtl_sha256', {})), 'hash_mismatches': mismatches,
               'missing': missing, 'baseline_blob_differences': baseline_diffs})
    except Exception as exc:
        check('frozen_baseline_rtl_inventory', False, {'error': str(exc)})
    try:
        v105 = read_json('experiments/python-gamebub-v105/selection.json')
        pins = []
        for path, expected in v105['source_sha256'].items():
            data = read(path)
            pins.append({'path': path, 'sha256': sha(data), 'selected_sha256': expected,
                         'matches_selected': sha(data) == expected,
                         'matches_baseline_blob': data == git_blob(BASELINE, path)})
        selected_ok = v105.get('selected_variant') == 'geometry' and all(
            row['matches_selected'] and row['matches_baseline_blob'] for row in pins)
        check('inherited_v105_geometry_selection_sources', selected_ok,
              {'selection': 'experiments/python-gamebub-v105/selection.json',
               'selected_variant': v105.get('selected_variant'), 'source_pins': pins})
    except Exception as exc:
        check('inherited_v105_geometry_selection_sources', False, {'error': str(exc)})
    try:
        source = read_json('experiments/python-gamebub-v105/source-audit.json')
        native = read_json('experiments/python-gamebub-v105/native-audit.json')
        sp = sum(row.get('status') == 'PASS' for row in source.get('checks', []))
        npass = sum(row.get('status') == 'PASS' for row in native.get('checks', []))
        ok = (source.get('status') == 'PASS_EVIDENCE' and len(source.get('checks', [])) == sp == 24
              and native.get('status') == 'PASS_EVIDENCE' and len(native.get('checks', [])) == npass == 6
              and not native.get('pending_variants'))
        check('retained_v105_source_and_native_audits', ok,
              {'source_status': source.get('status'), 'source_pass': sp, 'source_total': len(source.get('checks', [])),
               'native_status': native.get('status'), 'native_pass': npass, 'native_total': len(native.get('checks', [])),
               'native_pending_variants': native.get('pending_variants')})
    except Exception as exc:
        check('retained_v105_source_and_native_audits', False, {'error': str(exc)})

def audit_math_recipes() -> dict[str, Any]:
    math_paths = read_json(f'{MATH_ROOT}/recipes.json')
    expected_paths = [f'{MATH_ROOT}/{kind}/{name}.recipe.json'
                      for kind in ('narrow', 'lut')
                      for name in ('cu66_inverse_stream_v91j', 'cs88_coefficients_v91k', 'cs88_pipeline_v91i2b')]
    check('math_recipe_index_frozen', math_paths.get('schema') == 'v106-math-recipes-v1'
          and math_paths.get('recipes') == expected_paths,
          {'schema': math_paths.get('schema'), 'recipes': math_paths.get('recipes'), 'expected': expected_paths})
    summary_path = MATH_SUMMARY
    if not (ROOT / summary_path).is_file():
        need('focused_math_receipt_and_independent_trace_audit', {'expected': summary_path})
        return {}
    try:
        summary = read_json(summary_path)
        selected = summary.get('selected_report')
        if not selected or not (ROOT / selected).is_file():
            need('focused_math_selected_receipt', {'summary': summary_path, 'selected_report': selected})
            return {}
        attempt = read_json(selected)
        production = attempt.get('production', [])
        prod_by_path = {row.get('path'): row for row in production}
        bad, recovered_rows = [], []
        for recipe_path in expected_paths:
            try:
                recipe = read_json(recipe_path)
                original_path, candidate_path = recipe['original_path'], recipe['candidate_path']
                original = read(original_path)
                baseline = git_blob(BASELINE, original_path)
                candidate = read(candidate_path)
                rebuilt, ledger = apply_recipe(original, recipe)
                prod = prod_by_path.get(candidate_path, {})
                ok = (recipe.get('schema') == 'v106-edit-recipe-v1' and len(recipe.get('edits', [])) == 1
                      and all(row.get('expected_occurrences') == 1 for row in recipe['edits'])
                      and sha(original) == recipe.get('original_sha256') and original == baseline
                      and sha(candidate) == recipe.get('candidate_sha256') and rebuilt == candidate
                      and module_header(original, Path(original_path).stem) == module_header(candidate, Path(candidate_path).stem)
                      and prod.get('sha256') == sha(candidate) and prod.get('recipe_path') == recipe_path
                      and prod.get('recipe_sha256') == sha(read(recipe_path)))
                if not ok:
                    bad.append({'recipe': recipe_path, 'original': original_path, 'candidate': candidate_path})
                recovered_rows.append({'variant': recipe.get('variant'), 'path': candidate_path,
                                       'sha256': sha(candidate), 'recipe_path': recipe_path,
                                       'original_sha256': sha(original), 'exact_recovery': rebuilt == candidate,
                                       'baseline_original_equal': original == baseline, 'edits': ledger})
            except Exception as exc:
                bad.append({'recipe': recipe_path, 'error': str(exc)})
        production_exact = len(production) == 6 and set(prod_by_path) == {
            f'{MATH_ROOT}/{kind}/{name}.sv' for kind in ('narrow', 'lut')
            for name in ('cu66_inverse_stream_v91j', 'cs88_coefficients_v91k', 'cs88_pipeline_v91i2b')}
        check('six_exact_math_recipes_recover_over_baseline_sources', not bad and production_exact,
              {'recipe_count': len(expected_paths), 'production_count': len(production),
               'production_exact_set': production_exact, 'mismatches': bad, 'recovery': recovered_rows})
        attempt_dir = (ROOT / selected).parent
        artifact_errors = verify_artifacts(attempt, attempt_dir)
        source_errors = verify_source_map(attempt.get('source_sha256', {}))
        verdict = attempt.get('terminal_verdict', {})
        proof = attempt.get('python_proof', {})
        replay = attempt.get('trace_replay', {})
        commands = [c for c in attempt.get('commands', []) if '--build' in c.get('argv', []) and '--cc' in c.get('argv', [])]
        strict = (len(commands) == 1 and commands[0].get('exit_code') == 0
                  and '--assert' in commands[0].get('argv', []) and '-Wall' in commands[0].get('argv', [])
                  and '-Werror' in ' '.join(commands[0].get('argv', []))
                  and attempt.get('strict_warnings') is True
                  and b'%Warning-' not in (attempt_dir / 'compile.log').read_bytes())
        focused_ok = (summary.get('schema') == 'v106-math-combinational-exhaustive-v1'
                      and summary.get('status') == 'PASS' and summary.get('baseline_revision') == BASELINE
                      and attempt.get('schema') == 'v106-math-combinational-exhaustive-v1'
                      and attempt.get('status') == 'PASS' and attempt.get('baseline_revision') == BASELINE
                      and attempt.get('actual_RTL_run') is True
                      and attempt.get('frozen_after_focused_PASS') is True
                      and attempt.get('assertions_disabled_or_downgraded') is False and strict
                      and verdict == {'cases': 32768, 'planes': 4, 'status': 'TEST_PASS', 'tile_inputs_per_plane': 8192}
                      and proof.get('status') == 'PASS' and proof.get('input_cases') == 32768
                      and proof.get('LUT_constants_reconstructed') == 704 and proof.get('Y_return_wrap_inputs') == 44
                      and replay.get('status') == 'PASS' and replay.get('rows') == 32768
                      and not artifact_errors and not source_errors)
        side_path = 'experiments/python-gamebub-v106/math/trace-audit.json'
        if not (ROOT / side_path).is_file():
            need('focused_math_independent_trace_audit', {'expected': side_path, 'selected_receipt': selected})
        else:
            side = read_json(side_path)
            aud = side.get('auditor', {})
            side_prod = side.get('production', [])
            expected_side_prod = [{'variant': r.get('variant'), 'path': r.get('path'), 'sha256': r.get('sha256'),
                                   'recipe_path': r.get('recipe_path'), 'recipe_sha256': r.get('recipe_sha256')}
                                  for r in production]
            trace_gz = attempt_dir / 'trace.tsv.gz'
            side_ok = (side.get('schema') == 'v106-math-independent-trace-audit-v1'
                       and side.get('status') == 'PASS' and aud.get('path')
                       and sha(read(aud['path'])) == aud.get('sha256')
                       and side.get('selected_receipt') == {'path': selected, 'sha256': sha(read(selected))}
                       and side.get('selected_summary') == {'path': summary_path, 'sha256': sha(read(summary_path))}
                       and side_prod == expected_side_prod
                       and side.get('trace_sha256') == sha(trace_gz.read_bytes())
                       and side.get('raw_trace_sha256') == attempt.get('raw_trace_sha256')
                       and side.get('rows') == 32768 and side.get('plane_values') == 4
                       and side.get('tile_values_per_plane') == 8192
                       and side.get('LUT_constants_reconstructed') == 704
                       and side.get('Y_return_wrap_inputs') == 44)
            focused_ok &= side_ok
        check('focused_math_receipt_and_independent_trace_audit', focused_ok,
              {'summary': summary_path, 'selected_receipt': selected, 'status': attempt.get('status'),
               'strict_compile': strict, 'source_errors': source_errors, 'artifact_errors': artifact_errors,
               'independent_sidecar': side_ok if (ROOT / side_path).is_file() else 'PENDING'})
        return {'production': production, 'selected_receipt': selected, 'summary': summary_path}
    except Exception as exc:
        check('focused_math_receipt_and_independent_trace_audit', False, {'error': str(exc)})
        return {}

def verify_artifacts(receipt: dict[str, Any], attempt_dir: Path) -> list[dict[str, str]]:
    bad = []
    for rel, expected in receipt.get('artifacts_sha256', {}).items():
        path = attempt_dir / rel
        try:
            data = record(str(path.relative_to(ROOT)), path.read_bytes())
        except Exception:
            bad.append({'path': rel, 'reason': 'missing'})
            continue
        if sha(data) != expected:
            bad.append({'path': rel, 'reason': 'sha256'})
    return bad

def verify_source_map(source_map: dict[str, str]) -> list[dict[str, str]]:
    bad = []
    for path, expected in source_map.items():
        try:
            data = read(path)
            if sha(data) != expected:
                bad.append({'path': path, 'reason': 'sha256'})
        except Exception:
            bad.append({'path': path, 'reason': 'missing'})
    return bad

def compile_log_path(attempt_dir: Path, command: dict[str, Any]) -> Path:
    name = command.get('log')
    if name:
        return attempt_dir / name
    # Some focused receipts pin artifact files but leave the command's log name
    # implicit. In those schemas the compile artifact has the canonical name.
    return attempt_dir / 'compile.log'

def audit_locality_recipe() -> dict[str, Any]:
    recipe_path = 'fpga/experiments/cu66-v106-locality/edit-proof.json'
    try:
        recipe = read_json(recipe_path)
        original = read(recipe['original_path'])
        candidate = read(recipe['candidate_path'])
        baseline = git_blob(BASELINE, recipe['original_path'])
        rebuilt, ledger = apply_recipe(original, recipe)
        ok = (recipe.get('schema') == 'v106-edit-recipe-v1' and recipe.get('original_path') == INVERSE
              and recipe.get('candidate_path') == LOCALITY_CANDIDATE and len(recipe.get('edits', [])) == 2
              and sha(original) == recipe.get('original_sha256') and original == baseline
              and sha(candidate) == recipe.get('candidate_sha256') and rebuilt == candidate
              and module_header(original, 'cu66_inverse_stream_v91j') == module_header(candidate, 'cu66_inverse_stream_v91j'))
        check('locality_two_edit_recipe_exact_recovery', ok,
              {'recipe': recipe_path, 'candidate': LOCALITY_CANDIDATE, 'candidate_sha256': sha(candidate),
               'original_baseline_equal': original == baseline, 'exact_recovery': rebuilt == candidate,
               'edits': ledger})
        return {'recipe': recipe, 'path': recipe_path, 'original': original, 'candidate': candidate}
    except Exception as exc:
        check('locality_two_edit_recipe_exact_recovery', False, {'error': str(exc)})
        return {}

def audit_campaign_policy() -> None:
    """Pin the measured timing redirection and explicitly distinguish deferred routes."""
    try:
        import ast
        path = 'scripts/cu66-v106/campaign.py'
        source = read(path).decode()
        tree = ast.parse(source, filename=path)
        assigned: dict[str, Any] = {}
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id in ('NATIVE_PHASES', 'DEFERRED_NATIVE',
                                                                     'REDIRECTION', 'REJECTED_FUNCTIONAL'):
                        if (target.id == 'NATIVE_PHASES' and isinstance(node.value, ast.DictComp)
                                and isinstance(node.value.key, ast.Name) and node.value.key.id == 'name'
                                and isinstance(node.value.value, ast.Constant) and node.value.value.value is False
                                and len(node.value.generators) == 1
                                and isinstance(node.value.generators[0].iter, ast.Tuple)):
                            assigned[target.id] = {item.value: False for item in node.value.generators[0].iter.elts
                                                   if isinstance(item, ast.Constant) and isinstance(item.value, str)}
                        else:
                            assigned[target.id] = ast.literal_eval(node.value)
        expected_deferred = ['narrow', 'storage', 'lut-storage', 'lut-storage-memory', 'memory',
                             'lut-plan', 'lut-storage-plan-context']
        expected_required = {'lut': False, 'lut-storage-plan': False, 'closure': False,
                             'closure-prefix-telemetry': False, 'guarded-suffix-idct-cache': False,
                             'local-guards-scratch-area': False}
        expected_rejected = {'guarded-suffix-idct-cache': {
            'fresh': 'FAIL_STRICT_PRODUCTION_LINT',
            'fresh_receipt': 'experiments/python-gamebub-v106/regression/guarded-suffix-idct-cache/fresh/attempts/20261108T023622841266Z-22231e3b/results.json',
            'canonical': 'NOT_RUN_REJECTED_CANDIDATE',
            'reason': 'Placement failed area/packing; strict full-production lint also rejects unused suffix_extracted[63:24]. Keep both failures; do not suppress warning or treat focused wrapper exports as production lint qualification. Replace with separately proved private24-bit projection and area-qualified IDCT in the sixth candidate.'}}
        expected_redirect = {
            'evidence': 'experiments/python-gamebub-v106/native/20261108T005012241750Z/reports/synth-setup-paths.rpt',
            'evidence_sha256': '6c732f65f791f71c6ef395609d3c4c5452cc2c8c21b224292da4a2c68f4985f8',
            'synthesis_WNS_ns': -5.303,
            'route_evidence': 'experiments/python-gamebub-v106/native/20261108T005012241750Z/reports/route-setup-paths.rpt',
            'route_evidence_sha256': '915b2331b769ee3a06d269482ce707bfecaa410d0056d9978392f35beb90873b',
            'route_WNS_ns': -7.130,
            'Rice_route_WNS_ns': -6.531,
            'closure_route_evidence': 'experiments/python-gamebub-v106/native/20261108T013032873883Z/reports/route-setup-paths.rpt',
            'closure_route_evidence_sha256': '4da106d91e7cb99b7ba84d83252621f3489fb7e1fd9663d2fd20bb234b4953bd',
            'closure_route_WNS_ns': -4.034,
            'final_trial_reason': 'Actual closure routing exposes Rice prefix and indexed telemetry counters. Compare exact parallel rank/static counters; retain separately measured IDCT operand selection, scratch and scale cones as open obligations. The IDCT path is not the V104 dequantizer product-prefetch block.',
            'prefix_telemetry_route_evidence': 'experiments/python-gamebub-v106/native/20261108T015540764948Z/reports/route-setup-paths.rpt',
            'prefix_telemetry_route_evidence_sha256': '83be4d6b68d4eb3f700499ad6dab938c4fb698af31d71b7fe3b674a8c4676d15',
            'prefix_telemetry_route_WNS_ns': -4.700,
            'prefix_telemetry_synth_evidence': 'experiments/python-gamebub-v106/native/20261108T015540764948Z/reports/synth-setup-paths.rpt',
            'prefix_telemetry_synth_evidence_sha256': 'c5ddc85de4180035ae2f25a8329be05f0640c070ee91692795bfa88fb803e001',
            'prefix_telemetry_synthesis_WNS_ns': -3.897,
            'pipeline_trial_reason': 'Parallel prefix factoring alone did not close the shared parser output path. Specialize SUFFIX extraction independently; prefetch actual IDCT operands within existing slots; cache the producer lookup coordinate at every original plane/tile transition. Preserve all public cycles and independently test before routing. No claim that prior path names remain final limiters.',
            'rejected_pipeline_receipt': 'experiments/python-gamebub-v106/native/20261108T021556317071Z/receipt.json',
            'rejected_pipeline_receipt_sha256': 'aa7d1db0875b5a5fe4312bb894eff2018453e79f70a7b6fb44929db0d26041f3',
            'rejected_pipeline_log': 'experiments/python-gamebub-v106/native/20261108T021556317071Z/vivado.log',
            'rejected_pipeline_log_sha256': 'c756c12a137e1f31d50725293cd5068ea41a948d3426e631a212694e98c19fe7',
            'rejected_functional_receipt_sha256': '748c8274bd9daca2d5229157391c2254c6b0718b87fc4fb9cb0ceade0b405a7d',
            'area_preflight_comparison': 'experiments/python-gamebub-v106/idct-area/unit-synthesis-comparison.json',
            'area_preflight_comparison_sha256': '037e606e21f05edfd8d79840b8db3f89c0f66dd6be1706dc689711bd09ccdd9e',
            'last_trial_reason': 'Reject the over-packed fifth full-flow attempt and its strict-production-lint failure. Retain every failure; canonical tests of that rejected candidate are not run. The sixth candidate uses the separately clocked-tested shared-selector IDCT, matched unit-area preflight, exact24-bit suffix temporary projection, live ingress replay-count cache and all-offset scratch/head position predecode. Require strict fresh pipeline PASS before launching the last full flow; keep actual parent input-capture timing open.',
        }
        redirection = assigned.get('REDIRECTION', {})
        policy_ok = (assigned.get('DEFERRED_NATIVE') == expected_deferred
                     and assigned.get('NATIVE_PHASES') == expected_required
                     and assigned.get('REJECTED_FUNCTIONAL') == expected_rejected
                     and all(redirection.get(k) == v for k, v in expected_redirect.items())
                     and redirection.get('reason') and redirection.get('scope'))
        check('adaptive_native_campaign_policy_and_deferred_variants', policy_ok,
              {'required_native': assigned.get('NATIVE_PHASES'), 'deferred_native': assigned.get('DEFERRED_NATIVE'),
               'rejected_functional': assigned.get('REJECTED_FUNCTIONAL'),
               'redirection': redirection})
        rejected_path = assigned.get('REJECTED_FUNCTIONAL', {}).get('guarded-suffix-idct-cache', {}).get('fresh_receipt')
        if rejected_path and (ROOT / rejected_path).is_file():
            rejected_sha_ok = sha(read(rejected_path)) == redirection.get('rejected_functional_receipt_sha256')
            check('adaptive_campaign_rejected_functional_receipt_pin', rejected_sha_ok,
                  {'path': rejected_path, 'sha256': sha(read(rejected_path)),
                   'expected_sha256': redirection.get('rejected_functional_receipt_sha256')})
        else:
            need('adaptive_campaign_rejected_functional_receipt_pin', {'expected': rejected_path})
        for name, digest_key, literal in (
                ('evidence', 'evidence_sha256', b'Slack (VIOLATED) :        -5.303ns'),
                ('route_evidence', 'route_evidence_sha256', b'Slack (VIOLATED) :        -7.130ns'),
                ('closure_route_evidence', 'closure_route_evidence_sha256', b'Slack (VIOLATED) :        -4.034ns'),
                ('prefix_telemetry_route_evidence', 'prefix_telemetry_route_evidence_sha256', b'Slack (VIOLATED) :        -4.700ns'),
                ('prefix_telemetry_synth_evidence', 'prefix_telemetry_synth_evidence_sha256', b'Slack (VIOLATED) :        -3.897ns')):
            evidence_path = expected_redirect[name]
            check_name = 'adaptive_redirection_' + name
            if not (ROOT / evidence_path).is_file():
                need(check_name, {'expected': evidence_path, 'sha256': expected_redirect[digest_key]})
            else:
                evidence = read(evidence_path)
                evidence_ok = sha(evidence) == expected_redirect[digest_key] and literal in evidence
                if name == 'route_evidence':
                    source_paths = b'Source:                 coefficients/child/packet_decoder/synchronous.ingress/context_decoder/parser/size_bits_reg'
                    destination_paths = b'Destination:            coefficients/child/packet_decoder/synchronous.ingress/context_decoder/parser/out_value_reg'
                    evidence_ok &= (b'Slack (VIOLATED) :        -6.531ns' in evidence
                                    and evidence.count(source_paths) == 12
                                    and evidence.count(destination_paths) == 12)
                if name == 'closure_route_evidence':
                    evidence_ok &= (b'coefficients/child/packet_decoder/synchronous.ingress/context_decoder/parser/available_reg' in evidence
                                    and b'coefficients/child/packet_decoder/synchronous.ingress/context_decoder/parser/out_value_reg' in evidence)
                check(check_name, evidence_ok, {'path': evidence_path, 'sha256': sha(evidence),
                                                'expected_sha256': expected_redirect[digest_key],
                                                'reports_expected_WNS': literal in evidence,
                                                'rice_size_bits_to_out_value_paths':
                                                    (evidence.count(source_paths) if name == 'route_evidence' else None)})
        for field, digest_field in (('rejected_pipeline_receipt', 'rejected_pipeline_receipt_sha256'),
                                    ('rejected_pipeline_log', 'rejected_pipeline_log_sha256'),
                                    ('area_preflight_comparison', 'area_preflight_comparison_sha256')):
            evidence_path = redirection.get(field)
            check_name = 'adaptive_campaign_' + field
            if not evidence_path or not (ROOT / evidence_path).is_file():
                need(check_name, {'expected': evidence_path, 'sha256': redirection.get(digest_field)})
            else:
                evidence = read(evidence_path)
                ok = sha(evidence) == redirection.get(digest_field)
                if field == 'rejected_pipeline_receipt' and ok:
                    receipt = json.loads(evidence)
                    ok &= (receipt.get('schema') == 'v106-vivado2026-ooc-build-v1'
                           and receipt.get('status') == 'TOOL_OR_BUILD_FAILED'
                           and receipt.get('observed_exit_code') == 1
                           and receipt.get('top') == 'cs88_pipeline_v91k'
                           and receipt.get('placement_reports_present') is False
                           and receipt.get('component_route_finished') is False
                           and receipt.get('source_snapshot_unchanged') is True
                           and receipt.get('clock_period_ns') == 10.0)
                if field == 'rejected_pipeline_log' and ok:
                    ok &= b'[Place 30-487]' in evidence
                if field == 'area_preflight_comparison' and ok:
                    comparison = json.loads(evidence)
                    ok &= (comparison.get('schema') == 'v106-idct-area-matched-unit-synthesis-comparison-v1'
                           and comparison.get('status') == 'UNIT_SYNTHESIS_EVIDENCE_COMPLETE')
                check(check_name, ok, {'path': evidence_path, 'sha256': sha(evidence),
                                       'expected_sha256': redirection.get(digest_field)})
    except Exception as exc:
        check('adaptive_native_campaign_policy_and_deferred_variants', False, {'error': str(exc)})

def audit_plan_recipe() -> dict[str, Any]:
    recipe_path = 'fpga/experiments/cu66-v106-plan/edit-recipe.json'
    try:
        recipe = read_json(recipe_path)
        original = read(recipe['original_path'])
        candidate = read(recipe['candidate_path'])
        baseline = git_blob(BASELINE, recipe['original_path'])
        rebuilt, ledger = apply_recipe(original, recipe)
        recipe_ok = (recipe.get('schema') == 'v106-edit-recipe-v1' and recipe.get('variant') == 'plan'
                     and recipe.get('original_path') == PLAN_ORIGINAL and recipe.get('candidate_path') == PLAN_CANDIDATE
                     and len(recipe.get('edits', [])) == 2
                     and all(row.get('expected_occurrences') == 1 for row in recipe.get('edits', []))
                     and sha(original) == recipe.get('original_sha256') and original == baseline
                     and sha(candidate) == recipe.get('candidate_sha256') and rebuilt == candidate
                     and module_header(original, 'packed_scratch_v91g2')
                         == module_header(candidate, 'packed_scratch_v91g2'))
        check('plan_two_edit_recipe_exact_recovery_over_baseline', recipe_ok,
              {'recipe': recipe_path, 'original_baseline_equal': original == baseline,
               'candidate_sha256': sha(candidate), 'exact_recovery': rebuilt == candidate, 'edits': ledger})
        return {'recipe': recipe, 'path': recipe_path, 'candidate': candidate, 'original': original}
    except Exception as exc:
        check('plan_two_edit_recipe_exact_recovery_over_baseline', False, {'error': str(exc)})
        return {}

def audit_plan_focused() -> None:
    summary_path = 'experiments/python-gamebub-v106/plan/results.json'
    if not (ROOT / summary_path).is_file():
        need('focused_plan_receipt_and_independent_trace_audit', {'expected': summary_path})
        return
    try:
        summary = read_json(summary_path)
        selected = summary.get('selected_report')
        if not selected or not (ROOT / selected).is_file():
            need('focused_plan_selected_receipt', {'summary': summary_path, 'selected_report': selected})
            return
        receipt = read_json(selected)
        ad = (ROOT / selected).parent
        artifact_errors = verify_artifacts(receipt, ad)
        source_errors = verify_source_map(receipt.get('source_sha256', {}))
        compile_rows = [c for c in receipt.get('commands', []) if '--build' in c.get('argv', []) and '--cc' in c.get('argv', [])]
        strict = (len(compile_rows) == 1 and compile_rows[0].get('exit_code') == 0
                  and '--assert' in compile_rows[0].get('argv', []) and '-Wall' in compile_rows[0].get('argv', [])
                  and '-Werror' in ' '.join(compile_rows[0].get('argv', []))
                  and receipt.get('strict_warnings') is True
                  and b'%Warning-' not in compile_log_path(ad, compile_rows[0]).read_bytes())
        model = receipt.get('model', {})
        verdicts = receipt.get('terminal_verdicts', [])
        adapter = read_json('fpga/experiments/cu66-v106-plan/adapter.json')
        adapter_rows = []
        for side in ('original', 'candidate'):
            wrapper = read(f'fpga/experiments/cu66-v106-plan/plan_{side}.sv')
            normalized = wrapper.replace(f'module plan_{side} ('.encode(),
                                         b'module packed_scratch_v91g2 (', 1)
            extra = adapter['extra_ports'].encode()
            assignments = adapter['assignments'].encode()
            exact_counts = normalized.count(extra) == 1 and normalized.count(assignments) == 1
            if exact_counts:
                normalized = normalized.replace(extra, b'\n);', 1).replace(assignments, b'', 1)
            target = read(PLAN_ORIGINAL if side == 'original' else PLAN_CANDIDATE)
            adapter_rows.append({'variant': side, 'exact_after_probe_removal': exact_counts and normalized == target})
        adapters_ok = len(adapter_rows) == 2 and all(row['exact_after_probe_removal'] for row in adapter_rows)
        verdict_ok = (len(verdicts) == 2 and verdicts[0].get('status') == 'TEST_PASS'
                      and verdicts[0].get('rows') == model.get('rows') == 290816
                      and verdicts[0].get('clocked_begin_cases') == 9088
                      and verdicts[0].get('priority_checks') == 1
                      and verdicts[1].get('status') == 'TEST_PASS'
                      and verdicts[1].get('directed_checks') == 9)
        receipt_ok = (summary.get('schema') == 'v106-plan-clocked-production-comparison-v1'
                      and summary.get('status') == 'PASS' and summary.get('baseline_revision') == BASELINE
                      and summary.get('frozen_after_focused_PASS') is True
                      and receipt.get('schema') == 'v106-plan-clocked-production-comparison-v1'
                      and receipt.get('status') == 'PASS' and receipt.get('baseline_revision') == BASELINE
                      and receipt.get('actual_RTL_run') is True
                      and receipt.get('assertions_disabled_or_downgraded') is False
                      and receipt.get('complete_production_body_preserved_by_adapters') is True
                      and receipt.get('candidate', {}).get('path') == PLAN_CANDIDATE
                      and receipt.get('candidate', {}).get('sha256') == sha(read(PLAN_CANDIDATE))
                      and receipt.get('candidate', {}).get('recipe_sha256') == sha(read('fpga/experiments/cu66-v106-plan/edit-recipe.json'))
                      and model.get('schema') == 'v106-plan-independent-modular-model-v1'
                      and model.get('status') == 'PASS' and model.get('rows') == 290816
                      and model.get('all17bit_block_values_exercised') == 131072
                      and adapters_ok
                      and receipt.get('trace_replay', {}).get('status') == 'PASS'
                      and receipt.get('trace_replay', {}).get('rows') == 290816 and verdict_ok and strict
                      and not artifact_errors and not source_errors)
        side_path = 'experiments/python-gamebub-v106/plan/trace-audit.json'
        if not (ROOT / side_path).is_file():
            need('focused_plan_independent_trace_audit', {'expected': side_path, 'selected_receipt': selected})
            side_ok: bool | str = 'PENDING'
        else:
            side = read_json(side_path)
            auditor = side.get('auditor', {})
            side_ok = (side.get('status') == 'PASS' and auditor.get('path')
                       and sha(read(auditor['path'])) == auditor.get('sha256')
                       and side.get('schema') == 'v106-plan-independent-trace-audit-v1'
                       and side.get('selected_receipt', {}).get('path') == selected
                       and side.get('selected_receipt', {}).get('sha256') == sha(read(selected))
                       and side.get('selected_summary', {}).get('path') == summary_path
                       and side.get('selected_summary', {}).get('sha256') == sha(read(summary_path))
                       and side.get('candidate') == receipt.get('candidate')
                       and side.get('prefix_rows') == 290816
                       and side.get('all17bit_block_values') == 131072
                       and side.get('valid_plan_inputs') == 6132
                       and side.get('high_count_inputs') == 165393
                       and side.get('clocked_begin_cases') == 9088
                       and side.get('priority_checks') == 1
                       and side.get('accepted_write_hazard_checks') == 9
                       and side.get('public_port_count') == 79
                       and side.get('raw_trace_sha256') == receipt.get('raw_trace_sha256')
                       and side.get('trace_sha256') == receipt.get('artifacts_sha256', {}).get('trace.tsv.gz'))
        check('focused_plan_receipt_and_independent_trace_audit', receipt_ok and side_ok is True,
              {'summary': summary_path, 'selected_receipt': selected,
               'status': receipt.get('status'), 'strict_compile': strict, 'verdicts_pass': verdict_ok,
               'adapters_exact': adapters_ok, 'adapter_rows': adapter_rows,
               'source_errors': source_errors, 'artifact_errors': artifact_errors,
               'independent_sidecar': side_ok})
    except Exception as exc:
        check('focused_plan_receipt_and_independent_trace_audit', False, {'error': str(exc)})

def audit_context_recipe() -> dict[str, Any]:
    recipe_path = 'fpga/experiments/cu66-v106-context/edit-recipe.json'
    try:
        recipe = read_json(recipe_path)
        original = read(recipe['original_path'])
        candidate = read(recipe['candidate_path'])
        baseline = git_blob(BASELINE, recipe['original_path'])
        rebuilt, ledger = apply_recipe(original, recipe)
        ok = (recipe.get('schema') == 'v106-edit-recipe-v1' and recipe.get('variant') == 'context'
              and recipe.get('original_path') == CONTEXT_ORIGINAL
              and recipe.get('candidate_path') == CONTEXT_CANDIDATE
              and len(recipe.get('edits', [])) == 2
              and all(row.get('expected_occurrences') == 1 for row in recipe.get('edits', []))
              and sha(original) == recipe.get('original_sha256') and original == baseline
              and sha(candidate) == recipe.get('candidate_sha256') and rebuilt == candidate
              and module_header(original, 'br88_context') == module_header(candidate, 'br88_context'))
        check('context_two_edit_recipe_exact_recovery_over_baseline', ok,
              {'recipe': recipe_path, 'original_baseline_equal': original == baseline,
               'candidate_sha256': sha(candidate), 'exact_recovery': rebuilt == candidate, 'edits': ledger})
        return {'recipe': recipe, 'path': recipe_path, 'candidate': candidate, 'original': original}
    except Exception as exc:
        check('context_two_edit_recipe_exact_recovery_over_baseline', False, {'error': str(exc)})
        return {}

def audit_context_focused() -> None:
    summary_path = 'experiments/python-gamebub-v106/context/results.json'
    if not (ROOT / summary_path).is_file():
        need('focused_context_receipt_and_independent_trace_audit', {'expected': summary_path})
        return
    try:
        summary = read_json(summary_path)
        selected = summary.get('selected_report')
        if not selected or not (ROOT / selected).is_file():
            need('focused_context_selected_receipt', {'summary': summary_path, 'selected_report': selected})
            return
        receipt = read_json(selected)
        ad = (ROOT / selected).parent
        artifact_errors = verify_artifacts(receipt, ad)
        source_errors = verify_source_map(receipt.get('source_sha256', {}))
        compile_rows = [c for c in receipt.get('commands', []) if '--build' in c.get('argv', []) and '--cc' in c.get('argv', [])]
        strict = (len(compile_rows) == 1 and compile_rows[0].get('exit_code') == 0
                  and '--assert' in compile_rows[0].get('argv', []) and '-Wall' in compile_rows[0].get('argv', [])
                  and '-Werror' in ' '.join(compile_rows[0].get('argv', []))
                  and receipt.get('strict_warnings') is True
                  and b'%Warning-' not in compile_log_path(ad, compile_rows[0]).read_bytes())
        model = receipt.get('model', {})
        geom = receipt.get('geometry_verdict', {})
        verdict = receipt.get('terminal_verdict', {})
        adapter = read_json('fpga/experiments/cu66-v106-context/adapter.json')
        adapter_rows = []
        for side in ('original', 'candidate'):
            wrapper = read(f'fpga/experiments/cu66-v106-context/context_{side}.sv')
            normalized = wrapper.replace(f'module context_{side} ('.encode(), b'module br88_context (', 1)
            extra, assignments = adapter['extra_ports'].encode(), adapter['assignments'].encode()
            exact_counts = normalized.count(extra) == 1 and normalized.count(assignments) == 1
            if exact_counts:
                normalized = normalized.replace(extra, b'\n);', 1).replace(assignments, b'', 1)
            target = read(CONTEXT_ORIGINAL if side == 'original' else CONTEXT_CANDIDATE)
            adapter_rows.append({'variant': side, 'exact_after_probe_removal': exact_counts and normalized == target})
        adapters_ok = len(adapter_rows) == 2 and all(row['exact_after_probe_removal'] for row in adapter_rows)
        terminal_ok = (geom.get('status') == 'TEST_PASS' and geom.get('cases') == 4260918
                       and geom.get('valid_domain_cases') == 4128771 and geom.get('random_full32_cases') == 131072
                       and verdict.get('status') == 'TEST_PASS' and verdict.get('cases') == 55
                       and verdict.get('configurations') == 8 and verdict.get('directed_checks') == 172
                       and verdict.get('outputs_per_configuration') == 84265
                       and verdict.get('seed') == 1068001)
        receipt_ok = (summary.get('schema') == 'v106-context-clocked-production-comparison-v1'
                      and summary.get('status') == 'PASS' and summary.get('baseline_revision') == BASELINE
                      and summary.get('frozen_after_focused_PASS') is True
                      and receipt.get('schema') == 'v106-context-clocked-production-comparison-v1'
                      and receipt.get('status') == 'PASS' and receipt.get('baseline_revision') == BASELINE
                      and receipt.get('actual_RTL_run') is True
                      and receipt.get('assertions_disabled_or_downgraded') is False
                      and receipt.get('complete_production_bodies_preserved_by_adapters') is True
                      and receipt.get('candidate', {}).get('path') == CONTEXT_CANDIDATE
                      and receipt.get('candidate', {}).get('sha256') == sha(read(CONTEXT_CANDIDATE))
                      and receipt.get('candidate', {}).get('recipe_sha256') == sha(read('fpga/experiments/cu66-v106-context/edit-recipe.json'))
                      and model.get('schema') == 'v106-context-full32-byte-identity-model-v1'
                      and model.get('status') == 'PASS' and model.get('rows') == 4260918
                      and model.get('byte_constants_checked') == 3072
                      and model.get('correction_index_constants_checked') == 768
                      and model.get('all_band_values_covered') == 256
                      and model.get('max_remainder_sum') == 168
                      and model.get('coverage') == {'default': 1012, 'edge': 63, 'random': 131072, 'valid': 4128771}
                      and receipt.get('trace_replay', {}).get('status') == 'PASS'
                      and receipt.get('trace_replay', {}).get('rows') == 4260918
                      and receipt.get('trace_replay', {}).get('raw_sha256') == receipt.get('raw_trace_sha256')
                      and adapters_ok and terminal_ok and strict and not artifact_errors and not source_errors)
        side_path = 'experiments/python-gamebub-v106/context/trace-audit.json'
        if not (ROOT / side_path).is_file():
            need('focused_context_independent_trace_audit', {'expected': side_path, 'selected_receipt': selected})
            side_ok: bool | str = 'PENDING'
        else:
            side = read_json(side_path)
            auditor = side.get('auditor', {})
            side_ok = (side.get('schema') == 'v106-context-independent-trace-audit-v1'
                       and side.get('status') == 'PASS'
                       and auditor.get('path') and sha(read(auditor['path'])) == auditor.get('sha256')
                       and side.get('selected_receipt', {}).get('path') == selected
                       and side.get('selected_receipt', {}).get('sha256') == sha(read(selected))
                       and side.get('selected_summary', {}).get('path') == summary_path
                       and side.get('selected_summary', {}).get('sha256') == sha(read(summary_path))
                       and side.get('candidate', {}).get('path') == CONTEXT_CANDIDATE
                       and side.get('candidate', {}).get('sha256') == sha(read(CONTEXT_CANDIDATE))
                       and side.get('candidate', {}).get('recipe_sha256') == sha(read('fpga/experiments/cu66-v106-context/edit-recipe.json'))
                       and side.get('rows') == 4260918
                       and side.get('byte_constants_checked') == 3072
                       and side.get('correction_index_constants_checked') == 768
                       and side.get('all_band_values_covered') == 256
                       and side.get('coverage') == {'valid': 4128771, 'random': 131072, 'edge': 63, 'default': 1012}
                       and side.get('contexts') == 55 and side.get('profiles') == 8
                       and side.get('outputs_per_profile') == 84265 and side.get('directed_checks') == 172
                       and side.get('raw_trace_sha256') == receipt.get('raw_trace_sha256')
                       and side.get('trace_sha256') == receipt.get('artifacts_sha256', {}).get('geometry.tsv.gz'))
        check('focused_context_receipt_and_independent_trace_audit', receipt_ok and side_ok is True,
              {'summary': summary_path, 'selected_receipt': selected, 'status': receipt.get('status'),
               'strict_compile': strict, 'terminal_verdicts_pass': terminal_ok, 'adapters_exact': adapters_ok,
               'source_errors': source_errors, 'artifact_errors': artifact_errors,
               'independent_sidecar': side_ok})
    except Exception as exc:
        check('focused_context_receipt_and_independent_trace_audit', False, {'error': str(exc)})

def audit_rice_recipe() -> dict[str, Any]:
    recipe_path = 'fpga/experiments/cu66-v106-rice/edit-proof.json'
    try:
        recipe = read_json(recipe_path)
        original = read(recipe['original_path'])
        candidate = read(recipe['candidate_path'])
        baseline = git_blob(BASELINE, recipe['original_path'])
        rebuilt, ledger = apply_recipe(original, recipe)
        ok = (recipe.get('schema') == 'v106-edit-recipe-v1' and recipe['original_path'] == RICE_ORIGINAL
              and recipe['candidate_path'] == RICE_CANDIDATE and len(recipe.get('edits', [])) == 8
              and all(row.get('expected_occurrences') == 1 for row in recipe.get('edits', []))
              and sha(original) == recipe.get('original_sha256') and original == baseline
              and sha(candidate) == recipe.get('candidate_sha256') and rebuilt == candidate
              and module_header(original, 'br88_rice_elastic') == module_header(candidate, 'br88_rice_elastic'))
        check('rice_eight_edit_recipe_exact_recovery_over_baseline', ok,
              {'recipe': recipe_path, 'original_baseline_equal': original == baseline,
               'candidate_sha256': sha(candidate), 'exact_recovery': rebuilt == candidate, 'edits': ledger})
        return {'recipe': recipe, 'path': recipe_path, 'candidate': candidate, 'original': original}
    except Exception as exc:
        check('rice_eight_edit_recipe_exact_recovery_over_baseline', False, {'error': str(exc)})
        return {}

def audit_prefix_recipe() -> dict[str, Any]:
    recipe_path = 'fpga/experiments/cu66-v106-prefix/edit-proof.json'
    try:
        recipe = read_json(recipe_path)
        original = read(recipe['original_path'])
        candidate = read(recipe['candidate_path'])
        rice_bytes = read(RICE_CANDIDATE)
        rebuilt, ledger = apply_recipe(original, recipe)
        ok = (recipe.get('schema') == 'v106-edit-recipe-v1'
              and recipe.get('original_path') == RICE_CANDIDATE
              and recipe.get('candidate_path') == PREFIX_CANDIDATE
              and len(recipe.get('edits', [])) == 2
              and all(row.get('expected_occurrences') == 1 for row in recipe.get('edits', []))
              and original == rice_bytes and sha(original) == recipe.get('original_sha256')
              and sha(candidate) == recipe.get('candidate_sha256') and rebuilt == candidate
              and module_header(original, 'br88_rice_elastic')
                  == module_header(candidate, 'br88_rice_elastic'))
        check('prefix_two_edit_recipe_exact_recovery_over_rice_candidate', ok,
              {'recipe': recipe_path, 'original_matches_rice_candidate': original == rice_bytes,
               'candidate_sha256': sha(candidate), 'exact_recovery': rebuilt == candidate, 'edits': ledger})
        return {'recipe': recipe, 'path': recipe_path, 'candidate': candidate, 'original': original}
    except Exception as exc:
        check('prefix_two_edit_recipe_exact_recovery_over_rice_candidate', False, {'error': str(exc)})
        return {}

def audit_suffix_recipe() -> dict[str, Any]:
    recipe_path = 'fpga/experiments/cu66-v106-suffix/edit-proof.json'
    try:
        recipe = read_json(recipe_path)
        original = read(recipe['original_path'])
        candidate = read(recipe['candidate_path'])
        prefix = read(PREFIX_CANDIDATE)
        rebuilt, ledger = apply_recipe(original, recipe)
        ok = (recipe.get('schema') == 'v106-edit-recipe-v1'
              and recipe.get('original_path') == PREFIX_CANDIDATE
              and recipe.get('candidate_path') == SUFFIX_CANDIDATE
              and len(recipe.get('edits', [])) == 3
              and all(row.get('expected_occurrences') == 1 for row in recipe.get('edits', []))
              and original == prefix and sha(original) == recipe.get('original_sha256')
              and sha(candidate) == recipe.get('candidate_sha256') and rebuilt == candidate
              and module_header(original, 'br88_rice_elastic')
                  == module_header(candidate, 'br88_rice_elastic'))
        check('suffix_three_edit_recipe_exact_recovery_over_prefix_candidate', ok,
              {'recipe': recipe_path, 'original_matches_prefix_candidate': original == prefix,
               'candidate_sha256': sha(candidate), 'exact_recovery': rebuilt == candidate, 'edits': ledger})
        return {'recipe': recipe, 'path': recipe_path, 'candidate': candidate, 'original': original}
    except Exception as exc:
        check('suffix_three_edit_recipe_exact_recovery_over_prefix_candidate', False, {'error': str(exc)})
        return {}

def audit_suffix24_recipe_and_model() -> dict[str, Any]:
    recipe_path = 'fpga/experiments/cu66-v106-suffix24/edit-recipe.json'
    summary_path = 'experiments/python-gamebub-v106/suffix24/results.json'
    try:
        recipe = read_json(recipe_path)
        original = read(recipe['original_path'])
        candidate = read(recipe['candidate_path'])
        suffix = read(SUFFIX_CANDIDATE)
        rebuilt, ledger = apply_recipe(original, recipe)
        recipe_ok = (recipe.get('schema') == 'v106-edit-recipe-v1'
                     and recipe.get('variant') == 'suffix24'
                     and recipe.get('original_path') == SUFFIX_CANDIDATE
                     and recipe.get('candidate_path') == SUFFIX24_CANDIDATE
                     and len(recipe.get('edits', [])) == 2
                     and all(row.get('expected_occurrences') == 1 for row in recipe.get('edits', []))
                     and original == suffix and sha(original) == recipe.get('original_sha256')
                     and sha(candidate) == recipe.get('candidate_sha256') and rebuilt == candidate
                     and module_header(original, 'br88_rice_elastic')
                         == module_header(candidate, 'br88_rice_elastic'))
        check('suffix24_two_edit_recipe_exact_recovery_over_suffix', recipe_ok,
              {'recipe': recipe_path, 'original_matches_suffix': original == suffix,
               'candidate_sha256': sha(candidate), 'exact_recovery': rebuilt == candidate, 'edits': ledger})
        summary = read_json(summary_path)
        model_ok = (summary.get('schema') == 'v106-suffix24-projection-model-v1'
                    and summary.get('status') == 'PASS_EXACT_PROJECTION_AND_RECIPES'
                    and summary.get('actual_RTL_run') is False
                    and summary.get('integrated_RTL_required') is True
                    and summary.get('candidate') == {'path': SUFFIX24_CANDIDATE, 'sha256': sha(candidate)}
                    and summary.get('original') == {'path': SUFFIX_CANDIDATE, 'sha256': sha(suffix)}
                    and summary.get('recipe') == {'path': recipe_path, 'sha256': sha(read(recipe_path))}
                    and summary.get('exhaustive_boundary_pattern_cases') == 196608
                    and summary.get('full_width_random_cases') == 100000
                    and summary.get('transcript_sha256'))
        check('suffix24_exact_projection_model_and_open_RTL_obligation', model_ok,
              {'schema': summary.get('schema'), 'status': summary.get('status'),
               'actual_RTL_run': summary.get('actual_RTL_run'),
               'integrated_RTL_required': summary.get('integrated_RTL_required'),
               'boundary_pattern_cases': summary.get('exhaustive_boundary_pattern_cases'),
               'full_width_random_cases': summary.get('full_width_random_cases'),
               'scope': 'exact projection/source model only; full production strict-lint and paired pipeline lanes remain required'})
        return {'path': SUFFIX24_CANDIDATE, 'sha256': sha(candidate),
                'recipe': recipe_path, 'recipe_sha256': sha(read(recipe_path))}
    except Exception as exc:
        check('suffix24_recipe_and_model', False, {'error': str(exc)})
        return {}

def audit_ingress_recipe_and_model() -> dict[str, Any]:
    recipe_path = 'fpga/experiments/cu66-v106-ingress/edit-recipe.json'
    model_path = 'experiments/python-gamebub-v106/ingress/model.json'
    try:
        recipe = read_json(recipe_path)
        original = read(recipe['original_path'])
        candidate = read(recipe['candidate_path'])
        baseline = git_blob(BASELINE, INGRESS_SYNC_ORIGINAL)
        rebuilt, ledger = apply_recipe(original, recipe)
        recipe_ok = (recipe.get('schema') == 'v106-edit-recipe-v1'
                     and recipe.get('original_path') == INGRESS_SYNC_ORIGINAL
                     and recipe.get('candidate_path') == INGRESS_SYNC_CANDIDATE
                     and len(recipe.get('edits', [])) == 7
                     and all(row.get('expected_occurrences') == 1 for row in recipe.get('edits', []))
                     and original == baseline and sha(original) == recipe.get('original_sha256')
                     and sha(candidate) == recipe.get('candidate_sha256') and rebuilt == candidate
                     and module_header(original, 'br88_packet_ingress_sync_v91h')
                         == module_header(candidate, 'br88_packet_ingress_sync_v91h'))
        check('ingress_seven_edit_recipe_exact_recovery_over_baseline', recipe_ok,
              {'recipe': recipe_path, 'original_baseline_equal': original == baseline,
               'candidate_sha256': sha(candidate), 'exact_recovery': rebuilt == candidate, 'edits': ledger})
        model = read_json(model_path)
        induction = model.get('full32_induction', {})
        model_ok = (model.get('schema') == 'v106-ingress-mod32-model-v1'
                    and model.get('status') == 'PASS' and model.get('rows') == 200450
                    and model.get('wrapped_subtractions') == 99660
                    and set(induction) == {'accepted_word', 'context_start', 'hold', 'last', 'reset_abort_replacement_start'}
                    and 'Z/(2^32)' in induction.get('last', '')
                    and 'universal modulo32' in model.get('scope', ''))
        check('ingress_full32_modular_invariant_model', model_ok,
              {'schema': model.get('schema'), 'status': model.get('status'), 'rows': model.get('rows'),
               'wrapped_subtractions': model.get('wrapped_subtractions'),
               'inactive_private_scope': 'ctx_bits/ctx_last remain deliberately unqualified outside CONTEXT_RUN'})
        return {'path': INGRESS_SYNC_CANDIDATE, 'sha256': sha(candidate),
                'recipe': recipe_path, 'recipe_sha256': sha(read(recipe_path))}
    except Exception as exc:
        check('ingress_recipe_and_model', False, {'error': str(exc)})
        return {}

def audit_telemetry_recipe() -> dict[str, Any]:
    recipe_path = 'fpga/experiments/cu66-v106-telemetry/edit-recipe.json'
    try:
        recipe = read_json(recipe_path)
        original = read(recipe['original_path'])
        candidate = read(recipe['candidate_path'])
        baseline = git_blob(BASELINE, recipe['original_path'])
        rebuilt, ledger = apply_recipe(original, recipe)
        ok = (recipe.get('schema') == 'v106-edit-recipe-v1' and recipe.get('variant') == 'telemetry'
              and recipe.get('original_path') == TELEMETRY_ORIGINAL
              and recipe.get('candidate_path') == TELEMETRY_CANDIDATE
              and len(recipe.get('edits', [])) == 3
              and all(row.get('expected_occurrences') == 1 for row in recipe.get('edits', []))
              and sha(original) == recipe.get('original_sha256') and original == baseline
              and sha(candidate) == recipe.get('candidate_sha256') and rebuilt == candidate
              and module_header(original, 'br88_pipeline_v91h')
                  == module_header(candidate, 'br88_pipeline_v91h'))
        check('telemetry_three_edit_recipe_exact_recovery_over_baseline', ok,
              {'recipe': recipe_path, 'original_baseline_equal': original == baseline,
               'candidate_sha256': sha(candidate), 'exact_recovery': rebuilt == candidate, 'edits': ledger})
        return {'recipe': recipe, 'path': recipe_path, 'candidate': candidate, 'original': original}
    except Exception as exc:
        check('telemetry_three_edit_recipe_exact_recovery_over_baseline', False, {'error': str(exc)})
        return {}

def audit_producer_cache_model() -> dict[str, Any]:
    """Rebuild both cache edits and independently replay the finite transition table.

    This is source/model evidence only. The integrated matrix remains responsible
    for exercising the live cache assertions in the actual production modules.
    """
    try:
        summary = read_json(PRODUCER_CACHE_SUMMARY)
        names = ('cs88_coefficients_v91k.sv', 'cs88_pipeline_v91i2b.sv')
        products = summary.get('production', [])
        details = []
        for index, name in enumerate(names):
            base = f'{PRODUCER_CACHE_ROOT}/{name}'
            recipe_path = f'{PRODUCER_CACHE_ROOT}/{name[:-3]}.recipe.json'
            recipe = read_json(recipe_path)
            original = read(recipe['original_path'])
            inherited = read(f'{MATH_ROOT}/lut/{name}')
            candidate = read(recipe['candidate_path'])
            rebuilt, ledger = apply_recipe(original, recipe)
            source_pin = {'path': recipe['candidate_path'], 'sha256': sha(candidate)}
            recipe_pin = {'path': recipe_path, 'sha256': sha(read(recipe_path))}
            inherited_pin = {'path': recipe['original_path'], 'sha256': sha(original)}
            expected_edits = ('private_cache', 'lookup_address', 'reset_abort', 'accepted_start',
                              'entropy_success_plane_zero', 'prepare_tile_zero', 'capture_mapped_cell',
                              'skip_tile', 'advance_tile', 'advance_plane', 'live_invariant')
            rhs = lambda src, var: __import__('re').findall(rb'\b' + var + rb'\s*<=([^;]+);', src)
            plane_equal = rhs(original, b'plane') == rhs(candidate, b'plane')
            tile_equal = rhs(original, b'tile_cursor') == rhs(candidate, b'tile_cursor')
            entry = products[index] if index < len(products) else {}
            entry_ok = (entry.get('source') == source_pin and entry.get('recipe') == recipe_pin
                        and entry.get('inherited') == {'path': recipe['original_path'], 'sha256': sha(inherited)})
            ok = (recipe.get('schema') == 'v106-edit-recipe-v1'
                  and recipe.get('variant') == 'producer-cache'
                  and recipe.get('original_path') == f'{MATH_ROOT}/lut/{name}'
                  and recipe.get('candidate_path') == base
                  and original == inherited and len(recipe.get('edits', [])) == 11
                  and tuple(row.get('name') for row in recipe.get('edits', [])) == expected_edits
                  and all(row.get('expected_occurrences') == 1 for row in recipe.get('edits', []))
                  and sha(original) == recipe.get('original_sha256')
                  and sha(candidate) == recipe.get('candidate_sha256')
                  and rebuilt == candidate and plane_equal and tile_equal
                  and module_header(original, 'cs88_coefficients_v91k' if index == 0 else 'cs88_pipeline_v91i2b')
                      == module_header(candidate, 'cs88_coefficients_v91k' if index == 0 else 'cs88_pipeline_v91i2b')
                  and entry_ok)
            check(f'producer_cache_{name}_exact_recipe_over_lut_source', ok,
                  {'recipe': recipe_path, 'candidate': base, 'candidate_sha256': sha(candidate),
                   'inherited_lut_source_equal': original == inherited, 'exact_recovery': rebuilt == candidate,
                   'plane_assignments_unchanged': plane_equal, 'tile_assignments_unchanged': tile_equal,
                   'production_pin_matches': entry_ok, 'edits': ledger})
            details.append({'path': base, 'sha256': sha(candidate), 'recipe': recipe_path,
                            'recipe_sha256': sha(read(recipe_path))})

        helper = read_json(summary['helper']['path'])
        lut_text = helper['lut']
        banks: dict[int, dict[int, int]] = {}
        import re
        for bank, body in re.findall(r"6'd(\d+):begin(.*?)end", lut_text, re.S):
            banks[int(bank)] = {int(bit): int(value, 16)
                                for bit, value in re.findall(r"lut(\d+)=64'h([0-9a-f]{16});", body)}
        lut_ok = set(banks) == set(range(64)) and all(set(row) == set(range(11)) for row in banks.values())
        def helper_value(plane: int, tile: int) -> int:
            if plane:
                return tile & 2047
            return sum(((banks[tile >> 7][bit] >> ((tile & 127) >> 1)) & 1) << bit
                       for bit in range(11))

        compressed = read(PRODUCER_CACHE_TRACE)
        raw = gzip.decompress(compressed)
        trace_sha_ok = (sha(compressed) == summary.get('trace_sha256')
                        and sha(raw) == summary.get('raw_trace_sha256')
                        and summary.get('helper') == {'path': 'fpga/experiments/cu66-v106-math/helpers.json',
                                                      'sha256': sha(read('fpga/experiments/cu66-v106-math/helpers.json'))})
        rows = 0
        transitions_ok = lut_ok
        operations = ('hold', 'reset_or_abort', 'accepted_start', 'entropy_plane_zero',
                      'prepare_tile_zero', 'skip_tile', 'advance_tile', 'advance_plane')
        for line in raw.splitlines():
            fields = tuple(int(item) for item in line.split(b'\t'))
            if len(fields) != 6:
                transitions_ok = False
                break
            p, t, op, np, nt, cache = fields
            if not (0 <= p < 4 and 0 <= np < 4 and 0 <= t < 8192 and 0 <= nt < 8192 and 0 <= op < 8):
                transitions_ok = False
                break
            if (p, t, op) != (rows // 8 // 8192, (rows // 8) % 8192, rows % 8):
                transitions_ok = False
                break
            if op in (1, 2):
                want_p, want_t = 0, 0
            elif op == 3:
                want_p, want_t = 0, t
            elif op == 4:
                want_p, want_t = p, 0
            elif op in (5, 6):
                want_p, want_t = p, (t + 1) & 8191
            elif op == 7:
                want_p, want_t = (p + 1) & 3, t
            else:
                want_p, want_t = p, t
            if (np, nt) != (want_p, want_t) or cache != helper_value(np, nt):
                transitions_ok = False
                break
            rows += 1
        summary_ok = (summary.get('schema') == 'v106-producer-cache-transition-model-v1'
                      and summary.get('status') == 'PASS_MODEL_AND_EXACT_SOURCE_RECIPES'
                      and summary.get('helper_domain_cases') == 32768
                      and summary.get('transition_model_rows') == 262144
                      and summary.get('operations') == list(operations)
                      and summary.get('actual_RTL_run') is False
                      and summary.get('integrated_RTL_required') is True
                      and len(products) == 2)
        check('producer_cache_model_trace_and_scope', summary_ok and trace_sha_ok
              and rows == 262144 and transitions_ok,
              {'summary_schema_status': [summary.get('schema'), summary.get('status')],
               'actual_RTL_run': summary.get('actual_RTL_run'),
               'integrated_RTL_required': summary.get('integrated_RTL_required'),
               'trace_sha256_matches': trace_sha_ok, 'helper_table_complete': lut_ok,
               'transition_rows_replayed': rows, 'transitions_match_model': transitions_ok,
               'scope': 'finite transition model and exact source recipes; integrated whole-module RTL lanes remain required'})
        return {'summary': summary, 'products': details}
    except Exception as exc:
        check('producer_cache_model_trace_and_scope', False, {'error': str(exc)})
        return {}

def audit_idct_recipe_and_model(area_variant: bool = False) -> dict[str, Any]:
    area = 'idct-area' if area_variant else 'idct'
    candidate_path = IDCT_AREA_CANDIDATE if area_variant else IDCT_CANDIDATE
    recipe_path = f'fpga/experiments/cu66-v106-{area}/edit-recipe.json'
    model_path = f'experiments/python-gamebub-v106/{area}/model.json'
    check_prefix = area.replace('-', '_')
    try:
        recipe = read_json(recipe_path)
        original = read(recipe['original_path'])
        candidate = read(recipe['candidate_path'])
        baseline = git_blob(BASELINE, recipe['original_path'])
        rebuilt, ledger = apply_recipe(original, recipe)
        recipe_ok = (recipe.get('schema') == 'v106-edit-recipe-v1'
                     and recipe.get('variant') == area
                     and recipe.get('original_path') == IDCT_ORIGINAL
                     and recipe.get('candidate_path') == candidate_path
                     and len(recipe.get('edits', [])) == (6 if area_variant else 11)
                     and all(row.get('expected_occurrences') == 1 for row in recipe.get('edits', []))
                     and original == baseline and sha(original) == recipe.get('original_sha256')
                     and sha(candidate) == recipe.get('candidate_sha256') and rebuilt == candidate
                     and module_header(original, 'cu66_idct8x8') == module_header(candidate, 'cu66_idct8x8'))
        check(f'{check_prefix}_recipe_exact_recovery_over_baseline', recipe_ok,
              {'recipe': recipe_path, 'original_baseline_equal': original == baseline,
               'candidate_sha256': sha(candidate), 'exact_recovery': rebuilt == candidate,
               'edits': ledger})
        model = read_json(model_path)
        vectors = model.get('vectors', {})
        vector_raw = gzip.decompress(read(vectors.get('path', '')))
        model_ok = (model.get('schema') == 'v106-idct-independent-integer-model-v1'
                    and model.get('status') == 'PASS' and model.get('tiles') == 4303
                    and model.get('original_tiles') == 3471 and model.get('extra_tiles') == 832
                    and vectors.get('sha256') == sha(read(vectors['path']))
                    and vectors.get('raw_sha256') == sha(vector_raw)
                    and sum(model.get(k, 0) for k in ('arbitrary_AC_tiles', 'additional_DC_tiles',
                                                       'additional_invalid_domain_tiles')) == 832)
        check(f'{check_prefix}_independent_integer_model_and_vector_pins', model_ok,
              {'schema': model.get('schema'), 'status': model.get('status'), 'tiles': model.get('tiles'),
               'original_tiles': model.get('original_tiles'), 'extra_tiles': model.get('extra_tiles'),
               'vector_sha256_matches': vectors.get('sha256') == sha(read(vectors['path'])),
               'vector_raw_sha256_matches': vectors.get('raw_sha256') == sha(vector_raw),
               'scope': 'independent integer model only; clocked production equivalence must be established by integrated lanes'})
        return {'recipe': recipe_path, 'candidate': candidate_path, 'candidate_sha256': sha(candidate),
                'model': model_path, 'model_status': model.get('status')}
    except Exception as exc:
        check(f'{check_prefix}_recipe_and_model', False, {'error': str(exc)})
        return {}

def audit_scratch_recipe_and_model() -> dict[str, Any]:
    recipe_path = 'fpga/experiments/cu66-v106-scratch/edit-recipe.json'
    model_path = 'experiments/python-gamebub-v106/scratch/model.json'
    try:
        recipe = read_json(recipe_path)
        original = read(recipe['original_path'])
        candidate = read(recipe['candidate_path'])
        plan = read(PLAN_CANDIDATE)
        rebuilt, ledger = apply_recipe(original, recipe)
        recipe_ok = (recipe.get('schema') == 'v106-edit-recipe-v1'
                     and recipe.get('variant') == 'scratch-position-predecode'
                     and recipe.get('original_path') == PLAN_CANDIDATE
                     and recipe.get('candidate_path') == SCRATCH_CANDIDATE
                     and len(recipe.get('edits', [])) == 9
                     and all(row.get('expected_occurrences') == 1 for row in recipe.get('edits', []))
                     and original == plan and sha(original) == recipe.get('original_sha256')
                     and sha(candidate) == recipe.get('candidate_sha256') and rebuilt == candidate
                     and module_header(original, 'packed_scratch_v91g2')
                         == module_header(candidate, 'packed_scratch_v91g2'))
        check('scratch_nine_edit_recipe_exact_recovery_over_plan_candidate', recipe_ok,
              {'recipe': recipe_path, 'original_matches_plan': original == plan,
               'candidate_sha256': sha(candidate), 'exact_recovery': rebuilt == candidate,
               'edits': ledger})
        model = read_json(model_path)
        model_ok = (model.get('schema') == 'v106-scratch-independent-position-model-v1'
                    and model.get('status') == 'PASS'
                    and model.get('all19bit_upper_record_values') == 524288
                    and model.get('all16_offset_line_probes') == 262144
                    and model.get('random_full32_word_address_pairs') == 262144
                    and model.get('band_rank_pairs') == 256
                    and model.get('seed') == 1061101)
        check('scratch_position_predecode_independent_model', model_ok,
              {'schema': model.get('schema'), 'status': model.get('status'),
               'all19bit_upper_record_values': model.get('all19bit_upper_record_values'),
               'all16_offset_line_probes': model.get('all16_offset_line_probes'),
               'random_full32_word_address_pairs': model.get('random_full32_word_address_pairs'),
               'band_rank_pairs': model.get('band_rank_pairs'),
               'scope': model.get('scope')})
        return {'path': SCRATCH_CANDIDATE, 'sha256': sha(candidate),
                'recipe': recipe_path, 'recipe_sha256': sha(read(recipe_path))}
    except Exception as exc:
        check('scratch_recipe_and_model', False, {'error': str(exc)})
        return {}

def audit_idct_area_unit_synthesis() -> None:
    comparison_path = 'experiments/python-gamebub-v106/idct-area/unit-synthesis-comparison.json'
    try:
        comparison = read_json(comparison_path)
        selected = comparison.get('selected_receipt', {})
        receipt_path = selected.get('path')
        if not receipt_path or not (ROOT / receipt_path).is_file():
            need('idct_area_matched_unit_synthesis_receipt', {'expected': receipt_path})
            return
        receipt_bytes = read(receipt_path)
        receipt = json.loads(receipt_bytes)
        auditor = comparison.get('analyzer', {})
        expected_sources = {
            'original': (IDCT_ORIGINAL, '251d4c11d762f6a040c1934d9dca9d80e6187f470a90b7261c63d06d1f3c310c'),
            'prefetch': (IDCT_CANDIDATE, 'f972987d80a062b4969c71ac6157e8f17ab9e6b18088bafb77c4030eac78990e'),
            'shared': (IDCT_AREA_CANDIDATE, '1ed49416dae06b727544ad1d2f96440f553cd99e5324dc895a0af5edbca5cc32'),
        }
        reports_ok, variants_ok = True, True
        report_count = 0
        for name, (source_path, source_hash) in expected_sources.items():
            row = comparison.get('variants', {}).get(name, {})
            src = row.get('source', {})
            variants_ok &= (src == {'path': source_path, 'sha256': source_hash}
                            and sha(read(source_path)) == source_hash)
            for report_path, expected_hash in row.get('reports', {}).items():
                try:
                    report = read(report_path)
                    reports_ok &= sha(report) == expected_hash
                    report_count += 1
                except Exception:
                    reports_ok = False
        original = comparison.get('variants', {}).get('original', {})
        prefetch = comparison.get('variants', {}).get('prefetch', {})
        shared = comparison.get('variants', {}).get('shared', {})
        metrics_ok = (all(original.get(k) == v for k, v in {'synthesis_slice_LUTs': 7690,
                       'synthesis_slice_registers': 5149, 'synthesis_DSPs': 17,
                       'synthesis_estimated_worst_slack_ns': 0.796}.items())
                      and all(prefetch.get(k) == v for k, v in {'synthesis_slice_LUTs': 16256,
                       'synthesis_slice_registers': 5176, 'synthesis_DSPs': 19,
                       'synthesis_estimated_worst_slack_ns': -0.700}.items())
                      and all(shared.get(k) == v for k, v in {'synthesis_slice_LUTs': 7772,
                       'synthesis_slice_registers': 5129, 'synthesis_DSPs': 17,
                       'synthesis_estimated_worst_slack_ns': 2.920}.items())
                      and comparison.get('shared_minus_original_LUTs') == 82
                      and comparison.get('shared_minus_prefetch_LUTs') == -8484)
        receipt_ok = (comparison.get('schema') == 'v106-idct-area-matched-unit-synthesis-comparison-v1'
                      and comparison.get('status') == 'UNIT_SYNTHESIS_EVIDENCE_COMPLETE'
                      and comparison.get('all_settings_matched') is True
                      and comparison.get('top') == 'cu66_idct8x8'
                      and comparison.get('part') == 'xc7a100tcsg324-1'
                      and comparison.get('clock_period_ns') == 10.0
                      and selected.get('sha256') == sha(receipt_bytes)
                      and receipt.get('schema') == 'v106-idct-area-unit-synthesis-v1'
                      and receipt.get('status') == 'SYNTHESIS_ONLY_FINISHED_SIGNOFF_OPEN'
                      and receipt.get('observed_exit_code') == 0
                      and receipt.get('synthesis_only_finished') is True
                      and receipt.get('source_snapshot_unchanged') is True
                      and receipt.get('placement_reports_present') is False
                      and receipt.get('component_route_finished') is False
                      and receipt.get('clock_period_ns') == 10.0 and receipt.get('top') == 'cu66_idct8x8'
                      and receipt.get('part') == 'xc7a100tcsg324-1'
                      and receipt.get('max_threads') == 2 and receipt.get('memory_limit_bytes') == 8589934592
                      and receipt.get('existing_legitimate_license_readonly') is True
                      and receipt.get('license_contents_logged') is False
                      and auditor.get('path') and sha(read(auditor['path'])) == auditor.get('sha256'))
        check('idct_area_matched_unit_synthesis_evidence_and_limits', receipt_ok and variants_ok
              and metrics_ok and reports_ok and report_count == 9,
              {'comparison': comparison_path, 'selected_receipt': receipt_path,
               'receipt_status': receipt.get('status'), 'matched_source_variants': variants_ok,
               'report_count': report_count, 'report_hashes_match': reports_ok,
               'unit_synthesis_metrics_match': metrics_ok,
               'scope': 'matched unit synthesis only; no placement, route, full-top fit or board qualification'})
    except Exception as exc:
        check('idct_area_matched_unit_synthesis_evidence_and_limits', False, {'error': str(exc)})

def audit_suffix_focused() -> None:
    summary_path = 'experiments/python-gamebub-v106/suffix/probe-results.json'
    if not (ROOT / summary_path).is_file():
        need('focused_suffix_receipt_and_independent_trace_audit', {'expected': summary_path})
        return
    try:
        summary = read_json(summary_path)
        selected = summary.get('selected_receipt')
        if not selected or not (ROOT / selected).is_file():
            need('focused_suffix_selected_receipt', {'summary': summary_path, 'selected_receipt': selected})
            return
        receipt_bytes = read(selected)
        receipt = json.loads(receipt_bytes)
        attempt_dir = (ROOT / selected).parent
        artifacts = verify_artifacts(receipt, attempt_dir)
        sources = verify_source_map(receipt.get('source_sha256', {}))
        compile_rows = [row for row in receipt.get('commands', [])
                        if '--cc' in row.get('argv', []) and '--build' in row.get('argv', [])]
        strict = (len(compile_rows) == 1 and compile_rows[0].get('exit_code') == 0
                  and '--assert' in compile_rows[0].get('argv', [])
                  and '-Wall' in compile_rows[0].get('argv', [])
                  and '-Werror' in ' '.join(compile_rows[0].get('argv', []))
                  and b'%Warning-' not in compile_log_path(attempt_dir, compile_rows[0]).read_bytes())
        runs = receipt.get('runs', [])
        runs_ok = (len(runs) == 2 and [row.get('seed') for row in runs] == [106401, 106402]
                   and all(row.get('status') == 'TEST_PASS'
                           and row.get('prepared_clocks') == 611057
                           and row.get('prepared_trace_records') == 611057
                           and row.get('historical_verdict', {}).get('cases') == 1520
                           and row.get('historical_verdict', {}).get('configurations') == 8
                           and row.get('historical_verdict', {}).get('requests_per_configuration') == 173061
                           and row.get('historical_verdict', {}).get('directed_checks') == 104
                           and row.get('suffix_domain_cases') == 12480
                           and row.get('prefix_rank_pattern_window_cases') == 524288
                           and row.get('prefix_available_corner_cases') == 8320 for row in runs))
        side_path = 'experiments/python-gamebub-v106/suffix/trace-audit.json'
        if not (ROOT / side_path).is_file():
            need('focused_suffix_independent_trace_audit', {'expected': side_path, 'selected_receipt': selected})
            side_ok: bool | str = 'PENDING'
        else:
            side = read_json(side_path)
            auditor = side.get('auditor', {})
            side_runs = side.get('runs', [])
            side_ok = (side.get('schema') == 'v106-suffix-evidence-audit-v1'
                       and side.get('status') == 'PASS_SUFFIX_MODEL_ADAPTERS_AND_CHECKPOINTS'
                       and side.get('receipt') == selected
                       and side.get('receipt_sha256') == sha(receipt_bytes)
                       and auditor.get('path') and sha(read(auditor['path'])) == auditor.get('sha256')
                       and side.get('suffix_model', {}).get('status') == 'PASS_SELECTED_SUFFIX_IDENTITY'
                       and side.get('inherited_rank_model', {}).get('status') == 'PASS_EXHAUSTIVE_RANK_WINDOW_AND_AVAILABLE_MODEL'
                       and side.get('inherited_cache_algebra', {}).get('status') == 'PASS_EXACT_AFFINE_RING_IDENTITIES'
                       and any(row.get('status') == 'PASS'
                               and row.get('path') == 'fpga/experiments/cu66-v106-suffix/edit-proof.json'
                               and row.get('sha256') == sha(read('fpga/experiments/cu66-v106-suffix/edit-proof.json'))
                               for row in side.get('checks', []))
                       and len(side_runs) == 2
                       and [row.get('seed') for row in side_runs] == [106401, 106402]
                       and all(row.get('status') == 'PASS'
                               and row.get('prepared_complete_trace_records') == 611057
                               and row.get('actual_every_clock_oracle_edges', 0) > 9_000_000
                               and row.get('historical_sampled_checkpoint_records', 0) > 0 for row in side_runs)
                       and [row.get('trace_sha256') for row in side_runs]
                           == [receipt.get('artifacts_sha256', {}).get(f"seed-{seed}.jsonl.gz")
                               for seed in (106401, 106402)])
        receipt_ok = (summary.get('schema') == 'v106-suffix-probe-selection-v1'
                      and summary.get('status') == 'PASS_ACTUAL_SUFFIX_EQUIVALENCE'
                      and summary.get('sha256') == sha(receipt_bytes)
                      and receipt.get('schema') == 'v106-suffix-clocked-probe-v1'
                      and receipt.get('status') == 'PASS_ACTUAL_SUFFIX_EQUIVALENCE'
                      and receipt.get('candidate', {}).get('path') == SUFFIX_CANDIDATE
                      and receipt.get('candidate', {}).get('sha256') == sha(read(SUFFIX_CANDIDATE))
                      and receipt.get('source_sha256', {}).get(SUFFIX_CANDIDATE) == sha(read(SUFFIX_CANDIDATE))
                      and all(row.get('exit_code') == 0 for row in receipt.get('commands', []))
                      and runs_ok and strict and not artifacts and not sources)
        check('focused_suffix_receipt_and_independent_trace_audit', receipt_ok and side_ok is True,
              {'summary': summary_path, 'selected_receipt': selected, 'receipt_status': receipt.get('status'),
               'runs_pass': runs_ok, 'strict_compile': strict, 'source_errors': sources,
               'artifact_errors': artifacts, 'independent_sidecar': side_ok})
    except Exception as exc:
        check('focused_suffix_receipt_and_independent_trace_audit', False, {'error': str(exc)})

def audit_idct_focused(area_variant: bool = False) -> None:
    area = 'idct-area' if area_variant else 'idct'
    schema = f'v106-{area}-clocked-production-comparison-v1'
    side_schema = f'v106-{area}-independent-trace-audit-v1'
    candidate_path = IDCT_AREA_CANDIDATE if area_variant else IDCT_CANDIDATE
    check_prefix = 'focused_' + area.replace('-', '_')
    summary_path = f'experiments/python-gamebub-v106/{area}/results.json'
    if not (ROOT / summary_path).is_file():
        need(check_prefix + '_receipt_and_independent_trace_audit', {'expected': summary_path})
        return
    try:
        summary = read_json(summary_path)
        selected = summary.get('selected_report')
        if not selected or not (ROOT / selected).is_file():
            need(check_prefix + '_selected_receipt', {'summary': summary_path, 'selected_report': selected})
            return
        receipt = read_json(selected)
        ad = (ROOT / selected).parent
        artifacts = verify_artifacts(receipt, ad)
        sources = verify_source_map(receipt.get('source_sha256', {}))
        compile_rows = [row for row in receipt.get('commands', [])
                        if '--cc' in row.get('argv', []) and '--build' in row.get('argv', [])]
        strict = (len(compile_rows) == 1 and compile_rows[0].get('exit_code') == 0
                  and '--assert' in compile_rows[0].get('argv', [])
                  and '-Wall' in compile_rows[0].get('argv', [])
                  and '-Werror' in ' '.join(compile_rows[0].get('argv', []))
                  and b'%Warning-' not in compile_log_path(ad, compile_rows[0]).read_bytes())
        expected_edges = {106401: 270128, 106402: 270240}
        runs = receipt.get('runs', [])
        runs_ok = (len(runs) == 2 and [row.get('seed') for row in runs] == [106401, 106402]
                   and all(row.get('verdict', {}).get('status') == 'TEST_PASS'
                           and row.get('verdict', {}).get('seed') == row.get('seed')
                           and row.get('verdict', {}).get('tiles') == 4303
                           and row.get('verdict', {}).get('completed_tiles') == 4333
                           and row.get('verdict', {}).get('clock_edges') == expected_edges.get(row.get('seed'))
                           and row.get('verdict', {}).get('states') == 1023
                           and row.get('verdict', {}).get('directed_abort_reset_cases') == 30
                           and row.get('trace_replay', {}).get('status') == 'PASS'
                           and row.get('trace_replay', {}).get('rows') == expected_edges.get(row.get('seed'))
                           and row.get('trace_replay', {}).get('multiply_edges') == 122024 for row in runs))
        side_path = f'experiments/python-gamebub-v106/{area}/trace-audit.json'
        if not (ROOT / side_path).is_file():
            need(check_prefix + '_independent_trace_audit', {'expected': side_path, 'selected_report': selected})
            side_ok: bool | str = 'PENDING'
        else:
            side = read_json(side_path)
            auditor = side.get('auditor', {})
            side_runs = side.get('runs', [])
            side_ok = (side.get('schema') == side_schema
                       and side.get('status') == 'PASS'
                       and side.get('selected_receipt', {}).get('path') == selected
                       and side.get('selected_receipt', {}).get('sha256') == sha(read(selected))
                       and side.get('selected_summary', {}).get('path') == summary_path
                       and side.get('selected_summary', {}).get('sha256') == sha(read(summary_path))
                       and side.get('candidate', {}).get('path') == candidate_path
                       and side.get('candidate', {}).get('sha256') == sha(read(candidate_path))
                       and side.get('candidate', {}).get('recipe_sha256')
                           == sha(read(f'fpga/experiments/cu66-v106-{area}/edit-recipe.json'))
                       and auditor.get('path') and sha(read(auditor['path'])) == auditor.get('sha256')
                       and side.get('independent_integer_gold_tiles') == 4303
                       and len(side_runs) == 2 and [row.get('seed') for row in side_runs] == [106401, 106402]
                       and all(row.get('tiles') == 4303 and row.get('states') == 10
                               and row.get('all_state_guard_pairs') == 30 for row in side_runs)
                       and [row.get('trace', {}).get('sha256') for row in side_runs]
                           == [receipt.get('artifacts_sha256', {}).get(f"trace-{seed}.jsonl.gz")
                               for seed in (106401, 106402)])
        receipt_ok = (summary.get('schema') == schema
                      and summary.get('status') == 'PASS' and summary.get('frozen_after_focused_PASS') is True
                      and receipt.get('schema') == schema
                      and receipt.get('status') == 'PASS' and receipt.get('baseline_revision') == BASELINE
                      and receipt.get('actual_RTL_run') is True
                      and receipt.get('frozen_after_focused_PASS') is True
                      and receipt.get('assertions_disabled_or_downgraded') is False
                      and receipt.get('candidate', {}).get('path') == candidate_path
                      and receipt.get('candidate', {}).get('sha256') == sha(read(candidate_path))
                      and receipt.get('candidate', {}).get('recipe_sha256')
                          == sha(read(f'fpga/experiments/cu66-v106-{area}/edit-recipe.json'))
                      and len(receipt.get('commands', [])) > 0
                      and all(row.get('exit_code') == 0 for row in receipt.get('commands', []))
                      and runs_ok and strict and not artifacts and not sources)
        check(check_prefix + '_receipt_and_independent_trace_audit', receipt_ok and side_ok is True,
              {'summary': summary_path, 'selected_report': selected, 'status': receipt.get('status'),
               'runs_pass': runs_ok, 'strict_compile': strict, 'source_mismatches': sources,
               'artifact_mismatches': artifacts, 'independent_sidecar': side_ok})
    except Exception as exc:
        check(check_prefix + '_receipt_and_independent_trace_audit', False, {'error': str(exc)})

def audit_scratch_focused() -> None:
    summary_path = 'experiments/python-gamebub-v106/scratch/results.json'
    if not (ROOT / summary_path).is_file():
        need('focused_scratch_receipt_and_independent_trace_audit', {'expected': summary_path})
        return
    try:
        summary = read_json(summary_path)
        selected = summary.get('selected_report')
        if not selected or not (ROOT / selected).is_file():
            need('focused_scratch_selected_receipt', {'summary': summary_path, 'selected_report': selected})
            return
        receipt_bytes = read(selected)
        receipt = json.loads(receipt_bytes)
        ad = (ROOT / selected).parent
        artifacts = verify_artifacts(receipt, ad)
        sources = verify_source_map(receipt.get('source_sha256', {}))
        compile_rows = [row for row in receipt.get('commands', [])
                        if '--cc' in row.get('argv', []) and '--build' in row.get('argv', [])]
        strict = (len(compile_rows) == 1 and compile_rows[0].get('exit_code') == 0
                  and '--assert' in compile_rows[0].get('argv', [])
                  and '-Wall' in compile_rows[0].get('argv', [])
                  and '-Werror' in ' '.join(compile_rows[0].get('argv', []))
                  and receipt.get('strict_warnings') is True
                  and b'%Warning-' not in compile_log_path(ad, compile_rows[0]).read_bytes())
        expected = {106401: (111571, 7673712, 2978, 3314),
                    106402: (111458, 7659168, 2975, 3311)}
        runs = receipt.get('runs', [])
        runs_ok = (len(runs) == 2 and [row.get('seed') for row in runs] == [106401, 106402]
                   and all(row.get('verdict', {}).get('status') == 'TEST_PASS'
                           and row.get('verdict', {}).get('type') == 'scratch_predecode_verdict'
                           and row.get('verdict', {}).get('seed') == row.get('seed')
                           and row.get('verdict', {}).get('clock_edges') == expected[row.get('seed')][0]
                           and row.get('verdict', {}).get('cache_position_checks') == expected[row.get('seed')][1]
                           and row.get('verdict', {}).get('head_compares') == expected[row.get('seed')][2]
                           and row.get('verdict', {}).get('live_reads') == expected[row.get('seed')][3]
                           and row.get('verdict', {}).get('full_transactions') == 72
                           and row.get('verdict', {}).get('corrupt_response_cases') == 128
                           and row.get('verdict', {}).get('read_owner_cases') == 4
                           and row.get('verdict', {}).get('offset_mask') == 65535
                           and row.get('verdict', {}).get('bank_mask') == 15
                           and row.get('historical_verdict', {}).get('status') == 'TEST_PASS'
                           and row.get('historical_verdict', {}).get('directed_checks') == 9
                           and row.get('historical_verdict', {}).get('edges') == 311
                           and row.get('historical_verdict', {}).get('physical_accepts') == 8
                           and row.get('trace_replay', {}).get('status') == 'PASS' for row in runs))
        side_path = 'experiments/python-gamebub-v106/scratch/trace-audit.json'
        if not (ROOT / side_path).is_file():
            need('focused_scratch_independent_trace_audit', {'expected': side_path, 'selected_report': selected})
            side_ok: bool | str = 'PENDING'
        else:
            side = read_json(side_path)
            auditor = side.get('auditor', {})
            side_runs = side.get('runs', [])
            side_ok = (side.get('schema') == 'v106-scratch-independent-trace-audit-v1'
                       and side.get('status') == 'PASS'
                       and side.get('selected_receipt') == {'path': selected, 'sha256': sha(receipt_bytes)}
                       and side.get('selected_summary') == {'path': summary_path, 'sha256': sha(read(summary_path))}
                       and side.get('candidate') == summary.get('candidate')
                       and auditor.get('path') and sha(read(auditor['path'])) == auditor.get('sha256')
                       and side.get('all_upper19_geometries') == 524288
                       and side.get('band_rank_pairs') == 256
                       and side.get('total_clock_edges') == 223651
                       and side.get('total_cache_events') == 3874
                       and side.get('total_live_reads') == 6625
                       and side.get('total_head_compares') == 5953
                       and len(side_runs) == 2 and [row.get('seed') for row in side_runs] == [106401, 106402]
                       and all(row.get('clock_edges') == expected[row.get('seed')][0]
                               and row.get('cache_events') == 1937
                               and row.get('full_transactions') == 72
                               and row.get('corrupt_response_cases') == 128
                               and row.get('read_owner_cases') == 4
                               and row.get('historical_edges') == 311
                               and row.get('historical_hazards') == 9 for row in side_runs)
                       and [row.get('trace', {}).get('sha256') for row in side_runs]
                           == [receipt.get('artifacts_sha256', {}).get(f'trace-{seed}.jsonl.gz')
                               for seed in (106401, 106402)])
        receipt_ok = (summary.get('schema') == 'v106-scratch-clocked-production-comparison-v1'
                      and summary.get('status') == 'PASS'
                      and summary.get('baseline_revision') == BASELINE
                      and summary.get('frozen_after_focused_PASS') is True
                      and receipt.get('schema') == 'v106-scratch-clocked-production-comparison-v1'
                      and receipt.get('status') == 'PASS' and receipt.get('baseline_revision') == BASELINE
                      and receipt.get('actual_RTL_run') is True
                      and receipt.get('assertions_disabled_or_downgraded') is False
                      and receipt.get('strict_warnings') is True
                      and receipt.get('candidate') == summary.get('candidate')
                      and receipt.get('candidate', {}).get('path') == SCRATCH_CANDIDATE
                      and receipt.get('candidate', {}).get('sha256') == sha(read(SCRATCH_CANDIDATE))
                      and receipt.get('candidate', {}).get('recipe_sha256')
                          == sha(read('fpga/experiments/cu66-v106-scratch/edit-recipe.json'))
                      and receipt.get('baseline_plan_sha256') == sha(read(PLAN_CANDIDATE))
                      and all(row.get('exit_code') == 0 for row in receipt.get('commands', []))
                      and runs_ok and strict and not artifacts and not sources)
        check('focused_scratch_receipt_and_independent_trace_audit', receipt_ok and side_ok is True,
              {'summary': summary_path, 'selected_report': selected, 'status': receipt.get('status'),
               'runs_pass': runs_ok, 'strict_compile': strict, 'source_mismatches': sources,
               'artifact_mismatches': artifacts, 'independent_sidecar': side_ok})
    except Exception as exc:
        check('focused_scratch_receipt_and_independent_trace_audit', False, {'error': str(exc)})

def audit_ingress_focused() -> None:
    summary_path = 'experiments/python-gamebub-v106/ingress/probe-results.json'
    if not (ROOT / summary_path).is_file():
        need('focused_ingress_receipt_and_independent_trace_audit', {'expected': summary_path})
        return
    try:
        summary = read_json(summary_path)
        selected = summary.get('selected_receipt')
        if not selected or not (ROOT / selected).is_file():
            need('focused_ingress_selected_receipt', {'summary': summary_path, 'selected_receipt': selected})
            return
        receipt_bytes = read(selected)
        receipt = json.loads(receipt_bytes)
        ad = (ROOT / selected).parent
        artifacts = verify_artifacts(receipt, ad)
        sources = verify_source_map(receipt.get('source_sha256', {}))
        compile_rows = [row for row in receipt.get('commands', [])
                        if '--cc' in row.get('argv', []) and '--build' in row.get('argv', [])]
        strict = (len(compile_rows) == 1 and compile_rows[0].get('exit_code') == 0
                  and '--assert' in compile_rows[0].get('argv', [])
                  and '-Wall' in compile_rows[0].get('argv', [])
                  and '-Werror' in ' '.join(compile_rows[0].get('argv', []))
                  and receipt.get('strict_warnings') is True
                  and b'%Warning-' not in compile_log_path(ad, compile_rows[0]).read_bytes())
        expected_hist = {106401: 7983546, 106402: 7981974}
        runs = receipt.get('runs', [])
        sync_names = ['unaligned_header_descriptor_partial_word', 'padding_rejected_before_metadata',
                      'abort_queued_ram_request', 'abort_registered_ram_response',
                      'reset_registered_ram_response', 'restart_registered_ram_response',
                      'context_failure_cancels_inflight_fetch', 'held_sparse_visible_during_ram_fetch',
                      'raw_pair_held_until_acceptance']
        runs_ok = (len(runs) == 2 and [row.get('seed') for row in runs] == [106401, 106402]
                   and all(row.get('status') == 'TEST_PASS'
                           and row.get('prepared_cases') == 5760 and row.get('prepared_edges') == 11521
                           and row.get('prepared_initializations') == 240 and row.get('prepared_updates') == 224
                           and row.get('historical_edges') == expected_hist[row.get('seed')]
                           and row.get('historical_updates') == 47514
                           and row.get('historical_verdict', {}).get('status') == 'TEST_PASS'
                           and row.get('historical_verdict', {}).get('packets') == 20
                           and row.get('historical_verdict', {}).get('configurations') == 2
                           and row.get('historical_verdict', {}).get('dense_comparisons') == 4501888
                           and row.get('historical_verdict', {}).get('directed_checks') == 56
                           and row.get('historical_verdict', {}).get('sync_staging_checks') == 9
                           and row.get('historical_verdict', {}).get('sync_staging_check_names') == sync_names
                           for row in runs))
        side_path = 'experiments/python-gamebub-v106/ingress/trace-audit.json'
        if not (ROOT / side_path).is_file():
            need('focused_ingress_independent_trace_audit', {'expected': side_path, 'selected_receipt': selected})
            side_ok: bool | str = 'PENDING'
        else:
            side = read_json(side_path)
            auditor = side.get('auditor', {})
            side_runs = side.get('runs', [])
            side_ok = (side.get('schema') == 'v106-ingress-evidence-audit-v1'
                       and side.get('status') == 'PASS_INGRESS_MODEL_ADAPTERS_AND_CHECKPOINTS'
                       and side.get('receipt') == selected and side.get('receipt_sha256') == sha(receipt_bytes)
                       and auditor.get('path') and sha(read(auditor['path'])) == auditor.get('sha256')
                       and side.get('model') == read_json('experiments/python-gamebub-v106/ingress/model.json')
                       and side.get('total_clock_edges') == 15988562 and len(side_runs) == 2
                       and [row.get('seed') for row in side_runs] == [106401, 106402]
                       and all(row.get('prepared_cases') == 5760 and row.get('prepared_edges') == 11521
                               and row.get('prepared_initializations') == 240 and row.get('prepared_updates') == 224
                               and row.get('historical_edges') == expected_hist[row.get('seed')]
                               and row.get('historical_checkpoints', 0) > 30000 for row in side_runs)
                       and [row.get('complete_trace_sha256') for row in side_runs]
                           == [receipt.get('artifacts_sha256', {}).get(f"seed-{seed}.jsonl.gz")
                               for seed in (106401, 106402)]
                       and any('Unchanged child in_ready independent' in row
                               for row in side.get('checks', [])))
        receipt_ok = (summary.get('schema') == 'v106-ingress-probe-selection-v1'
                      and summary.get('status') == 'PASS_ACTUAL_INGRESS_CACHE_EQUIVALENCE'
                      and summary.get('sha256') == sha(receipt_bytes)
                      and receipt.get('schema') == 'v106-ingress-clocked-production-comparison-v1'
                      and receipt.get('status') == 'PASS_ACTUAL_INGRESS_CACHE_EQUIVALENCE'
                      and receipt.get('baseline_revision') == BASELINE
                      and receipt.get('actual_RTL_run') is True
                      and receipt.get('frozen_after_focused_PASS') is True
                      and receipt.get('assertions_disabled_or_downgraded') is False
                      and receipt.get('complete_production_bodies_preserved_by_module_rename_and_type_substitution') is True
                      and receipt.get('historical_bench_only_renames_and_pre_post_hooks') is True
                      and receipt.get('candidate', {}).get('path') == INGRESS_SYNC_CANDIDATE
                      and receipt.get('candidate', {}).get('sha256') == sha(read(INGRESS_SYNC_CANDIDATE))
                      and receipt.get('candidate', {}).get('recipe_sha256')
                          == sha(read('fpga/experiments/cu66-v106-ingress/edit-recipe.json'))
                      and receipt.get('fixtures', {}).get('cases') == 20
                      and receipt.get('fixtures', {}).get('sha256')
                          == sha(read('experiments/python-gamebub-v91e/vectors/coefficients.jsonl.gz'))
                      and receipt.get('total_clock_edges') == 15988562
                      and sum(row.get('prepared_edges', 0) + row.get('historical_edges', 0) for row in runs)
                          == receipt.get('total_clock_edges')
                      and all(row.get('exit_code') == 0 for row in receipt.get('commands', []))
                      and runs_ok and strict and not artifacts and not sources)
        check('focused_ingress_receipt_and_independent_trace_audit', receipt_ok and side_ok is True,
              {'summary': summary_path, 'selected_receipt': selected, 'receipt_status': receipt.get('status'),
               'runs_pass': runs_ok, 'strict_compile': strict, 'source_mismatches': sources,
               'artifact_mismatches': artifacts, 'independent_sidecar': side_ok,
               'inactive_private_scope': 'ctx_bits/ctx_last are unqualified outside CONTEXT_RUN; public and parent/child outputs compare every clock'})
    except Exception as exc:
        check('focused_ingress_receipt_and_independent_trace_audit', False, {'error': str(exc)})

def audit_prefix_focused() -> None:
    summary_path = 'experiments/python-gamebub-v106/prefix/probe-results.json'
    if not (ROOT / summary_path).is_file():
        need('focused_prefix_receipt_and_independent_evidence_audit', {'expected': summary_path})
        return
    try:
        summary = read_json(summary_path)
        selected = summary.get('selected_receipt')
        if not selected or not (ROOT / selected).is_file():
            need('focused_prefix_selected_receipt', {'summary': summary_path, 'selected_receipt': selected})
            return
        receipt_bytes = read(selected)
        receipt = json.loads(receipt_bytes)
        ad = (ROOT / selected).parent
        artifacts = verify_artifacts(receipt, ad)
        sources = verify_source_map(receipt.get('source_sha256', {}))
        compile_rows = [c for c in receipt.get('commands', []) if '--build' in c.get('argv', []) and '--cc' in c.get('argv', [])]
        strict = (len(compile_rows) == 1 and compile_rows[0].get('exit_code') == 0
                  and '--assert' in compile_rows[0].get('argv', []) and '-Wall' in compile_rows[0].get('argv', [])
                  and '-Werror' in ' '.join(compile_rows[0].get('argv', []))
                  and b'%Warning-' not in compile_log_path(ad, compile_rows[0]).read_bytes())
        runs = receipt.get('runs', [])
        runs_ok = (len(runs) == 2 and [r.get('seed') for r in runs] == [106401, 106402]
                   and all(r.get('status') == 'TEST_PASS' and r.get('prepared_clocks') == 598577
                           and r.get('prefix_rank_pattern_window_cases') == 524288
                           and r.get('prefix_available_corner_cases') == 8320
                           and r.get('historical_verdict', {}).get('status') == 'TEST_PASS'
                           and r.get('historical_verdict', {}).get('cases') == 1520
                           and r.get('historical_verdict', {}).get('configurations') == 8
                           and r.get('historical_verdict', {}).get('directed_checks') == 104 for r in runs))
        commands_ok = bool(receipt.get('commands')) and all(c.get('exit_code') == 0 for c in receipt.get('commands', []))
        receipt_ok = (summary.get('schema') == 'v106-prefix-probe-selection-v1'
                      and summary.get('status') == 'PASS_ACTUAL_PREFIX_EQUIVALENCE'
                      and summary.get('sha256') == sha(receipt_bytes)
                      and receipt.get('schema') == 'v106-prefix-clocked-probe-v1'
                      and receipt.get('status') == 'PASS_ACTUAL_PREFIX_EQUIVALENCE'
                      and receipt.get('baseline') == BASELINE
                      and receipt.get('original') == {'path': RICE_CANDIDATE, 'sha256': sha(read(RICE_CANDIDATE))}
                      and receipt.get('candidate') == {'path': PREFIX_CANDIDATE, 'sha256': sha(read(PREFIX_CANDIDATE))}
                      and receipt.get('historical_vector_cases') == 1520
                      and receipt.get('historical_requests_per_configuration') == 173061
                      and receipt.get('port_names') == 27 and receipt.get('output_names') == 13
                      and receipt.get('total_clock_edges') == 18497061
                      and runs_ok and strict and commands_ok and not artifacts and not sources)
        side_path = 'experiments/python-gamebub-v106/prefix/trace-audit.json'
        if not (ROOT / side_path).is_file():
            need('focused_prefix_independent_evidence_audit', {'expected': side_path, 'selected_receipt': selected})
            side_ok: bool | str = 'PENDING'
        else:
            side = read_json(side_path)
            auditor = side.get('auditor', {})
            side_runs = side.get('runs', [])
            side_ok = (side.get('receipt') == selected and side.get('receipt_sha256') == sha(receipt_bytes)
                       and auditor.get('path') and sha(read(auditor['path'])) == auditor.get('sha256')
                       and side.get('schema') == 'v106-prefix-evidence-audit-v1'
                       and side.get('status') == 'PASS_PREFIX_MODEL_ADAPTERS_AND_CHECKPOINTS'
                       and len(side.get('checks', [])) == 4
                       and all(row.get('status') == 'PASS' for row in side.get('checks', []))
                       and side.get('inherited_cache_algebra', {}).get('status') == 'PASS_EXACT_AFFINE_RING_IDENTITIES'
                       and side.get('inherited_cache_algebra', {}).get('supplementary_numeric_cases') == 102197
                       and side.get('rank_model', {}).get('status') == 'PASS_EXHAUSTIVE_RANK_WINDOW_AND_AVAILABLE_MODEL'
                       and side.get('rank_model', {}).get('all15bit_patterns') == 32768
                       and side.get('rank_model', {}).get('all_windows') == 16
                       and side.get('rank_model', {}).get('serial_modes') == 2
                       and side.get('rank_model', {}).get('pattern_window_mode_comparisons') == 1048576
                       and side.get('rank_model', {}).get('availability_corner_mode_comparisons') == 16640
                       and side.get('rank_model', {}).get('random_full64_reservoir_cases') == 100000
                       and side.get('rank_model', {}).get('historical_reference', {}).get('sha256') == '5115b5e15f6fd149dfae14e0389cd51b8cafd13f315be3e1be7955183062b20d'
                       and [r.get('seed') for r in side_runs] == [106401, 106402]
                       and all(r.get('status') == 'PASS' and r.get('configurations') == 8
                               and r.get('directed_checks') == 104
                               and r.get('actual_every_clock_oracle_edges') > 9_200_000
                               and r.get('prepared_complete_trace_records') == 598577
                               and r.get('historical_sampled_checkpoint_records') > 45000 for r in side_runs)
                       and [r.get('trace_sha256') for r in side_runs]
                           == [receipt.get('artifacts_sha256', {}).get(f'seed-{seed}.jsonl.gz')
                               for seed in (106401, 106402)])
        pretool_notes = sorted((ROOT / 'experiments/python-gamebub-v106/prefix/attempts').glob('*/failure-note.json'))
        pretool_rows = []
        for note_path in pretool_notes:
            note = read(str(note_path.relative_to(ROOT)))
            row = json.loads(note)
            attempt_receipt = read_json(str(note_path.with_name('receipt.json').relative_to(ROOT)))
            pretool_rows.append({'path': str(note_path.relative_to(ROOT)),
                                 'status': row.get('status'), 'commands_started': row.get('commands_started'),
                                 'receipt_commands': len(attempt_receipt.get('commands', []))})
        pretool_ok = bool(pretool_rows) and all(row['status'] == 'PRE_TOOL_RESOURCE_GATE_DENIAL'
                                                and row['commands_started'] == 0
                                                and row['receipt_commands'] == 0 for row in pretool_rows)
        check('prefix_pretool_resource_gate_denial_retained_without_execution', pretool_ok,
              {'attempts': pretool_rows})
        check('focused_prefix_receipt_and_independent_evidence_audit', receipt_ok and side_ok is True,
              {'summary': summary_path, 'selected_receipt': selected, 'receipt_status': receipt.get('status'),
               'strict_compile': strict, 'runs_pass': runs_ok, 'source_mismatches': sources,
               'artifact_mismatches': artifacts, 'independent_sidecar': side_ok})
    except Exception as exc:
        check('focused_prefix_receipt_and_independent_evidence_audit', False, {'error': str(exc)})

def audit_rice_focused() -> None:
    summary_path = 'experiments/python-gamebub-v106/rice/probe-results.json'
    if not (ROOT / summary_path).is_file():
        need('focused_rice_receipt_and_independent_evidence_audit', {'expected': summary_path})
        return
    try:
        summary = read_json(summary_path)
        selected = summary.get('selected_receipt')
        if not selected or not (ROOT / selected).is_file():
            need('focused_rice_selected_receipt', {'summary': summary_path, 'selected_receipt': selected})
            return
        receipt_bytes = read(selected)
        receipt = json.loads(receipt_bytes)
        ad = (ROOT / selected).parent
        artifacts = verify_artifacts(receipt, ad)
        sources = verify_source_map(receipt.get('source_sha256', {}))
        compile_rows = [c for c in receipt.get('commands', []) if '--build' in c.get('argv', []) and '--cc' in c.get('argv', [])]
        strict = (len(compile_rows) == 1 and compile_rows[0].get('exit_code') == 0
                  and '--assert' in compile_rows[0].get('argv', []) and '-Wall' in compile_rows[0].get('argv', [])
                  and '-Werror' in ' '.join(compile_rows[0].get('argv', []))
                  and b'%Warning-' not in compile_log_path(ad, compile_rows[0]).read_bytes())
        runs = receipt.get('runs', [])
        runs_ok = (len(runs) == 2 and [r.get('seed') for r in runs] == [106401, 106402]
                   and all(r.get('status') == 'TEST_PASS' and r.get('prepared_clocks') == 65969
                           and r.get('historical_verdict', {}).get('cases') == 1520
                           and r.get('historical_verdict', {}).get('status') == 'TEST_PASS'
                           and r.get('historical_verdict', {}).get('configurations') == 8
                           and r.get('historical_verdict', {}).get('requests_per_configuration') == 173061
                           and r.get('historical_verdict', {}).get('directed_checks') == 104 for r in runs))
        commands_ok = bool(receipt.get('commands')) and all(c.get('exit_code') == 0 for c in receipt.get('commands', []))
        receipt_ok = (summary.get('schema') == 'v106-rice-probe-selection-v1'
                      and summary.get('status') == 'PASS_ACTUAL_RICE_CACHE_EQUIVALENCE'
                      and summary.get('sha256') == sha(receipt_bytes)
                      and receipt.get('schema') == 'v106-rice-clocked-probe-v1'
                      and receipt.get('status') == 'PASS_ACTUAL_RICE_CACHE_EQUIVALENCE'
                      and receipt.get('baseline') == BASELINE
                      and receipt.get('original') == {'path': RICE_ORIGINAL,
                          'sha256': hashlib.sha256(git_blob(BASELINE, RICE_ORIGINAL) or b'').hexdigest()}
                      and receipt.get('candidate') == {'path': RICE_CANDIDATE, 'sha256': sha(read(RICE_CANDIDATE))}
                      and receipt.get('historical_vector_cases') == 1520
                      and receipt.get('historical_requests_per_configuration') == 173061
                      and receipt.get('port_names') == 27 and receipt.get('output_names') == 13
                      and receipt.get('total_clock_edges') == 17431845
                      and runs_ok and strict and commands_ok and not artifacts and not sources)
        side_path = 'experiments/python-gamebub-v106/rice/trace-audit.json'
        if not (ROOT / side_path).is_file():
            need('focused_rice_independent_evidence_audit', {'expected': side_path, 'selected_receipt': selected})
            side_ok: bool | str = 'PENDING'
        else:
            side = read_json(side_path)
            auditor = side.get('auditor', {})
            side_runs = side.get('runs', [])
            side_ok = (side.get('schema') == 'v106-rice-cache-evidence-audit-v1'
                       and side.get('status') == 'PASS_RICE_CACHE_ALGEBRA_ADAPTERS_AND_CHECKPOINTS'
                       and side.get('receipt') == selected and side.get('receipt_sha256') == sha(receipt_bytes)
                       and auditor.get('path') and sha(read(auditor['path'])) == auditor.get('sha256')
                       and len(side.get('checks', [])) == 4
                       and all(row.get('status') == 'PASS' for row in side.get('checks', []))
                       and side.get('algebra', {}).get('status') == 'PASS_EXACT_AFFINE_RING_IDENTITIES'
                       and side.get('algebra', {}).get('supplementary_numeric_cases') == 102197
                       and side.get('algebra', {}).get('numeric_wrap_cases') == 50810
                       and [r.get('seed') for r in side_runs] == [106401, 106402]
                       and all(r.get('status') == 'PASS' and r.get('configurations') == 8
                               and r.get('directed_checks') == 104 and r.get('actual_every_clock_oracle_edges') > 8_700_000
                               and r.get('prepared_complete_trace_records') == 65969
                               and r.get('historical_sampled_checkpoint_records') > 45_000
                               for r in side_runs)
                       and [r.get('trace_sha256') for r in side_runs]
                           == [receipt.get('artifacts_sha256', {}).get(f'seed-{seed}.jsonl.gz')
                               for seed in (106401, 106402)])
        check('focused_rice_receipt_and_independent_evidence_audit', receipt_ok and side_ok is True,
              {'summary': summary_path, 'selected_receipt': selected, 'receipt_status': receipt.get('status'),
               'strict_compile': strict, 'runs_pass': runs_ok, 'source_mismatches': sources,
               'artifact_mismatches': artifacts, 'independent_sidecar': side_ok})
    except Exception as exc:
        check('focused_rice_receipt_and_independent_evidence_audit', False, {'error': str(exc)})

def audit_telemetry_focused() -> None:
    summary_path = 'experiments/python-gamebub-v106/telemetry/results.json'
    if not (ROOT / summary_path).is_file():
        need('focused_telemetry_receipt_and_independent_trace_audit', {'expected': summary_path})
        return
    try:
        summary = read_json(summary_path)
        selected = summary.get('selected_report')
        if not selected or not (ROOT / selected).is_file():
            need('focused_telemetry_selected_receipt', {'summary': summary_path, 'selected_report': selected})
            return
        receipt = read_json(selected)
        ad = (ROOT / selected).parent
        artifacts = verify_artifacts(receipt, ad)
        sources = verify_source_map(receipt.get('source_sha256', {}))
        compile_rows = [c for c in receipt.get('commands', []) if '--build' in c.get('argv', []) and '--cc' in c.get('argv', [])]
        strict = (len(compile_rows) == 1 and compile_rows[0].get('exit_code') == 0
                  and '--assert' in compile_rows[0].get('argv', []) and '-Wall' in compile_rows[0].get('argv', [])
                  and '-Werror' in ' '.join(compile_rows[0].get('argv', []))
                  and receipt.get('strict_warnings') is True
                  and b'%Warning-' not in compile_log_path(ad, compile_rows[0]).read_bytes())
        commands_ok = bool(receipt.get('commands')) and all(c.get('exit_code') == 0 for c in receipt.get('commands', []))
        historical = receipt.get('historical_verdict', {})
        terminal = receipt.get('terminal_verdict', {})
        fixtures = receipt.get('fixtures', {})
        wrappers = []
        for kind in ('original', 'candidate'):
            wrapper = read(f'fpga/experiments/cu66-v106-telemetry/telemetry_{kind}.sv')
            normalized = wrapper.replace(f'module telemetry_{kind} #('.encode(),
                                         b'module br88_pipeline_v91h #(', 1)
            production = read(TELEMETRY_ORIGINAL if kind == 'original' else TELEMETRY_CANDIDATE)
            wrappers.append({'kind': kind, 'exact_module_rename_only': normalized == production})
        wrappers_ok = len(wrappers) == 2 and all(row['exact_module_rename_only'] for row in wrappers)
        receipt_ok = (summary.get('schema') == 'v106-telemetry-clocked-production-comparison-v1'
                      and summary.get('status') == 'PASS' and summary.get('baseline_revision') == BASELINE
                      and summary.get('frozen_after_focused_PASS') is True
                      and receipt.get('schema') == 'v106-telemetry-clocked-production-comparison-v1'
                      and receipt.get('status') == 'PASS' and receipt.get('baseline_revision') == BASELINE
                      and receipt.get('actual_RTL_run') is True
                      and receipt.get('frozen_after_focused_PASS') is True
                      and receipt.get('assertions_disabled_or_downgraded') is False
                      and receipt.get('complete_production_bodies_preserved_by_module_rename') is True
                      and receipt.get('historical_bench_only_renames_and_pre_post_hooks') is True
                      and receipt.get('candidate', {}).get('path') == TELEMETRY_CANDIDATE
                      and receipt.get('candidate', {}).get('sha256') == sha(read(TELEMETRY_CANDIDATE))
                      and receipt.get('candidate', {}).get('recipe_sha256') == sha(read('fpga/experiments/cu66-v106-telemetry/edit-recipe.json'))
                      and fixtures.get('cases') == 20
                      and fixtures.get('sha256') == sha(read('experiments/python-gamebub-v91e/vectors/coefficients.jsonl.gz'))
                      and historical.get('status') == 'TEST_PASS' and historical.get('packets') == 20
                      and historical.get('case_rows') == 40 and historical.get('configurations') == 2
                      and historical.get('directed_checks') == 56
                      and historical.get('sync_staging_checks') == 9
                      and historical.get('dense_comparisons') == 4501888
                      and terminal.get('status') == 'TEST_PASS' and terminal.get('counter_words') == 52
                      and terminal.get('carry_positions') == 64 and terminal.get('guard_running_combinations') == 16
                      and terminal.get('prepared_cases') == 53248 and terminal.get('prepared_edges') == 106497
                      and terminal.get('historical_edges') == 7982233
                      and terminal.get('prepared_trace_rows') == 106497
                      and terminal.get('historical_trace_rows') == 31404
                      and terminal.get('prepared_edges', 0) + terminal.get('historical_edges', 0) == 8088730
                      and receipt.get('trace_replay', {}).get('status') == 'PASS'
                      and receipt.get('trace_replay', {}).get('prepared_cases') == 53248
                      and receipt.get('trace_replay', {}).get('prepared_clocks') == 106497
                      and receipt.get('trace_replay', {}).get('historical_checkpoints') == 31404
                      and receipt.get('trace_replay', {}).get('raw_sha256') == receipt.get('raw_trace_sha256')
                      and wrappers_ok and strict and commands_ok and not artifacts and not sources)
        side_path = 'experiments/python-gamebub-v106/telemetry/trace-audit.json'
        if not (ROOT / side_path).is_file():
            need('focused_telemetry_independent_trace_audit', {'expected': side_path, 'selected_receipt': selected})
            side_ok: bool | str = 'PENDING'
        else:
            side = read_json(side_path)
            side_auditor = side.get('auditor', {})
            side_ok = (side.get('status') == 'PASS' and side_auditor.get('path')
                       and sha(read(side_auditor['path'])) == side_auditor.get('sha256')
                       and side.get('selected_receipt', {}).get('path') == selected
                       and side.get('selected_receipt', {}).get('sha256') == sha(read(selected))
                       and side.get('selected_summary', {}).get('path') == summary_path
                       and side.get('selected_summary', {}).get('sha256') == sha(read(summary_path))
                       and side.get('candidate', {}).get('path') == TELEMETRY_CANDIDATE
                       and side.get('candidate', {}).get('sha256') == sha(read(TELEMETRY_CANDIDATE))
                       and side.get('prepared_edges') == 106497
                       and side.get('counter_words') == 52 and side.get('carry_positions') == 64
                       and side.get('guard_running_combinations') == 16
                       and side.get('historical_edges') == 7982233
                       and side.get('historical_checkpoints') == 31404
                       and side.get('historical_packets') == 20 and side.get('historical_profiles') == 2
                       and side.get('dense_comparisons') == 4501888
                       and side.get('directed_checks') == 56 and side.get('sync_staging_checks') == 9
                       and side.get('raw_trace_sha256') == receipt.get('raw_trace_sha256')
                       and side.get('trace_sha256') == receipt.get('artifacts_sha256', {}).get('trace.jsonl.gz'))
        check('focused_telemetry_receipt_and_independent_trace_audit', receipt_ok and side_ok is True,
              {'summary': summary_path, 'selected_receipt': selected, 'status': receipt.get('status'),
               'strict_compile': strict, 'commands_pass': commands_ok, 'wrappers_exact': wrappers_ok,
               'source_mismatches': sources, 'artifact_mismatches': artifacts,
               'independent_sidecar': side_ok})
    except Exception as exc:
        check('focused_telemetry_receipt_and_independent_trace_audit', False, {'error': str(exc)})

def audit_composition(math_data: dict[str, Any], locality: dict[str, Any]) -> dict[str, Any]:
    if not math_data or not locality:
        need('math_storage_composition_both_orders', {'reason': 'exact component recipes must pass first'})
        return {}
    try:
        lut_inverse_path = f'{MATH_ROOT}/lut/cu66_inverse_stream_v91j.recipe.json'
        math_recipe = read_json(lut_inverse_path)
        storage_recipe = locality['recipe']
        original_path = math_recipe['original_path']
        original_bytes = read(original_path)
        math_first, _ = apply_recipe(original_bytes, math_recipe)
        math_then_storage, _ = apply_recipe(math_first, storage_recipe)
        storage_first, _ = apply_recipe(original_bytes, storage_recipe)
        storage_then_math, _ = apply_recipe(storage_first, math_recipe)
        orders_equal = math_then_storage == storage_then_math
        check('math_storage_recipes_commute_both_orders', orders_equal,
              {'math_then_storage_sha256': sha(math_then_storage),
               'storage_then_math_sha256': sha(storage_then_math), 'byte_identical': orders_equal})
        if not (ROOT / COMPOSITION).is_file():
            need('emitted_lut_storage_source_matches_both_orders', {'expected_proof': COMPOSITION,
                                                                   'expected_sha256': sha(math_then_storage)})
        else:
            proof = read_json(COMPOSITION)
            composed = read(COMPOSED_LUT_STORAGE)
            orders = {tuple(row.get('order', [])): row.get('sha256') for row in proof.get('orders', [])}
            proof_ok = (proof.get('schema') == 'v106-both-order-composition-v1'
                        and proof.get('status') == 'PASS' and proof.get('both_orders_identical') is True
                        and proof.get('module_header_byte_identical') is True
                        and proof.get('candidate') == COMPOSED_LUT_STORAGE
                        and proof.get('candidate_sha256') == sha(composed)
                        and orders.get(('math', 'storage')) == sha(math_then_storage)
                        and orders.get(('storage', 'math')) == sha(storage_then_math)
                        and composed == math_then_storage)
            check('emitted_lut_storage_source_matches_both_orders', proof_ok,
                  {'proof': COMPOSITION, 'candidate': COMPOSED_LUT_STORAGE,
                   'candidate_sha256': sha(composed), 'independent_sha256': sha(math_then_storage),
                   'order_hashes': {str(k): v for k, v in orders.items()}})
        return {'sha256': sha(math_then_storage), 'both_orders_identical': orders_equal,
                'candidate': COMPOSED_LUT_STORAGE}
    except Exception as exc:
        check('math_storage_recipes_commute_both_orders', False, {'error': str(exc)})
        return {}

def audit_locality_focused() -> None:
    if not (ROOT / LOCALITY_SUMMARY).is_file():
        need('focused_locality_receipt_and_independent_trace_audit', {'expected': LOCALITY_SUMMARY})
        return
    try:
        summary = read_json(LOCALITY_SUMMARY)
        selected = summary.get('selected_receipt')
        if not selected or not (ROOT / selected).is_file():
            need('focused_locality_selected_receipt', {'summary': LOCALITY_SUMMARY, 'selected': selected})
            return
        receipt_bytes = read(selected)
        receipt = json.loads(receipt_bytes)
        attempt_dir = (ROOT / selected).parent
        artifact_errors = verify_artifacts(receipt, attempt_dir)
        source_errors = verify_source_map(receipt.get('source_sha256', {}))
        compile_rows = [c for c in receipt.get('commands', []) if '--build' in c.get('argv', []) and '--cc' in c.get('argv', [])]
        strict = (len(compile_rows) == 1 and compile_rows[0].get('exit_code') == 0
                  and '--assert' in compile_rows[0].get('argv', []) and '-Wall' in compile_rows[0].get('argv', [])
                  and '-Werror' in ' '.join(compile_rows[0].get('argv', []))
                  and b'%Warning-' not in compile_log_path(attempt_dir, compile_rows[0]).read_bytes())
        runs = receipt.get('runs', [])
        run_ok = (len(runs) == 2 and [row.get('seed') for row in runs] == [106401, 106402]
                  and all(row.get('status') == 'TEST_PASS' and row.get('word_count') == 128
                          and row.get('prepared_clocks') == 9365 and row.get('guarded_clocks') == 897
                          and row.get('late_same_edge_write_fail_cases') == 2 for row in runs))
        receipt_ok = (summary.get('schema') == 'v106-locality-probe-selection-v1'
                      and summary.get('status') == 'PASS_ACTUAL_INVERSE_STORAGE_EQUIVALENCE'
                      and sha(receipt_bytes) == summary.get('sha256')
                      and receipt.get('schema') == 'v106-locality-clocked-probe-v1'
                      and receipt.get('baseline') == BASELINE
                      and receipt.get('status') == 'PASS_ACTUAL_INVERSE_STORAGE_EQUIVALENCE'
                      and receipt.get('original') == {'path': INVERSE,
                          'sha256': hashlib.sha256(git_blob(BASELINE, INVERSE) or b'').hexdigest()}
                      and receipt.get('candidate') == {'path': LOCALITY_CANDIDATE,
                          'sha256': sha(read(LOCALITY_CANDIDATE))}
                      and receipt.get('port_names') == 58 and receipt.get('output_names') == 42
                      and receipt.get('total_clock_edges') == sum(r.get('prepared_clocks', 0) + r.get('historical_clocks', 0) for r in runs)
                      and run_ok and strict and not artifact_errors and not source_errors)
        side_path = 'experiments/python-gamebub-v106/locality/trace-audit.json'
        if not (ROOT / side_path).is_file():
            need('focused_locality_independent_trace_audit', {'expected': side_path, 'selected_receipt': selected})
            side_ok: bool | str = 'PENDING'
        else:
            side = read_json(side_path)
            aud = side.get('auditor', {})
            side_ok = (side.get('schema') == 'v106-storage-independent-replay-v1'
                       and side.get('status') == 'PASS_STORAGE_TRACE_AND_ADAPTER_AUDIT'
                       and side.get('receipt') == selected and side.get('receipt_sha256') == sha(receipt_bytes)
                       and aud.get('path') and sha(read(aud['path'])) == aud.get('sha256')
                       and len(side.get('checks', [])) == 4
                       and all(row.get('status') == 'PASS' for row in side.get('checks', []))
                       and [row.get('seed') for row in side.get('runs', [])] == [106401, 106402]
                       and all(row.get('status') == 'PASS' and row.get('coefficient_words_checked_per_clock') == 128
                               and row.get('unique_written_words') == 128 for row in side.get('runs', []))
                       and [row.get('trace_sha256') for row in side.get('runs', [])]
                           == [receipt.get('artifacts_sha256', {}).get(f"seed-{seed}.jsonl.gz")
                               for seed in (106401, 106402)])
        check('focused_locality_receipt_and_independent_trace_audit', receipt_ok and side_ok is True,
              {'summary': LOCALITY_SUMMARY, 'selected_receipt': selected, 'receipt_status': receipt.get('status'),
               'run_contract': run_ok, 'strict_compile': strict, 'source_errors': source_errors,
               'artifact_errors': artifact_errors, 'independent_sidecar': side_ok})
    except Exception as exc:
        check('focused_locality_receipt_and_independent_trace_audit', False, {'error': str(exc)})

def audit_lanes() -> None:
    for lane, (variant, mode, cases, directed) in LANES.items():
        summary_path = f'experiments/python-gamebub-v106/regression/{variant}/{mode}/results.json'
        if not (ROOT / summary_path).is_file():
            need(f'lane_{lane}_paired_exact_receipt', {'expected': summary_path, 'case_profile_runs': cases,
                                                       'directed_checks': directed, 'seeds': [106401, 106402]})
            continue
        try:
            summary = read_json(summary_path)
            selected = summary.get('selected_report')
            if not selected or not (ROOT / selected).is_file():
                need(f'lane_{lane}_selected_attempt', {'summary': summary_path, 'selected_report': selected})
                continue
            attempt = read_json(selected)
            ad = (ROOT / selected).parent
            bad_art = verify_artifacts(attempt, ad)
            bad_src = verify_source_map(attempt.get('source_sha256', {}))
            expected = expected_candidates(variant)
            candidate_rows = {row.get('original'): row.get('path') for row in attempt.get('candidates', [])}
            candidate_ok = candidate_rows == expected
            for row in attempt.get('candidates', []):
                path = row.get('path')
                if not path or attempt.get('source_sha256', {}).get(path) != row.get('sha256'):
                    candidate_ok = False
            runs = attempt.get('runs', [])
            seeds = [row.get('seed') for row in runs]
            equal = seeds == [106401, 106402]
            verdicts = []
            for row in runs:
                seed = row.get('seed')
                eq = row.get('equalities', {})
                equal &= eq.get('stdout') is True and eq.get('events') is True
                if mode == 'canonical':
                    equal &= eq.get('canonical') is True
                for suffix in ('simulation.jsonl',):
                    paths = [ad / f'{side}-{seed}-{suffix}' for side in ('baseline', 'candidate')]
                    try:
                        left, right = (p.read_bytes() for p in paths)
                        record(str(paths[0].relative_to(ROOT)), left)
                        record(str(paths[1].relative_to(ROOT)), right)
                        equal &= left == right
                    except Exception:
                        equal = False
                fields = ['events'] + (['canonical_actual'] if mode == 'canonical' else [])
                for field in fields:
                    packed = {}
                    for side in ('baseline', 'candidate'):
                        meta = row.get('variants', {}).get(side, {}).get(field)
                        if not meta:
                            equal = False
                            continue
                        path = ad / meta.get('path', '')
                        try:
                            zipped = path.read_bytes()
                            raw = gzip.decompress(zipped)
                            record(str(path.relative_to(ROOT)), zipped)
                            packed[side] = (zipped, raw)
                            equal &= sha(zipped) == meta.get('sha256') and sha(raw) == meta.get('raw_sha256')
                        except Exception:
                            equal = False
                    if len(packed) == 2:
                        equal &= packed['baseline'] == packed['candidate']
                for side in ('baseline', 'candidate'):
                    verdict = row.get('variants', {}).get(side, {}).get('verdict', {})
                    verdicts.append({'seed': seed, 'side': side, 'status': verdict.get('status'),
                                     'cases': verdict.get('cases'), 'directed_checks': verdict.get('directed_checks')})
                    equal &= (verdict.get('status') == 'TEST_PASS'
                              and verdict.get('cases') == (6 if mode == 'fresh' else 22)
                              and verdict.get('directed_checks') == (13 if mode == 'fresh' else 21))
            compile_rows = [c for c in attempt.get('commands', []) if '--cc' in c.get('argv', []) and '--build' in c.get('argv', [])]
            strict = (len(compile_rows) == 2 and all(c.get('exit_code') == 0 and '--assert' in c.get('argv', [])
                      and '-Wall' in c.get('argv', []) and '-Werror' in ' '.join(c.get('argv', [])) for c in compile_rows)
                      and attempt.get('assertions_disabled_or_downgraded') is False)
            for command in compile_rows:
                log = ad / command.get('log', '')
                try:
                    data = log.read_bytes()
                    record(str(log.relative_to(ROOT)), data)
                    if b'%Warning-' in data:
                        strict = False
                except Exception:
                    strict = False
            ok = (summary.get('status') == 'PASS' and attempt.get('schema') == 'v106-paired-regression-v1'
                  and attempt.get('status') == 'PASS' and attempt.get('baseline_revision') == BASELINE
                  and attempt.get('baseline_overrides') == BASELINE_OVERRIDES
                  and attempt.get('variant') == variant and attempt.get('mode') == mode
                  and attempt.get('case_profile_runs') == cases and attempt.get('directed_checks') == directed
                  and attempt.get('actual_RTL_run') is True and attempt.get('exact_same_seed_transcripts_events_cycles') is True
                  and seeds == [106401, 106402] and equal and strict and candidate_ok
                  and not bad_art and not bad_src)
            check(f'lane_{lane}_paired_exact_receipt', ok,
                  {'summary': summary_path, 'selected_attempt': selected,
                   'case_profile_runs': attempt.get('case_profile_runs'), 'directed_checks': attempt.get('directed_checks'),
                   'seeds': seeds, 'paired_equalities': equal, 'terminal_verdicts': verdicts,
                   'strict_compile': strict, 'candidate_source_map': candidate_rows,
                   'expected_candidate_source_map': expected, 'candidate_map_matches': candidate_ok,
                   'source_mismatches': bad_src, 'artifact_mismatches': bad_art})
        except Exception as exc:
            check(f'lane_{lane}_paired_exact_receipt', False, {'error': str(exc)})

def audit_rejected_pipeline_fifth_pair() -> None:
    """Keep the strict-lint rejection and unrun canonical lane visible as failure history."""
    variant = 'guarded-suffix-idct-cache'
    fresh_summary_path = f'experiments/python-gamebub-v106/regression/{variant}/fresh/results.json'
    canonical_summary_path = f'experiments/python-gamebub-v106/regression/{variant}/canonical/results.json'
    preflight_path = 'experiments/python-gamebub-v106/preflight-failures/pipeline-import.json'
    try:
        if not (ROOT / fresh_summary_path).is_file():
            need('rejected_pipeline_fifth_fresh_strict_lint_failure_retained', {'expected': fresh_summary_path})
            return
        summary = read_json(fresh_summary_path)
        selected = summary.get('selected_report')
        if not selected or not (ROOT / selected).is_file():
            need('rejected_pipeline_fifth_fresh_failure_attempt', {'summary': fresh_summary_path,
                                                                    'selected_report': selected})
            return
        attempt = read_json(selected)
        ad = (ROOT / selected).parent
        candidate_rows = {row.get('original'): row.get('path') for row in attempt.get('candidates', [])}
        candidate_ok = candidate_rows == expected_candidates(variant)
        source_errors = verify_source_map(attempt.get('source_sha256', {}))
        artifacts = verify_artifacts(attempt, ad)
        compile_row = next((row for row in attempt.get('commands', [])
                            if row.get('log') == 'compile-candidate.log'), None)
        compile_bytes = (ad / 'compile-candidate.log').read_bytes() if (ad / 'compile-candidate.log').is_file() else b''
        warning_is_real = (b'%Warning-UNUSEDSIGNAL' in compile_bytes
                           and b"suffix_extracted'[63:24]" in compile_bytes
                           and b'%Error: Exiting due to 1 warning(s)' in compile_bytes)
        canonical_unrun = not (ROOT / canonical_summary_path).exists()
        failed_as_expected = (summary.get('status') == 'FAIL' and summary.get('selected_report') == selected
                              and attempt.get('status') == 'FAIL' and attempt.get('variant') == variant
                              and attempt.get('mode') == 'fresh' and attempt.get('actual_RTL_run') is False
                              and attempt.get('error') == 'command failed compile-candidate.log'
                              and compile_row is not None and compile_row.get('exit_code') != 0
                              and not attempt.get('runs') and warning_is_real and canonical_unrun
                              and candidate_ok and not source_errors and not artifacts)
        check('rejected_pipeline_fifth_fresh_strict_lint_failure_retained', failed_as_expected,
              {'status': attempt.get('status'), 'selected_attempt': selected,
               'compile_candidate_exit_code': compile_row.get('exit_code') if compile_row else None,
               'unused_suffix_high_bits_warning_preserved': warning_is_real,
               'candidate_map_matches_rejected_variant': candidate_ok,
               'source_mismatches': source_errors, 'artifact_mismatches': artifacts,
               'canonical_status': 'UNRUN' if canonical_unrun else 'unexpected result exists',
               'policy': 'rejected lane is preserved as failure evidence and excluded from required paired lanes'})
        if not (ROOT / preflight_path).is_file():
            need('pipeline_import_preflight_failure_preserved', {'expected': preflight_path})
        else:
            failure = read_json(preflight_path)
            snapshot = failure.get('source_snapshot')
            snapshot_ok = bool(snapshot and (ROOT / snapshot).is_file()
                               and sha(read(snapshot)) == failure.get('source_sha256'))
            preflight_ok = (failure.get('status') == 'PRE_TOOL_ORCHESTRATION_IMPORT_FAILURE'
                            and failure.get('error') == "NameError: name '_final_spec' is not defined"
                            and failure.get('vendor_or_RTL_tools_started') is False
                            and failure.get('production_RTL_changed') is False and snapshot_ok)
            check('pipeline_import_preflight_failure_preserved', preflight_ok,
                  {'status': failure.get('status'), 'vendor_or_RTL_tools_started': failure.get('vendor_or_RTL_tools_started'),
                   'production_RTL_changed': failure.get('production_RTL_changed'),
                   'source_snapshot_pinned': snapshot_ok})
    except Exception as exc:
        check('rejected_pipeline_fifth_fresh_strict_lint_failure_retained', False, {'error': str(exc)})

def main() -> int:
    audit_baseline()
    math_data = audit_math_recipes()
    locality = audit_locality_recipe()
    composition = audit_composition(math_data, locality)
    plan = audit_plan_recipe()
    context = audit_context_recipe()
    rice = audit_rice_recipe()
    prefix = audit_prefix_recipe()
    suffix = audit_suffix_recipe()
    telemetry = audit_telemetry_recipe()
    producer_cache = audit_producer_cache_model()
    idct = audit_idct_recipe_and_model()
    scratch = audit_scratch_recipe_and_model()
    idct_area = audit_idct_recipe_and_model(area_variant=True)
    suffix24 = audit_suffix24_recipe_and_model()
    ingress = audit_ingress_recipe_and_model()
    audit_idct_area_unit_synthesis()
    audit_campaign_policy()
    audit_plan_focused()
    audit_context_focused()
    audit_rice_focused()
    audit_prefix_focused()
    audit_suffix_focused()
    audit_idct_focused()
    audit_idct_focused(area_variant=True)
    audit_scratch_focused()
    audit_ingress_focused()
    audit_telemetry_focused()
    audit_locality_focused()
    audit_lanes()
    audit_rejected_pipeline_fifth_pair()
    status = 'FAIL' if errors else ('PENDING' if pending else 'PASS_EVIDENCE')
    auditor_path = 'scripts/cu66-v106/audit_sources.py'
    auditor_sha = sha(read(auditor_path))
    output = {'schema': 'v106-source-functional-audit-v1', 'status': status,
              'baseline_revision': BASELINE, 'auditor': {'path': auditor_path, 'sha256': auditor_sha},
              'checks': checks, 'errors': sorted(set(errors)), 'pending': pending,
              'composition': composition, 'candidate_sources': {
                  'math': math_data.get('production', []),
                  'locality': {'path': LOCALITY_CANDIDATE,
                               'sha256': sha(read(LOCALITY_CANDIDATE)) if (ROOT / LOCALITY_CANDIDATE).is_file() else None},
                  'plan': {'path': PLAN_CANDIDATE,
                           'sha256': sha(read(PLAN_CANDIDATE)) if (ROOT / PLAN_CANDIDATE).is_file() else None},
                  'context': {'path': CONTEXT_CANDIDATE,
                              'sha256': sha(read(CONTEXT_CANDIDATE)) if (ROOT / CONTEXT_CANDIDATE).is_file() else None},
                  'rice': {'path': RICE_CANDIDATE,
                           'sha256': sha(read(RICE_CANDIDATE)) if (ROOT / RICE_CANDIDATE).is_file() else None},
                  'prefix': {'path': PREFIX_CANDIDATE,
                             'sha256': sha(read(PREFIX_CANDIDATE)) if (ROOT / PREFIX_CANDIDATE).is_file() else None},
                  'suffix': {'path': SUFFIX_CANDIDATE,
                             'sha256': sha(read(SUFFIX_CANDIDATE)) if (ROOT / SUFFIX_CANDIDATE).is_file() else None},
                  'telemetry': {'path': TELEMETRY_CANDIDATE,
                                'sha256': sha(read(TELEMETRY_CANDIDATE)) if (ROOT / TELEMETRY_CANDIDATE).is_file() else None},
                  'producer_cache': producer_cache.get('products', []),
                  'idct': idct, 'idct_area': idct_area, 'scratch': scratch,
                  'suffix24': suffix24, 'ingress': ingress},
              'matrix': {'lanes': list(LANES), 'lane_count': len(LANES),
                         'case_profile_runs': sum(x[2] for x in LANES.values()),
                         'directed_checks': sum(x[3] for x in LANES.values()),
                         'seeds': [106401, 106402]},
              'input_sha256': dict(sorted(inputs.items())),
              'scope': ('Independent source provenance, exact edit-recipe recovery and composition, focused component evidence, '
                        'and retained paired component-functional matrix. PASS_EVIDENCE is not full formal equivalence, '
                        'hardware timing closure, board service proof, or product qualification.')}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(output, indent=2, sort_keys=True) + '\n')
    lines = ['# V106 source and functional audit', '',
             f'**Status: `{status}`.** This offline auditor checks pinned files and retained evidence; it does not run compilers, simulations, or vendor flows.', '',
             '## Contract', '',
             f'- Baseline `{BASELINE}` and frozen 720×480 profile with a 49,152-byte cap are checked against Git baseline contents.',
             '- The selected V105 geometry admission/reconstruction sources are pinned and used as this study’s inherited starting point.',
             '- Six exact math recipes and the two-edit inverse storage recipe are reconstructed from baseline source bytes.',
             '- Math plus storage recipes are independently applied in both orders and compared with the emitted LUT-storage source.',
             '- Focused math and storage receipts require strict tool flags, pinned artifacts and independent trace replay sidecars.',
             '- The adaptive native policy records measured −5.303 ns synthesis, −7.130 ns routed worst path, twelve Rice paths at −6.531 ns, closure at −4.034 ns, and prefix/telemetry routing at −4.700 ns (synthesis −3.897 ns). Six full-flow attempts are tracked, including the rejected fifth candidate; seven controls are explicitly deferred. The replacement targets Rice suffix, IDCT operand, ingress replay and scratch-position logic.',
             '- The plan scratch-layout edit has its own exact source recipe, clocked production comparison and independent modular trace audit.',
             '- The context byte-divmod edit has its own exact source recipe, recorded exhaustive valid-position and deterministic full-width edge/random checks, and independent trace audit.',
             '- The Rice cache edit has its own exact recipe, whole-module clocked equivalence receipt and independent checkpoint/algebra audit.',
             '- The prefix/telemetry variant layers the balanced prefix window over the tested Rice cache and applies the telemetry counter recipe. The guarded-suffix-IDCT-cache map then adds suffix specialization, actual IDCT operand prefetch and producer-coordinate cache edits.',
             '- The guarded-suffix focused probe scopes its private comparison to SUFFIX and checks all public/common private signals on every clock; its historical offline checkpoints are sampled, while the C++ oracle checks every edge.',
             '- The producer lookup-cache sources have exact recipes over the frozen LUT siblings and an independently replayed finite transition model. This is model and source evidence only; the selected integrated pipeline lanes must exercise both live cache assertions.',
             '- The IDCT operand-prefetch edit is reconstructed over baseline RTL and its separate integer model vectors are hash-checked. Integrated component lanes establish the clocked production comparison.',
             '- The focused IDCT probe compares public cycles and outputs with a complete per-edge product/state oracle; its sidecar independently recomputes all 4,303 integer output goldens.',
             '- The area-prefetch IDCT also has a separately pinned three-way unit-synthesis comparison at 10 ns; the shared source maps 7,772 slice LUTs, 5,129 registers and 17 DSPs with +2.920 ns estimated unit slack. This is unit synthesis evidence only, not whole-top area fit or routed timing.',
             '- The final scratch predecode edit is a nine-step recipe over the measured PLAN candidate, with exhaustive upper-position and finite edge/random source model evidence, plus a clocked production probe. Its new parent-response capture timing depends on real input delays and remains open.',
             '- The synchronous ingress replay cache is reconstructed from baseline source and checked by a universal modulo-32 model plus actual two-seed whole-pipeline clocked probes. Inactive private `ctx_bits`/`ctx_last` outside `CONTEXT_RUN` remain outside its claim.',
             '- The earlier guarded-suffix-IDCT-cache candidate is excluded from required functional lanes after strict production lint failed on unused `suffix_extracted[63:24]`; its canonical attempt remains UNRUN. The exact failed receipt and lint log are verified and preserved. The replacement uses the private 24-bit suffix projection, area-qualified IDCT, ingress cache, and scratch cache.',
             '- The paired matrix checks six initial and six follow-up/closure variants in fresh and canonical modes at seeds 106401 and 106402.',
             '- Missing evidence remains PENDING. `PASS_EVIDENCE` is an evidence audit result, not a timing or hardware signoff.', '', '## Results', '']
    if status == 'PASS_EVIDENCE':
        lines += ['All 24 lanes passed: 1,344 case-profile runs and 1,632 directed checks. Same-seed simulation transcripts and event traces are compared byte-for-byte; canonical lanes also compare canonical output artifacts.', '']
    for row in checks:
        lines.append(f"- `{row['status']}` `{row['name']}`")
    if pending:
        lines += ['', '## Pending evidence', ''] + [f'- {item}' for item in pending]
    if errors:
        lines += ['', '## Audit failures', ''] + [f'- {item}' for item in sorted(set(errors))]
    lines += ['', 'The focused math lane exhaustively checks the listed combinational input space. The context arithmetic lane covers all recorded valid positions, every byte lookup constant, and deterministic full-width edge/random inputs; it does not exhaust all 2^32 positions. The focused storage probe compares actual clocked behavior, prepared internal states, and retained historical boundary/interface tests; prepared states do not establish complete packet reachability. The Rice offline auditor replays complete prepared-phase checkpoints and sampled historical-phase checkpoints; the focused C++ run separately compares all public and private oracle fields each clock. The prefix-window suite exercises every rank/window pattern and crafted available-window edges, plus retained historical traffic. The telemetry offline audit replays every prepared edge and sampled historical checkpoints; the C++ comparator checks the full model each historical edge. This evidence does not establish full formal state-space equivalence, routed timing closure, parent-clock or I/O signoff, hardware 30 fps, board service, or under-10-ms decode qualification. See `experiments/python-gamebub-v106/source-audit.json` for paths, hashes and receipt details.', '']
    DOC.parent.mkdir(parents=True, exist_ok=True)
    DOC.write_text('\n'.join(lines))
    print(json.dumps({'status': status, 'checks': len(checks), 'errors': sorted(set(errors)),
                      'pending': pending, 'output': str(OUT.relative_to(ROOT))}, indent=2))
    return 1 if status == 'FAIL' else (2 if status == 'PENDING' else 0)

if __name__ == '__main__':
    raise SystemExit(main())
