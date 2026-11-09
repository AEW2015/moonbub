# V116: local control timing and overlapping write/hash service

Branch: `study/gamebub-v116-control-rowjoin-20261109`.
Base: `c83718fa0f62c55f948bcc34b32481791d1859e6`.
Status: qualification and all four planned native measurements complete.
All A/B/C functional suites pass; all four routes still fail setup.
C is the best measured 125 MHz candidate at −1.847 ns WNS, not timing closure.

V116 preserves the 720×480 codec packet format and reconstructed YUV420 bytes.
It separates Rice result payload from its reset/error zero view, prepares the
admission plane-selected bounds on existing edges, and introduces an optional
three-slot eight-byte write/ACK/hash pipeline. Filling, accepted physical debt,
and ACK-retired hashing overlap. The frozen byte join remains the control.

## Measured parent results

Each profile uses actual selected decoder, validator/SHA, and bank-publication
RTL with software HUD decoding and finite abstract memory service. Last input
means the last accepted outer FPGA packet byte; completion means validated
commit, including the original C2/HUD/seal work.

| Service profile | Byte control, cycles | Three-slot rows, cycles | Reduction | Rows, conditional ms at 125 MHz |
| --- | ---: | ---: | ---: | ---: |
| Fast | 4,166,111 | 1,416,449 | 66.00% | 11.331592 |
| Stalled | 9,873,327 | 1,844,338 | 81.32% | 14.754704 |

All four runs per composition pass exact 518,400 canonical and 42,240 HUD byte checks, current
owner ACK-before-hash checks, all 1,025 hash jobs, exact C2 root/HUD digest/seal,
accepted bank contents, wrong-ACK debt retention and no-reset clean retry.
Rows use 70,080 physical requests/ACKs while still checking all 560,640 bytes.
Three-slot occupancy and actual three-way overlap are observed, not inferred
from wider request counts. See the [independent terminal audit](../../experiments/python-gamebub-v116/audit/live-parent-terminal.json).
Fresh B and C executions match A's `live_case`, fence, service and verdict
records exactly for every corresponding byte/row profile; the table applies
to all three qualified source compositions.
The final C execution is independently checked in
[live-c-terminal.json](../../experiments/python-gamebub-v116/audit/live-c-terminal.json).

The fast model charges one x16 data edge plus two overhead edges per byte
request, or four data edges plus two overhead edges per row. The stalled model
charges data edges plus 8–16 overhead edges. Each permits one pending physical
request. Stalled variants share the rule and seed, but consume different RNG
sequences and are not identical cycle-trace comparisons. These stricter costs
also differ from V115's memory model; use the V116 byte control for comparison.
No SDRAM pins, refresh/CDC implementation, ESP32 execution or physical scanout
are qualified by this test.

The fast row result misses the strict 1,250,000-cycle budget by 166,450 cycles
when requiring strictly less than 10 ms at a genuinely achieved 125 MHz.
The millisecond column is a conditional normalization, not achieved hardware
latency. One keyframe and retries do not prove sustained distinct-frame 30 fps.
The [integration boundaries](handoff.md) keep those gates separate. The
[source-bound latency study](latency-next.md) identifies the coupled inverse
II=2 and serialized reconstruction limits for the next throughput iteration.

## Timing evidence

The selected V115 control fails setup at −2.974 ns for 8 ns and −0.263 ns for
10 ns. The actual V116 routes so far are:

| Composition | Target | WNS | Setup-failing endpoints | Result |
| --- | ---: | ---: | ---: | --- |
| A | 125 MHz | −2.219 ns | 23,310 | FAIL |
| A | 100 MHz | −0.108 ns | 2 | FAIL |
| B | 125 MHz | −2.238 ns | 26,346 | FAIL |
| C | 125 MHz | −1.847 ns | 16,725 | FAIL |

Hold, pulse and routing checks pass in these runs. B factors the actual owned
abort target and held-payload domain predicate. Its route moves the worst path
to the ingress mode → input validation → pending-record reset/control cone.
C targets that measured cone with two speculative private record banks and a
single-bit publication selection; its focused proofs preserve every old tuple
view on every clock. Its routed WNS improves by 0.391 ns versus B and 1.127 ns
versus V115, but 16,725 setup endpoints still fail. The new worst path is
scratch `read_address[2]` through selected-read/AC legality and error ownership
into `busy_owned/D`: 9 logic levels, 9.794 ns data delay, 75.424% routing.
See the [actual mapped/routed analysis](control-c-mapping.md) for the remaining
source cause and bank-control evidence. No V116 timing PASS is claimed. Timing measures the
18-source decoder body, excluding the
new join, SHA, physical memory/CDC, transport and display parent.

