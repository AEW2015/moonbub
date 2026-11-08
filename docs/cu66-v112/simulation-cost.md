# V112 measured simulation cost

[The analysis](../../experiments/python-gamebub-v112/simulation-cost.json)
binds the actual full-component qualification and its two command receipts.
The new candidate took 802.56 host seconds overall, including 118.02 seconds
to compile. The seeded executions took 342.07 and 334.07 seconds for
29,845,741 and 29,837,683 complete decoder-clock steps respectively: about
87,250–89,315 steps per host second.

The inherited verdict field is named `clock_edges`, but the pinned bench
increments it once after evaluating both low and high phases. It counts
complete clock steps, not half cycles. Dense public-event and pixel trace I/O,
scoreboards and software service models are included. Compilation initially
overlapped the bounded JPEG harness; there was no simultaneous native route
during these seed executions. These are instrumented simulator costs, not
target clock frequency or validated decode latency.

At an **assumed** 125 MHz and constant measured cost, simulating 60 continuous
target seconds would take about 23.33–23.88 host hours, and 600 seconds about
9.72–9.95 host days, before compile/setup/fault-campaign overhead. Those are
conditional extrapolations of this component bench. No 60/600-second system
campaign ran, and complete parent/emulator/bridge costs may differ greatly.

Before long campaigns, implement online independent scoreboards and bounded
failure windows instead of unbounded dense logs, preserving assertion and
coverage requirements. Benchmark and cross-check that faster verification
mode before using it for a system-throughput result. The faster JPEG bridge
is a different workload and cannot establish custom-codec simulation speed.
