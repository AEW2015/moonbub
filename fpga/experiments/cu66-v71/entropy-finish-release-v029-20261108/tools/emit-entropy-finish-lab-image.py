"""Emit entropy-finish V029 only after routed and exact 12-frame gates.
Adapted from emit-parser-stage-image.py. Never programs hardware."""
from pathlib import Path
import hashlib, json, os, re, subprocess, time

p = Path('C:/moon/builds/entropy-finish-v001')
out = Path('C:/moon/builds/entropy-finish-image-v029')
sim = Path('C:/moon/dev/experiments/stb1-v55-entropy-finish-video12-system-20261108')
functional = sim / 'result.json'
template = Path('C:/moon/builds/stb1-selected-image01/emit.tcl')
expected_freeze = 'b53321d85c8e1677484e61db6a35b89ec9913509fa6a5c1b5348dec29b465c4e'
expected_template = 'ecc3909d6712f2df319acd0e2611606b77c5db4527588c18ec674488299f5725'
expected_route_dcp = '443b537169be53bfdf39b0085a8cdc099787f7ebece0d17b54b449927187fb5f'
acceptance_path = Path('C:/moon/maintenance/entropy-finish-v029-lab-zero-setup-acceptance.json')
expected_entropy = '54f1238f50ca2d42ec407bb568f2562b818054d4081e0f4301bea16e43c5142f'
expected_modules = {
    'cu71_receiver_final_v022': '316123fb1db92d67a797b2a49263500314d5173561a2eff52ef451734f94deb9',
    'cu71_packet_rxstage_v001': '39197a682b894f55d4a9a73ed039e58c0f3bed1aeb3a6cc24139c1c4d5325c56',
    'cu71_ab38_decoder_metadata_v021': expected_entropy,
}
bit_name = 'moonbub-v029-entropyfinish-rev4.1.bit'
marker = 'V029_ENTROPY_FINISH_BIT_EMITTED_NO_HARDWARE'
sha = lambda f: hashlib.sha256(Path(f).read_bytes()).hexdigest()

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

def hash_map(mapping, base=None):
    require(isinstance(mapping, dict) and bool(mapping), 'Missing or empty hash map')
    for name, expected in mapping.items():
        path = Path(name) if base is None else base / name
        require(path.is_file(), f'Missing pinned input: {path}')
        require(sha(path) == expected, f'Pinned input changed: {path}')

# Unique paths and the reviewed image-emission template are checked first.
require(not out.exists(), 'Unique entropy-finish image output required')
tmp = Path('C:/moon/tmp/entropy-finish-image-v029')
require(not tmp.exists(), 'Unique entropy-finish Vivado temporary directory required')
require(template.is_file() and sha(template) == expected_template, 'Reviewed template ECC changed')
require((p / 'routed.dcp').is_file() and sha(p / 'routed.dcp') == expected_route_dcp,
        'Lab acceptance is bound to a different routed checkpoint')
require(acceptance_path.is_file(), 'Explicit lab-only zero-setup acceptance receipt is required')
acceptance = json.loads(acceptance_path.read_text(encoding='utf-8-sig'))
require(acceptance['status'] == 'USER_ACCEPTED_FOR_HARDWARE_LAB_ONLY'
        and acceptance['accepted_setup_slack_ns'] == 0.0
        and acceptance['build'] == str(p).replace('\\', '/')
        and acceptance['source_freeze_sha256'] == expected_freeze
        and acceptance['routed_dcp_sha256'] == expected_route_dcp
        and acceptance['output'] == str(out).replace('\\', '/')
        and acceptance['bit_name'] == bit_name and acceptance['user_code'] == '44593741',
        'Lab acceptance receipt does not match this exact candidate')

# Bind the exact 79-input source set and selected overlay.
freeze_path = p / 'source-freeze.json'
freeze = json.loads(freeze_path.read_text())
require(len(freeze) == 79, 'Expected exactly 79 frozen source inputs')
require(sha(freeze_path) == expected_freeze, 'Entropy-finish source freeze changed')
hash_map(freeze, p / 'inputs')
overlay = json.loads((p / 'overlay-binding.json').read_text())
require(overlay['source_freeze_sha256'] == expected_freeze and overlay['source_entries'] == 79,
        'Overlay is not bound to the exact entropy-finish source freeze')
