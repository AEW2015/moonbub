# V106 remaining fixed-100-MHz timing work

Keep the **10 ns / 100 MHz target fixed**. V106 is now a completed study with four completed Default-flow routes, a fifth placement failure and a sixth watchdog timeout after synthesis. The selected completed source remains **closure**, routed WNS **−4.034 ns**; the latest sixth source has only synthesis WNS **−3.205 ns**, with placement/routing unmeasured. A separate unselected post-route diagnostic reached **−3.777 ns** and still failed 44,630 setup endpoints. None meets the fixed target. The historical route tables below retain the reasons for each experiment; final outcomes and next-step priorities are recorded at the end.

## Pinned completed route

Native receipt: [20261108T013032873883Z](../../experiments/python-gamebub-v106/native/20261108T013032873883Z/receipt.json), SHA-256 `b8f3402ced4ae9873cd335cc30c409855b83db004d356446e9c911ac4c0de575`.

The [top-50 setup-path report](../../experiments/python-gamebub-v106/native/20261108T013032873883Z/reports/route-setup-paths.rpt) has SHA-256 `4da106d91e7cb99b7ba84d83252621f3489fb7e1fd9663d2fd20bb234b4953bd`; the [timing summary](../../experiments/python-gamebub-v106/native/20261108T013032873883Z/reports/route-timing-summary.rpt) has SHA-256 `ec30e52e4d623b726a341bc0b7bba2c98e94a1cbf94a919ebad7ef3435643159`. This is one OOC component route with timing signoff open.

| Cone | Actual routed source → destination | WNS | Data delay | Logic / route | Levels |
| --- | --- | ---: | ---: | ---: | ---: |
| Rice prefix/output | parser `available_reg[0]` → `out_value_reg[5]/D` | −4.034 ns | 14.025 ns | 3.713 / 10.312 ns | 19 |
| **IDCT operand selection** | `transform/inverse/k_reg[1]_replica` → `transform/inverse/products_reg[3]/A[4]`, DSP48E1 | −3.952 ns | 10.146 ns | 2.499 / 7.647 ns | 8 |
| Scratch cached-word validation | scratch `read_segment_reg[0]` → `state_reg[3]_rep__0/D` | −3.831 ns | 13.685 ns | 3.512 / 10.173 ns | 17 |
| Scale lookup | coefficients `tile_cursor_reg[8]` → admission `lookup_scale_reg[1]/D` | −3.438 ns | 13.429 ns | 3.689 / 9.740 ns | 14 |
| Telemetry | scratch `state_reg[3]_rep__0` → child `count_emitter_state_reg[3][53]/D` | −3.404 ns | 13.040 ns | 4.214 / 8.826 ns | 25 |

The DSP cone is **IDCT**, not dequantization. The V104 dequantizer-prefetch experiment does not directly remove this path; it is omitted from the new final candidate. Also, do not derive an achieved Fmax from one path or reciprocal slack: the current task is closure at the unchanged 10 ns constraint, with setup/hold/pulse/legality and parent integration considered separately.

## Completed combined follow-up route review

PREFIX factors the late remaining-bit window after a balanced first-one rank tree, preserving the existing guarded reservoir selects. Its whole-module and exhaustive-rank evidence is in [prefix-results.md](prefix-results.md). Telemetry changes must preserve every public counter edge and invalid-state/reset/priority behavior, rather than deleting observability. Their combined Default route completed at −4.700 ns; the actual Rice available-to-output cone remained critical. The isolated subsequent fixes passed behavioral checks, but their latest combined source did not complete routing. Source-model evidence alone is not frequency qualification.

## IDCT operand-selection candidate

Implementation status is updated below; the isolated operand-prefetch source and focused proof are now complete, while native attribution remains separate.

