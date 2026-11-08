# V55 Xtensa native optimization audit

This is an isolated object compile of the exact frozen V55 `native/endpoint.cpp`. The compiler is Xtensa ESP32-S3 GCC 14.2.0. The common arguments are `-std=c++17 -mlongcalls -ffunction-sections -fdata-sections -fexceptions -fstack-usage -Wall -Wextra -Werror -c`; only `-Os`, `-O2`, or `-O3` changes. Each output is in a separate directory. No app link, SDK target cache, firmware image, Vivado run, or hardware operation was used.

The V55 build recipe uses `-Os`. That run compiled in 5.57 seconds to a 202,380-byte object. `xtensa-size -A` reported 49,187 aggregate section bytes (20,047 `.text`, 3,936 `.rodata`, 3,744 group, 3,528 literal, 1,720 eh_frame, 660 gcc_except_table, plus other sections). Selected symbol sizes were Huffman 1,062 bytes, channel33 1,058, `Endpoint::transact` 1,730, and `v34_hud_transact` 75.

Static stack-usage values for those functions are respectively 752, 160, 224, and 48 bytes. All four match the preserved selected V55 `.su` record. These are individual function frames; this does not calculate the full call chain or establish runtime stack margin.

`-O2` and `-O3` both fail the unchanged `-Wall -Wextra -Werror` compile with GCC `-Werror=maybe-uninitialized` diagnostics in optimized `std::basic_string` cleanup and `cu66_port::Alloc<char>::deallocate`. Their compiler stdout/stderr and return codes are preserved. Since those builds produced no object, there are no size, symbol, or `.su` results for them. The warning was not suppressed and the source was not changed. Source inspection notes that `Endpoint` explicitly resets its gate, the arena member precedes the optional gate, and the allocator captures the active arena or throws if absent. This does not resolve the compiler warning; no runtime bug or false positive is inferred, and no reproducer/sanitizer was run.

The first launch attempt used the requested `.../xtensa-esp32s3-elf/bin` directory, which is absent on this host, so no process started. The installed compiler is in the sibling `.../xtensa-esp-elf/bin` directory. The rerun used that installed compiler; its binary and commands are bound in `bindings.json` and `result.json`.

## Recommendation

Do not select an optimization from this audit. `-Os` is the reproducible baseline. `-O2` and `-O3` do not build under the required warning policy, and an object-only comparison would not prove a linked firmware code/stack benefit anyway. The warning cause is unresolved. The diagnostics touch `std::optional`/`std::basic_string` cleanup and the custom allocator; compiler output alone proves neither a runtime bug nor a false positive. Before any source/compiler/allocator change, use a minimal optional/allocator-lifetime reproducer and sanitizer/fault tests. Do not suppress `-Werror` based on this audit. A later candidate requires linked target measurements and existing behavior, stack, and hardware gates. No optimization is selected, and this audit makes no runtime performance, physical throughput, or stack-safety claim.

All eight V55 native source hashes are identical before and after the compile attempts.


