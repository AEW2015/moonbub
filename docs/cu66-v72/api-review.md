# V72 accepted write contract

The controller and adapter workers agreed these interfaces before integration.
The final source, tests and model use the following definitions. Exact output
checks are separate from timing and physical-implementation qualification.

| Boundary | Contract |
| --- | --- |
| Controller request | One `valid && ready` captures aligned x16 address, all 128 data bits and 16 byte enables |
| Byte order | Bus word `i` occupies bits `16*i +: 16`; enables `2*i` / `2*i+1` select its low / high bytes |
| DQM | Active high masks the byte, so it is the inverse of the corresponding byte enable |
| Burst ownership | The controller owns all eight beats after acceptance; the producer may change its inputs afterward |
| Visible completion | All eight physical beats and write recovery have completed; enqueue/acceptance alone is insufficient |
| Masked beat | Occupies a bus beat; disabled bytes retain their previous values. Final-beat recovery is still charged |
| Canonical row | Four x16 words occupy the lower or upper half of the aligned burst; masks `0x00ff` / `0xff00` |
| Canonical tile | Eight independently drained row bursts, then one identity-qualified tile completion |
| Painter | One full `0xffff` burst per eight contiguous portrait words; no scalar-ACK coalescer |
| Scalar fallback | One x16 word expands to its aligned burst position with exactly two byte enables |
| Adapter validation | Reject unaligned, read-with-burst, zero-mask or enabled-outside-allocation requests before SDRAM issue |
| Cache ordering | Invalidate every matching physical BL8 tag in both scalar clients before a valid write; later requests cannot overtake it |
| Reset | Ready/idle are false during controller reset. All owners/adapters and both clock domains need coordinated flush and fresh ownership |

Canonical half selection uses the **actual row address**, not only the tile's
starting address: chroma pitch 180 words alternates lower/upper placement.
Each half-row preserves the other four words. No producer waits for an
unfilled burst whose missing data cannot arrive until that producer's ACK.

Abort before acceptance suppresses work. Abort after acceptance drains the
accepted burst, suppresses the adapter's normal result and reports the abort
only after drain. Previously written candidate words are not rolled back;
transaction ownership prevents their publication. Reset may leave a partial
candidate prefix and clears modeled protocol state; this is not proof of
physical SDRAM recovery or rollback. The controller's read responses cannot
be backpressured, so the existing LCD elastic buffer must absorb the whole BL8.

The processor HUD path retains scalar admission and its sequential-word guard.
Its whole-frame semantic/tag and completed-word fence remain unchanged. A later
HUD burst API needs its own coverage/count contract before it can replace this
fallback.

Tests cover both half placements, mixed byte masks, guards, payload mutation,
read-after-write through both caches, response holds, abort at accepted burst
positions, reset prefixes and fresh progress. The independent review found a
ready/idle reset-edge exposure in the initial low-level interface; the final
controller gates both outputs with reset and adds a direct regression. The
superseded source and evidence are preserved in `system/before-reset-gate/`.

The painter also rejects overlapping Y/U/V/HUD/RGB allocations, RGB misalignment,
invalid generation/frame IDs and overflowing ranges. Its standalone bench
charges an accepted write before completing it, but applies each whole burst
at response time. Physical per-beat mask/reset behavior is tested separately
through the real controller/model; do not treat the painter bench as that proof.