If the actual final route still has `k`/group selection → DSP operand paths, explore prefetching the next selected sample and basis into local operand registers using the IDCT's existing alternating multiply/accumulate slots. Initial launch, first/second-pass transitions, group boundaries, zero/DC shortcuts and abort/reset paths require distinct correct initialization. Do not add a public cycle, move output acceptance, or assume an unwritten intermediate is available.

An initial study should inventory all sample/basis source cases and their readiness edges, compare the complete actual old/new IDCT module, and use existing golden 64-sample tiles for arbitrary AC, DC, zero, invalid coefficient and held-output cases. Assertions should compare each valid prefetched operand with the original combinational selector. Native evidence must show the resulting DSP input/register settings, enables, resources and new worst endpoint. A source register declaration or DSP attribute alone is not proof of mapping or timing gain.

## Scale lookup: address cache versus actual two-port memory

The producer address-cache option is now implemented and model-verified as recorded below. The true-dual-port scale-table option remains unimplemented.

The current `scales[0:1349]` table is 1,350 × two bits. External cache writes and Q_FILL writes can target different addresses on the same clock; Q_FILL wins when they target the same address. Lookups are registered only in FINISHED, hold through every non-lookup edge/reset/start/abort, and return old data for a simultaneous external write to the lookup address.

Two distinct candidates can be compared if the final scale path remains critical:

1. Cache or predecode the producer's quant-cell address at validated tile/plane transitions, avoiding a late coordinate calculation in the lookup path. Keep full original counters, invalid tile/plane behavior, cancellation and ownership semantics. Compare a live cache against the original helper; invalidate it on every relevant reset/replacement/error transition. A dead/prepared cache must not affect rejection or held outputs.
2. Express a true-dual-port scale table: port A handles guarded external writes, suppressed only for a simultaneous same-address Q_FILL; port B chooses Q_FILL writes or FINISHED lookups. Preserve capacity, original address truncation and undefined out-of-range behavior. **Port A must provide READ_FIRST cross-port behavior for same-address external-write/lookup; port B must preserve the held lookup result during Q_FILL writes, using NO_CHANGE or a proven equivalent.** A simple source rewrite or `ram_style` attribute does not establish these properties.

AMD's [7-series memory guide, UG473](https://docs.amd.com/v/u/en-US/ug473_7Series_Memory_Resources), Table 1-4, specifies common-clock read/write collision behavior: READ_FIRST on the writing port allows the opposite read port to obtain the old word; WRITE_FIRST/NO_CHANGE writing-port cases do not provide that same guarantee. Both ports must use the actual common clock. This is architectural support, not proof that a future inference selected the required configuration.

Qualification for the TDP candidate must include complete source old/new comparison over all 1,350 valid words, two distinct concurrent writes, same-address Q_FILL priority, external-write/lookup collisions, holds across Q_FILL, guards/reset/start/abort and real packet transactions. Then inspect actual RAMB18E1 port modes, clock/enables, read latency and optional output registers in synthesis and route, and run actual UNISIM primitive tests for collisions/holds. Behavioral array tests cannot establish physical collision behavior by themselves. No external SDRAM timing is assumed.

## Scratch word-selection candidate

If scratch `read_segment` remains critical, inspect the complete measured chain from segment selection through `cache_data[read_segment]`, byte shifting, sparse/zigzag decoding and bounds/error priority. Source-level predecode should respect the exact accepted cache-hit/response owner and epoch, not merely the expected nominal address.

A candidate can preselect per-segment words or latch a word at an existing fetch/response transition, preserving the original consuming edge. Handle live cache hits, outstanding reads, prefetch updates, cancel/reset drain, mismatched/late responses and validity changes separately. An alternative one-hot segment/byte decode must preserve **all 16 byte offsets**, including zero-extension of shifted words near the 128-bit cache-line end; do not assume aligned four-byte accesses for malformed inputs unless the original checked control path establishes that condition.

