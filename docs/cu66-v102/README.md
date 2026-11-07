# V102: packet-memory inference and fixed-geometry control logic

V102 tests two isolated RTL changes and their combination against the frozen
V101 native baseline, commit `6b36a3228804953c50c10db61f620cad5412ecce`.
The CS88/all-BR88 q16 profile, 720×480 resolution, 49,152-byte packet cap,
interfaces, diagnostic visibility, rounding and cycle schedule are preserved.
Historical sources and the existing production JPEG/MSV1 image are unchanged.

## Functional evidence

| Lane | Case/profile runs | Directed checks | Result |
| --- | ---: | ---: | --- |
| Memory candidate, fresh key/P/late-CRC vectors | 24 | 52 | PASS |
| Memory candidate, historical canonical reconstruction | 88 | 84 | PASS |
| Predicate candidate, historical canonical reconstruction | 88 | 84 | PASS |
| Combined candidate, historical canonical reconstruction | 88 | 84 | PASS |
| Total | 288 | 304 | PASS |

Every lane compares actual baseline and candidate RTL with the unchanged
strict C++ pipeline checkers under seeds `102401` and `102402`. Same-seed
transcripts, cycle counters and stage events are byte-identical; canonical
lanes also compare actual canonical memory bytes. Counts include baseline,
candidate, memory profiles and expected rejection cases. They do not denote
288 distinct displayed source frames or a measured hardware frame rate.
The predicate module is outside the fresh V91j closure, so a redundant
predicate-only fresh run is deliberately omitted. Combined fresh compilation
would use the same changed source closure as the qualified memory fresh run.

The separate [memory test](memory-results.md) passes 19,072 clocked cases,
including 64 forced same-address read-first collisions, with independently
modeled final RAM bytes. The [predicate test](predicate-results.md) exhausts
all 32,768 two-bit-plane/thirteen-bit-tile combinations through actual RTL and
an independent model, with zero clock edges in that combinational probe.
Both focused traces have independent Python replays. Retained failed
verification-harness attempts remain distinguished from candidate behavior.

## What changed

The [memory candidate](../../fpga/experiments/cu66-v102-memory/cs88_admission_v91i2a.sv)
selects the stage-fetch/replay read address and enable before a single
registered packet-memory read. It preserves stage priority, old-data collision
behavior, held data, address/epoch alignment, initialization policy, reset,
cancellation and all public outputs. It adds no RAM-style attribute and does
not shrink storage or the packet cap.

The [predicate candidate](../../fpga/experiments/cu66-v102-predicate/cu66_reconstruct_stream_v91k.sv)
replaces only `safe_hidden`'s runtime division/modulo by fixed tile intervals
for the existing geometry. Full-domain equivalence includes invalid plane 3
and out-of-picture tiles. Validation, counters, other arithmetic and all
observable scheduling remain intact. The combined design uses these same two
frozen files, without an additional RTL rewrite.

## Native comparison

The [vendor comparison](vendor-comparison.md) and
[native evidence audit](../../experiments/python-gamebub-v102/native-audit.json)
record the final matched matrix. The [machine-readable checkpoint](../../experiments/python-gamebub-v102/summary.json)
binds selected functional/native reports and their qualification gates.
All runs retain Vivado 2026.1 build 6511674,
`xc7a100tcsg324-1`, the 10-ns OOC clock loaded before synthesis, original public
ports and Default directives, with no retiming, false-path workaround or DRC
severity change. Memory-only and predicate-only runs isolate synthesis effects;
the combined candidate is the implementation experiment. V101's actual failed
placement remains the original control; an unplaceable control has no routed
clock to compare.

The measured memory-only result reduces total LUTs from 74,340 to **50,548**
and LUT RAMs from 22,286 to **3,854**, while RAMB36 rises from 16 to **32**.
Vivado maps admission storage into BRAM without an attribute. WNS remains
−16.629 ns for this isolated variant, so the memory rewrite alone supplies no
timing improvement. RAM configuration records are observed primitive settings;
behavioral collision tests and those settings do not constitute mapped-netlist
or board-level validation.

The predicate-only variant reduces synthesis LUTs to 71,822 and improves
synthesis WNS to −12.333 ns, but retains the memory-capacity blocker. Combined,
the two changes reduce synthesis LUTs to **49,040** (34.03% below V101), with
**3,854 LUT RAMs** (82.71% below V101), **32 RAMB36** and **28 DSPs**.
Combined synthesis WNS is −12.181 ns; all synthesis comparisons use the same
10-ns target and original control. These are area/control optimizations,
not changes to the codec's compression or behavioral cycle count.

