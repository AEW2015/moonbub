# V114: reserved control and application-specific restart chunks

Branch: `study/gamebub-v114-reserved-control-20261108`.
Base: `3c2f644933d438c3ecb6d74677b896a3e2b42e38`.
Status: **functional qualification passed; routed timing remains open**.

V113 improved service cycles while failing routed setup at both 100 and
125 MHz. V114 first addresses the actual cross-module ownership/readiness
paths. Public command acceptance reserves capacity and captures the complete
command; registered local delivery and owner-qualified cancellation separate
that event from distant ingress enables. Public revocation masks and accepted
physical memory drains remain part of the functional contract.

The focused actual-top control campaign passes both seeds: 78 directed checks
and four real scratch/reference abort/reset drain cases per seed. In each run,
77 accepted commands equal 75 deliveries plus two canceled pending commands.
The full independent decoder/transport regression now passes 44 case profiles,
42 directed checks, and 24 transport profiles plus four abort/reset retries.
Both seeds produce the exact frozen canonical output. The API adapter adds a
pending-command eligibility check while retaining every original assertion
(144 `need(` occurrences including the helper definition); it
waits for registered child delivery before interpreting child counters.
See [functional qualification](spatial.md) and [control contract](control.md).
Frozen V113 sources and old exact-cycle checkers remain unchanged.

The [peer-fault campaign](control-peer.md) also passes eight fault cases and
eight complete canonical retries in each of two seeds, including real accepted
read/write replies and queued replay cancellation.

The optional [prepared-prefetch candidate](prefetch.md) computes private scratch
addresses before their use, retaining current cache priority and existing public
cycles. Two paired seeds pass 72 transactions, 128 corrupt cases, four read-owner
cases and 48 DC boundary cases each. The combined candidate passes the same
44/42 canonical and 24/four transport
qualification. Its [recovery provenance](optimized.md) separates completed
certificates from newly executed transport work. Routed timing remains a
separate adoption gate.

The [service-cycle ledger](performance.md) separates actual cycles from
conditional clock conversions and the still-open full decode latency target.
The [reproduction guide](reproduce.md) records the bounded commands and gates.
The [final functional audit](functional-final.md) checks the selected proofs
and distinguishes inherited, reused and newly executed evidence.

In parallel, the [restart-chunk prototype](syntax.md) compares two explicit
experimental formats with exact Python/native coefficient round trips. Compact
headers improve the byte cost of independent BR88 contexts. It is not enabled
in the unchanged CS88 timing candidate or production firmware.

The [inventory](inventory.md) distinguishes existing Sunshine serialization,
JPEG firmware/parent execution and custom component proofs from missing
CS88 encoder negotiation, production QSPI/CDC, full-parent memory service,
C2/HUD validation and display publication. The original
[V111–V115 roadmap](../gamebub-v111-v115-simulation-spatial-plan.md) keeps those
gates visible. A source-level codec experiment or OOC component pass cannot
close the 300-frame complete-parent, sustained hardware 30-fps or validated
under-10-ms milestones.

All three fresh routes fail setup: control-only 100 MHz at −1.670 ns,
prepared-prefetch 100 MHz at −0.965 ns, and prepared-prefetch 125 MHz at
−2.696 ns. Hold, pulse-width and routing-error counts are zero. The
[routed results and next gate](timing-summary.md) distinguish each target's
actual critical paths, physical packing and DSP mapping. No candidate is
timing-qualified or adopted; the full V114 parent exit remains open.

Native measurements use fresh RTL at actual 10/8 ns with the same
Default synthesis/opt/route and ExtraNetDelay_high placement method as the six
retained controls. No timing exceptions, guessed I/O delays, strategy sweep,
hardware contact or bitstream generation is introduced. Vivado MCP again
reported `Transport closed`; the existing Artix-enabled 2026.1 CLI and read-only
license are the explicit fallback. Verilator is the selected behavioral backend.