for name, expected in overlay['script_sha256'].items():
    require(sha(p / name) == expected, f'Reviewed build script changed: {name}')
source_order_path = p / 'source-order.json'
source_order = json.loads(source_order_path.read_text())
synth_tcl = (p / 'synth.tcl').read_text()
tcl_read_order = re.findall(r'^read_verilog -sv \[file join \$root ([^\]]+)\]$', synth_tcl, re.M)
require(len(source_order['read_order']) == 33 and tcl_read_order == source_order['read_order']
        and set(source_order['read_order']) == set(overlay['compiled_sources'])
        and source_order['Tcl_sha256'] == overlay['script_sha256']['synth.tcl'] == sha(p / 'synth.tcl'),
        'Tcl/source-order/source-inventory binding changed')
entropy_rel = 'fpga/experiments/cu66-v71/metadata-registers-v021/cu71_ab38_decoder_metadata_v021.sv'
require(freeze.get(entropy_rel) == expected_entropy, 'Frozen entropy FINISH58 RTL hash mismatch')

# Require a completed, source-unchanged routed implementation with positive timing,
# clean route/DRC, and zero timing-coverage holes before considering image emission.
run_path = p / 'implementation-execution.json'
run = json.loads(run_path.read_text())
require(run['returncode'] == 0 and run['completion_marker'] and run['inputs_unchanged']
        and not run['native_errors'] and run.get('BIT') is False and run.get('hardware') is False,
        'Implementation execution did not complete cleanly without BIT or hardware')
launch = json.loads((p / 'implementation-launch.json').read_text())
implementation_review_path = p / 'review-implementation-root.json'
implementation_review = json.loads(implementation_review_path.read_text())
require(implementation_review['allow_implementation'] is True
        and implementation_review['source_freeze_sha256'] == expected_freeze
        and implementation_review['overlay_binding_sha256'] == sha(p / 'overlay-binding.json'),
        'Implementation review receipt is not approved for this frozen source/overlay')
require(launch['source_freeze_sha256'] == expected_freeze
        and launch['script_sha256'] == overlay['script_sha256']['implementation.tcl']
        and launch['review_receipt_sha256'] == sha(implementation_review_path),
        'Implementation launch is not bound to the frozen source/script/review')
for name in ['routed.dcp', 'timing-summary.rpt', 'route-status.rpt', 'drc.rpt', 'cdc.rpt',
             'check-timing.rpt', 'exceptions.rpt', 'implementation-console.log',
             'implementation-vivado.log', 'implementation-vivado.jou']:
    require((p / name).is_file() and (p / name).stat().st_size > 0, f'Missing routed evidence: {name}')
require('All user specified timing constraints are met.' in (p / 'timing-summary.rpt').read_text(),
        'Strict timing summary is not a positive closure report')
timing = (p / 'timing-summary.rpt').read_text()
lines = timing.splitlines()
header = next(i for i, line in enumerate(lines) if 'WNS(ns)' in line and 'WPWS(ns)' in line)
values = lines[header + 2].split()
require(len(values) == 12, 'Unexpected routed timing summary schema')
require(float(values[0]) >= 0 and float(values[4]) > 0 and float(values[8]) > 0,
        'Lab setup may equal zero only; hold and pulse slack must remain positive')
require(all(float(values[i]) == 0 for i in [1, 2, 5, 6, 9, 10]),
        'Timing TNS and failing endpoint counts must all be zero')
routes = (p / 'route-status.rpt').read_text()
number = lambda key: int(re.search(re.escape(key) + r'\.+\s*:\s*(\d+)', routes).group(1))
require(number('# of routable nets') == number('# of fully routed nets') > 0
        and number('# of nets with routing errors') == 0, 'Route status is not clean')
drc = (p / 'drc.rpt').read_text()
require(not re.search(r'^\|[^\n]*\|\s*(?:Error|Critical Warning)\s*\|', drc, re.M),
        'Unwaived DRC Error/Critical Warning remains')
check = (p / 'check-timing.rpt').read_text()
for key in ['no_clock', 'unconstrained_internal_endpoints', 'loops', 'latch_loops']:
    match = re.search(r'checking ' + re.escape(key) + r' \((\d+)\)', check)
    require(match is not None and int(match.group(1)) == 0,
            f'Timing coverage gate is missing or nonzero: {key}')

