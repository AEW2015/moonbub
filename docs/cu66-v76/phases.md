# V76 fixed-phase replay after warm scanout

This bench replays the frozen V75 RTL after the initial display has already
presented complete exact rasters. It tests whether the favorable bootstrap P
measurement survives when the old front is continuously consuming SDRAM service.
It introduces no production RTL or codec-format change.

## Contract and timing

The first two chronological fixtures in the frozen V69 native index supply key
source 0 and predicted source 1. Each trial resets the model, executes the real
key packet and native HUD endpoint, checks all canonical planes and RGB565
framebuffer words, and continues live LCD scanout while waiting for the planned
P admission. The predicted reference is the previous RTL-produced SDRAM bank;
no golden reference pixels are injected.

P acceptance is fixed at memory-clock tick-end cycle `20,000,000 + offset`, with
`offset` in **0, 384171, 768342, 1152513**. At the assumed 100-MHz memory clock,
the base is 200 ms and the offsets approximate quarter-panel-refresh steps.
These are declared independent source phases, not timings slid until the system
happens to be ready. The immutable P packet is marked complete exactly one
memory cycle before its scheduled acceptance. The bench fails if readiness is
missing at that boundary or actual admission differs from the plan.

The request handshake is sampled halfway through the clock tick, so its exact
simulator timestamp is `admission_cycle * 10000 - 5000` picoseconds. The bench
records physical X/Y, data-enable, front frame ID and front generation at that
sample, rather than reading them after a later pixel edge. During blanking,
physical coordinate outputs can contain unsigned porch-offset wrap values;
active-image coordinate bounds apply only when data-enable is asserted. Every scalar/burst
pair must have identical schedule and sampled phase fields. Generation 1/source
0 must still own the active front, at least one complete exact warm raster must
have finished, and all pre-admission display checks must remain clean.

Four offsets are run in scalar-HUD mode and full-BL8 HUD mode under identical
source pins. The runtime modes retain the V75 read/write command totals:

| Per source | Scalar HUD | Burst HUD |
|---|---:|---:|
| Active x16 writes | 664,320 | 664,320 |
| Physical write commands | 101,520 | 83,040 |
| Physical write beats | 812,160 | 664,320 |
| HUD requests in each direction | 21,120 | 2,640 |
| Painter read commands / input words | 35,040 / 280,320 | 35,040 / 280,320 |
| Painter write commands / output words | 48,000 / 384,000 | 48,000 / 384,000 |

The full packet/qmap/base path, actual processor-side native HUD semantic
preparation and functional memory readback, canonical hash, every portrait
RGB565 word, live LCD order/generation checks and lost-COMMIT-acknowledgment
reconciliation are retained. Each trial must complete both distinct sources,
show at least one complete exact raster of each source, and finish with zero
underruns and zero mismatching black lines. Repeated panel refreshes are not
counted as new source frames.

## Measured eight-case result

All eight trials pass exact canonical/RGB565 and live-LCD checks with zero
underruns and zero mismatching black lines. Every P is admitted at its declared
cycle after **nine complete exact warm rasters**. Each trial has two distinct
source identities; the same sources 0 and 1 are replayed across phases, so this
is **16 accepted source transactions, not 16 distinct source IDs**.

| HUD mode | Offset cycles | P validated | P composition | P transaction |
|---|---:|---:|---:|---:|
| scalar | 0 | 38.24718 ms | 58.49148 ms | 96.73935 ms |
| scalar | 384,171 | 40.28688 ms | 58.32003 ms | 98.60760 ms |
| scalar | 768,342 | 38.19920 ms | 58.81579 ms | 97.01568 ms |
| scalar | 1,152,513 | 36.20444 ms | 59.23407 ms | 95.43920 ms |
| burst | 0 | 30.36680 ms | 58.83406 ms | 89.20155 ms |
| burst | 384,171 | 28.63533 ms | 59.16383 ms | 87.79985 ms |
| burst | 768,342 | 28.16892 ms | 58.43450 ms | 86.60411 ms |
| burst | 1,152,513 | 28.89977 ms | 58.36391 ms | 87.26437 ms |

Warm burst-HUD validated intervals span **28.16892–30.36680 ms**, compared
with **36.20444–40.28688 ms** for scalar HUD. Burst transactions span
**86.60411–89.20155 ms**, versus **95.43920–98.60760 ms** for scalar. The
V75 bootstrap P measurement of 16.98661 ms validated / 75.86986 ms transaction
does not generalize to this already-active front. Composition remains roughly
58–59 ms in both modes.

**Every modeled P transaction misses the 30-fps budget, and every validated
interval misses the strict under-10-ms budget.** Functional correctness is a
PASS; the modeled performance status is `FAIL_30FPS_OR_SUB10MS_BUDGETS`.
The bounded four-phase experiment establishes these observed ranges only.

| Offset cycles | Actual admission cycle | Sample X / Y | Data-enable | Front ID / generation |
|---|---:|---:|---:|---:|
| 0 | 20,000,000 | 304 / 1012 | 0 | 0 / 1 |
| 384,171 | 20,384,171 | 34 / 197 | 1 | 0 / 1 |
| 768,342 | 20,768,342 | 305 / 405 | 1 | 0 / 1 |
| 1,152,513 | 21,152,513 | 35 / 614 | 1 | 0 / 1 |

The same actual admission timestamps, sample positions/data-enable and front
identities are asserted equal between scalar and burst runs. The result JSON
retains nine successful build/run command records, all 38 source/fixture hashes,
and every command-log hash. They were independently rechecked after completion.

## Budgets and result interpretation

Functional PASS and performance verdicts are separate. The recorded P validated
interval runs from immutable packet-complete staging to actual validated-ready.
Composition runs from validated-ready to RGB-ready. The transaction interval
ends at processor commit acknowledgment; it is not full-panel presentation
latency or input-to-photon latency. The raw first-complete-raster timestamps are
also retained, while first-correct-pixel may include black border pixels.

The transaction budget is conservatively 3,333,333 memory cycles for 30 fps.
The under-10-ms validated budget is strict: fewer than 1,000,000 cycles. A missed
budget is recorded as a failed modeled performance goal even if pixels and
ownership remain correct. The finite two-source/four-phase matrix is not the
1,800-distinct-source fixed-arrival or ten-minute physical qualification.
Native HUD CPU execution, hashing/control CPU work and live ESP32 Wi-Fi/QSPI
service remain outside simulated clock time. The command model is not vendor
or electrical signoff; the 100-MHz clock is an assumption, not routed target Fmax.

## Reproduce and audit

```sh
python3 scripts/cu66-v76/run_phases.py --workers 2
```

The runner compiles the frozen V75 source list once with Verilator `--Wall`,
`--timing`, `-j 1`, then runs at most two independent simulations under the
shared 4-CPU/4-GiB container cap. Logs are separate and final command records are
ordered canonically. Subprocess and in-model watchdogs are bounded. Results
retain all source/fixture and command-log hashes; hashes are checked again at
completion.

`fpga/experiments/cu66-v76/phases/first-proof/` preserves the first burst/offset-0
functional qualification before adding runtime concurrency. Its ZIP has six
internally hashed members, including the then-current runner/testbench, result
and logs. The initial result is superseded by the complete matrix and must not
be treated as eight-case qualification. No production RTL changed.
