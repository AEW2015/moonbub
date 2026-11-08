# Independent V45 ingress-cache / native / count-binding review

November7,2026 (America/Denver). Read-only review of the current candidate; no source edits, hardware access or transmission. Exact reviewed file SHA-256 values are recorded in `INDEPENDENT-REVIEW-PINS.json`. Later changes outside these pins need an explicit addendum/revalidation.

## Verdict

**No new correctness/ownership blocker found in the reviewed changes.** This is a code-boundary review, not target memory/stack, timing, RF or physical playback proof. Target build, exact-system replay and the receiver readiness receipt remain separate gates. V44's retained physical endpoint must not be replaced or force-released by this work.

## Ingress cache and lifetime

- Frame count is checked1..12000 before bus IO; diagnostic storage stays fixed at three records. Header length80..49152 and checked HU offset/end arithmetic are validated before START. Zero/over20000 HU lengths fail. Cache mode allocates exactly one `HU_length+36` HC70 input buffer earlier, rather than allocating a duplicate HU buffer or a complete-frame cache.
- The early buffer allocation can fail before this frame's START. It still coexists with the prior accepted native cache and is fallible; it does not prove a reserve for every possible future packet. Subsequent native allocations keep the real physical8192-byte reserve. Earlier wire-buffer allocation changes its lifetime across staging but not its peak native-call size. The new twelve-frame model is useful evidence, not a substitute for target heap/fragmentation checks.
- For the real network Source, `header()` and the pending first chunk originate from the same validated datagram. Cache mode additionally compares the first streamed76bytes exactly with the supplied header prefix before forwarding payload words. This comparison occurs **after staging START**, so a malicious/inconsistent generic Source fails without native preparation/publication but not necessarily before all FPGA mutation. The existing failed/mutated-owner retention rules remain necessary.
- Every Source chunk must have the exact remaining bounded length and current offset. `cache_hu_chunk` uses checked ranges and copies only the HU overlap into HC70 payload bytes32..32+HU_length. Its expected destination byte count detects skipped/replayed HU overlap; framing/trailer bytes are left untouched. Cached input remains owned until the synchronous native transaction returns and its response identity/tag is checked, then is dropped.

## Integrity and live authorities

- Cached bytes are not used for native PREPARE merely because they were received. Driver first requires complete streamed CRC, exact cached HU byte count, actual FPGA staged/stored counts, FPGA CRC and zero staging error; then seals and admits through the existing mailbox authorities.
- It waits for a live HUD request and stable ticket snapshot, checking generation/frame/reference, HU offset/length, key flag and bank bounds. Native response length/state/word count, generation/frame/reference and output tag must match that request before any pixel-write authority is granted.
- Cached mode removes command21 **only for compressed HU retrieval**. It preserves actual HUD writes, actual full pixel readback comparisons, native acknowledgment, tagged HUD drain, real software COMMIT/ABORT acknowledgment, owner status, presentation count, canonical tag and front-frame checks. No ingress/stored ACK is promoted into a presentation ACK.
- The cache path no longer independently rereads staged compressed HU bytes. Its equality argument is the existing full-packet staging integrity contract plus the live identity/tag checks, not a new byte-for-byte FPGA HU readback claim. Pixel HUD readback remains real. Standard CRC checks are not a cryptographic transport/authentication guarantee.
- Scalar `run_sequence` remains an explicit control. Its later HU buffer/command21 retrieval and all subsequent native/HUD/commit checks are retained. Cached HU timestamps describe a span during ingress and are correctly labeled separately from post-admission scalar-fetch time; those timings should not be compared as the same isolated service interval.

## Native owned-motion in-place reconstruction

- Plain co-located HS modes1/9 continue to borrow only immutable accepted-reference words; output is distinct owned storage. The accepted cache remains owned by the gate through the synchronous PREPARE, and the local prediction pointer does not escape.
- For owned motion modes2/3/10/11, the local motion-prediction vector becomes `out` and `prediction` points to that stable vector object. No resize/reallocation occurs during the component loops. Each component reads its original predicted bits before replacing only that component's nonoverlapping RGB565 mask. Earlier red/green changes cannot affect later predicted green/blue channels. This preserves per-component residual and row-delta semantics while removing a second complete output allocation.
- Independent mode0 still starts with zeroed output. Range, Huffman/Rice/geometry, exact body and final reconstructed patch/envelope tag checks remain. An exception destroys only the candidate/owned temporary; accepted-reference words are never modified by this path. The actual-native12-frame253440-word comparison and broad457-frame semantic regression support this reasoning, but broad-corpus logical-cap tests do not qualify all inputs under the target arena.

## Finite ring and network count

- Each ordinal resets its ring slot before recording. Returned reports carry actual ordinal, frameID and generation; formatter visits the last retained ordinals and verifies slot identity. Cumulative acceptance/presentation checks use ordinal+1, not ring slot+1. Counts/word totals for12000 remain withinu32, and generation/mailbox sequence increments are checked. This supports bounded finite reuse, not unbounded streaming or restart recovery.
- Actual v3 decoder binds finite `sequence_count`1..12000 at offset46 into packet identity and CRC; replies echo it. `Input::new_for_sequence` validates the selected count. Every datagram is CRC/header decoded and count-matched **before** peer/current metadata is accepted or a Source header is returned, so count-mismatched first packets cannot reach driver START/staging.
- Once latched, peer address/port, session and increasing frame identity remain fixed; subsequent packet identity equality includes count. The header payload's frame/reference must match the envelope. Actual stored-prefix replies follow completed FPGA storage, and `presented()` requires full stored length before the driver's post-presentation call. No new session negotiation, STOP or automatic new-KEY recovery is claimed.

## Remaining limits for the hardware window

- Actual target worker stack, largest allocation and minimum free heap are still physical measurements. ELF static SRAM and host modeled memory are insufficient by themselves.
- Complete stage arrays on error are not retained; bounded active ordinal/frame/generation/phase observations are better attribution but must not be reported as full failed-frame timing.
- Only the final three timing records are retained after long sequences; earlier details are intentionally omitted with counts/identities. A paced/indexed retained snapshot addresses the V44 burst-loss risk, but a complete indexed export must still be verified on physical USB.
- Exact three/12-frame native/canonical/scanout gates and the package/updater identity must be bound to the final selected images. Host models and virtual CPU timestamps cannot establish target FPS.
- Native/FPGA failures still retain/quarantine ownership after mutation. Final success still holds the endpoint/lease. Do not infer that finite count support implements production continuous recovery or permits reconfiguration underneath a held owner.
