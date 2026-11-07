# V101 scratch priority compatibility experiment

The isolated candidate replaces the conditional three-band procedural iterator
in `packed_scratch_v91g2` with three explicit, ordered priority blocks. The
original V91g2 RTL, its interface, assertions, initialization and every byte
outside that one source span remain unchanged. This is a synthesis-frontend
compatibility experiment, with no demonstrated cycle, resource or clock gain.

## Frozen change

- Original: [`packed_scratch_v91g2.sv`](../../fpga/experiments/cu66-v91g2/packed_scratch_v91g2.sv), from V100 commit `e8bb1c9cc3cec6775cf128c8fd538a56f022575f`.
- Candidate: [V101 source](../../fpga/experiments/cu66-v101-scratch/packed_scratch_v91g2.sv), SHA-256 `ba0f184ae2f1a70b550208fa36535457c5115398a12a5f25ec7707426c5ee142`.
- [Approved-span manifest](../../experiments/python-gamebub-v101/scratch/change.json) binds both source hashes, unchanged prefix/suffix and module header, and both replaced source spans.

The priority stays DC, band 1, band 2, band 3. Each later slot still checks
`!candidate_valid`. Each address expression remains 32 bits; alignment precedes
the 18-bit request cast. The final `candidate_word_address` still holds the
band-3 expression on the normal EMIT branch, even if DC or an earlier band wins.
The raw branch, cancellation/guard predicates, ownership and cache checks do
not change. No new state, diagnostic tie-off, port reduction or timing exception
is introduced.

## Actual RTL priority-cone comparison

**PASS:** seeds `101401` and `101402` each execute **21,534 prepared-state
cases**, for **43,068 comparisons**. The test compiles both complete original
and candidate modules and compares all **47 public output names** on their
unchanged **79-port** interface. It separately compares candidate valid,
segment, address, final word address and prefetch-launch views. All agree with
the original and the independent unsigned-integer selection oracle.

| Per seed | Cases |
| --- | ---: |
| All 16 DC/AC miss masks under all 256 guard combinations | 4,096 |
| Start/cursor boundaries, line crossings, exhaustion, truncation and wrap | 1,024 |
| Raw-mode last-sample/index/block boundary cases | 30 |
| Deterministic seeded mixed states and addresses | 16,384 |
| Total | 21,534 |

Both seeds reach every priority selection. Seed 101401 selects segments
0/1/2/3 in 3,854/228/146/43 cases; seed 101402 selects them in
3,947/228/146/43 cases. The remaining cases correctly suppress the offer.
Guard cases include prefetch disable, tile-overlap suppression, unsealed,
already offered, outstanding request, reset, matching abort and error. The
seeded set also checks mismatched abort epochs and unrelated states.

Backend: explicitly configured Verilator 5.020, compiled two-state behavioral
RTL, with `--assert -Wall --public-flat-rw`, GCC C++17 `-O2 -Wall -Wextra
-Werror`, and two build jobs. The sole disabled warning is `DECLFILENAME` for
the verification-only module renames. Public-flat instrumentation lets the
bench prepare identical internal states. The generated wrapper connects all
ports and only compares outputs; it adds no candidate behavior.

**Scope:** there are **zero clock edges** in this focused probe. It does not
exercise clocked assertions, establish a sequential protocol, prove reachability
of prepared states, test accepted-request drain over time, or provide hardware
results. Full fresh/historical pipeline regressions are a separate integration
lane. No XSim, formal equivalence or mapped-netlist simulation is claimed.

The [selected receipt](../../experiments/python-gamebub-v101/scratch/probe-results.json)
points to immutable source snapshots, strict compile and terminal `TEST_PASS`
transcripts, the public-port ledger and two complete compressed input/output
traces. Each trace contains 21,534 rows. A separate
[Python trace auditor](../../fpga/experiments/cu66-v101-scratch/audit_trace.py)
parses and replays every retained input using unsigned-32 arithmetic;
[all 43,068 tuples pass](../../experiments/python-gamebub-v101/scratch/trace-audit.json).
Run `python3 fpga/experiments/cu66-v101-scratch/audit_trace.py` to reproduce
this check and the selected raw-artifact hash verification. The
[post-run provenance check](../../experiments/python-gamebub-v101/scratch/probe-provenance.json)
independently matches the actual compiled source copies, preserves the executed
runner snapshot by SHA-256, and pins the external executable. The runner gained
additional tool-provenance capture afterward; its old executed bytes remain
available rather than being silently replaced.

The first verification compile stopped on GCC's array-bounds error: the
Verilator C++ representation of SV `cursors[1:3]` is indexed `0..2`. Only the
new testbench index was corrected. That failed attempt and its original
bench/transcript remain retained. No RTL, warning severity or assertion was
changed to obtain the pass. This was a verification-source defect, not a tool
or candidate behavior failure.

Reproduce the focused comparison into a new immutable directory:

```sh
python3 scripts/cu66-v101/scratch.py
```

The configured container is `gamebub-cu66-v69-build`, with the repository at
its host absolute path and `/home/lori/gamebub-build/cu66-v69` mounted as
`/build`. The runner gates on at least 8 GiB host available RAM and memory PSI
full avg10 below 1. Swap occupancy alone does not stop work. Compile and run
watchdogs are 300 and 120 seconds, respectively.

## Scratch-only frontend probe

The selected frontend receipt is generated separately by:

```sh
python3 scripts/cu66-v101/scratch.py --frontend
```

It uses pinned sv2v 0.0.13 with `-D SYNTHESIS --exclude=Always`, then the native
Yosys 0.33 SV frontend and standard `proc` sequence for the actual scratch
module. There are no source rewrites or IR normalization in this isolated
probe. Conversion is bounded at 120 seconds with one GHC capability and a
1-GiB heap; Yosys is bounded at 360 seconds and a 2.5-GiB address-space limit.
The full transcript, exact scripts, tool hashes and source hashes are retained.
**Terminal result: failed at a different converted function iterator.** The
[raw frontend receipt](../../experiments/python-gamebub-v101/scratch/frontend-results.json)
records successful conversion followed by Yosys exit 1 after 169.96 seconds,
with no timeout or memory-limit termination. Process lowering reaches
`proc_dlatch` and rejects `zigzag$func$converted.sv:279$525.sv2v_autoblock_1.diagonal`.
The original function's diagonal loop is at source line 112. The removed
priority iterator symbol is absent from the converted source, but the scratch
module still has **no successful process-lowering result**.

The [exact-error diagnosis](../../experiments/python-gamebub-v101/scratch/frontend-diagnosis.json)
binds the full transcript and raw receipt. It also corrects one raw diagnostic
boolean: the initial runner detected any `sv2v_autoblock` latch and mislabeled
that as the old priority iterator. The raw receipt stays unchanged; this
precise diagnosis supersedes that boolean. The runner now checks the exact
removed symbol and returns failure for non-PASS frontend outcomes. No rerun is
needed to relabel the already retained actual error line; the executed runner
source is preserved alongside that attempt.

The retained [native primary tool help](../../experiments/python-gamebub-v101/scratch/frontend-help.log)
documents the limited SV frontend and the latch extraction pass. The original
function, standard-converted source and exact fatal were inspected; bounded
Verilator parity passes independently. This identifies a further old-frontend /
retained-`always_comb` incompatibility, not a measured functional latch in the
original RTL or a published tool defect/Answer Record. No additional source or
IR workaround was applied. Scratch synthesis compatibility remains open; the
next step requires a separately reviewed function-lowering change or a more
capable native frontend. There is no complete-component mapping, resource,
routed-clock or 30-fps/under-10-ms hardware result.
