# V113: spatial inverse pipeline and custom-packet integration

Branch: `study/gamebub-v113-spatial-pipeline-20261108`.
Base: `0ac58eb19cb634186ad5a65da4f5e1fd70409c27`.
Status: **functional composition and actual custom transport PASS; routed timing FAIL at 100 and 125 MHz**.
This continues the [V111–V115 roadmap](../gamebub-v111-v115-simulation-spatial-plan.md).

## Architecture and contracts

The experimental source starts from the actual V112 18-body composition,
then replaces context geometry, scratch ingestion validation and inverse
scheduling. The production parent remains unchanged. Count is still the
retained control, and V112 remains a negative timing diagnostic rather than a
qualified replacement. The [inventory](inventory.md) pins the actual sources,
controls, physical memory and integration gaps.

- [Context geometry](geometry.md): prepare byte quotient/remainder contributions
  and final geometry on existing Rice request/wait edges. Both complete-context
  and private-stage probes preserve public cycles, invalid-cycle observations,
  counters, full32/default behavior and the prior Count specialization scope.
- [Scratch phase validation](scratch.md): validate each constant phase before
  selecting a one-bit result. All eight phase encodings, raw/DC/AC behavior and
  original error priorities are retained, with no public latency change.
- [Inverse IV113.1](inverse.md): accept a complete coefficient tuple, validate
  registered operands, then commit to its reserved bank/word. Two finite result
  slots separate arithmetic from emission. A completed result is physically
  copied before the math bank is released; held output keeps its slot until
  sample 63 transfers.

IV113.1 intentionally changes public latency and diagnostic lifetime. It keeps
accepted values/identities, held offers, ordered results, EOF, fault and local
flush requirements explicit. Its coefficient intake is II=2, not one per
cycle. The selected standalone benchmark improves AC-heavy cases but regresses
the zero-coefficient fast case; overlap alone is not a uniform speedup.
The enclosing PCTL1 supervisor, unique external session/transaction ownership
and complete parent are not implemented by this unchanged-port inverse module.

## Full-component and transport evidence

The full-component runner uses the original independent 496-line coefficient,
dequant/residual/pixel/reference/memory ownership bench unchanged. A passing
new-contract run must satisfy its original value, ordering, held-data, error,
counter and accepted physical-drain assertions and match the old canonical
pixel files. Old stdout/event cycles are not required to match under IV113.1;
the frozen exact-cycle checker is unchanged.

The [separate custom transport chain](spatial-harness.md) connects actual V97
forwarding RTL to the actual CS88 decoder through ready/valid byte handshakes.
It models a synchronous parallel DMA adapter with actual 2,048-byte FIFO,
two descriptors, returned credit and ACK identities. Ingress commit remains
distinct from decoder completion and a drained, checked tentative candidate.
It does not serialize QSPI pins or execute ESP32 firmware or native Sunshine.
The retained V112 JPEG test remains a separate comparison path.

The [lane study](lane-study.md) bounds conditional 1/2/4-lane resources and
shared input/consumer bottlenecks using actual source and benchmark evidence.
Two or four compute lanes have not been instantiated or routed. No spare RAM
port, linear speedup or modeled hardware FPS is assumed.

The selected [spatial receipt](../../experiments/python-gamebub-v113/spatial/results.json)
qualifies 44 full-component case/profile rows and 42 directed checks across two
seeds. Both original full-component campaigns ran in the first attempt and
passed; that attempt then failed in the separate tool-header adapter compile.
The final adapter-only retry reuses those pinned component certificates and
records **zero newly executed canonical rows**. It newly executes both actual
transport campaigns: 12 successful profiles and two abort/reset canonical
retries per seed. Both reach the full 2,048-byte FIFO/credit bound and two
descriptors, reject wrong tokens, check held ACKs, and match prior canonical
pixels exactly. The failed attempts remain retained.

## Measured cycles

The [performance report](../../experiments/python-gamebub-v113/performance.json)
uses 24 successful case/profile rows across both seeds. It excludes provisional
output prefixes from rejected frames. First accepted component byte to local
done spans:

| Service profile | Minimum cycles | Median cycles | Maximum cycles | Conditional range at 125 MHz |
| --- | ---: | ---: | ---: | ---: |
| Fast deterministic service | 642,491 | 1,012,911 | 1,383,951 | 5.140–11.072 ms |
| Stalled service | 1,760,941 | 2,085,462 | 2,464,059 | 14.088–19.712 ms |

