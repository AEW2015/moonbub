# V112 proposed clock-ratio CDC behavioral screen

**PASS for an isolated existing CDC fabric at the proposed ratios.** This is
verification-only work; it does not integrate the fabric into the decoder,
change a board clock, or qualify physical CDC or a 125-MHz parent.

The [selected result](../../experiments/python-gamebub-v112/cdc/results.json)
binds [attempt 20261108T194120914406Z](../../experiments/python-gamebub-v112/cdc/attempts/20261108T194120914406Z/receipt.json),
SHA-256 `f7cc563732a59e5a2bdf05b8caa40c1808d70e3403f4e66da49424f912457a66`.
All three existing
[V107 synchronous-control CDC RTL files](../cu66-v107/cdc-sync.md) are unchanged
and hash matched to their original passing receipt, then compiled fresh.
Eight source pins, the Docker image content ID, binary hash, actual commands,
full compressed transfer traces, reset model and per-channel coverage logs
are retained. Strict Verilator `--assert -Wall` and C++
`-Wall -Wextra -Werror` compilation passed with **zero warnings**.

| Profile | Transport / decoder / memory / display half-periods | Accepted | Delivered | Reset-discarded |
| --- | --- | ---: | ---: | ---: |
| Nominal | 2,500 / 4,000 / 5,000 / 17,029 ps | 52,309 | 51,821 | 488 |
| Slightly detuned | 2,501 / 4,001 / 5,003 / 17,031 ps | 52,301 | 51,817 | 484 |

Nominal frequencies are 200 MHz transport, proposed 125 MHz decoder,
100 MHz memory and approximately 29.362 MHz display. The detuned profile is
an additional deterministic phase/ratio sensitivity test, not clock-jitter
or metastability modeling. Each profile runs original seeds 107001–107003;
each run has a continuous 120,000-ns stimulus epoch with the original
six reset epochs, independently stopped clocks, reset while memory is
stopped, delayed initial clocks, deterministic full-queue stalls, randomized
backpressure and final drain. Across six runs: **104,610 accepted = 103,638
delivered + 972 reset-discarded**, with no phantom, reordered, stale-epoch or
changed payload delivery.

The [new bench](../../fpga/experiments/cu66-v112-cdc/tb_cdc.cpp) retains the
original C++ payload/order/epoch/accounting checks and coverage requirements.
Only CLI/profile selection, clock scheduling and trace-time units change.
The scheduler advances to the next exact integer-picosecond clock edge or
original nanosecond stimulus boundary; it never rounds the 17,029-ps half
period. Original reset, clock-stop and long-stall windows remain in
nanoseconds. Random stimulus is sampled at each new scheduler event, so
accepted workloads differ from V107 and between profiles; this is not a
cycle-exact A/B comparison.

The original independent Python accepted-stream replay passes every trace.
An additional replay checks monotonic picosecond timestamps, empty final
ownership, and **exactly nine maximum owned words on every channel in every
run**. The nine slots include eight reserved RAM words (including staged
write) and one output word; no extra staging capacity is assumed. The
unchanged reset contract model also passes and retains its counterexample
showing why fully synchronous up-notifications fail with a stopped peer.

Reproduce with:

```sh
python3 scripts/cu66-v112/cdc/run.py
```

The runner snapshots inputs and runs each compile/test serially under Docker
with two CPUs, 8 GiB memory equal to memory+swap, no additional swap, no
network and bounded watchdogs. Compilation took 2.92 host seconds and each
run approximately 0.41 host seconds, including container overhead. Those are
simulation costs.

This screen uses two-state RTL simulation of the actual isolated five-channel
fabric, without analog metastability or primitive recovery/removal behavior.
There is no new native synthesis, placement, route, mapped synchronizer/Gray
constraint audit, board timing, physical clock-stop qualification, actual
parent PCTL/drain/ownership integration, complete display service or target
throughput result. The synchronous FIFO's previously measured half-rate
read schedule is unchanged; this result does not make it a direct replacement
for the real LCD line-bank path. Original native evidence remains tied to its
original synthetic clocks and cannot be promoted to this proposed profile.

The earlier [original-fabric native report](../cu66-v107/cdc-native.md)
reported **10 CDC-6 Gray-bus warnings, 8 critical CDC-11 peer-up fanout
findings, REQP-1839/1840 asynchronous RAM address/control hazards** (at least
20 displayed findings per rule, report caps reached), and **LUTAR-1** for
the ORed asynchronous reset source. The later synchronous-control prototype
used here previously removed the targeted CDC-11 and REQP findings in its
own mapped unit screen; its reports still retained 10 CDC-6 warnings and
LUTAR-1. Those historical reports remain source/constraint-specific. This
new behavioral ratio PASS closes none of the primitive reset/collision,
metastability, asynchronous reset OR/pulse, physical constraint or complete
parent ownership obligations and supplies no new waiver.

Both original V107 native unit screens used synthetic periods
5 / 10 / 10 / 16.667 ns: **200 / 100 / 100 / approximately 60 MHz**.
The new simulated ratio **200 / 125 / 100 / approximately 29.36 MHz** is
a separate scenario. No old positive route or mapped Gray/skew bound is
reused as physical qualification for the changed decoder/display clocks.