# Read the current producer's exact bindings. Included header pins live directly in
# bindings.json; this helper intentionally does not require a header-source sidecar.
binding_path = sim / 'bindings.json'
b = json.loads(binding_path.read_text())
require(b['source_package']['count'] == 12 and b['source_package']['source_unique_frames'] == 12,
        'Functional package is not the exact 12-frame source set')
require(len(b['production_RTL_deltas_vs_selected_V028']) == 3 and not b['bounds_factor_combined']
        and b['positive_12_only'] is True and b['positive_pair_only'] is False,
        'Unexpected production RTL composition or positive-frame scope')
require(b['source_composition'] == 'Exact CE316123fb + parser39197a68 + entropy54f1238f; no bounds-factor candidate'
        and b['entropy_runtime_scope'] ==
        'begin39 and validate58 exact per-frame counts and plane/stream masks; parser19 once per actual frame; expected counts derived from immutable packet dispatch/raw flags',
        'Unexpected entropy-finish source composition')
require(len(b['production_RTL_deltas_vs_selected_V028']) == 3,
        'Expected exactly three production RTL module pins')
module_hashes = {row['module']: row['sha256'] for row in b['production_RTL_deltas_vs_selected_V028']}
require(module_hashes == expected_modules, 'Three-module RTL hash map changed')
module_files = {
    'cu71_receiver_final_v022': sim / 'rtl/cu71_receiver_final_v022.sv',
    'cu71_packet_rxstage_v001': sim / 'rtl/cu71_packet_rxstage_v001.sv',
    'cu71_ab38_decoder_metadata_v021': sim / 'rtl/cu71_ab38_decoder_metadata_v021.sv',
}
for module, path in module_files.items():
    require(sha(path) == expected_modules[module], f'Production RTL changed: {module}')

hash_map(b['executed_RTL_CPP_support_inputs'])
hash_map(b['harness_source_files'], sim)
hash_map(b['copied_Rust_all_files_sha256'], sim)
hash_map(b['package_packet_files_sha256'], sim)
hash_map(b['independent_goldens']['goldens_sha256'], sim)
require(b['independent_goldens']['selected_oracle'] == 'layout-v2/goldens'
        and len(b['independent_goldens']['goldens_sha256']) == 48,
        'Independent full-image/HUD golden set changed')
for name, equal in b['exact_firmware_source_match'].items():
    require(equal, f'Firmware source-copy equality not certified: {name}')
    copy = sim / 'cu66' / name
    original = Path(b['V55_origin']) / 'handheld/src/cu66' / name
    require(sha(copy) == sha(original), f'Firmware source copy mismatch: {name}')
for name, record in b['native_binary_bindings'].items():
    local = sim / name
    origin = Path(record['origin'])
    require(sha(local) == record['sha256'] and sha(origin) == record['sha256'],
            f'Native library binding mismatch: {name}')
require(len(b['included_header_sources']) == 3, 'Expected exactly three direct included-header pins')
for row in b['included_header_sources']:
    require(sha(Path(row['path'])) == row['sha256'], f'Included header changed: {row["path"]}')

# Require the real before/after execution-input snapshots, exact current comparison,
# and actual RTL runtime witness. Missing evidence blocks output creation.
before_path = sim / 'execution-inputs-before.json'
after_path = sim / 'execution-inputs-after.json'
require(before_path.is_file() and after_path.is_file(), 'Both execution-input snapshots are required')
before = json.loads(before_path.read_text())
after = json.loads(after_path.read_text())
binding_sha = sha(binding_path)
for snapshot, phase in [(before, 'before'), (after, 'after')]:
    require(snapshot['status'] == 'PASS_IMMUTABLE_SOURCE_HEADER_NATIVE_BINARY_GATE'
            and snapshot['phase'] == phase and snapshot['binding_sha256'] == binding_sha,
            f'Invalid {phase} execution-input snapshot')
require(before['approval_sha256'] == after['approval_sha256'], 'Input snapshot approval changed')
require(before['pins'] == after['pins'] and len(before['pins']) == 57,
        'Before/after execution input pins differ or are incomplete')
hash_map(before['pins'])

