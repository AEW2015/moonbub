# V55 native ASan/UBSan host checks

Status: **PASS** for the existing native oracle harness under WSL Ubuntu 22.04 GCC 11.4 with AddressSanitizer and UndefinedBehaviorSanitizer. The `-Os` and `-O2` builds use the same unchanged harness and V55 `native/endpoint.cpp`, `-Wall -Wextra -Werror`, `-fsanitize=address,undefined`, and `-fno-omit-frame-pointer`. The native arena cap remains 98,304 bytes. No source or harness was edited.

`tools/endpoint_check.cpp` ran against the explicit `C:/moon/dev/experiments/cu66-source-bridge-20261108/video12` fixture directory. At both optimization levels, the 12-frame run verified 253,440 HUD words, reached arena peak 95,053 bytes, recorded zero allocation failures, passed 24 malformed/late-failure rollback checks and 12 recovery checks. The three-frame historical prefix also passed at both levels: 63,360 HUD words, the same arena peak, zero allocation failures, six fault checks and three recovery checks. No ASan or UBSan reports were emitted.

The first `prepare12_native.cpp` probe aborted after Prepare frame 0 because that harness expects unpadded `frame0.hud` names while the source bridge fixture uses `frame000.hud`. That log is preserved. The audit then reused the already-existing `endpoint_check.cpp` harness, whose fixture naming matches the source bridge. A first compile attempt also omitted its existing `-I native`; that failed log is preserved, and the corrected unchanged harness compiled and passed.

The MSYS2 UCRT compiler lacks sanitizer runtimes, but WSL had a running Ubuntu 22.04 distribution with GCC 11.4 and both runtime libraries. The initial WSL availability skip was corrected and retained as historical metadata. No installation was attempted.

All eight V55 native source hashes match before and after the runs. Source and fixture pins, commands, durations, logs, and exact outputs are in `source-hash-pins.json` and `sanitizer-result.json`. This is host sanitizer evidence only: it does not establish Xtensa runtime stack safety, resolve the Xtensa warning, or claim physical performance or hardware qualification.
