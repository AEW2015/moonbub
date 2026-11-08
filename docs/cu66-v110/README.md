# V110 timing prerequisites and hardware qualification

The target remains **100 MHz / 10.000 ns** on `xc7a100tcsg324-1`, retaining
720×480 CS88 q16/all-BR88 and the 49,152-byte cap. V110's hardware gates depend
on the unresolved V109 integration and timing prerequisites. This iteration
works on those prerequisites; a component route cannot pass the hardware gates.

The measured control baseline is V109 FETCH, WNS **−1.635 ns**. Its response
address cut removes the earlier ingress address launch sources from the top
fifty paths. V109 fault-only remains the better prior diagnostic frontier at
**−1.589 ns**. Every V109 route fails setup at the fixed clock.

**V110 is partial: 100 MHz remains open.** Nine source compositions pass their
fixed two-seed functional qualification, and nine native routes have completed.
The best final WNS is **−1.022 ns**, versus the prior V109 frontier's −1.589 ns.
It still has **4,620 setup-failing endpoints**. Absolute TNS is 86.391% lower
than the actual V109 FETCH control; that reduction does not pass the clock gate.

## Source-bound changes

| Change | Existing-edge behavior | Qualification |
| --- | --- | --- |
| [Private cursor controls](cursors.md) | Clear/advance only private cursor payload locally, restore it before a new owner, and preserve all public cycles. Retired private values may differ. | Two-seed focused public/live-cursor RTL PASS and complete canonical PASS; Runtime route still fails 100 MHz. |
| [Scratch busy predicate](busy.md) | Pair all 63 actual state writes with the exact busy predicate, including DRAIN, reset, dynamic return and final overrides. | Strict focused RTL PASS on both seeds; complete busy-only canonical PASS. |
| [Owned fault pulse](fault.md) | Produce the unacknowledged fault on the original failure edge; preserve actual parent ack/reset/retry priority and all immediate fences. | Strict inverse/reconstruction focused PASS; complete combined canonical PASS. |
| [Producer readiness](ready.md) | Pair active-state and cache-nonzero flags with the original register writes, including reset, abort, count wrap and last-write priority. | Two-seed whole-producer port/RAM comparison PASS; complete ready/Rice canonical PASS. |
| [Validated-caller count specialization](count-domain.md) | Default-false generic checks stay intact; the selected caller opts out only of the AC count bound it already validates. Runtime limits and all other checks remain. | Generic and conditional context plus complete ingress focused PASS; complete decoder canonical PASS; final routed WNS −1.022 ns, still failing 100 MHz. |
| [Owned request addresses](request-address-next.md) | Reuse the frozen request/bounds preparation on existing fetch edges; keep invalid public addresses live and exact. | Reused source-bound V109 focused PASS plus new complete address/cursor composition canonical PASS. |
| [Parallel prefix selection](prefix.md) | Factor guarded prefix rank and take-length selection; preserve all public and stored-state cycles. | Two-seed focused RTL PASS, independent arithmetic review and complete prefix composition canonical PASS. |
| [Rice prefix taps](rice.md) | Remove availability masks only from fixed taps whose consumption remains availability-guarded. | Two-seed public/raw-state RTL PASS; complete ready/Rice canonical PASS. |
| [DSP operand preparation](dequant.md) | Prepare first-beat operands during IDLE and later operands on the preceding MULTIPLY edge. Preserve the original partial output/write/done schedule. | Three-seed focused RTL PASS; complete combined-dequant canonical PASS. |

Nine compositions (busy, fault, combined controls, dequant, readiness/Rice,
parallel-prefix factoring, private cursors, request-address/cursor composition and
validated-caller count specialization) each passed the same two frozen
reference seeds: **44 case profiles and 42 directed checks per composition**,
with exact stdout, public events, cycles and canonical pixels. V109's actual
control is reused and hash-bound, not falsely reported as newly rerun. Original
goldens/assertions and malformed/reset/abort/stall checks remain active.
The [final source-chain review](final-source-review.md) independently rehashes
the complete closure and documents each conditional/private observation scope.

The dequant candidate adds 192 private, reset-free coefficient/quantizer bits.
The [retained routed analysis](dequant-next.md) identifies the measured
group-selection/quantizer/multiplier path and its unregistered DSP inputs.
The [actual mapped DSP report](dsp-mapping.md) shows all eight dequant AREGs and
three BREGs enabled in the initial dequant composition; MREG/PREG remain zero.
The later Runtime R5 route maps two of those BREGs, with 34 total DSPs. The
[Default same-source audit](default-native-final-audit.md) measures seven BREGs,
42 total DSPs and 38 BRAM tiles instead of Runtime R5's 46.5. These are actual
mapping changes; none establishes a cycle-throughput or clock-closure claim.

