"""Bind final offline evidence; never treats untested hardware as a pass."""
from pathlib import Path
import hashlib
import json
import shutil

root = Path('C:/moon')
candidate = root / 'publish/firmware/experiments/v44-dy71-three-frame-20261107'
release = candidate / 'release-bounded3-v001'
evidence = candidate / 'evidence/readiness-v001'
evidence.mkdir(exist_ok=True)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

build = root / 'builds/v44-target-run03'
built = json.loads((build / 'result.json').read_text())
assert built['returncode'] == 0 and not built['source_changes'] and not built['native_changes']
for label, base in [('source', candidate / 'handheld'), ('native', candidate / 'native')]:
    pins = json.loads((build / f'{label}-before.json').read_text())
    for relative, expected in pins.items():
        assert sha(base / relative) == expected, (label, relative)
image_pins = json.loads((release / 'hashes.json').read_text())
for name, expected in image_pins.items():
    assert sha(release / name) == expected, name
assert image_pins['moonshine-rev4.elf'] == built['elf_sha256']
package = json.loads((release / 'verification/commands.json').read_text())
assert len(package) == 6 and all(row['returncode'] == 0 for row in package)

system = root / 'maintenance/streaming-verification-20261107/system-three-frame-final'
sim = json.loads((system / 'result.json').read_text())
assert (sim['frames'], sim['accepted'], sim['presented'], sim['rejected'], sim['underruns']) == (3, 3, 3, 0, 0)
assert sim['native_arena_limit'] == 98304
assert sim['actual_HUD_words_written_and_compared'] == 63360
assert sim['native_hud_sha256'] == sha(candidate / 'native/hud.hpp')
for frame in sim['canonical_and_raster_comparison']['frames']:
    assert frame['canonical_mismatched_bytes'] == frame['composed_mismatched_pixels'] == frame['black_border_mismatches'] == 0
binding = json.loads((system / 'source-binding.json').read_text())
for path, expected in binding['files_sha256'].items():
    assert sha(Path(path)) == expected, path

loopback = root / 'maintenance/v44-localhost/run02/RESULT.json'
net = json.loads(loopback.read_text())
assert net['status'] == 'PASS' and len(net['host_outcomes']) == 3
assert all(x['status'] == 'presented' for x in net['host_outcomes'])
host = candidate / 'evidence/host-final-borrow01'
host_commands = json.loads((host / 'execution.json').read_text())
assert all(row['returncode'] == 0 for row in host_commands)
bit = root / 'dev/dy71-v027-20261107-v001/image01/moonbub-v027-lab.bit'
assert sha(bit) == '9922aa617c21a03e8a31f932d45e22d905e91d4e263ef593692898d363d07dee'

copies = {
    'target-build.json': build / 'result.json',
    'target-source-pins.json': build / 'source-before.json',
    'target-native-pins.json': build / 'native-before.json',
    'system-result.json': system / 'result.json',
    'system-source-binding.json': system / 'source-binding.json',
    'system-results.md': system / 'RESULTS.md',
    'system-native-run.log': system / 'native-run.log',
    'system-rtl-log.txt': system / 'rtl-stderr.log',
    'localhost-result.json': loopback,
    'localhost-receiver.log': loopback.parent / 'receiver.log',
    'memory-risk.md': root / 'maintenance/v44-localhost/MEMORY-RISK.md',
    'native-fix-receipt.json': root / 'maintenance/v44-localhost/native-fix-receipt.json',
    'memory-model-results.json': root / 'maintenance/v44-localhost/memory-model-results.json',
    'final-review.md': root / 'maintenance/streaming-verification-20261107/v44-final-review-addendum.md',
}
artifacts = []
for name, src in copies.items():
    assert src.is_file() and src.stat().st_size > 0, src
    dst = evidence / name
    shutil.copyfile(src, dst)
    artifacts.append({'role': 'executed_evidence', 'path': str(dst), 'sha256': sha(dst)})
for name in ('moonshine-rev4.elf', 'moonshine-rev4.bin', 'moonshine-rev4.uf2'):
    artifacts.append({'role': 'firmware_image', 'path': str(release / name), 'sha256': sha(release / name)})
artifacts.append({'role': 'existing_fpga_image', 'path': str(bit), 'sha256': sha(bit)})
manifest = {
    'overall': 'INCOMPLETE',
    'offline_candidate_status': 'PASS_READY_FOR_COORDINATED_BOUNDED3_HARDWARE_TEST',
    'physical_qualification': 'NOT_TESTED_V44',
    'date': '2026-11-07 America/Denver',
    'profile': 'dy71-bounded3-v2',
    'source_bindings_revalidated': len(binding['files_sha256']),
    'artifacts': artifacts,
    'checks': {
        'final_host_driver_native_wire': {'status': 'pass', 'evidence': str(host / 'execution.json')},
        'full_selected_system_functional': {'status': 'pass', 'evidence': str(evidence / 'system-result.json')},
        'actual_localhost_transport': {'status': 'pass', 'evidence': str(evidence / 'localhost-result.json')},
        'target_compile_source_identity': {'status': 'pass', 'evidence': str(evidence / 'target-build.json')},
        'effective_sdk_and_static_sram': {'status': 'pass', 'evidence': str(release / 'verification/memory-budget.log')},
        'production_updater_roundtrip': {'status': 'pass', 'evidence': str(release / 'verification/parser-check.log')},
        'physical_runtime_heap_stack_rf_lcd': {'status': 'incomplete', 'evidence': 'Pending controlled physical trial'},
    },
    'formal_handoff_checker': 'UNAVAILABLE_NOT_RUN; manual hash/source/evidence validation only',
    'limits': ['Finite three-frame trial only; not continuous-session recovery,120-second replay or30fps.',
               'Functional system model omits physical SPI/CDC/PLL and real target CPU timing.',
               'Historical-baseline allocator model is not physical heap/fragmentation qualification.'],
}
(evidence / 'readiness.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(manifest['offline_candidate_status'])
print(f"Validated {len(binding['files_sha256'])} final system bindings, target sources and exact release hashes")
print(evidence / 'readiness.json')
