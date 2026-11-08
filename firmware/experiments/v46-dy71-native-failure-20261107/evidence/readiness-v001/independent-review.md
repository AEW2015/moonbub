# Independent V46 diagnostics review

2026-11-07. Reviewed the frozen candidate at `C:/moon/publish/firmware/experiments/v46-dy71-native-failure-20261107` against V45. No production source edits or hardware access were performed during this review.

## Decision

**No blocking source defect found in the reviewed diagnostics delta.** This is approval for a bounded diagnostic build/test, not proof of target stack safety, twelve-frame playback, or a fix for the V45 failure. Target build, exact identity verification and measured stack/heap checks remain required.

The host relay now narrows the physical history: frames 0–2 received matching status-2 presentation replies; frame 3 received status 3 after completed-prefix ACKs; uploader exited 1 without timeout; frames 4–11 were withheld. This supports deliberate receiver failure at frame 3, rather than a missing first ACK or later transmitter timeout. It still does not select the native failure branch or cause.

## Behavior and authority

- `native/endpoint.hpp` and the decoding/gating semantics are unchanged. Native diagnostics are a separate getter, not a synthetic HC70 command, and do not overwrite the previous transaction identity/reply.
- `network_driver.rs` retains all original Prepare, commit and abort predicates. Changed expressions compute the same rejection conditions and additionally retain a mismatch mask. Payload slices are indexed only after the 72-byte length check; the tag conversion to a 16-byte array is guarded by that same check.
- No extra Prepare/commit/abort, reset, transfer ACK, admission credit, FPGA command or endpoint release is introduced. Existing post-mutation quarantine/held lease behavior remains intact.
- The precise last HC70 opcode distinguishes initial Prepare from op5/op6 service while Source phase remains NATIVE. The retained accepted identity and native gate status allow the next failure to test the previously unresolved reference-state alternative.

## FFI and lifetimes

`v46_hud_diagnostics` writes exactly 24 `uint64_t` values; Rust supplies `[u64;24]`. Text capacity is explicitly supplied as 96 bytes; C copies at most that capacity and separately returns full text length through `size_t*`, matching Rust `usize*`. Stats remain six `size_t` values, matching `[usize;6]`. No cross-language C++ struct layout is assumed. The largest/free callbacks use the existing C ABI and target `usize`/`size_t` pairing.

The native pointer is the existing exclusive live `Hud` owner. Getter access occurs before dropping that owner. `gate` is constructed by the successful Endpoint constructor; its accepted shared pointer is copied temporarily without a new allocation or accepted-state mutation. The getter does not retain pointers into Rust buffers. Rust `transact` response lifetime remains tied to the caller's output buffer, and does not borrow the Hud after the call; added diagnostic mutation is therefore compatible with subsequent payload checks.

`identity_valid`, `reply_valid` and `tag_valid` are reset before each real transaction. Old backing numeric values may remain, but are explicitly invalid when a new transaction fails before replacing them. The exported `native valid` flag must govern interpretation of the native array, and `probes` governs free/largest availability; absent measurements must not be read as measured zeroes.

## Allocator diagnostics

`Arena::allocate` keeps its budget, reserve and malloc acceptance predicates. The new failure record is fixed-size; normal successful allocations do not call the largest-block observer. Allocation-failure callbacks sample free/largest only on the failure path. The target callbacks use ESP heap queries and do not allocate or log; their noexcept use is appropriate under that contract.

The diagnostics add Endpoint/Rust-owner storage and failure-path heap-query work. They can perturb memory layout and failure timing despite unchanged admission policy. A different V46 result must not be called an isolated decoder fix. Final free/largest remain post-unwind values; the new failing-allocation fields are the relevant evidence when their probe bits are present.

The allocator-overflow failure record stores the requested element count, whereas ordinary allocation records store bytes. Interpret `kind=4` accordingly. This is a documentation limitation, not an unsafe allocation or changed rejection decision.

## Failure-only FPGA reads and cleanup

On error, `PassiveFpga::read_once` performs exactly six reads: 0x350, 0x354, 0x358, 0x35c, 0x360 and 0x110. It does not write. Each result is retained independently as `Result`; contention, epoch change or I/O failure does not replace the original driver error. The existing Adapter keeps address bounds, nonblocking Device lock acquisition and program-epoch checks.

These reads happen before health/export and `source.inner.failed()`. Thus failure feedback is delayed by six existing SPI transactions and diagnostic work. There is no new polling loop, deadline extension or cleanup command; the underlying SPI driver's existing completion bounds still apply. The passive samples are sequential observations, not a coherent atomic FPGA snapshot. Health read/QSPI counters include these extra six attempts when issued, which should be stated when comparing V45 counts. Retained endpoint/quarantine behavior is unchanged after mutation.

## Export and stack bounds

The retained diagnostic arrays/text/counters are fixed-size. Failure strings are hex-encoded into three parts of at most 32 bytes each, with original length and truncation explicitly recorded. Export still sends at most one record per 40-ms tick, with count/index/digest coverage and no catch-up burst. No synchronous giant Diagnostics Debug line was added to the network error path.

The network worker remains 16 KiB. New diagnostics add bounded local copies and retained storage; static size and bounded formatting do **not** prove maximum target call-stack use. The V45 observed low-water of 4,776 bytes is encouraging historical evidence, not a V46 guarantee. Check the target's measured minimum after the optional cold CPU probe and bounded cached12 trial. Existing telemetry tests explicitly cover long fields, corruption/truncation detection, fixed storage and diagnostic line-length bounds; target ABI/compiler behavior remains a separate build gate.

The optional new USB-I probe has an 8 KiB lazy worker, 98,304-byte arena, 8,192-byte per-allocation physical reserve, 150,000-byte preflight and ROM-only HU fixtures. Its host typecheck and actual-native first12 golden-word/exception tests passed. It exercises cold target-native semantics without FPGA/radio access; it does not reproduce the network workload's fragmentation, concurrent allocations or owner timing.

## Remaining evidence gaps

No new fix should be selected before inspecting the next real failure's local stage, actual opcode, native reply/exception text, allocation failure record, accepted identity and FPGA read results. Exact software-request ticket and call start/end timestamps are not newly retained; passive status cannot reconstruct every prior owner transition. A failure inside an outer C catch before native gate status updates can leave older gate fields alongside the newer Rust FFI failure; last-call validity/stage/opcode takes precedence.

Hardware remains untouched by this review. No stack-overflow, heap-exhaustion, decoder or FPGA cause is asserted.