## Measured implementation results

These are completed OOC routes at the fixed 10-ns clock, not synthesis estimates.
The [machine-readable comparison](../../experiments/python-gamebub-v110/native-comparison.csv)
and [receipt summary](../../experiments/python-gamebub-v110/results.json) bind each actual source/recipe.

| Fresh-RTL source composition | WNS ns | TNS ns | Setup-failing endpoints | Hold / pulse ns |
| --- | ---: | ---: | ---: | --- |
| V109 FETCH control baseline | −1.635 | −8,267.052 | 13,122 | +0.044 / +3.750 |
| Busy + owned fault controls | −1.700 | −6,860.993 | 12,612 | +0.104 / +3.750 |
| Controls + DSP preparation | −4.845 | −23,128.131 | 23,412 | +0.049 / +3.750 |
| Controls + DSP + readiness + Rice taps | −2.871 | −10,185.816 | 16,322 | +0.110 / +3.750 |
| Owned fault controls alone | −2.578 | −8,838.627 | 13,862 | +0.086 / +3.750 |
| Complete composition + parallel prefix factoring | −1.654 | −3,716.410 | 8,328 | +0.086 / +3.750 |
| Same prefix source, Default synthesis | −1.199 | −1,582.964 | 6,203 | +0.079 / +3.750 |
| Private cursor composition, RuntimeOptimized | −1.595 | −4,610.536 | 10,103 | +0.096 / +3.750 |
| Request-address + cursor composition, Default | −1.365 | −1,662.130 | 6,031 | +0.043 / +3.750 |
| Validated-caller count specialization, Default | **−1.022** | **−1,125.069** | **4,620** | +0.085 / +3.750 |

All nine completed new routes have zero routing errors and zero unconstrained
internal endpoints; none passes 100 MHz. The best V110 result improves WNS by
0.567 ns versus the prior V109 fault-only diagnostic frontier (−1.589 ns). Reduced aggregate violations or improved DSP mapping
do not compensate for a negative worst slack.

The readiness/Rice-tap route launches at `cached_remaining[5]` and ends at the
Rice quotient clock enable: 17 logic levels, 12.618-ns data delay, 74.751% routing.
Most path nets have fanout 1–5; intermediate fanouts 76/50 do not justify treating
the whole cone as a reset-fanout problem. Serial-only extraction cleanup was
rejected as the native child fixes serial mode to zero.

The fully qualified parallel-prefix factoring then improves that composition's
WNS to −1.654 ns and reduces aggregate failures to 8,328. Its final worst path
now launches from scratch `read_segment[1]` and ends at `cursors[1][29]/R`: 14
levels and 11.140-ns data delay. Setup still fails. At that intermediate checkpoint, the prior V109 −1.589-ns
frontier was slightly better in WNS; subsequent routes below improve it.
No negative candidate is promoted.

A separately bounded [same-source Default synthesis comparison](default-method.md)
finished at −1.199 ns. Its actual tool command omits the synthesis directive,
and the absent separate directive-info message remains `None`; the log and
recipe hashes establish the documented Default mode. It uses identical RTL and
implementation settings, with no retiming or clock/constraint change. The worst
path shifts to ingress band/address/bounds control; the 100-MHz gate remains open.
The private-cursor Runtime route removes cursor destinations from its top fifty
paths, but WNS is −1.595 ns and aggregate failures increase versus its Runtime
control. Its worst path becomes fetch-return/address-bounds to ingress error.
The complete address/cursor composition then passes both canonical seeds and
finishes Default routing at −1.365 ns. Its worst path is now the context
start-limit validation/control cone; it remains negative and is not promoted.
The validated-caller specialization targets only the redundant AC count
rejection in that cone. Its generic and conditional focused tests and full
canonical composition pass.
The final Default route improves WNS to −1.022 ns and aggregate setup failures
to 4,620, but remains negative. The generic parameter defaults false; enabling
it in another caller requires the same discharged count bound.

