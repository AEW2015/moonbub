# V55 native and worker stack risk audit

## Scope and result

This is a read-only static review of the selected V55 target `.su` capture and release ELF. It does not establish a full worst-case call chain, a Rust task stack high-water mark, or physical stack safety. The release ELF is the selected artifact with SHA-256 `ef005e82d795b3ea1bdb6248901b821a7b5e78ad753de5fe0b6d2766a663976b`; the captured native `.su` file is SHA-256 `5c097bc581f75d066cb9d46f6e510260128eb0cbfa76c8d4bc3f0212cbfd4945`.

The native `.su` records static individual frames. The largest entries include `cu66::huffman` 752 bytes, `decode_hud` overload 368, `decode_block` 320, `decode_patch` 256, `v46_hud_diagnostics` 240, `decode_hud(View,...)` 224, and `channel33` 160. These are per-function compiler reports; adding these entries would be invalid without proving a complete path and accounting for inlining, exceptions, allocator calls, and other callees.

Root's read-only review of the selected ELF reports a 5,328-byte network worker prologue and a 4,000-byte run-mode prologue. These figures are individual Rust frames. The caller/callee overlap and full Rust/native/USB/allocator/error paths were not reconstructed here, so they are not summed or treated as an upper bound. The worker's configured 16,384-byte stack is capacity, not evidence of remaining headroom.

## What has explicit bounds

`endpoint.hpp` rejects HC70 packets above 49,152 payload bytes (49,188 including framing). READ output is limited to 21,120 words. `hud.hpp` bounds Huffman count to 21,120, maximum symbol to 255, code lengths to 16 bits, symbol table count to `min(count, maximum + 1)`, and encoded bit count to `16 * count`. The fixed Huffman tables (`lengths`, `counts`, `first_code`, `first_symbol`, `symbols`) have compile-time sizes; the source comment estimates their combined data at 648 bytes. This supports bounded local table storage for that routine, consistent with its reported 752-byte frame, but says nothing about caller frames or other paths.

Channel 33 limits events to the symbol count, Rice parameter to 14, and encoded size/bit counts as shown in source. Patch decode limits each patch to 21,120 words and validates packet sizes. The arena caps dynamic native allocations at 98,304 bytes per operation; test evidence reached 95,053 bytes for the twelve-frame native oracle. That heap arena cap does not cap automatic stack, exception-unwind depth, Rust worker stack, FreeRTOS task stack, interrupt stack, or call depth.

The native source uses `std::map`/`std::set` aliases and the `.su` capture includes red-black tree routines, including `_Rb_tree::_M_erase` at 32 bytes per reported activation. A recursive tree erase can use multiple activations; this review did not prove maximum tree-node count along each reachable call path or derive a recursion bound from all protocol states. Standard-library allocator and `shared_ptr` construction/destruction, exception creation/unwinding, and Rust-to-C wrapper transitions add indirect/exception paths that are not covered by the native `.su` maximum.

## Evidence limits and risk

The V48 prior physical observation of 2,904 bytes lowest remaining stack is not transferable as a V55 guarantee. V55 changes native Huffman/channel code and runs the larger twelve-frame sequence; available records do not show a V55 physical high-water measurement. Runtime stack safety is **UNKNOWN**. The sanitizer work is host-native and does not provide Xtensa stack evidence.

## First physical checks

Before making a stack-safety claim, install only the specifically selected V55 image on the intended board and record its ELF/BIN/UF2 hashes. Instrument the actual network worker/task stack with the platform's high-water or watermark mechanism and a canary/guard check. Record initial stack size and minimum-ever free bytes while running the twelve-frame HU25 workload, both cached and scalar modes where applicable, including key and dependent frames, Huffman and channel 33, maximum accepted packet/patch shapes, malformed-input rejection, rollback/recovery, allocation failure, and error reporting. Exercise the same worker under realistic USB/QSPI/interrupt activity and repeat enough runs to cover scheduling variation. Capture task identity, stack capacity, high-water result, canary status, reset/watchdog state, heap/reserve telemetry, and exact image hashes. A pass must leave a documented margin against the configured stack limit; one sample or an unchanged V48 margin is insufficient.

No source, build, image, or hardware was changed or tested for this audit.
