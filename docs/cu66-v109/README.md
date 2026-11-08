# V109: integrated-closure prerequisites and control locality

The target remains **100 MHz / 10.000 ns** on `xc7a100tcsg324-1`, with the
720×480 CS88 q16/all-BR88 representation and 49,152-byte cap unchanged.
V108's functionally qualified composition routed at WNS **−2.020 ns**.
V109 improved the best routed WNS to **−1.589 ns**, but every tested route still
fails setup. This is a **partial V109 checkpoint**, not integrated closure.

## Functionally qualified RTL changes

| Cut | Behavioral evidence | Purpose |
| --- | --- | --- |
| [Same-edge fault predicates](fault.md) | Complete inverse/reconstruction goldens and simultaneous failures; exact error-assignment pairing; full canonical fault regression | Remove repeated wide status decoding without delaying cancellation |
| [Existing-edge prefetch arithmetic](prefetch.md) | 31,855,149 complete paired public-cycle edges, both staging modes and seeds | Move address/range arithmetic before the original launch decision |
| [Four-bank selection](bank.md) | Complete direct scratch goldens/hazards, two seeds and 48 extra 9/17-block boundary transactions per seed | Use registered local bank selection while preserving live tags/validity and forwarding |
| [Owned fetch address](fetch.md) | 15,495,499 exact-cycle ingress comparisons, 1,509,288 independent golden coefficients and all six original stale-response rejection checks | Capture the expected RAM-response address on the existing request edge, shortening the measured header-byte CE cone |
| [Prepared request address and bounds](request.md) | 15,496,047 exact-cycle ingress comparisons, 1,509,288 golden coefficients and all six original stale-response rejection checks | Prepare the next request before its acceptance edge, retaining full-width wrapping, jump addresses and immediate cancellation |

Every original assertion, public/invalid value, error, counter, memory request
order and cancellation fence remains in the applicable comparisons. Same-edge
fault bits update with the existing error register, not one cycle after it.
The bank candidate derives from the qualified prefetch candidate; that original
source and its proof stay frozen.

The full canonical harness uses the unchanged V108 bench, vectors and goldens.
Each variant must reproduce both original seeds' exact stdout, events, cycles
and canonical pixels: 44 case profiles and 42 directed checks. Native builds
require current focused and canonical PASS receipts, exact 17-RTL/one-header
source closure and a matching independent preflight audit.

## Physical comparison and scope

Two initial fresh-RTL builds use RuntimeOptimized synthesis, ExtraNetDelay_high
placement and Default routing, with the 10-ns XDC loaded before synthesis:
fault-only and fault/prefetch/bank composition. Completed routed results decide
the outcome; synthesis or placement estimates do not establish closure.
A passing candidate requires a clean fresh-RTL validation repeat. At most two
further physical trials may test specifically recorded remaining hypotheses.
There is no seed sweep, clock relaxation, false/multicycle exception or guessed
board delay.

All four fresh-RTL routes completed. The clock was loaded before synthesis in
every run; the same synthesis, placement and routing directives were used:

| Actual routed source | WNS (ns) | TNS (ns) | Failing setup endpoints | 100 MHz |
| --- | ---: | ---: | ---: | --- |
| V108 frozen baseline | −2.020 | −11,717.641 | 16,953 | Fail |
| V109 same-edge fault predicates | −1.589 | −8,342.999 | 14,204 | Fail |
| V109 fault + prefetch + bank selection | −1.737 | −5,988.869 | 12,615 | Fail |
| V109 fault + owned response address | −1.635 | −8,267.052 | 13,122 | Fail |
| V109 fault + response/request address preparation | −2.275 | −10,280.347 | 15,277 | Fail |

