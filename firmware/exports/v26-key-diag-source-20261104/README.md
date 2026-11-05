# v26 ESP32 application source export

This Git-sized package contains all575 selected inputs from prebuild03, with
complete handheld source/assets, Cargo.lock, sdkconfig.defaults, managed-component
lock, tests and the selected production UF2 parser. Firmware/default bytes are
unchanged. Original nonportable review/build wrappers are archived under
provenance/selected-inputs/; use the portable commands below instead.

```powershell
python verify_source.py
python inspect_sources.py
python host_check.py --cargo C:/Users/you/.cargo/bin/cargo.exe --rustc C:/Users/you/.cargo/bin/rustc.exe
python check_metadata.py
python full_metadata.py
powershell -NoProfile -ExecutionPolicy Bypass -File build_rev4.ps1 -PreflightOnly
```

Executed after relocation:39 production-core tests,66 fake-SDK orchestration
tests and24 expected compiler rejections PASS;125 embedded/import/path references
resolve locally; four locked/offline Cargo metadata checks PASS; full selected
rev4 metadata resolves424 packages from the installed cache, with handheld the
only local package. These host64/fake-SDK results are not ESP ABI, physical drain,
heap/stack, logger or timing evidence. No target check/build was rerun here.
The preflight-only launcher passed without compiling firmware or accessing hardware.

For a future explicitly requested target build:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File build_rev4.ps1 -Action build -TargetDirectory C:/v26src02
```

That command is supplied, NOT executed by this packaging task. It selects
cargo +esp193 build --offline --locked --release --features rev4, preserving all
default std/embassy/native features. Use a genuinely fresh short target path.
The unchanged rust-toolchain.toml says esp; the launcher explicitly overrides it
with the selected esp193 alias. It never calls cargo run or a flash command.
The retained .cargo config has an espflash runner, so it is not the portable
launcher. See DEPENDENCIES.md for required externally installed tools and caches.

build.rs remains byte-identical: it invokes git rev-parse HEAD and falls back to
aa281c073693bd92850720a2e43998f1d8faf569. The launcher sets a package-root Git
discovery ceiling and checks that rev-parse fails, preserving that selected
fallback instead of silently using a surrounding publication repository commit.
Git itself must be installed. No existing GameBub checkout is a source/path
dependency. Complete Slint images/imports, JPEG loops, bootloader.bin and partition
inputs are included. The small bootloader.bin is a frozen source input; no
bootloader/update is performed. External Cargo/IDF dependencies are not vendored.

Inherited target evidence is under provenance/inherited-target/. The selected
esp193/IDF5.4.3 rev4 release/check passed in the parent; application-only UF2
validation passed12419 blocks through the production updater parser. These are
inherited executed records, NOT a new target build. Original parent manifest
SHA00b3d4a4bd6190646d72b817dc22d3802e6f70b87cfec35d9d5b2547cf8c4a66
binds3844 artifacts; selected snapshot SHA
6530279c0655723183e53c95877b534c8e69a386d923b9fb2cd500926c03eb97
binds575 inputs. All were verified before export, and originals remain untouched.

Selected release outputs are omitted, not regenerated or replaced:

| Original image | SHA256 |
| --- | --- |
| moonshine-rev4.uf2 | 80003d79887976d8a49889a0e0bcda2905cb58763ff21d720169c3a87432bc63 |
| moonshine-rev4.bin | 40cd845d6fb4cd6c4e0e5a7761d8bef776b931f78bac76eb2a9c4c29561e2d30 |
| moonshine-rev4.elf | 521f529ed99e587cfbd47e63be0de99f4a5f9a13fbf099752a24065655ed49e6 |

No SDK, registry cache, target outputs, ELF, UF2 or application BIN is bundled.
GPL-3.0-only firmware/script license and upstream attribution are retained in
licenses/. The package does not export a complete DFU firmware project: it
contains the exact selected updater parser needed by the application UF2 harness.

Variant v26-key-diag-access-20261104, stacks/priorities, UI/defaults, MSV1/AV1
layouts, audio identities and rev4/ILI9806E selection remain unchanged. v26 does
not explain/fix the observed v22 reboot. Physical programming, USB/COM/SD/JTAG,
runtime stack/heap and access tests were not performed by this export task.
Root owns publication and hardware actions.