The [final count-domain audit](count-domain-native-final-audit.md) binds the
actual terminal receipt and reports. Its worst path is now header
`fetch_bytes_reg[23][0]` to `counts_reg[1][5]/CE`: 15 logic levels, seven CARRY4s,
10.769-ns data delay (3.384 ns logic and 7.385 ns routing). Of the final top fifty
paths, 44 launch from the header length field, four from `context_blocks[9]`,
and two from `coefficients/admission/tile[5]` to `group_visible`. The context mapper path seen after placement is
absent from those final fifty paths. The next causal target is the
[owned header-length validation pipeline](header-validation-next.md); its
implementation and clock qualification remain open. The
[mapper pipeline proposal](mapper-next.md) is conditional on a future routed
mapper bottleneck, rather than a fix selected from placement estimates.

The [FSM extraction review](fsm-method-next.md) rejects a speculative global
one-hot trial: actual logs identify only the already-one-hot dequant FSM and
the sequential inverse-math FSM. The measured context/ingress control cones
are not reported as extracted FSMs. Extra flip-flops alone would not establish
a causal fix for their current critical paths.

## Native implementation policy

[The frozen policy](../../experiments/python-gamebub-v110/study-policy.json)
permits at most two heavy jobs, each capped at two CPUs/threads and 8 GiB with
no extra swap, plus available-RAM/pressure and 2,400-second watchdog gates.
Fresh RTL uses RuntimeOptimized synthesis, ExtraNetDelay_high placement and
Default routing, with the 10-ns clock read before synthesis. No clock relaxation,
timing exceptions, waivers or guessed board I/O delays are introduced.

Native dispatch requires actual focused and complete canonical PASS, the exact
17-SV/one-header source closure, current source/proof/recipe hashes and an
independent prepared-input audit. The flow reports mapped local predicates and
DSP registers without preservation or fanout properties. A passing candidate
needs a fresh RTL repeat before a reproducible component-clock claim.

The later fresh-RTL Default compositions retain their control’s functional Tcl/XDC
and use an explicitly pinned 3,600-second operational watchdog; the earlier
2,400-second policy and receipts remain unchanged. No passing result exists;
the globally shared positive fresh-repeat budget remains unused.

Vivado MCP returned `Transport closed`; the existing qualified Vivado 2026.1
build 6511674 CLI and legitimate read-only license installation are retained.
Functional verification continues with Verilator 5.020 and assertions enabled.
This does not silently substitute XSim or claim post-route timing simulation.

## Latency evidence and follow-up

The [actual phase attribution](phase-budget.md) separates signed completion
fences from overlapping work. In the qualified two-seed workload, only 2 of 24
successful case/profile rows fall below the conditional one-million-cycle
start-to-finish budget; both are fast-profile zero-residual cases. These are
component counters, not calibrated validated-frame latency.

Residual-case coefficient spans are 912,855–1,310,869 cycles in the fast service
profile. Producer completion to last residual adds 198–3,681 cycles. That small
tail does not prove IDCT cannot stall the producer during their overlap. Canonical
pixel output can begin before the first coefficient, and its span must not be
added to the coefficient span. The slow zero-residual case still needs roughly
1.77 million cycles despite using no IDCT/dequant, so memory/output service and
readiness/stall attribution are required before choosing the next acceleration.

The [matched transform events](transform-budget.md) add a concrete scheduling
finding: all 63,412 complete tile identities per seed join without orphans,
and launched math does not overlap the previous 64-sample residual burst. The
[unimplemented two-result-slot proposal](overlap-next.md) separates those owners,
with explicit cancellation, EOF and drain rules and a new latency-aware oracle.
No throughput gain or clock improvement is claimed before RTL and route tests.

## Product gates remain separate

[Hardware gates](hardware-gates.md) require clean boot and calibrated counters,
then 1,800 distinct frames over 60 seconds and 18,000 over 600 seconds, followed
by every complete validated-decode sample strictly below 10 ms. The production
parent still uses JPEG and requires CS88 transport/reference/HUD/hash/display
integration and complete clock/I/O/CDC/memory qualification.

The [control-contract contingency](control-contract.md) describes the explicitly
versioned admission/flush/final-drain protocol required if equivalent local
predicates are insufficient. Delaying live cancellation is not an exact fix.
Hardware is elsewhere; no hardware operation or 30-fps/<10-ms claim is made.

The [reproduction instructions](reproduce.md) retain failed attempts and exact
source-only replay exports. The [current export checks](export-current-checks.md)
include the best count-domain diagnostic source composition. The [offline evidence checker](hardware-evidence.md)
passes 12 synthetic tests, including rejection of a single exact-10-ms outlier,
duplicate frame identities and missing calibration. It is a proposed trace
contract and numeric checker; it cannot attest hardware execution.