All four V109 routes pass hold/pulse checks and have zero routing errors and zero
unconstrained internal endpoints. The fault-only worst path moved to ingress
`fetch_index[3] → fetch_bytes[8][0]/CE`: 14 levels, 11.300-ns data delay,
3.541 ns logic and 7.759 ns routing. The combined route instead ends at ingress
`error[0]/CE` from `fetch_return[2]`, with 15 levels and 11.448-ns data delay.
Lower total negative slack does not imply a better worst clock path.

The fault-only source is the best **diagnostic timing frontier**, improving WNS
by 0.431 ns and absolute TNS by 28.8% against V108. The bank composition has the
lowest absolute TNS (48.89% lower than V108), but a worse worst path. Neither is
clock-qualified. The later address experiments are not promoted: the request
variant regresses even against V108. There was no passing candidate to repeat.

Both address variants passed their complete canonical comparisons before native
execution. Their request/response capture edges, public addresses, ownership and
error priority remained exact. Passing functional tests did not guarantee better
physical timing. The two adaptive runs used the policy's two reserved trials;
[the scheduling decision](../../experiments/python-gamebub-v109/coordination/parallel-request-dispatch-decision.json)
records why the independently justified request trial ran in parallel once its
full regression passed and a heavy-job slot became free.

The [FETCH route analysis](fetch-route-findings.md) finds zero old
`fetch_index`/`fetch_return` launch sources among its top fifty paths. Its new
worst route is scratch quiescence/start/cancel control into coefficient-bank CE:
10 LUT levels, 11.346 ns data delay, **84.506% routing**. A separate fault-ack
path into Rice CE remains at −1.599 ns with 14 levels. The
[REQUEST route analysis](request-route-findings.md) records a new worst
`transform/fault_o → producer_cell_cache RAM enable` path: 14 levels,
11.748 ns, **81.342% routing**. These are operational fences; treating them as
ordinary delayed debug status would change behavior.
The REQUEST endpoint is the quant-cell ROM's read enable, so adding a RAM
output register would not cut this measured enable path.

The [full measured comparison](../../experiments/python-gamebub-v109/native-comparison.csv)
and [receipt summary](../../experiments/python-gamebub-v109/results.json) bind all
terminal outcomes. All four complete source compositions independently matched
the same frozen reference workloads: **44 case profiles and 42 directed checks
per composition**, exact stdout/events/cycles and canonical pixels, both seeds.
The original baseline was reused, not falsely recounted as newly executed.

[Policy](../../experiments/python-gamebub-v109/study-policy.json): at most two
heavy jobs, 2 CPUs/threads and 8 GiB per native job with no extra swap, a
2,400-second watchdog, available-RAM and memory-pressure gates. Failures and
their snapshots are retained. The selected RTL simulator remains Verilator;
the unavailable Vivado MCP transport is recorded and the established native
Vivado 2026.1 CLI is used.

The [methodology interpretation](methodology.md) distinguishes unresolved setup,
OOC I/O boundaries, RAM output-register findings and control-set warnings. Its
listed methodology-warning counts are separate from the actual failing setup
endpoints above. No warning was waived. [Reproduction instructions](reproduce.md)
explain the focused/canonical jobs and checkpoint-independent source exporter.

## Remaining full-system gates

[Integration inventory](integration-gaps.md) identifies the actual production
JPEG path, 200/100-MHz service clocks, phase-shifted SDRAM capture, pixel domain,
CDC/reset interfaces and finite memory/display service. An OOC decoder result
does not qualify `moonshine_top`, its board I/O, framebuffer/reference ownership
or presentation under contention. These remain separate V109 integration gates.

The [cycle-budget report](../../experiments/python-gamebub-v109/cycle-budget.json)
uses actual RTL counters and labels its start/finish and last-input/done fences.
It is not calibrated hardware publication latency. Even after clock closure,
sustained hardware 30 fps and strict validated decoding below 10 ms require
their own measurements and endpoint implementation.
The [next implementation work](next-implementation.md) keeps these gates and any
latency-aware or production telemetry contract changes explicit.