The combined component completes actual placement and routing: **48,522 LUTs**,
**2,718 LUT RAMs**, **34,795 FFs**, **32 RAMB36** and **28 DSPs**. All **72,867
routable nets** are fully routed, with zero reported routing errors. The
unchanged 100-MHz timing target still fails: routed WNS **−13.976 ns** and
TNS **−313,514.625 ns**; hold slack is +0.095 ns. Routing completion is not
timing closure. V101 never placed, so there is no routed baseline comparison.

The routed critical path now runs from reconstruction `tile_reg[10]` to
`residual_reg[1082]/CE`: 29 logic levels and 23.687-ns data delay. Admission
cell indexing also remains a measured long cone at synthesis/placement. The
next isolated experiment should bound or register these geometry/control
calculations, preserving transaction tags, stall/reset/abort behavior and
canonical bytes. Admission's tile is **32 bits**; the exhaustive thirteen-bit
`safe_hidden` proof does not justify narrowing that different state variable.

OOC parent clock location, boundary pin locations and external I/O timing are
unknown. Native warnings and methodology findings are retained; no invented
constraints or waived findings are used. Internal register timing, board I/O
timing, complete custom-top integration and both hardware goals still need
qualification. No achieved Fmax, flashed bitstream or hardware test is claimed.

## Reproduce and verify

Use the V101 documented build environment: Verilator 5.020/GCC 13.3 in
`gamebub-cu66-v69-build`, plus the existing 2026.1 runtime image
`acorn-nexys4-ddr:2026.1`. The native runner mounts installed tools and the
operator-supplied `/home/lori/acorn-nexys4-ddr/cache/vivado.lic` read-only, with
the real host network identity. It copies prepared sources into a new external
`/build` directory; no license contents, generated executables or checkpoints
are included in Git. Native reports and their checkpoint hashes are retained.
Vivado MCP returned `Transport closed`, so native jobs use the working batch
flow. No attached hardware or new installer download is required.

```sh
python3 scripts/cu66-v102/memory.py
python3 scripts/cu66-v102/predicate.py
python3 scripts/cu66-v102/regress.py --variant memory --mode fresh
python3 scripts/cu66-v102/regress.py --variant memory --mode canonical
python3 scripts/cu66-v102/regress.py --variant predicate --mode canonical
python3 scripts/cu66-v102/regress.py --variant combined --mode canonical
python3 scripts/cu66-v102/build.py --variant memory --synth-only --run
python3 scripts/cu66-v102/build.py --variant predicate --synth-only --run
python3 scripts/cu66-v102/build.py --variant combined --run
```

Each command creates fresh attempts. Do not overwrite published evidence.
Launch heavy work only with at least 8 GiB available RAM and memory PSI full
avg10 below 1. Use at most two heavy jobs; native containers have 8-GiB hard
limits, two CPUs/threads and finite watchdogs. Swap occupancy alone is not the
gate. The shared Verilator container retains its separate 4-GiB limit.

The [source audit](audit.md) covers candidate spans, unchanged historical
inputs and functional receipts. `audit_sources.py` and `audit_native.py` verify
retained evidence with Python's standard library. Their evidence PASS statuses
are distinct from physical and hardware qualification. Re-running experiments
requires a new audit/bundle, rather than changing the published checkpoint.

```sh
python3 scripts/cu66-v102/audit_sources.py
python3 scripts/cu66-v102/audit_native.py
python3 scripts/cu66-v102/bundle_manifest.py --verify
```

The bundle manifest hashes this handoff's exact source/report/document scope.
Raw tool-report formatting, frozen snapshots and verified unified-diff context
are retained byte-for-byte; unrelated experiments and external build binaries
are excluded. All three native jobs exited successfully. No V102 build remains
running; setup-timing failure is retained as a result, rather than a job failure.

Sustained hardware 30 fps and complete validated decoding below 10 ms remain
open. Cycle equality preserves the earlier workload: even at the 100-MHz
comparison target the fresh key's 1,386,271 component cycles exceed 10 ms,
before missing whole-system work is included. No achieved clock or hardware
decode latency is derived from these behavioral counters.