Before native work, compare original/new full scratch modules under the existing accepted-write hazard suite and full packet lanes, with independent word/address/epoch binding, exact error priority, output holds and cancellation ownership. Assert any prefetched value equals the original expression whenever it is live. Confirm actual fanout/control-set/congestion and the new routed endpoint before attributing improvement.

## Completion gates

For each new candidate, preserve an isolated exact-edit recipe and source hashes; prove arithmetic identities over their stated full domains, run strict bounded actual RTL comparison and independent oracles, then run matched synthesis through routing at the unchanged constraint. Keep failed and resource-gated attempts. Compare like implementation stages and preserve unmeasured controls explicitly.

The component gate is nonnegative setup, hold and pulse slack, no corresponding failing endpoints, complete legal routing, resource fit and no clockless/unconstrained internal endpoints or loops. A component pass still leaves parent clock/boundary/I/O/CDC, actual memory arbitration/service, whole-system integration, hardware sustained 30 fps and validated complete decode below 10 ms open.


## Implemented guarded follow-up; native result remains separately audited

Four completed native routes precede the new guarded source. Their immutable setup reports remain historical evidence:

| Variant | Routed WNS | Completed route report | SHA-256 |
| --- | ---: | --- | --- |
| lut | -7.130 ns | [20261108T005012241750Z](../../experiments/python-gamebub-v106/native/20261108T005012241750Z/reports/route-setup-paths.rpt) | `915b2331b769ee3a06d269482ce707bfecaa410d0056d9978392f35beb90873b` |
| lut-storage-plan | -6.628 ns | [20261108T010638248027Z](../../experiments/python-gamebub-v106/native/20261108T010638248027Z/reports/route-setup-paths.rpt) | `655b58b7c9709fe32608d24a292f97020db3a3369792e9415e6728117e6dc50a` |
| closure | -4.034 ns | [20261108T013032873883Z](../../experiments/python-gamebub-v106/native/20261108T013032873883Z/reports/route-setup-paths.rpt) | `4da106d91e7cb99b7ba84d83252621f3489fb7e1fd9663d2fd20bb234b4953bd` |
| closure-prefix-telemetry | -4.700 ns | [20261108T015540764948Z](../../experiments/python-gamebub-v106/native/20261108T015540764948Z/reports/route-setup-paths.rpt) | `83be4d6b68d4eb3f700499ad6dab938c4fb698af31d71b7fe3b674a8c4676d15` |

The fourth route is still negative: parser `available_reg[1]` → `out_value_reg[3]`, WNS −4.700 ns, data 14.693 ns (3.947 logic/10.746 route), 18 levels. Its receipt SHA-256 is `35e5b2e72e146fc0847b564009a36c90993d8db9d18f6724cefdb8092e210180`. This is an actual routed result, not the earlier −3.897 ns synthesis estimate. The following three new sources now have isolated proof and are combined only in the separate `guarded-suffix-idct-cache` trial:

- **Selected SUFFIX extraction:** frozen source SHA-256 `8940a4313a1efc88bdc7b55e885ae58d55e0e1f88208659010c5e5eb4e409ef7`. The independent six-bit take expression avoids PREFIX/state dependencies only for the selected SUFFIX value; common extraction/counter updates stay unchanged. [Focused evidence](suffix-results.md) checks 18,522,021 actual old/new edges, all public outputs/counters, and an independent selected-state identity. Unused private suffix/decoded values may differ outside SUFFIX.
- **IDCT operand prefetch:** source SHA-256 `f972987d80a062b4969c71ac6157e8f17ab9e6b18088bafb77c4030eac78990e`. Selected signed sample/basis values are registered on the preceding existing IDLE/ACC edge; MUL and public output timing remain unchanged. [Focused evidence](idct-results.md) verifies 540,368 edges, 244,048 multiply edges, 4,303 independent integer-golden tiles and reset/abort in all ten states. The selected summary SHA-256 is `2443f23bd5070e4048a0a348cc14336d30d08d82ac7bb532499c2995cf719ee0`; its independent audit SHA-256 is `4bbe9621dfabcd7fefed30d2196e903175de87cbe6baeded774a5f26603bc10d`.
- **Producer quant-cell cache:** both fresh/canonical producer sources mirror every existing plane/tile update with a private lookup-address cache; the scale table's write/read/collision semantics are unchanged. [Evidence](producer-cache-results.md) checks all 32,768 helper inputs and 262,144 Python transitions with exact recipes and an inductive update argument. This is **model-only standalone evidence**, not a standalone whole-controller RTL simulation. Live cache assertions and complete paired pipeline lanes are required separately. The model-result SHA-256 is `2b29c6d70466f4ac1afe40aaa0142a8fac3f37b3c0a9c894c19762d4d4898e84`.

