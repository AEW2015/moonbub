# Measured component simulation cost

The actual complete V111 canonical qualification passed both seeds. Hardware
timing is not measured by simulator wall time. This separate
analysis answers how expensive long verification campaigns may be with the
current **instrumented component testbench**.

| Seed | Full clock steps | Simulation command wall time | Steps / host second | Projected host time for 60 simulated seconds at 125 MHz |
| --- | ---: | ---: | ---: | ---: |
| 107601 | 29,845,741 | 342.067 s | 87,251 | 23.88 hours |
| 107602 | 29,837,683 | 338.065 s | 88,260 | 23.60 hours |

The benchmark calls `tick()`, evaluates low and high clock phases, then
increments `cycle` once. The verdict's legacy `clock_edges` field is that
full-clock-step counter, not twice the number of cycles. The analysis binds
the actual bench source and receipt. Each run has two memory-service profiles,
dense event/pixel trace output and verification-only reference helpers. Another
bounded native job ran concurrently on this host. Compilation took 116.026 s;
whole qualification including setup/hashing/compression took 803.508 s.

At the assumed scenario frequency, 60 seconds needs 7.5 billion cycles and
600 seconds needs 75 billion. Constant-cost extrapolation gives about
9.84–9.95 host days for 600 simulated seconds. This is not a forecast for a
different full-parent/emulator model; evaluation and I/O costs can change
substantially. The clock is an assumed simulation scenario, not an achieved
FPGA clock or calibrated ESP32 frequency. Compilation and campaign overhead
are excluded from the projections.

For V112, profile evaluation versus trace/scoreboard I/O. Keep all assertions
and independent comparisons while evaluating compact online checkers and
bounded failure traces. A transaction/service model can accelerate broad
parameter sweeps, but remains a separate fidelity level. Preserve continuous
owner/frame/memory state across checkpointed campaign segments. Do not count a
short run repeatedly or append drain time to satisfy the 60/600-second gates.

No system-FPS, shared-time, RF, MCU silicon-cycle or validated-decode claim is
made by this cost analysis. No 60/600-second system campaign was executed.

Reproduce the calculation from retained actual commands/counters:

```sh
python3 scripts/cu66-v111/simulation_cost.py
```

[Machine-readable findings](../../experiments/python-gamebub-v111/simulation-cost.json)
pin the exact qualification, selected receipt and counter source.