expectations_path = sim / 'finish-expectations.json'
expectations = json.loads(expectations_path.read_text())
require(sha(expectations_path) == b['finish_expectations_sha256'], 'Packet-derived finish expectations changed')
require(len(expectations['frames']) == 12 and expectations['total_expected_finishes'] == 144,
        'Expected twelve packet-derived frame finish records')
for index, frame in enumerate(expectations['frames']):
    require(frame['frame'] == index and frame['expected_finish_count'] == 12
            and frame['expected_plane_stream_mask'] == 0xFFF,
            f'Unexpected packet-derived entropy expectation for frame {index}')
    packet = sim / 'packets' / f"frame{index:03}.cu66"
    require(sha(packet) == frame['packet_sha256'],
            f'Packet-derived entropy expectation input changed for frame {index}')

witness_path = sim / 'runtime-witness.json'
comparison_path = sim / 'layout-v2/comparison.json'
require(witness_path.is_file() and comparison_path.is_file(),
        'Actual entropy/parser runtime witness and full-frame comparison are required')
witness = json.loads(witness_path.read_text())
require(witness['status'] == 'PASS_ACTUAL_PARSER19_AND_ENTROPY58_PER_FRAME_PLANE_STREAM_WITNESS'
        and witness['actual_validations'] == witness['expected_validations_packet_derived'] == 144
        and witness['expected_source_sha256'] == sha(expectations_path),
        'Runtime witness does not prove all 144 expected FINISH58 validations')
require(witness['generation_qualifier'] ==
        'RTL witness asserts active_generation==frame+1 at each actual state39/58 and parser19 visit',
        'Runtime witness generation qualifier changed')
rows = witness['frames']
require(len(rows) == 12 and {row['frame'] for row in rows} == set(range(12)),
        'Runtime witness does not cover exactly frames 0 through 11')
for row in rows:
    frame = expectations['frames'][row['frame']]
    require(row['begin'] == row['validate'] == frame['expected_finish_count'] == 12
            and row['mask'] == frame['expected_plane_stream_mask'] == 0xFFF
            and row['parser'] == 1,
            f'Actual begin/validate/mask/parser witness failed for frame {row["frame"]}')
require(sum(row['validate'] for row in rows) == 144, 'Actual FINISH58 validation total is not 144')

comparison = json.loads(comparison_path.read_text())
require(comparison['status'].startswith('PASS') and len(comparison['frames']) == 12,
        'Full 12-frame comparison did not pass')
for index, frame in enumerate(comparison['frames']):
    require(frame.get('canonical_mismatched_bytes') == 0
            and frame.get('composed_mismatched_pixels') == 0
            and frame.get('displayed_HUD_mismatched_words') == 0,
            f'Full-image/HUD comparison failed on frame {index}')

f = json.loads(functional.read_text())
require(f['status'] == 'PASS_EXACT_V55_CE_PARSER19_ENTROPY58_VIDEO12'
        and f['actual_compressed_finish_validations'] == 144
        and f['entropy_runtime_witness_sha256'] == sha(witness_path)
        and f['binding_sha256'] == binding_sha
        and f['comparison_sha256'] == sha(comparison_path),
        'Functional result is missing exact source/witness/comparison bindings')
require(f['production_RTL_deltas'] == b['production_RTL_deltas_vs_selected_V028'],
        'Functional result module map differs from the direct source bindings')
require(f['parser_state19_visits'] == f['accepted'] == f['presented'] == 12
        and f['rejected'] == f['underruns'] == 0,
        'Parser19/accept/present counts do not match twelve frames')
require(f['HUD_words_written'] == f['HUD_words_verified'] == 253440
        and f['actual_composed_video_pixels'] == 4147200,
        'Full-image/HUD coverage is incomplete')
for key in ['canonical_mismatched_bytes', 'composed_mismatched_pixels',
            'displayed_HUD_mismatched_words']:
    require(f[key] == 0, f'Aggregate image/HUD comparison failed: {key}')
require(f['native_arena'][0] == 98304 and f['native_arena'][2] <= 98304
        and f['native_arena'][5] == 0, 'Native arena witness is invalid')
require(f['front_bank_sequence'] == [row['front_bank'] for row in comparison['frames']]
        and len(f['front_bank_sequence']) == 12 and f['banks_exercised'] == [0, 1]
        and f['bank2_covered'] is False, 'Frame/bank sequence does not match the comparison')
