# Minimal optional/custom allocator warning reproducer

This package preserves the exact root-prepared `minimal.cpp` and `bounded.hpp` source files and compiles only the reduced translation unit to Xtensa object files. `licenses/LICENSE-GPL-V3` preserves the firmware licensing context. The reduced example is diagnostic-only and is not firmware. `bounded.hpp` byte-matches V55's audited custom allocator header. `minimal.cpp` retains the essential lifetime shape: an `Endpoint` owns `Arena` before `optional<MiniGate>`, the constructor creates the gate under an arena scope, the destructor resets it under scope, and `MiniGate` owns the custom-allocator string. It also includes a failure-string assignment entry point.

## Executed results

`result.json` records source hashes before and after each compilation, exact command arrays, local temporary directory, times, return codes and scope. Xtensa ESP32-S3 GCC 14.2.0 used `-std=c++17 -mlongcalls -ffunction-sections -fdata-sections -fexceptions -fstack-usage -Wall -Wextra -Werror -c`; only `-Os`, `-O2`, and `-O3` varied.

- `-Os`: return code 0; object 19,944 bytes; size report and `.su` output are preserved.
- `-O2`: return code 1 with three `-Werror=maybe-uninitialized` diagnostics; no object was produced. `.su` output remains available.
- `-O3`: return code 1 with the same three diagnostics as `-O2`; no object was produced. `.su` output remains available.

The reduced example therefore reproduces the warning under both failing optimization flags. This shows that the warning does not require the full endpoint translation unit; it does not prove a runtime bug, undefined behavior, or a false positive. No sanitizer, link, app build, source edit, firmware change, or hardware run was performed. The original audit and its raw warning logs are bound in `warning-map/bindings.json` and summarized in `warning-map/WARNING-MAP.md`.

## Harness history

Two incomplete PowerShell harness attempts are preserved in `initial-harness-attempt` and `interrupted-startprocess-attempt`. Their outputs are not the source of the final return-code claim. The final three runs were performed by `run_repro.py`, using Python `subprocess.run` with byte-captured stdout/stderr and explicit `C:\moon\tmp\native-optional-lifetime-repro-20261108` `TEMP`/`TMP`. The runner used the preserved source directory directly and verified unchanged source hashes. No output was written into the source directory.

