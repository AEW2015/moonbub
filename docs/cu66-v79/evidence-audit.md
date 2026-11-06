# V79 evidence audit

Run the retained checks from the repository root:

```sh
python3 scripts/cu66-v79/verify_baseline.py
python3 scripts/cu66-v79/verify_evidence.py
```

The baseline verifier requires the V78 parent commit to be an ancestor of
`HEAD`, checks pinned V78 RTL and benchmark inputs, then runs the V78 baseline,
bundle, and evidence verifiers. It establishes integrity and ancestry only.

The evidence auditor checks each retained V79 system result independently. It
requires source SHA-256 pins, successful command records with matching log
hashes, a unique terminal execution marker, and matching frame, timing,
deadline, and summary values between logs and JSON. It checks unique source
identities, the complete native physical raster for each identity, zero
underruns, memory errors, black lines, sticky health flags, and RGB framebuffer
writes. It recomputes packet/admission/validation/ACK timing arithmetic,
modeled threshold flags, performance aggregates, write-beat counts, and the
ACK-to-raster deadline record. That 100 ms raster deadline is a functional
liveness bound only. It also checks that the eight base/tile/auxiliary
occupancy bins and sixteen stage bins each partition every transaction's
recorded cycle total, and that base 1 occupancy equals stage 5 (`BASE_RUN`).

When `campaign/results.json` is retained, the audit additionally requires all
four immutable fixture cohorts (119, 119, 119, and 100 distinct sources) and
their hashed logs and unique terminal markers. This is 457 finite fixture
sources across four independent histories. It does not establish a continuous
60-second/1,800-source or 600-second/18,000-source qualification. Queue
occupancy maxima are sampled by the simulator monitor and retained as summary
values rather than a full per-cycle queue trace. They are a model over the
recorded release schedule, not a hardware queue capacity proof.

The audit reports functional results separately from modeled 30-fps serial
budget and strict under-10-ms observations. Simulator timing is not physical
frame rate or a target clock measurement. No live ESP32, CPU HUD execution
cost, fitted FPGA, CDC, electrical, or long-duration claim follows from these
artifacts.

When present, `paired-comparison.json` is checked against its pinned V78 and
V79 result files. The auditor independently recomputes the count of exactly
preserved original transaction and presentation fields and verifies the
retained observation differences. `analysis.json` is checked against pins for
exactly the audited system runs; its distributions, finite cadence, raster
latency, queue summaries, and disjoint profile-bin ratios are recomputed from
those source results.

When `queue-budget.json` is present, the auditor verifies the pinned fixture
index, fixture packet bytes, system result files, and queue model script. It
replays release, admission, and ACK ownership with the model's conservative
same-cycle event order and recomputes retained packet and byte peaks. The
illustrative reservation sizes are endpoint budgeting scenarios; they do not
measure free SRAM on an ESP32 or account for transport, application, or runtime
memory. Variable actual-packet-byte totals are shown separately from the fixed
48 KiB-per-slot reservation estimate.

When `prefetch/results.json` is present, the auditor verifies only the final
attempt's pinned RTL, testbench, runner, frozen address map, archived source
snapshots, four command logs, nine directed case records, and terminal summary.
Its required scope markers keep the prototype separate: a deterministic simple
backend, zero physical SDRAM model, zero system integration, and no speedup
claim. Earlier prototype attempts remain historical evidence and are not
treated as source-reproducible qualification runs.

When `layout-study/results.json` is present, the auditor checks its pinned
source files, six grouped mappings, exact restoration of the pinned YUV
fixture, active/padded byte and tile counts, and completeness of the 96
synthetic service scenarios. It checks logical request-to-wire-byte
conservation and basic row-work counter consistency. The modeled service work
remains uncalibrated and does not represent latency, LCD deadlines, or a
hardware speedup.
