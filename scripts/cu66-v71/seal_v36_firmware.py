"""Seal the already built v36 image; no build, flash or source mutation."""
from pathlib import Path
import datetime, hashlib, json, re, subprocess

root = Path('C:/Users/lavat/codex/moonbub/firmware/experiments/v36-dual-local-fixture-20261106')
e = root / 'evidence'
release = root / 'release-dual-local-fixture-v001'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
summary = json.loads((e / 'release-summary.json').read_text())
snapshot = json.loads((e / 'source-snapshot-v001.json').read_text())
assert sha(e / 'source-snapshot-v001.json') == summary['source_snapshot_sha256']
for name, expected in snapshot['files'].items():
    assert sha(root / name) == expected, name
for name, details in summary['images'].items():
    assert sha(release / name) == details['sha256']
for label in ['target-check', 'target-build']:
    result = json.loads((e / (label + '-v001.json')).read_text())
    assert result['returncode'] == 0, result
assert json.loads((e / 'host-control-result-v001.json').read_text())['tests'] == 18
assert all(s['returncode'] == 0 for s in summary['steps'])
parent = root.parent / 'v35-cu71-local-fixture-20261105'
assert (e / 'compiled-sdkconfig.h').read_bytes() == (parent / 'evidence/compiled-sdkconfig.h').read_bytes()

objdump = Path.home() / '.espressif/tools/xtensa-esp-elf/esp-14.2.0_20250730/xtensa-esp-elf/bin/xtensa-esp32s3-elf-objdump.exe'
symbols = (e / 'elf-symbols.log').read_text()
selected = []
frames = e / 'selected-frames-v001'
frames.mkdir(exist_ok=False)
for needle in ['local::run_with_profile::<', 'local_usb::worker', 'usb_test::command']:
    found = [line for line in symbols.splitlines() if needle in line and ' T ' in line]
    assert len(found) == 1, found
    address = int(found[0].split()[0], 16)
    command = [str(objdump), '-d', f'--start-address={address}', f'--stop-address={address + 24}', str(release / 'moonshine-rev4.elf')]
    output = subprocess.check_output(command, text=True)
    frame = re.search(r'entry\s+a1,\s+(0x[0-9a-f]+|\d+)', output)
    assert frame, output
    filename = f'frame-{address:08x}.log'
    (frames / filename).write_text(output)
    selected.append(dict(symbol=found[0], frame_bytes=int(frame.group(1), 0), disassembly=filename, command=command))
(frames / 'result.json').write_text(json.dumps(dict(
    status='SELECTED_TARGET_FRAMES_NOT_WHOLE_STACK_SAFETY_PROOF',
    elf_sha256=sha(release / 'moonshine-rev4.elf'), frames=selected,
    declared_worker_stack_bytes=12288,
    limits=['Individual prologues exclude nested calls, interrupts, RTOS and C++ exception paths.',
            'Physical W/G/Y task high-water and first-throw overhead remain NOT_RUN.']), indent=2) + '\n')

proof = Path('C:/mb70/fpga/experiments/cu66-v71/direct-system/local-control/qualification-v001.json')
dy = json.loads(proof.read_text())
assert dy['status'] == 'PASS_DY71_LOCAL_CSR_ACTUAL_V36_NATIVE_KEY_P_CORRECTNESS_ONLY'
assert (dy['accepted'], dy['presented'], dy['rejected'], dy['lcd_underruns']) == (2, 2, 0, 0)
artifacts = {}
for directory in [e, root / 'provenance']:
    for p in sorted(directory.rglob('*')):
        if p.is_file() and p.name != 'build-manifest.json':
            artifacts[p.relative_to(root).as_posix()] = dict(bytes=p.stat().st_size, sha256=sha(p))
manifest = dict(
    status='PASS_OFFLINE_LOCAL_FIXTURE_GATES_PHYSICAL_NOT_RUN',
    created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    variant=summary['variant'], source_snapshot='evidence/source-snapshot-v001.json',
    source_snapshot_sha256=sha(e / 'source-snapshot-v001.json'),
    release_directory=str(release), images=summary['images'], artifacts=artifacts,
    external_proofs=[dict(path=str(proof), sha256=sha(proof), scope='Actual v36/native -> DY71 CSR/PIPE/grouped RTL + checked SDRAM model, before syncsafe/math/bus-split successors')],
    compiled_sdkconfig_sha256=sha(e / 'compiled-sdkconfig.h'),
    compiled_sdkconfig_byte_identical_to_v35=True,
    static_shared_sram_bytes=summary['static_shared_sram_bytes'],
    declared_worker_stack_bytes=12288, exception_pool_bytes=1024,
    profiles={'G': dict(magic='43553731', abi='00010000', capabilities='00000007'),
              'Y': dict(magic='44593731', abi='00010000', capabilities='0000000f')},
    profile_selection='Explicit; incompatible identity/capabilities rejected before writes; no autodetection',
    network_CU66_capability=False, installed=False,
    limits=summary['limits'] + [
        'No final FPGA bitstream pairing, physical SPI/FreeRTOS, local fixture playback, W exception probe or stack/heap qualification.',
        'Numeric CSR co-simulation excludes physical QSPI wire and CPU execution wall time.',
        'No 25/30 fps claim; preserve build50/installed v32 for the separate morning network control.',
        'USB_CU71_LOCAL is a historical shared log prefix; requested_profile/completed_profile identify G versus Y.'])
(e / 'build-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps(dict(status=manifest['status'], manifest_sha256=sha(e / 'build-manifest.json'),
                      source_files=len(snapshot['files']), artifact_files=len(artifacts), frames=selected), indent=2))
