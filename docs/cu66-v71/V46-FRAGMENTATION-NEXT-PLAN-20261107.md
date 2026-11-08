# V46 fragmentation evidence and focused next plan

2026-11-07. Read-only analysis of V46/V027 physical evidence. No candidate edits or hardware operations were performed.

## What the target now proves

`C:/moon/dev/evidence/v46-v027-network-20261107-run01/usb01/serial.raw` retains the native failure, including identical read-only re-export:

- Prepare op1, frame3/generation4/reference2, native reply4 (DecodeRejected).
- Native exception text: `HUD allocation unavailable`.
- Failing allocation kind3 (malloc returned null): requested11,520; arena live73,224; physical free35,284; largest contiguous block7,680; probe bits3 (free/largest measured).
- Arena cap98,304; peak92,235; native accepted frame2/generation3/reference1 retained.
- Passive FPGA reads show owner11, accepted3, presented3, rejected0, underruns0, staging error0. These are sequential post-failure observations, not a coherent prior-time snapshot.
- Cold CPU-only12 passed. Host received status2 for frames0–2 and status3 for3; later frames were withheld.

The request passed both logical policy checks:73,224+11,520=84,744<98,304, and35,284−11,520=23,764>8,192 reserve. It then failed the real allocator. Largest7,680<11,520 explains why sufficient aggregate free memory did not provide a suitable contiguous block. This is direct evidence of a contiguous-allocation/fragmentation limitation at this allocation, rather than an exhausted arena budget, failed reserve check or stack diagnosis. It does not describe the complete ESP heap-region layout or prove which earlier allocation split the last suitable block.

## Specific 11,520-byte allocation

The fixed HUD rectangles in `native/generated_constants.hpp:7` are160×24,160×24,320×24 and240×24. Their RGB565 output sizes are7,680,7,680,15,360 and11,520 bytes.

Frame3's fourth patch (zero-based index3) is HS33 mode9, so `plain=mode&7=1`. In `native/hud.hpp` the prediction borrows immutable `reference->words`; it does not allocate a prediction copy. `decode_patch` then executes `out.assign(w*hh,0)` before decoding its channels.240×24×sizeof(uint16_t)=11,520 exactly. Its mapped channel output is a byte vector of5,760 elements, not11,520. The mode9 route has no motion-vector/prediction allocation. This makes the fourth patch RGB565 output the specific source-level match to the observed request; no runtime call-site ID was recorded, so this mapping is an inference from the actual packet route and unique geometry-sized request, not a recorded return address.

At this point the accepted prior HUD (~42,240 pixel bytes plus metadata) must remain alive. The already decoded candidate's first three patch outputs occupy30,720 pixel bytes (7,680+7,680+15,360), consistent with recorded live73,224 after small container/metadata overhead. Those persistent candidate allocations surround transient Huffman tables/symbols/channel byte vectors from earlier patches. `channel33` can hold decoded symbols plus expanded channel output; Huffman uses separately allocated map nodes and vectors. These short-lived allocations can leave holes between the accepted and candidate pixel vectors. Accepted data cannot be freed or overwritten early: frame3 references frame2, and commit requires actual external drain/owner authority.

## Why cold CPU12 differs from the network trial

The CPU probe uses read-only ROM HC70 wires, so it allocates no per-frame HU input buffer. Its native owner begins before Wi-Fi, sockets or the network Input object; it runs one bounded native sequence without network-task allocation churn. This establishes target-native semantics and exception handling for those inputs, not network-time heap topology.

The network worker first acquires the hardware owner, brings up Wi-Fi, checks free/largest, creates the native endpoint, opens UDP and constructs Input. For each frame, cached mode allocates a new exact-size Rust HU wire (HU length+36) before ingress; frame3's wire is7,376 bytes and remains live through native Prepare. The previous frame's input vector is freed after successful Prepare. Accepted native patch vectors survive commit, while native decode temporaries and next-frame HU allocations have interleaved lifetimes. Wi-Fi/lwIP/SDK allocation activity is outside the native arena budget. Total-free reserve alone cannot guarantee a later11,520-byte or15,360-byte block.