These are measured RTL cycles with hypothetical clock conversions, not achieved
hardware latency. Local done is after the bench's tentative canonical checks
and real reference/memory drains; complete C2/HUD seal and publication remain
absent. The slower fast-service case already exceeds 10 ms at an assumed
125 MHz. Timing closure alone will not close the complete under-10-ms goal.
The stalled profile uses the same seeded policy, but changed scheduling changes
random draw times; it is not an identical service trace.

For the fast-service seed-107601 complete cases, whole-case cycles fall from
1,478,420 to 1,281,738 (`actual_001`, 13.3%), 1,196,953 to 1,021,013
(`actual_006`, 14.7%), 1,051,188 to 923,623 (`actual_043`, 12.1%), and
1,726,035 to 1,392,053 (`actual_031`, 19.3%). The structural all-copy case
stays at 650,593 cycles. These whole-case cycle comparisons have a different
start fence from the first-byte-to-done distribution above; neither includes
native Sunshine, an ESP32 CPU or a displayed frame deadline.

## Physical study and remaining gates

Both initial native runs completed with exit code 0, unchanged sources/recipes,
the requested clocks, and zero hold, pulse-width or routing failures. Both
fail setup. The candidate is **not adopted**, and neither result qualifies for
the positive-only fresh-repeat slot. Retained controls are reused, not rerun.

| Source / clock | WNS ns | TNS ns | Setup failures |
| --- | ---: | ---: | ---: |
| Count100, frozen | −1.022 | −1,125.069 | 4,620 |
| V112100, frozen | −1.034 | −2,028.748 | 5,607 |
| V113100, fresh | **−1.686** | −3,190.694 | 8,220 |
| Count125, frozen | −3.264 | −40,607.203 | 34,864 |
| V112125, frozen | −2.844 | −32,490.680 | 33,323 |
| V113125, fresh | **−3.303** | −48,746.754 | 44,277 |

The [aggregate receipts](../../experiments/python-gamebub-v113/results.json)
and [comparison CSV](../../experiments/python-gamebub-v113/native-comparison.csv)
bind actual route reports and same-clock controls. At 100 MHz the worst path
starts at inverse fault-pending state and ends at an ingress fetch-index
enable; at 125 MHz it starts at inverse acceptance state and ends at an ingress
prepared-request-address enable. These are cross-module control/readiness
paths. The arithmetic overlap improved cycles while these routed timing
results worsened; the three edits were tested together, so the data do not
isolate the physical cost of an individual edit.

The routed one-lane component uses 36,367 / 36,976 LUTs, 39,212 / 39,225 FFs,
38 BRAM tiles and 42 DSPs at 100 / 125 MHz respectively. Slice occupancy is
91.31% / 92.56%, despite the smaller fraction of DSPs occupied. Spare DSPs do
not establish placement room, new memory ports, full-parent fit or timing for
additional lanes.

The [policy](../../experiments/python-gamebub-v113/study-policy.json) permits
two initial fresh-RTL component runs at 100/125 MHz, plus one fresh repeat only
after a genuinely positive terminal result. The same Default synthesis/opt/route
and ExtraNetDelay_high placement method is retained. Every prepared card binds
actual proof/source/recipe/image/clock hashes. No timing exceptions, guessed
board I/O delays, retiming or strategy sweep are introduced.

Root coordinates at most two heavy jobs, each two CPUs and 8 GiB RAM with an
equal RAM+swap ceiling, available-memory/PSI gates and finite watchdogs. Native
runs also retain the combined RAM/swap secondary guard. Vivado MCP returned
`Transport closed`; the existing legitimate 2026.1 CLI and read-only license
are the explicit fallback. Verilator is the selected behavioral backend.

See [reproduce.md](reproduce.md) and the independent terminal
[100-MHz](spatial-100-final.md) / [125-MHz](spatial-125-final.md) audits for
commands and scopes. Full production
firmware/GP-SPI/DMA, native Sunshine custom encoding, C2/HUD seal and display
publication, physical parent/CDC/I/O/memory timing, sustained hardware 30 fps
and validated complete decoding below 10 ms remain open.

Retained failures and corrections are listed in [attempt-history.md](attempt-history.md).
The [warning review](synthesis-warnings.md) inspects the actual synthesis prefix
and source locations; it is not a blanket warning waiver or final signoff.
The [next scratch cut](next-scratch-cut.md) records a registered prefetch-plan
proposal tied to the provisional synthesis path. The broader [next steps](next.md)
keep clock, memory service, coding changes and complete harness integration as
separate measured gates.
