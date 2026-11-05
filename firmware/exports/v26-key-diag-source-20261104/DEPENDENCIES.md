# Exact selected build prerequisites

The application source is complete; these external tools/dependencies are not
bundled. No existing GameBub checkout is required. Initial installation/cache
population can require network access; --offline checks cannot install missing
dependencies. The export's metadata checks used already-installed local caches.

* Rustup alias esp193: Espressif1.93.0.0, rustc1.93.0-nightly,
  commit2b43689c53a55786249fe1d7263826eef2d74725 dated2026-01-27,
  LLVM20.1.1. Cargo1.93.0-nightly083ac5135 (2025-12-15). The plain esp alias
  is not assumed equivalent. The established newer1.97 path is not selected.
* ESP-IDF v5.4.3, ESP32-S3 target, Python3.11 IDF environment. Selected tool
  locations were ~/.espressif/esp-idf/v5.4.3 and
  ~/.espressif/python_env/idf5.4_py3.11_env/Scripts/python.exe. Launcher paths
  are parameters/default to USERPROFILE, not a GameBub repository.
* CMake3.30.2, Ninja1.12.1; selected IDF C compiler GCC14.2.0 at
  xtensa-esp-elf/esp-14.2.0_20250730/xtensa-esp-elf/bin/xtensa-esp32s3-elf-gcc.exe.
* ldproxy on the Cargo bin PATH; libclang.dll from the selected esp193
  xtensa-esp32-elf-clang/esp-clang/bin directory. No clang.exe is assumed there.
  Git must be executable for unchanged build.rs, even outside a repository.
* Main Cargo.lock has608 package entries. The selected rev4 metadata graph
  resolves424. esp-idf-sys0.36.1 is pinned to Git revision
  a9356d974c79f8de86ac8d77bc25e16f4a239bae (manifest rev a9356d9).
  Other registry versions/checksums are fixed by Cargo.lock. No unresolved
  external local-path package was found. The resolved license inventory is in
  checks/metadata/full-application-result.json.
* Slint/slint-build1.12.1 and embuild0.33.0 come from the lock/dependency graph.
  Slint std-widgets.slint is a crate-provided builtin;125 local embedded image/
  import/input references were checked. Rust-generated OUT_DIR content is built,
  not a missing checkout asset.
* components_esp32s3.lock selects ESP-IDF5.4.3,
  espressif/esp_tinyusb2.0.1~1 hash
  6f1f0c140990bf27a86611e3c1f47f9fa8468bffc3bf1eb6d551cb09f31f8908,
  and espressif/tinyusb0.18.0~6 hash
  7fa5016d792d8e4025a8352b4fd4af7c124947647037e9d2449c9e0b47fdf663.
  Their Espressif managed-component cache/sources are external prerequisites.
* Optional image conversion uses esptool.py4.13.0 in the selected IDF Python
  environment, ESP32-S3,dio,80m,8MB plus the included Rev4/application-only UF2
  packer/parser. Conversion was not rerun; no flash command is provided.
* Host checks used Rust stable/Cargo1.98.1 on x86_64-pc-windows-msvc, a Windows
  native linker, and cached anyhow1.0.104/log0.4.34 for tests/sdk-host. Those mocks
  do not establish ESP32 ABI or stack bounds.

Use a new short output directory such as C:/v26src02, not the original C:/mv26
or shared C:/gbt. SUBST does not solve canonical path-length limits. The portable
launcher checks exact compiler/IDF versions and source/Git-fallback integrity,
then only check/build. A future rebuild may embed new SDK date/time and cannot
be assumed byte-identical to the original selected ELF/BIN/UF2.
