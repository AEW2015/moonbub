# V102-B: exact fixed-geometry hidden-tile predicate

**PASS:** the isolated candidate and original RTL return the same predicate
for all **32,768 binary combinations** of the complete two-bit plane and
thirteen-bit tile domains. Both agree with a C++ geometry model, and a separate
Python replay of the retained RTL tuples also passes. This is combinational
functional evidence; native area/timing and integrated clocked regressions are
separate measurements.

## Frozen candidate

The original is
[`cu66_reconstruct_stream_v91k.sv`](../../fpga/experiments/cu66-v91k/cu66_reconstruct_stream_v91k.sv),
pinned at V101 commit `6b36a3228804953c50c10db61f620cad5412ecce`.
The [candidate](../../fpga/experiments/cu66-v102-predicate/cu66_reconstruct_stream_v91k.sv)
has SHA-256
`04b9fc85dc9ba12cd22e57c84fc9a6f38b782702f9009ce36208cead2945dc4b`.
Only the `safe_hidden` function body changes. The module name, function
signature, every byte outside that function, all 72 public ports, counters,
state, arithmetic, initialization and transaction logic remain unchanged.
The [change manifest](../../experiments/python-gamebub-v102/predicate/change.json)
binds the unchanged original prefix/suffix and both full-source hashes.

The original chooses 90 or 45 inside 32-bit division/modulo expressions to
calculate fixed rectangles. The candidate uses inclusive tile intervals:

- Plane 0: 633–651, 723–741, 993–1011, 1083–1101, 4071–4110,
  4161–4200, 4251–4290, 4431–4460 and 4521–4550.
- Every nonzero plane value: 1046–1064.

Testing the whole binary domain preserves plane 3 behavior and out-of-picture
tiles rather than assuming only normal video input. The other function,
`quant_cell`, and validation/counter behavior are unchanged.

## Actual RTL experiment

The [runner](../../scripts/cu66-v102/predicate.py) compiles two verification
copies of the **complete** original and candidate modules with the unchanged
reconstruction-tile dependency. Verification edits rename the modules, add
probe inputs/results and connect the existing function to those wires. The
runner reverses these edits and requires exact production-body equality.
The wrapper retains every original public input/output; the focused comparison
observes the predicate result, not all protocol behavior.

Backend: the explicitly retained Verilator 5.020 behavioral compiler in
`gamebub-cu66-v69-build`, `--assert -Wall`, C++17 `-O2 -Wall -Wextra -Werror`,
two compile jobs. **No warning class is disabled.** Every plane/tile pair is
applied once; the bench requires original/candidate/C++-oracle equality and
an explicit terminal `TEST_PASS`. True-result counts are **256/19/19/19** for
planes 0/1/2/3. There are **zero clock edges**: this probe does not exercise
clocked assertions, ownership/drain, frame publication or pixel output.

The [selected report](../../experiments/python-gamebub-v102/predicate/results.json)
points to immutable attempt `20261107T211638080148Z`, containing full sources,
strict compile and simulation transcripts, binary hash and all 32,768
compressed input/output tuples. The executable remains outside Git.
Verilator is a two-state backend; no four-state or formal equivalence claim
follows from this test.

## Independent replay

The [standalone auditor](../../fpga/experiments/cu66-v102-predicate/audit_trace.py)
constructs Cartesian rectangle tile sets independently of the candidate's
interval expression. It verifies all 15 retained artifact hashes, parses every
trace tuple, requires exact ordered coverage of all 32,768 inputs and checks
both actual RTL results. The [audit receipt](../../experiments/python-gamebub-v102/predicate/trace-audit.json)
pins its script, selected report, stdout and observed exit code.

Reproduce into a new immutable attempt, then replay its selected trace:

```sh
python3 scripts/cu66-v102/predicate.py
python3 fpga/experiments/cu66-v102-predicate/audit_trace.py
```

The runner uses at least 8 GiB available RAM and memory PSI full avg10 below 1
as its launch gate. Compile/run watchdogs are 300/60 seconds, respectively.
The repository bind must expose the checkout at its host absolute path, with
`/home/lori/gamebub-build/cu66-v69` mounted as `/build` in the build container.

The [V101 vendor review](../cu66-v101/vendor-rtl-review.md) identifies the real
49-level plane-to-counter-enable setup path motivating this experiment.
Parent V102 regression and native-Vivado comparisons determine whether this
candidate improves that path. No change in FPS, decode latency, routed clock,
resource fit or packet compression is established by the focused proof.
