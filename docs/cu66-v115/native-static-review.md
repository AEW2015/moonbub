# V115 native flow static prereview

**Static review only; this is not a preflight card, audit, or launch approval.** Reviewed driver SHA-256: `e0e27c924eda6b521fadee3e0fe4d60effda4c5c9392cb14ee81c0472fe02dde`. No card or audit was prepared, and no build/test/native flow was run.

## Static passes

- The V115 policy selects five candidate aliases out of the 18-origin frozen V114 composition. The source signature hashes the sorted alias-to-SHA map, so changing a source path without changing its bytes does not create a new composition or allow an unchanged-source/same-clock reroute.
- The three V114 control receipts match policy pins. The driver validates report hashes and parsed route fields. See the values and hashes in [`native-static-review.json`](../../experiments/python-gamebub-v115/inventory/native-static-review.json).
- The 8 ns or 10 ns clock XDC is loaded before `synth_design`; the run requires fresh RTL, then verifies clock name, period and waveform. Default synthesis is selected by omitting the directive; opt/route are Default, placement is ExtraNetDelay_high, and physical optimization is disabled, matching V114.
- Constraints contain only `create_clock`; they add no timing exceptions or guessed I/O delays. The driver checks Vivado build 6511674 and captures/rechecks the local image content ID. The existing V114 reproduction guide names the same image and Vivado installation paths.
- Resource limits are two CPUs, 8 GiB memory and an 8 GiB combined memory-plus-swap ceiling. Launch/stop RAM, PSI and combined-use gates are present. The run timeout is 3600 seconds.
- Audit checks bind the exact preflight, policy and native-driver SHA values. Before launch, the driver snapshots the validated preflight/audit bytes, rechecks their hashes, and creates its dispatch reservation exclusively.
- Budget logic enforces two initial clocks per coordination root, six global initial trials, at most three source compositions, and one positive fresh repeat with the same source signature and clock. The supplied author guard report records 13 passes: all three real V114 controls plus synthetic negative scheduler cases; it contains no positive timing fixture.

## Initial driver scope and pending qualification

This driver is intentionally scoped to the initial composition and writes to `experiments/python-gamebub-v115/coordination`. Refined/final roots are reserved for separate immutable driver/policy derivatives after actual new RTL changes; they are not implemented yet. Such derivatives must preserve the shared global dispatch ledger and alias-to-SHA signature checks, so renamed paths or copied bytes cannot retry a source/clock pair. The current initial driver is not a generic multi-root dispatcher.

Runtime proof qualification is pending while the V115 spatial and control-peer runs complete. `prepare()` correctly requires both selected summaries, along with inverse/ingress/scratch and inherited V114 control proofs. The spatial gate binds V113 canonical evidence and requires the frozen API and original oracles. No exact card exists or has been reviewed yet; wait for Root’s `CARD_READY` signal and audit only that exact pinned card.
