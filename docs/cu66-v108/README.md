# V108: fixed-clock placement and routing study

**The bounded experiments are finished; 100-MHz setup timing remains open.**
The functionally verified composition improves the matched fresh RTL route from
WNS **−2.342 ns to −2.020 ns**, with **34.6% less absolute TNS** and **28.7% fewer
failing setup endpoints**. This is one physical observation of the five-body
composition; it does not isolate the individual changes or establish robust
timing closure. All eight routes complete with passing hold/pulse checks and
zero routing errors. Every route still fails setup.

| Matched fresh RTL build | WNS (ns) | TNS (ns) | Setup failures |
| --- | ---: | ---: | ---: |
| Original source, selected m2 strategy | −2.342 | −17,923.600 | 23,783 |
| Verified output-word mask + capacity control | **−2.020** | **−11,717.641** | **16,953** |

The [final native results](native-results.md),
[machine-readable results](../../experiments/python-gamebub-v108/results.json)
and [comparison CSV](../../experiments/python-gamebub-v108/native-comparison.csv)
retain the distinction between checkpoint trials and actual fresh RTL runs.

The target is **100 MHz / 10.000 ns** on `xc7a100tcsg324-1`. V107's best
completed route has WNS **−2.333 ns**, 21,433 setup failures, hold +0.096 ns,
pulse +3.750 ns and complete zero-error routing. This study retains the same
720×480 CS88 q16/all-BR88 representation and 49,152-byte cap.

The initial matrix freezes the selected seventeen RTL files plus quantization
header and one **RuntimeOptimized synthesis checkpoint**. Each trial reads that
checkpoint without modifying it. No fresh synthesis is attributed to matrix
runs. The selected recipe was then repeated from RTL with the same 10 ns clock
supplied **before** synthesis.

| Trial | Placement | Pre-route physical optimization | Routing | Question |
| --- | --- | --- | --- | --- |
| m0 | Default | None | Default | Establish the checkpoint-reload baseline. |
| m1 | Explore | None | Default | Does more placement effort improve critical-path locality? |
| m2 | ExtraNetDelay_high | None | Default | Does pessimistic net delay produce a more local implementation? |
| m3 | AltSpreadLogic_high | None | Default | Does reduced congestion outweigh longer paths? |
| m4 | Default | AggressiveFanoutOpt | Default | Does pre-route replication shorten critical control nets? |
| m5 | Default | None | AggressiveExplore | Does routing exploration improve the same timing budget? |

All use Default logical optimization, Vivado 2026.1 build 6511674, two threads,
two CPUs, 8 GiB RAM with no additional swap, and a 2,400-second per-run cap.
At most two owned heavy jobs may run concurrently. Launch requires at least
8 GiB available RAM and full memory PSI average10 below 1. Stop below 4 GiB
available or after two full-PSI samples at least 5. Stale swap occupancy alone
is not a veto. The tool/image, source, checkpoint, recipe and resource facts
are retained with every successful or failed attempt.

## Completed frozen-source routes

| Trial | WNS (ns) | TNS (ns) | Failing setup endpoints | Result |
| --- | ---: | ---: | ---: | --- |
| m0 Default | −2.758 | −21,278.961 | 24,107 | Setup fails |
| m1 Explore | −2.788 | −23,398.332 | 24,747 | Setup fails |
| m2 ExtraNetDelay_high | **−2.038** | **−16,629.514** | **22,688** | Best matrix frontier; setup fails |
| m3 AltSpreadLogic_high | −2.667 | −25,030.396 | 26,420 | Setup fails |
| m4 AggressiveFanoutOpt | −2.758 | −21,278.961 | 24,107 | Zero optimized cells; same timing as m0 |
| m5 AggressiveExplore routing | −2.698 | −19,829.510 | 22,737 | Setup fails |

