# V51 heap probe performance audit ? 2026-11-08

Confirmed optimization candidate: V48's successful native allocations unnecessarily perform full internal-heap block walks. Split the reserve/free callback from the diagnostic-largest callback; retain every existing reserve and minimum-free check. No candidate files were changed and no hardware operation was performed in this audit.

## Source and compiled proof

V48 `handheld/src/cu66/network_usb.rs:6` implements `free_probe` as `let n=heap().0`, then updates MIN_FREE. `largest_probe` at line8 similarly uses `heap().1`. The shared `heap()` at line31 invokes BOTH `heap_caps_get_free_size` and `heap_caps_get_largest_free_block` for INTERNAL|8BIT (0x804). These are foreign calls with observable effects; dropping the tuple member does not remove the other call in the actual build.

Exact target ELF SHA256 `93a389adb4e5bf88fa9eb5d28fc3d82abdb012e4fb647cd50f81196c917aab74` confirms this. `free_probe` at0x420ba77c calls free_size0x42190dc8 and then largest_free_block0x42190e64. `largest_probe` at0x420ba7a0 also calls both. Xtensa disassembly and decoded L32R call-target literals are retained in `v51-heap-probe-audit/v48-probes.disassembly.txt` and `bindings.json`. This is compiled evidence, not an assumption that the optimizer retained the unused tuple field.

`native/bounded.hpp:21` calls free_probe before malloc to enforce `free >= reserve` and `n <= free-reserve`, then again after every successful malloc to update the sampled low-water. Failure diagnostics at line18 invoke largest_probe separately. The V48 physical cached12 result reports2260 successful arena allocations and0 allocator failures: this callback path therefore performs4520 largest-free-block calls in addition to4520 free-size calls. This count excludes the small number of deliberate startup/final heap snapshots.

## Actual local IDF5.4.3 complexity

The selected firmware config pins v5.4.3. Actual local SDK source is `C:/Users/lavat/.espressif/esp-idf/v5.4.3/components/heap`:

- `heap_caps.c:277`: free_size iterates registered heaps, selecting matching capabilities and summing multi_heap_free_size. `multi_heap.c:373` returns the cached heap->free_bytes. Cost is O(number of registered heaps), rather than a walk through each allocation.
- `heap_caps.c:301`: largest_free_block calls heap_caps_get_info.
- `heap_caps.c:367`: get_info iterates matching heaps and calls multi_heap_get_info.
- `multi_heap.c:409`: get_info locks the heap and calls tlsf_walk_pool, whose callback counts both allocated and free blocks and computes the largest free block.
- `tlsf/tlsf.c:205`: walk_pool traverses physical blocks until the terminal block. Thus each largest query costs O(total blocks in matching heaps), with a heap lock held during each pool traversal. It is not TLSF's constant-time allocation lookup.

Actual compiled sdkconfig preserves `CONFIG_HEAP_POISONING_DISABLED=1`, `CONFIG_HEAP_TRACING_OFF=1`. The exact ELF contains heap_caps_get_largest_free_block, multi_heap_get_info_impl and tlsf_walk_pool symbols, consistent with the selected source path. No web or replacement SDK was used.

## Minimal proposed change

Keep a capabilities constant with the same INTERNAL|8BIT value. Implement the free callback with ONLY heap_caps_get_free_size, then perform the exact existing MIN_FREE load/comparison/store and return that value. Implement largest_probe with ONLY heap_caps_get_largest_free_block. Keep the paired `heap()` helper for initial free/largest admission guards, final health and explicit diagnostic snapshots.

Do not remove, rate-limit or move the pre-allocation free/reserve check; do not remove the post-allocation sample. Keep the8192-byte reserve, subtraction guard, arena limit, failure codes and failure-largest reporting. This is a probe implementation change only; it does not change allocations, byte output, C ABI, FPGA image, transport or admission behavior. The removed free call inside largest_probe never updated MIN_FREE, so replacing that callback with largest-only preserves the existing low-water semantics.

## Verification and measured limits

Before promotion, compare control/candidate decoded words/tags and error codes, peak/live/allocation/failure stats, exact callbacks and negative reserve cases. Inject a counting probe to verify two free samples per successful allocation, pre-reserve rejection unchanged, and largest callback only on failure. Rebuild target and disassemble candidate callbacks to prove one intended IDF call each. Re-run the same bounded12 physical test with unchanged V027/fixtures, preserving elapsed/Prepare timing, minimum-free, stack and all failure counters.

The4520 redundant walk count is derived from a retained physical allocation count and exact compiled/source call paths. Target walk duration, contention contribution, percentage of total time and resulting frame rate have NOT been measured. Removing walks may improve CPU/lock pressure but cannot by itself establish the dominant bottleneck, 30fps capability, SDRAM/QSPI throughput or real video support. The old physical cached12 elapsed21.923482seconds is a complete network/native test, not an isolated probe benchmark. No new speed claim is made.

Pinned source/ELF hashes: `C:/moon/maintenance/v51-heap-probe-audit/bindings.json`. Physical baseline: `C:/moon/dev/evidence/v48-v027-local-20261107-run01/NETWORK-RESULT.json`.