The guarded candidate's [native receipt](../../experiments/python-gamebub-v106/native/20261108T021556317071Z/receipt.json) and final source/native audits own its integration and timing outcome. The fifth attempt failed placement, as recorded below; no fifth-route timing value exists. Use the final audited [comparison](vendor-comparison.md), measured path analysis and [physical locality](physical-locality.md) to choose any next experiment. A negative final setup result still misses the unchanged 100 MHz target; none of the isolated proofs establishes hardware FPS or complete decoding latency.


## Fifth attempt: area failure retained

The `guarded-suffix-idct-cache` [native receipt](../../experiments/python-gamebub-v106/native/20261108T021556317071Z/receipt.json), SHA-256 `aa7d1db0875b5a5fe4312bb894eff2018453e79f70a7b6fb44929db0d26041f3`, is terminal `TOOL_OR_BUILD_FAILED` with observed exit code 1. Synthesis reports are retained, but placement and routing did not complete. The [Vivado log](../../experiments/python-gamebub-v106/native/20261108T021556317071Z/vivado.log), SHA-256 `c756c12a137e1f31d50725293cd5068ea41a948d3426e631a212694e98c19fe7`, reports `[Place 30-487]`: 66,507 total LUTs after optimization versus a 63,400-device capacity, and unplaced instances needing 12,350 slices versus 10,647 available. This is an implementation area/packing failure, not a host RAM failure or a timing pass. The original IDCT candidate and failure remain retained while an isolated area repair is assessed.

Its synthesis-only worst setup path is `sizes_reg[0][1]` → Rice `out_value_reg[0]/R`: WNS −3.581 ns, data delay 12.940 ns (6.823 logic/6.117 estimated route), 28 levels including 18 CARRY4s. This identified a further ingress hypothesis: cache the live context's full32 remaining replay bits on the existing CONTEXT_START edge, mirror only accepted replay-word updates, and replace the modular last-word addition with equality against that cache. Public validity/bounds and error/done priority must stay unchanged. The isolated ingress candidate and focused proof must pass before integration; a synthesis estimate is not a routed result.


The rejected fifth trial also failed its strict fresh production compile because `suffix_extracted[63:24]` is unconsumed in the integrated production closure. The earlier focused probe exported private state and therefore did not expose that integration-specific unused-signal warning. No warning is waived and the rejected canonical lane is not a PASS. A separate private 24-bit projection candidate must prove that only the original low24 bits are consumed, retain the failed source unchanged, and pass the complete strict production pair before selection. Focused behavioral evidence and production lint/area qualification remain distinct gates.


## Sixth integration source: functional PASS, implementation timed out

The separate `local-guards-scratch-area` source combines the earlier guarded changes with four explicitly isolated refinements. It passed its complete required fresh/canonical production pair, then timed out after synthesis without a placement/routing result:

- [IDCT area repair](idct-area-results.md), source SHA-256 `1ed49416dae06b727544ad1d2f96440f553cd99e5324dc895a0af5edbca5cc32`: shared next-index/operand read selection keeps the existing prefetch schedule while avoiding the first candidate's replicated selector networks. Full original/candidate clocked proof passes; matched unit synthesis is a screening gate, not complete-top area/timing qualification.
- [Ingress live replay cache](ingress-results.md), source SHA-256 `4342972a6cf42cebf4f01a82841c0bc7c1850292ca23362817f7f071af126093`: removes the measured full32 subtraction/addition input-validation chain while retaining all replay bounds and event priorities. The frozen strict whole-pipeline probe passes 15,988,562 edges, both complete historical protocol suites, all 47 ingress public outputs and independent parent/child arithmetic/counter/reservoir oracles.
- [Scratch sparse-position predecode](scratch-results.md), source SHA-256 `0ee1196e2f0cafdf52742656d4c1a53604c79544c339b171989ad2785f051f8c`: mirrors original bank writes with exact position values for all sixteen byte offsets, including zero-filled tails. Ownership, epoch, valid bits, original record words and error ordering stay intact. This moves work to memory-response capture, whose actual parent input-arrival/setup/hold/CDC timing remains unqualified by the internal OOC experiment.
- [Private SUFFIX low24 projection](../../experiments/python-gamebub-v106/suffix24/results.json), source SHA-256 `d0e233eacb849476bac7c18157a6f29bd76228d378e07b2d7613db8a356cf919`: the original consumers already use only low24 bits. Two literal source edits and 296,608 model checks preserve that exact projection without waiving the integrated warning. This is model/source-only standalone evidence; the complete strict paired pipeline RTL supplies its clocked integrated qualification.

The completed required functional campaign is 24 PASS lanes: the earlier 22 plus the sixth candidate's fresh/canonical pair. The fifth failed fresh compile and unrun canonical lane remain explicit rejected evidence, not PASS lanes. Six full native implementation attempts are retained, including the failed fifth and timed-out sixth attempts; original versus composed unit synthesis is separately scoped. Any final selection must use actual legal complete-top routing, target resource fit and the unchanged 10 ns target. The actual last measured report, not these hypotheses or any synthesis estimate, decides whether timing closes.


## Final sixth outcome and next implementation priority

The sixth [receipt](../../experiments/python-gamebub-v106/native/20261108T025230842632Z/receipt.json), SHA-256 `0bfd292ecf0f35f77a0ebc5cb5c4b64e5a230182b4eca9a2fe815c160b20720d`, is terminal `TOOL_OR_BUILD_FAILED`, observed exit **124**, elapsed **1,800.722 s**. The unchanged watchdog ended the job during early placement after completed synthesis. No placement reports, routed checkpoint or routed timing result were produced. The [log](../../experiments/python-gamebub-v106/native/20261108T025230842632Z/vivado.log), SHA-256 `e5a95f2497fa9c4fda1756fbf2a7a5c6f874941ec1b77f95ae8cb99353fc50e5`, retains that endpoint. The [native audit](../../experiments/python-gamebub-v106/native-audit.json) checks the retained evidence; its PASS is not successful implementation.

Synthesis reports 47,352 LUTs, 1,825 LUTRAMs, 36,984 FFs, 32 RAMB36 plus 10 RAMB18 and 28 DSPs. Estimated setup WNS is **−3.205 ns**, with 4,546 failing setup endpoints. The [actual synthesized worst path](../../experiments/python-gamebub-v106/native/20261108T025230842632Z/reports/synth-setup-paths.rpt), SHA-256 `4493c87f8ff863ad6d3d4c7530729b2e6fe40c689f6957b25db69e440622e594`, is admission `qbuffer_reg[119][1]` → `q_index_reg[1]_rep/R`: data **12.564 ns**, **3.500 ns logic / 9.064 ns estimated route**, 15 levels. This is the next concrete RTL cone to inspect. Synthesis capacity and unit IDCT results do not establish placed/routed fit or timing.