Do not relax98,304 or8,192; the existing error is a correct fail-closed refusal. Do not free accepted state, fabricate commits, overwrite accepted prediction, change transport or rebuild FPGA to work around this ESP allocation failure.

## Smallest candidate to evaluate offline first

**Try largest-patch-first candidate construction while retaining canonical patch order in the final cache.** This is the smallest focused lifetime/order change worth testing before introducing a new allocator:

1. Parse/validate all four component views and their fixed rectangles without copying payloads.
2. Size the output patch descriptor vector once for four entries.
3. Decode in descending output-byte order: indices2,3,0,1. Place each result in its original index. Each predictor still reads only the immutable accepted patch at the same canonical index.
4. Preserve the existing per-patch and final envelope tags, accepted/candidate transaction rules, memory cap and physical reserve.

This allocates15,360 and11,520-byte outputs before small outputs and transient small allocations consume suitable blocks. It adds no persistent pixel buffer and changes neither wire format nor valid decoded output. It may change which invalid component is reported first; all components must still pass before candidate admission. It is a hypothesis, not a guaranteed fix: a pre-existing heap can already lack the required block at Prepare entry. Measure complete allocation peak and prove all modes against golden words before selecting it for hardware.

The alternative of always preallocating both entire HUD banks consumes84,480 pixel bytes permanently and can squeeze Wi-Fi/scratch capacity; do not adopt it as the first change without an explicit SRAM budget. A single98KiB malloc arena is also unsuitable without a proven contiguous block and initialization budget.

If ordering does not solve the representative fragmented-heap test, the next bounded storage design is reusable output blocks reserved before transient decoding (eventually a per-owner pool with explicit fixed blocks). That requires preserving double-state rollback, accounting every reserved byte against the same cap, and testing prediction modes that currently transfer owned motion buffers. It is a larger change and should not be mixed with the first experiment.

A fixed reusable max-HU input buffer can reduce per-frame Rust allocation churn, but adds memory compared with small-frame exact allocations. Evaluate it separately after native output order; allocating it before Wi-Fi requires a complete early-allocation/readiness budget rather than weakening current guards.

## Fragmented-heap reproduction and acceptance

1. Retain the original V46 native sources and exact twelve Prepare ROM fixtures as the failing control. Run real native decode and golden HUD comparisons for both implementations.
2. Capture a host allocation/free lifetime trace with stable allocation IDs, requested sizes, frame/patch/channel boundaries and accepted/candidate ownership. Avoid interpreting host malloc success as target evidence.
3. Build a test allocator using the ESP-IDF-matched TLSF/multi_heap implementation, with fixed backing region(s), realistic alignment/metadata and deterministic pinned holes representing Wi-Fi/socket/HU lifetimes. Use a dedicated pool, not the system host malloc. Supply real total-free/largest callbacks from this pool.
4. Exercise at least a precondition with aggregate free≥35,284 and largest7,680 at the observed allocation. The original must fail the real11,520-byte malloc while retaining accepted frame2. This demonstrates allocator fragmentation, unlike a total-free arithmetic model. Treat an injected `fail(request==11520)` test only as an exception-path control.
5. Replay identical pinned-hole and transient schedules for the proposed order. Compare all253,440 golden words and every output tag; check arena cap,8,192 reserve, no leak and accepted/candidate rollback. Add invalid-tag, low reserve, fragmented-no-fit and failure-after-partial-decode cases. A candidate must still fail cleanly when no valid allocation schedule can fit.
6. Use both 32-bit target-relevant allocation sizes and host ABI runs. A trace-derived synthetic topology is not the exact live ESP heap; document that limitation and vary hole placement/sizes rather than tuning one favorable layout.
7. Only after offline evidence, build a new app with unchanged V027. Run cold CPU12 first, then the same network cached12 once. Require12 real presentation replies,253,440 HUD comparisons, no allocator failures, cap/reserve preserved, target stack low-water and complete diagnostic export. Keep the original V46 rollback artifacts.

The next hardware objective is a reliable twelve-frame bounded sequence. The current ~seconds-per-frame diagnostic path is still separate from a sustained30fps streaming claim.
