# Portable build prerequisites

This source export is complete; build tools and external caches are not bundled. No other GameBub checkout is needed. The candidate build manifest records the separately executed v32 target check and release, and their image hashes, as candidate evidence; those gates were not rerun from this export.

* Rustup alias `esp193`: Espressif Rust 1.93.0.0, rustc commit `2b43689c53a55786249fe1d7263826eef2d74725`; Cargo locked packages are specified by `handheld/Cargo.lock`.
* ESP-IDF 5.4.3, ESP32-S3 target, Python 3.11 IDF environment.
* CMake 3.30.2, Ninja 1.12.1, `ldproxy`, Git, and `libclang.dll` from the esp193 Xtensa clang toolchain. `build_rev4.ps1` accepts explicit installation paths.
* Rust dependencies: `handheld/Cargo.lock` contains 608 packages. `esp-idf-sys` is pinned to Git revision `a9356d974c79f8de86ac8d77bc25e16f4a239bae`; Slint/slint-build are `~1.12.1`, and embuild is `0.33.4` per Cargo.lock. The SDK host lock contains 3 packages: anyhow `1.0.104`, log `0.4.34`, and the local test package.
* `handheld/components_esp32s3.lock` selects ESP-IDF `5.4.3`, `espressif/esp_tinyusb 2.0.1~1` (hash `6f1f0c140990bf27a86611e3c1f47f9fa8468bffc3bf1eb6d551cb09f31f8908`), and `espressif/tinyusb 0.18.0~6` (hash `7fa5016d792d8e4025a8352b4fd4af7c124947647037e9d2449c9e0b47fdf663`). The selected Xtensa compiler/toolchain and Espressif managed-component cache are external. Initial cache population may require network access. Cargo build is run `--offline --locked`, so missing caches fail visibly.
* Rust stable/Cargo and the `x86_64-pc-windows-msvc` target are used for host tests. `tests/sdk-host/Cargo.lock` pins that harness. The candidate replay used Rust stable/Cargo 1.98.1. Python 3 is used for packaging integrity and source tests.

The sealed candidate records original image hashes: ELF `5bbb988144eeee7fcd96fb442573171f25912168fa94586a6a6fb2ce36e3e8fd`, application BIN `932d515d032561623d36f4f9f14b0e534b5bc5deeca211c7b15eb99311e4b3fe`, and UF2 `13c27ca9a919dd7d40b7ff7aa4d55e5d97e00ad79e596d5aeee732966e9c3d4d`. None is included here. The handheld bootloader binary is a declared source input referenced by `espflash.toml`; fixture `.bin` files are test data, not build outputs.

`build_rev4.ps1 -PreflightOnly` checks package integrity, absence of Git identity discovery, and exact Rust/IDF versions without creating build output. `-Action check` or `-Action build` runs only Cargo check/build with locked offline dependencies; it never invokes `cargo run`, espflash, flashing, or hardware. A future build can embed different build timestamps and is not expected to reproduce the candidate image hashes. Use a new short target path and evidence directory.