The [execution policy](../../experiments/python-gamebub-v116/study-policy.json)
was fixed before dispatch: at most three 125 MHz source candidates, one 100 MHz
control, and one positive fresh repeat. Source identity uses all 18 alias→SHA
values. No unchanged negative reroute, timing exception, invented I/O delay,
retiming/phys-opt or strategy search is allowed. Each new candidate requires
fresh source-bound behavioral proofs and the previous actual routed cause.
The four initial measurements and three source compositions are consumed.
There was no positive result, so no positive fresh repeat was eligible or run.
This campaign is closed without an unchanged-source reroute or lower-clock
substitution. The [next latency work](latency-next.md) and remaining routed
control-path work are separate gates; neither sustained hardware 30 fps nor
validated under-10-ms hardware decoding is established.

## Functional qualification

- Rice: two parser seeds preserve the historical 1,520-case suite and 6,096
  parameter cases; two production-context ingress seeds pass about 59 million
  exact paired public-output clock checks in total.
- Admission: two seeds retain the original oracle and independent table replay;
  each adds 25,344 full-width boundary and 294 cancellation cases with no new
  public cycles.
- Row join: four seeds, each 30 directed checks and 4,185 independently expanded
  bytes, cover overlap, every ACK field, token wrap, cancel/error/drain and retry.
- Integrated body: 44 case profiles and 42 directed checks; transport adds 24
  successful profiles and four abort/reset retries with a 2,048-byte FIFO and
  two descriptors. Peer tests add 28 complete canonical retries. The actual
  main/transport TSVs contain 48 canonical records and peer TSVs add 28; these
  are sample-byte comparisons, not sustained-stream frames.
- B's abort-target and domain-predicate pairs retain the original generic,
  actual-caller, signed-domain and exhaustive metadata oracles. C adds two
  generic seeds of 1,048,576 coefficient/phase/format cases each, outer-priority
  cases and exact old pending-field comparisons; its two actual-caller seeds
  retain all 207 common public fields and preparation fault/reset checks.
  Fresh B and C body/transport/peer executions also pass with the selected
  five source replacements, rather than reusing A execution.

All original golden hashes, functional oracles and assertions remain active.
The source/recipe/snapshot and actual terminal checks have independent audits
under [audit/](../../experiments/python-gamebub-v116/audit/).
New C++ builds use `-O2` solely to speed host simulation. No clock cycles are
skipped. Root controls at most two heavy jobs, each two CPUs/8 GiB with no extra
swap; available RAM and pressure are the primary launch/stop gates.

## Retained failures and reproduction

The first admission RTL seed passed, then independent Python replay failed
because the captured inputs omitted `generated_constants.hpp`. A fresh run
adds that dependency and passes with unchanged RTL/oracles. Its earlier raw
receipt and snapshots remain; generated compiler/trace working files in that
failed attempt's local `build/` are excluded from Git.

Root stopped the first main/peer compilations before simulation to fix an
intermediate receipt self-hash bookkeeping issue. Fresh runs exclude their own
receipt from the artifact map and pass. No RTL was changed for these retries.
The [attempt notes](../../experiments/python-gamebub-v116/orchestration/attempt-notes.json)
retain the failed/stopped receipts and reasons.

Three later strict compile failures are also retained: B's initially empty new
observation connection, the domain flag's mixed packed-vector drivers, and C's
additive bench assigning a scalar to a wide C++ value. Each failed before RTL
simulation. Fixes retained the original functional checks and assertions;
fresh focused runs passed. Preparation-era source documents remain frozen when
they are pinned inputs; use this summary and terminal receipts for run status.

The [handoff](handoff.md) describes exact source selection and interface scope.
The scripts in `scripts/cu66-v116/` reproduce bounded focused/integrated tests
and native preflight/dispatch; native dispatch requires a fresh independent
preflight audit and legitimate local 2026.1 license. All older evidence is
frozen. [Collected measurements](../../experiments/python-gamebub-v116/results.json)
keep functional, native, full-parent and hardware milestones separate.