require(f['HUD_envelopes'] == ['HX33'] * 9 + ['HU25'] * 3,
        'Unexpected per-frame HUD envelope sequence')
require(f['source_kind'] == 'NEW local motion-test first12; not120s or live'
        and f['source_PTS_span_seconds'] == 0.366666667
        and f['modeled_yield_us'] == 100 and f['modeled_Prepare_us'] == 200000
        and f['native_CPU_virtual_timer_us'] == 0 and f['SDRAM_init'] == 'zero'
        and f['scope'] == 'Positive functional composition only; no hardware, SDK/radio/SPI throughput, target fragmentation, SDF or fault-injection claim.',
        'Functional source or modeled timing scope changed')
require(f['model_reads'] > 0 and f['model_writes'] > 0 and f['model_refreshes'] > 0,
        'Functional memory-model counters are absent')

# Enforce one Vivado process at a time. Failure to enumerate is a hard stop.
processes = subprocess.run(
    ['powershell', '-NoProfile', '-Command',
     "$ErrorActionPreference='Stop'; @(Get-CimInstance Win32_Process -Filter \"Name='vivado.exe'\" -ErrorAction Stop | Select-Object -ExpandProperty ProcessId) | ConvertTo-Json -Compress"],
    capture_output=True, text=True)
require(processes.returncode == 0 and not processes.stderr.strip(),
        'Could not enumerate Vivado processes safely')
require(not processes.stdout.strip() or json.loads(processes.stdout) == [],
        'One Vivado build at a time')

# Create a private Tcl from the ECC-pinned template only after every input gate passes.
tcl = template.read_text()
for old, new in [
    ('C:/moon/builds/stb1-v001/routed.dcp', str(p / 'routed.dcp').replace('\\', '/')),
    ('C:/moon/builds/stb1-selected-image01', str(out).replace('\\', '/')),
    ('0x44593740', '0x44593741'),
    ('moonbub-v028-stb1-rev4.1.bit', bit_name),
    ('V028_STB1_BIT_EMITTED_NO_HARDWARE', marker),
]:
    require(old in tcl, f'Expected reviewed Tcl template token missing: {old}')
    tcl = tcl.replace(old, new)
old_slack_gate = '''foreach type {max min} {
 set paths [get_timing_paths -delay_type $type -max_paths 1]
 if {[llength $paths] != 1 || [get_property SLACK $paths] <= 0} {error "Nonpositive routed slack"}
}'''
lab_slack_gate = '''foreach type {max min} {
 set paths [get_timing_paths -delay_type $type -max_paths 1]
 if {[llength $paths] != 1} {error "Missing routed timing path"}
 set slack [get_property SLACK $paths]
 if {$type eq "max" && $slack < 0} {error "Negative routed setup slack"}
 if {$type eq "min" && $slack <= 0} {error "Nonpositive routed hold slack"}
}'''
require(old_slack_gate in tcl, 'Reviewed template timing gate changed')
tcl = tcl.replace(old_slack_gate, lab_slack_gate)
require('C:/mb70' not in tcl and 'program_hw' not in tcl
        and 'write_bitstream' in tcl and '0x44593741' in tcl
        and 'Negative routed setup slack' in tcl and 'Nonpositive routed hold slack' in tcl,
        'Generated Tcl identity, lab timing exception, or no-hardware guard failed')

