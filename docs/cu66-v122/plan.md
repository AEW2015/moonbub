# V122: admission bounds timing and memory-service attribution

Preserve qualified V120 Source B at 100 MHz and the complete V121 evidence.
V121's refill request family closes at 125 MHz, while the component still fails
at −1.347 ns WNS, −3,248.192 ns TNS and 9,407 setup endpoints. This iteration
targets admission cursor/bounds preparation and independently studies the
remaining modeled frame-latency budget.

**Measured outcome:** [V122 results](README.md) retain all functional gates with
zero public-cycle change. Admission cursor/state improves to −0.250 ns but the
complete 125 MHz route regresses to −1.949 ns and is not promoted. The memory
study establishes request/fence accounting, a synthetic trace-schema checker
and analytical burst sensitivities; actual edge instrumentation and an
independent physical controller model remain open. These bounded results do not
close all roadmap V122 memory qualification exits.

## Timing experiment

Only the admission source changes relative to the selected V121 composition;
the V121 prepared request-address queue stays unchanged. Prepare literal full64
chunk-length arithmetic and the separately wrapped uint32 number bound during
existing word-read phases. The consumer states retain their original cycles,
generic arithmetic semantics and error priority. Payload registers do not need
a blanket runtime reset when their ownership is established before use.

Require a focused strict reference/candidate RTL pair plus independent full-width
and cancellation tests, then fresh full decoder/actual V97 transport, physical
debt/peer and guarded byte/row parent tests. Existing independent value, event,
canonical/HUD/root/seal and first-fault checks remain. Prepared-domain fixtures
must drive coherent predecessor phases and be labeled separately from natural
packet tests. No stale private predicate may be forced to manufacture PASS.

Freeze source and proof inputs before running the four-stage regression.
Independently audit its source-bound index and a fresh 125 MHz native preflight.
Use the existing V120 Tcl/report/8 ns recipe byte-for-byte, with constraints
loaded before fresh synthesis. No false paths, multicycle exceptions, guessed
board I/O delays, clock relaxation or directive search. A passing initial route
requires a separate same-source/tool/core-recipe fresh repeat. Retain failures;
do not reroute a negative source unchanged as qualification.

## Memory and frame budget

The [retained trace study](stall-baseline.md) separates observed request/service,
priority phase and fence accounting from unavailable causal wait attribution.
The [burst sensitivity](../../experiments/python-gamebub-v122/memory-study/burst-sensitivity.json)
is an analytical hypothesis, not a changed memory controller or speed benchmark.

The stalled row fixture needs 303,198 fewer cycles to be strictly below 1,250,000
cycles. Perfect overlap of its entire 193,865-cycle post-reconstruction tail
still leaves 1,359,332 cycles. Reconstruction/service therefore also needs work;
validation cannot simply be omitted or the two overlapping savings added.

Next service experiments need exclusive wait ownership and actual write-address,
request/ACK, validation and publication traces. Follow [the memory plan](memory-next.md)
before implementing bigger bursts or more in-flight writes. Keep accepted
physical debt, bank/epoch ownership and validated publication explicit.

## Resource and scope gates

At most two heavy jobs, each two CPUs and 8 GiB RAM with 8 GiB RAM-plus-swap.
Launch on available RAM/full-memory PSI and combined RAM/swap use; do not add
swap or require the cold swap allocation to disappear. Preserve the unrelated
marker-recovery files and their SHA/mtime.

No local hardware programming, complete board image, actual ESP32/RF calibration
or production endpoint change is part of this experiment. Clock qualification,
validated decode latency and sustained distinct hardware 30 fps remain separate
gates. The production parent remains JPEG until the negotiated custom path is
integrated and verified.
