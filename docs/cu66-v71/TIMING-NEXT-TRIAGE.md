# Next timing triage after final DY71 STA

Read-only proposals; no RTL, constraint, clock, speed-grade, PHY, build or hardware
change. Wait for **final DY02** routed setup/hold reports before selecting a fix.
The older CU71 implementation06 is evidence about its own frozen image, not a
timing result for the new DY71/validpipe/safe-staging selection.

| Cone | Measured implementation06 | Current interpretation |
|---|---|---|
| Reset→held reference payload R | −1.177ns;11.042ns data,95.870% route,0logic levels | Route/fanout candidate; use separately reviewed same-cycle replica plan only if final DY confirms it. |
| SHA hash_state→working FF CE | −1.177ns;20levels/11CARRY4;67.420% route | Trace crosses digest comparison/fail_now and result-ready/control gating; not simply a SHA round-adder failure. |
| Dequant output→IDCT result S | −1.171ns;17levels/11CARRY4;68.996% route | New validpipe explicitly stages input classification; full-board improvement remains unmeasured. |
| Plane selector→receiver event CE | −1.163ns;14levels/6CARRY4;65.286% route | Packet offset/mux/bounds→fatal→event priority/enable cone. Do not delete or weaken diagnostic events. |
| Entropy header→stream D | −1.161ns;13levels/3CARRY4;63.787% route | Header length validation/prefix arithmetic/control selection is a separate candidate from arithmetic decode. |
| Staging written count→held count CE | −1.154ns;22levels/14CARRY4 | Safe credit successor has matched OOC evidence; do not confuse leaf OOC with new routed board signoff. |

Source: `fpga/experiments/cu66-v71/board/implementation06/setup-paths.rpt`
(routed; first40 paths). DY01's **intermediate** phys_opt log names parser
`vector_end`/`plane_start` nets. That shows optimizer attention, not final slack,
full path identity or proof that this is DY02's next bottleneck.

## Smallest conditional experiments

**SHA completion/control.** Selected `hash/cu71_sha256_bytes_lookahead.sv`
publishes hash_state as digest. `direct-system/validpipe-v003/cu71_base_pipeline_math.sv`
tests its upper128 bits against wanted_tag in HASH_WAIT; fail_now also qualifies
tag/control. The old physical trace returns through canonical result_ready into
SHA CE/word enables. If reproduced, first compare an explicit balanced per-limb
equality reduction against the current mapping, with exact-cycle equivalence.
If mapping alone is insufficient, add a private qualified tag-check stage with
registered limb comparisons, reducing them on the following edge. Keep all
higher-priority write/entropy/scatter/dequant/IDCT/reconstruct/rows errors ahead
of tag mismatch0x50; keep abort behavior and real write drain. Hold the actual
SHA result until accepted, and publish neither tag nor COMMIT early. This adds
declared completion latency, not another SHA-round pipeline or changed digest.
Check malformed tag plus simultaneous higher-priority errors and abort on every
new state, full hash goldens, and whole KEY/P/P.

**Parser vector/plane prefixes.** In selected
`cu66-v69/packet/cu66_packet_control.sv:267`, CHECK_INNER builds16-bit modular
vector_end and three plane starts/addresses from several header lengths in one
edge. If final DY confirms that cone, isolate a registered prefix-sum stage
before READ_REQUEST. Preserve original32-bit validation sums, exact16-bit casts
and truncation, and errors6-before7. Do not derive narrowed “trusted” lengths
from an unchecked header. Keep metadata/plane headers invisible until their
original validation conditions pass. Measure any added private parse clocks;
test malformed/wrap/boundary headers, reset/abort in each new state, and the full
packet/CRC/error-priority suite. Precomputation during header ingestion is an
optional later way to hide latency, requiring a separate validity proof.

**Entropy header control.** `cu71_ab38_decoder_arithpipe_v4.sv:319` combines
CRC-first validation, header checks,32-bit length totals and stream_chunk prefix
construction. A small header-field/prefix capture stage can break this path if
it reappears. Preserve CRC0x02 before header0x03 before length0x04, full operand
width/wrap behavior and fail/abort draining. Do not optimize only the stream FF
or narrow unvalidated h32 fields. This is per-plane header overhead, not a
per-coefficient arithmetic latency change. Reuse all actual1371 entropy fixtures,
directed malformed/error-priority cases and new-state abort/reset tests.

**Packet bounds/event fanout.** Receiver calculated_packet_address is a17-bit
plane-base+relative-address mux; its bounds test feeds fatal0x75 and event_code.
Do not remove bounds checks or register fatal alone while changing acceptance
and first-fault records. First inspect final fanout and actual logic versus
route cost. An isolated diagnostic-only successor could capture the exact event
tuple/sequence/timestamp at its original cycle, write the ring one cycle later,
and bypass the pending record on reads. That requires proof of unchanged event
priority, timestamps, sequence/overwrite counts, back-to-back records, wrap and
CSR read-during-write behavior. It is more than “delay the event_valid bit.”
Alternatively pipeline the accepted packet request with held address/identity
and normal backpressure, but explicitly account for changed timing and all
fatal-priority interactions; do not silently alter event semantics.

**Valid-fenced reset relief.** Conditional candidates are held_ref_pixels512b
(ref_received/tag match fences consumption), captured_tile512b (write_busy fences
its RAM writes), and event payload2048b. Retain all valid/ownership/state resets.
For events, per-entry reset validity plus a zero-return mux must preserve the
existing zero contents visible after reset; simply removing events reset leaks
unknown/stale diagnostics. Prove first-use initialization, wrong-generation
responses, stalls, abort/reset/restart and unchanged qualified outputs with a
four-state simulator. Keep this separate from physical reset-FF replication so
cause and error/diagnostic behavior remain attributable.

No false paths, multicycle workarounds, ideal reset nets, speed-grade changes or
relaxed clocks/IO budgets are proposed. For any selected successor: frozen-source
functional/priority proof → matched exact-part OOC → actual native integration →
full routed setup **and** hold/pulse/route/DRC/CDC. Positive leaf setup and an
optimizer log are insufficient for a BIT or hardware gate.
