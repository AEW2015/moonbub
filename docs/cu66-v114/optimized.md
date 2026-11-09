# V114 reserved control plus prepared scratch prefetch

This is a separately qualified composition. It changes exactly two bodies from
the frozen V113 18-source component: the V114 registered-admission top
(`9e6d2b88ad0f06ca0df5a5218be0d78a9fa9d9e8151d3b0b43aebaafc3ba76bd`)
and the prepared scratch prefetch source
(`332da2058fd3e6413e8cc6336c1aab13eba7cddaaa76bb9d49c8426b1727854a`).
Geometry, inverse math/result slots and every other body remain unchanged.
The prepared-prefetch focused proof claims no additional public cycles; IV114.1
still supplies the top's explicitly changed public admission/delivery timing.
No clock-closure or hardware rate follows from those functional claims.

`scripts/cu66-v114/optimized_spatial.py` is separate from the primary runner.
It pins that frozen runner, the original 496-line oracle and all six shared
harness files. Both API and clock-hook adaptations are reconstructed and
reversed in memory, checked against their manifests and existing bytes, and
never written by the optimized runner. The original independent value/order,
held tuple, EOF, counter, malformed-frame, physical-memory/reference ownership
and drain assertions remain active. No primary proof or shared harness artifact
is changed by this run.

All inherited geometry/scratch/inverse proofs, the new control proof and the
new prepared-prefetch proof are checked through both summary and raw receipt
hashes, source pins, actual strict Verilator commands and retained artifacts.
The optimized campaign freshly compiles its actual changed component model;
it reuses neither the primary candidate model nor its canonical executions.
For seeds 107601/107602 it requires all 44 canonical case/profile rows and
42 original directed checks, with exact frozen canonical output bytes. Its
separate actual V97→CS88 campaigns additionally require 24 successful profiles,
four abort/reset canonical retries, finite FIFO/descriptor ownership and all
32 command captures/deliveries/poisoned tuples. Public ingress commit remains
separate from decoder completion and validated tentative pixel bytes.

Run with:

```sh
python3 scripts/cu66-v114/optimized_spatial.py
python3 scripts/cu66-v114/optimized_spatial.py --run
python3 scripts/cu66-v114/optimized_resume.py
python3 scripts/cu66-v114/optimized_resume.py --run
```

Attempt `20261108T230004120722Z` freshly compiled and passed all 44 canonical
profiles/42 directed checks and transport seed 107601's 12 profiles/two retries.
Its second transport seed was stopped by the unchanged host memory-pressure
gate (exit 143, full-memory PSI avg10 8.75), with no final verdict. That complete
attempt remains `FAIL`; its successful sub-results are retained certificates,
not a pass for the interrupted run. Both canonical stdout transcripts and the
completed first transport transcript exactly match the primary composition,
including cycle and counter observations.

The separate recovery script rehashes the failed parent, every retained source
and artifact, the actual transport binary and all expanded fixtures. It copies
the completed certificates and immutable source snapshots and executes the
entire missing seed 107602 with the same gates. Its receipt distinguishes zero
new canonical profiles/checks from 44/42 qualified, and 12/two new transport
profiles/retries from 24/four qualified. The parent stays failed; its partial
second-seed transcript is not treated as a successful result. Neither the
original runner nor the production source changes during recovery.

Selected recovery `20261108T233450283581Z` passed. Its raw receipt SHA-256 is
`ffdf5ea648f248f8f6826e2a1ba2a59ef688e30febf53a979020fe303362c3f0`;
the selected summary SHA-256 is
`f38b16ad038eb2c6cbabb5d9a1b84a57c4a24d48dcf2d05df2590ab038239e04`.
The new seed completed all 12 profiles/two retries with 16 command captures,
deliveries and poisoned tuples, 16 wrong tokens on each transport channel,
17,246 held-ACK cycles and the observed 2,048-byte/two-descriptor bounds.
The selected recovery has zero new canonical executions and 12/two new
transport executions, with the qualified totals above. The missing seed's
canonical bytes exactly match the frozen oracle.

Read-only `optimized/spatial/source-review.json` verifies all 47 current source
pins, 67 selected artifacts, all 61 parent artifacts and decompressed event/pixel
hashes. All four complete stdout transcripts are byte-identical to the frozen
primary composition: canonical clock edges 28,259,277/28,259,849 and transport
clock edges 23,641,437/23,638,696. This is measured preservation for these seeds,
not a claim of reduced cycles. Recovery saw no pressure stop (maximum full PSI
avg10 0.00). Native adoption also requires the separate control-peer proof;
this functional result alone does not qualify the registered kill or clock.

The workflow retains the explicit tools-image identity, Verilator assertions,
fatal SV `-Wall` and owned C++ `-Werror`, one compiler worker, two CPUs and
8 GiB memory with an equal swap limit, finite watchdogs and host memory/PSI
gates. Every failed attempt remains retained. A selected success must be
`PASS_V114_OPTIMIZED_SPATIAL_CANONICAL` under
`experiments/python-gamebub-v114/optimized/spatial/results.json`, with its own
raw receipt, source snapshots and artifact hashes. Native component trials are
separate Root-owned work. The JPEG comparison remains the frozen V112 path;
this is not a QSPI/ESP32/Sunshine wire-level or full publication qualification.