out.mkdir()
script = out / 'emit.tcl'
script.write_text(tcl, encoding='utf-8')
before_emit = {
    'routed_input_sha256': sha(p / 'routed.dcp'),
    'source_freeze_sha256': sha(freeze_path),
    'source_order_sha256': sha(source_order_path),
    'script_sha256': sha(script),
    'base_audit_script_sha256': sha(template),
    'functional_result_sha256': sha(functional),
    'functional_binding_sha256': binding_sha,
    'functional_comparison_sha256': sha(comparison_path),
    'functional_runtime_witness_sha256': sha(witness_path),
    'finish_expectations_sha256': sha(expectations_path),
    'execution_inputs_before_sha256': sha(before_path),
    'execution_inputs_after_sha256': sha(after_path),
    'execution_input_pins_sha256': before['pins'],
    'included_header_sources': b['included_header_sources'],
    'production_module_sha256': module_hashes,
    'USERCODE': '44593741',
    'lab_zero_setup_acceptance_sha256': sha(acceptance_path),
    'lab_scope': 'User-accepted 0.000ns setup only for hardware lab candidate; not production timing closure',
    'source_changes_during_image_emit': False,
    'hardware': False,
    'routed_slack_ns': {'setup': float(values[0]), 'hold': float(values[4]), 'pulse': float(values[8])},
    'gate_report_sha256': {name: sha(p / name) for name in [
        'timing-summary.rpt', 'route-status.rpt', 'drc.rpt', 'cdc.rpt',
        'check-timing.rpt', 'implementation-execution.json']},
    'functional_metrics': {
        'actual_compressed_finish_validations': 144,
        'parser_state19_visits': 12,
        'accepted': 12,
        'presented': 12,
        'rejected': 0,
        'underruns': 0,
        'HUD_words_verified': 253440,
    },
}
(out / 'binding.json').write_text(json.dumps(before_emit, indent=2), encoding='utf-8')
tmp.mkdir(exist_ok=False)
env = dict(os.environ, TEMP=str(tmp), TMP=str(tmp))
env.pop('NoDefaultCurrentDirectoryInExePath', None)
cmd = ['C:/Xilinx/2025.2/Vivado/bin/vivado.bat', '-mode', 'batch', '-source', str(script),
       '-log', str(out / 'vivado.log'), '-journal', str(out / 'vivado.jou')]
started = time.monotonic()
with (out / 'console.log').open('x') as log:
    child = subprocess.Popen(cmd, cwd=out, env=env, stdout=log, stderr=subprocess.STDOUT,
                             creationflags=subprocess.CREATE_NO_WINDOW)
    (out / 'launch.json').write_text(json.dumps({'command': cmd, 'pid': child.pid}, indent=2))
    code = child.wait()
text = (out / 'console.log').read_text(errors='replace')
result = {
    'returncode': code,
    'seconds': time.monotonic() - started,
    'marker': any(line.strip() == marker for line in text.splitlines()),
    'errors': re.findall(r'^ERROR:.*', text, re.M),
    'input_unchanged': sha(p / 'routed.dcp') == before_emit['routed_input_sha256'],
    'sources_unchanged': all(sha(p / 'inputs' / name) == digest for name, digest in freeze.items()),
    'source_order_unchanged': sha(source_order_path) == before_emit['source_order_sha256'],
    'functional_binding_unchanged': sha(binding_path) == before_emit['functional_binding_sha256'],
    'functional_result_unchanged': sha(functional) == before_emit['functional_result_sha256'],
    'functional_comparison_unchanged': sha(comparison_path) == before_emit['functional_comparison_sha256'],
    'functional_runtime_witness_unchanged': sha(witness_path) == before_emit['functional_runtime_witness_sha256'],
    'execution_inputs_unchanged': sha(before_path) == before_emit['execution_inputs_before_sha256']
                                  and sha(after_path) == before_emit['execution_inputs_after_sha256'],
    'execution_input_pins_unchanged': before['pins'] == after['pins']
                                      and all(sha(Path(name)) == digest
                                              for name, digest in before['pins'].items()),
    'lab_zero_setup_acceptance_unchanged': sha(acceptance_path) == before_emit['lab_zero_setup_acceptance_sha256'],
    'hardware': False,
    'artifacts': {file.name: sha(file) for file in out.iterdir()
                  if file.is_file() and file.suffix in ['.bit', '.dcp', '.v', '.tsv', '.rpt']},
}
(out / 'execution.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result), flush=True)
require(code == 0 and result['marker'] and not result['errors']
        and result['input_unchanged'] and result['sources_unchanged'] and result['source_order_unchanged']
        and result['functional_binding_unchanged'] and result['functional_result_unchanged']
        and result['functional_comparison_unchanged'] and result['functional_runtime_witness_unchanged']
        and result['execution_inputs_unchanged'] and result['execution_input_pins_unchanged']
        and result['lab_zero_setup_acceptance_unchanged'],
        'Image emission execution or input stability failed')
for name in [bit_name, 'routed-image.dcp']:
    artifact = out / name
    require(artifact.is_file() and artifact.stat().st_size > 1000000,
            f'Required nonempty image artifact missing: {name}')