All six completed legal routing with zero routing errors, no unclocked or
unconstrained internal endpoints/loops, zero hold/pulse-width failures, WHS at
least +0.096 ns and WPWS +3.750 ns. The selected m2 improves worst slack by
0.720 ns over the checkpoint-reload control. Compared with the earlier V107
route, worst slack improves 0.295 ns while TNS and failing endpoint count are
slightly worse; this is not a uniform QoR improvement. The unchanged-source
fresh RTL repeat and independently qualified composite build are separate
observations, compared at the start of this report. The −2.038-ns checkpoint
frontier did not reproduce in the fresh unchanged-source route (−2.342 ns).

The [matrix selection](../../experiments/python-gamebub-v108/matrix-selection.json)
binds every route receipt and explicitly labels the selected negative result
as a setup-failing frontier. Pre-route fanout optimization did not replicate
or optimize any cells in m4; its route is not evidence of a replication gain.

The timing clock, exceptions and I/O constraints stay fixed. There is no
random-seed knob, guessed board delay or clock-source location. Post-route
AggressiveExplore is excluded after V107's retained Vivado crash. A selected
negative WNS remains a failure. Internal closure requires nonnegative
setup/hold/pulse, zero corresponding failures, no unclocked or unconstrained
internal endpoints/loops and complete zero-error routing; the clean repeat
must also pass before claiming reproducible component closure.

A separate [capacity-control fallback](capacity.md) passed 31,856,511 complete
old/new public-cycle comparisons and the full two-seed canonical regression:
44 case profiles and 42 directed checks match V107's pixels, events and cycles.
It precomputes packet-only bounds while keeping live block, epoch and fault
checks at their original edge. These are actual RTL results, separate from
native clock qualification.

The completed m2 route exposed an error/cancellation path to a 384-load IDCT
output enable: twelve logic levels, 11.749 ns data delay, including 9.743 ns
routing. A separately qualified [output-word mask](outtile.md) replaces wide
physical output reset with private payload and 64 visibility bits. Two complete
4,303-tile unit seeds preserve every public partial/invalid output. The separate
[collision regression](outtile-kill-collisions.md) additionally checks all twelve
AC group × reset/abort/both write collisions and successful retries per seed.
The DC shortcut remains a same-edge broadcast to all 64 words, matching the
original procedural loop.

These five source changes are outside the frozen implementation matrix. Their
combined full canonical regression passed before the separate native
experiment. The [bounded fallback policy](../../experiments/python-gamebub-v108/output-control-fallback-policy.json)
allows one fresh-RTL composition using the best completed matrix strategy, after
all six matrix outcomes are recorded. This does not replace the unchanged-source
clean repeat. No public timing check, assertion, golden, cancellation fence or
output observation is weakened.

Current native observations are in
[`progress-summary.json`](../../experiments/python-gamebub-v108/progress-summary.json).
The [native diagnosis](native-diagnosis.md) distinguishes completed route metrics
from placement estimates. [Timing follow-up](timing-followup.md) relates the
measured paths to AMD's reset, fanout and physical-optimization guidance.

[Next timing cuts](next-timing-cuts.md) binds the final error/abort-to-Rice
reservoir path and remaining scratch prefetch/selector paths to the actual
selected sources. Priorities are a same-edge co-registered fault predicate,
owned private reservoir storage with an exact canonical view, and earlier
prefetch arithmetic. These are follow-up proposals; none is credited as an
implemented or proven clock fix. Timing closure continues before V109's full
parent implementation gate can pass.

The production parent still uses the legacy JPEG core. Parent clock/protocol,
reference/memory/publication/display integration, board I/O timing, sustained
hardware 30 fps and complete validated decoding below 10 ms remain separate
open milestones. No achieved Fmax is inferred from WNS.

[Independent audit](audit.md) checks the baseline and later trial/repeat
receipts. The immutable matrix is recorded in
[`native-matrix.json`](../../experiments/python-gamebub-v108/native-matrix.json),
and root's resource/scope policy in
[`study-policy.json`](../../experiments/python-gamebub-v108/study-policy.json).

[Portable replay](portable-replay.md) exports either fresh RTL source set without
requiring this host's checkpoint or build-directory paths. Preparation and Tcl
path checks are explicitly separate from native timing qualification.
