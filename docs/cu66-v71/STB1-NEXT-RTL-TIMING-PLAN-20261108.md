# Next STB1 RTL timing plan

Keep the selected V001/V028 image and recovery artifacts fixed. V003 physical replication finished but failed setup; use its reports to guide the next isolated source experiment. Do not replace a timing pass with a tool-success-only result.

## What the evidence actually says

V001's routed worst path is hud_gen_reg[7] ? HUD identity/result/receiver eligibility logic ? LUT4-driven control_plane/E[0] ? hud_ticket_reg[4]/CE. It has +0.005 ns setup slack, 9.637 ns data, nine logic levels and 82.276% routing. The source generation bit has only two loads; the final CE net has324 loads.

The controller captures hud_gen, hud_ticket and other request metadata on `hud_prepare_valid && hud_prepare_ready`; ready is `!hud_pending`. Its separate identity match governs HUD_RESULT/DRAIN and bulk commands. Therefore registering command identity is not automatically a direct replacement for the capture CE cone.

V003 targeted the correct combinational CE driver and created seven LUT4 replicas, but final setup was -0.197 ns / TNS -9.204 ns at105 endpoints. Hold +0.021 ns, pulse +2.000 ns, all56,569 routes complete and DRC warnings only do not make that acceptable. The final worst path moved to command_state_reg[2]_rep ? receiver/bank_generation_reg[2][29]/CE, with12 levels and73.799% route. The target ticket CE was not in the saved worst50; its exact final slack remains unknown. Early -.889 estimated and -.634 first-route values are intermediate evidence, not final results. V002 failed because forced replication is unsupported post-route; that is a distinct stage-support result.

## First source candidate: factor actual request eligibility

Use only the isolated reviewed one-line variant at `C:/moon/dev/experiments/hud-prepare-ce-factor-v001-20261108`:

`hud_prepare_valid ... && !fatal` ? `hud_prepare_valid ... && !fatal_non_hud`.

Request eligibility already requires !hud_requested. Both omitted fatal causes require hud_requested via actual hud_match/hud_write_match. The existing non-HUD fatal predicate retains all other failure causes. Global fatal, error-code priority, receiver state, command identity/result checks, reference/commit and reset semantics stay unchanged. This is combinational factoring with no latency, storage or new reset, not weaker error handling or a timing exception.

Offline gates passed: exact one-line delta hashes, universal64-row two-state Boolean identity, and a source-extracted Icarus miter with266,704 stimuli across three watchdog settings. It covers all16 encodings, simultaneous faults and requested/reset/abort/pending flags, identity/tag/bank/length boundaries and192 directed unknown patterns. This is not exhaustive four-state or full-system sequential proof. Root independently reviewed it and approved fresh synthesis at `C:/moon/builds/stb1-ce-v001`, using V001's79 inputs with only this receiver replaced. Every other RTL file and each XDC/Tcl/clock/pin is unchanged. Do not reuse V003's physical replicas.

Before implementation, inspect actual synthesized cones and reports: is the HUD-generation/result comparator removed from request-capture eligibility, what now drives the CE, and did another path become critical? Source-level factoring does not guarantee whole-chip timing, and V003's bank-generation path may remain a separate limit. Do not claim that Icarus proved a timing benefit.

## Separate optional candidate: registered command identity

Only consider this if the actual remaining critical path warrants it. A registered identity decision would apply to command validation (HUD_RESULT/DRAIN or bulk identity), not directly substitute for the request capture event. The existing mailbox holds until handshake, so validation latency can potentially be absorbed, but that requires an explicit valid/fence contract:

- Clear decision-valid when a new command is submitted, before any consumer can use an old matching result for new fields.
- Bind each result to the pending command sequence and the appropriate HUD request ticket, generation, frame, reference and bank. Reject or invalidate on ownership/fault changes; never silently reuse a cached match.
- Preserve immediate fault/quarantine gates and accepted-operation drain. Do not introduce a one-cycle window that admits an operation after cancellation or uses fields captured for a different owner.
- Respect the real ready/valid capture event. If adding a request skid stage instead, preserve stable metadata, single acceptance, ack timing, backpressure and ownership until drain. Treat that as a different design with separate tests.

Reset only the new valid/pending/fence control necessary to suppress use. Data registers may remain unreset only when no consumer can observe them before the valid contract is established. Configuration INIT does not replace runtime invalidation after joint reset, abort or clock-loss quarantine. Use the existing synchronized/reset distribution; do not add a broad payload reset or turn a reset signal into a fabric clock.

Stale-match tests must include back-to-back matching then mismatching commands; new sequence with identical payload; generation/ticket rollover refusal; bank/owner change; abort/fault coincident with validation or ready; reset between capture and response; valid clear while downstream stalls; and completion/release followed by a new request. Illegal sender activity must fail closed without consuming old operands. No added cycle is qualified just because SPI is slow.

## Required promotion gates

1. Preserve exact source delta and all clock/pin/external-memory constraints. Run bounded local unit/miter cases and the existing full-system KEY/P, packet staging, HUD write/readback, commit/presentation and fault/drain tests against the actual new sources. Do not substitute a same-interface old module.
2. Compare synthesized BRAM/FF/LUT/reset mapping and the actual CE/identity launch paths. Check clock and exception equality, no new missing clocks/internal unconstrained endpoints, and CDC endpoint differences. Two inherited LCD completion critical CDC endpoints must stay explicitly recorded/dispositioned; a positive timing number is not CDC proof.
3. Route the complete design with unchanged directives, then require nonnegative setup/hold/pulse, full routing, no DRC errors and honest external I/O coverage. Compare actual worst endpoints and margin against selected V001, not only the intended local net.
4. Only after root selects a complete passing candidate, assign a new image identity and hash the BIT/source/report package. Do not reuse V028's identity for a changed image. Hardware remains a separate gate: explicit ABI pairing, protected update/recovery, bounded fixtures, native counters, HUD verification and actual display observation.

No new RTL change beyond the isolated reviewed one-line candidate is authorized by this plan. No second Vivado, full-system test or hardware launch is implied; root controls those gates.