For the next version, first retain the current source/campaign and profile synthesis runtime, selector structure, fanout and inferred memory around the quantization-buffer decoder. A separately authorized new implementation experiment can budget a complete measured flow; do not silently extend this study's six-attempt cap or promote its synthesis-only source. Review the full qbuffer-select/length-decode/q-index/error-fence chain, not only its arithmetic operators. Any local rewrite must cover all malformed widths/counts, full32 boundary values, packet cancellation and same-edge error priorities.

### Permit explicit pipelining if local same-cycle rewrites are insufficient

Cycle-preserving rewrites have improved the selected routed setup deficit, but still do not close 100 MHz. The next design should therefore consider splitting long buffer selection/decode/control cones into registered stages with **ready/valid buffering** rather than requiring every new feature to preserve the original public clock schedule. This is a proposed new contract, **not implemented or proven in V106**.

A candidate pipeline can carry the selected data, decoded length, owner/epoch, band, full original counters and validation status together. Use explicit credits and a skid/FIFO boundary; held outputs must stay stable, stale owners must never write or publish, and cancellation must invalidate every in-flight token. Preserve packet rejection and error priority at defined commit points. Buffer depth must come from the real accepted-token and downstream-stall bound, not an assumed always-ready memory port. Avoid retiming control independently from its payload or dropping validation to gain frequency.

Introduce a **latency-aware reference scoreboard** before integrating such a change. It must compare complete ordered transactions, metadata, coefficients/pixels, errors, memory writes and publication ownership against the original reference while allowing the explicitly declared extra latency. Also check no duplicate/lost tokens, exact credit occupancy, stable held outputs, cancellation/drain, bounded progress under stated service conditions and worst-case latency. A scoreboard that only ignores cycle mismatches would hide performance regressions. Keep the existing cycle-exact tests for unchanged submodules, and add both adversarial protocol tests and separately bounded-service performance tests.

At the fixed 100 MHz clock, 30 fps allows approximately **3.333 million cycles per frame**; decoding strictly below 10 ms requires **fewer than one million cycles** across the defined complete decode boundary. Record that boundary explicitly—proposed first accepted encoded-frame byte through final reconstructed-pixel write and frame publication—and separately report transport/capture/display latency. Include parser and validation stages, inverse/reconstruction work, new pipeline/FIFO latency, reference/HUD operations, memory arbitration, backpressure and publication. Throughput after pipeline fill and single-frame latency are different measurements. An unbounded input or memory stall cannot support a bounded latency claim; use measured hardware service assumptions and report violations of those assumptions.

Use cycle budgets to choose stage count and buffering before RTL changes, then measure min/median/tail/max frame latency and sustained frame completion under representative video and stress patterns. Only completed legal routing at 10 ns and subsequent board measurements can qualify the clock and complete system. Hardware sustained 30 fps and validated complete under-10-ms decoding remain open.

## Separate post-route diagnostic remains unselected

The [bounded physical diagnostic](postroute-probe.md) reopened the earlier completed closure checkpoint and ran AggressiveExplore once without changing RTL, clock constraints or timing exceptions. Its [portable independent report](../../experiments/python-gamebub-v106/postroute/report-audit.json), SHA-256 `f2ffc6433d54644cac0f7f7b684860fa2223ade3f4c0e5b2e67f70c42314f5f2`, records routed WNS **−3.777 ns**, a **+0.257 ns** change from the reopened −4.034 ns parent, but **44,630 setup endpoints still fail**. The after-route worst path is the earlier IDCT `k_reg[1]_replica` → `products_reg[3]/A[0]`, data 9.971 ns (2.640 logic / 7.331 route).

The probe completed with legal routing and positive hold/pulse slack, but setup remains failing. Its strategy differs from the six matched Default-flow source trials; it is not selected or promoted, and is not evidence for the newer sixth source's timing. No achieved Fmax, hardware FPS or complete decoding latency follows from this diagnostic.
