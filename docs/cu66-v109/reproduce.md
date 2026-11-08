# Reproduce the V109 evidence

Use the complete Git branch, including its older tracked dependencies. The
source aliases in a receipt are historical read-order names; `source_origins`
identifies the actual source bodies. Do not substitute a similarly named file
from an earlier experiment. Each native closure contains 17 SystemVerilog files
and one table header.

## Functional checks

The host scripts require Python 3.10+ and Docker. Functional jobs use
`gamebub-cu66-v69-tools:20261105`; its build recipe is
[the retained Dockerfile](../../fpga/experiments/cu66-v69/build-env/Dockerfile).
They select Verilator with assertions and strict warnings, one compiler job,
bounded memory and no extra swap. Generated binaries remain outside Git under
`/home/lori/gamebub-build/cu66-v69`; portable receipts and source snapshots stay
in `experiments/python-gamebub-v109`.

The functional harnesses currently use the study host's absolute external build
root. Create it with write permission before running:

```sh
mkdir -p /home/lori/gamebub-build/cu66-v69
```

On another host, use an equivalent writable location and adjust the harness's
external build-root constant; record that verification-script change in the new
attempt. Do not change production RTL, reference hashes or goldens to relocate
a build. The functional inputs are tracked compressed fixtures; the original
gameplay video, old external build binaries and checkpoints are not required.

The leaf reports give each focused command and selected attempt. Complete
decoder comparisons use these separate harnesses:

```sh
python3 scripts/cu66-v109/canonical.py --variant fault --run
python3 scripts/cu66-v109/combined_canonical.py --variant combined --run
python3 scripts/cu66-v109/fetch_canonical.py --variant fault --run
python3 scripts/cu66-v109/request_canonical.py --variant fault --run
```

Run only after the corresponding focused proofs pass. Each invocation retains a
new attempt and checks both original seeds against the frozen V108 actual RTL
stdout, events and raw canonical pixels. Each complete pair has 44 case profiles
and 42 directed checks. This reuses an actual baseline run; it does not pretend
that the original control was newly rerun. The native read-order body containing
three admission modules is split losslessly for compilation, with independently
checked fragment hashes. The split is not an RTL replacement.

Respect the global limit of two heavy jobs and available-RAM/pressure gates.
Do not run all four commands concurrently. Failures remain evidence, including
the original fault verification fixture compilation failure and its separately
recorded repair. A PASS must refer to a terminal actual run.

## Fresh physical replay

Native study runs use Vivado **2026.1 build 6511674**, Artix-7 support and
`xc7a100tcsg324-1`. A legitimate license is required. The existing study runner
mounts the supplied license read-only; no license contents or host identifiers
are altered. The study ledger rejects duplicate trial tags and enforces its
bounded trial policy. Use the portable exporter for an independent replay:

```sh
python3 scripts/cu66-v109/export_replay.py \
  --preflight experiments/python-gamebub-v109/prepared/EXACT_TRIAL/preflight.json \
  --dest /absolute/path/to/a/new/external-build-directory
```

Replace `EXACT_TRIAL` with the prepared directory named by the selected native
receipt's `native_contract_path`. The export verifies all source and recipe
hashes and writes a relative-path fresh-RTL build. It needs neither the original
checkpoint nor original external build directory. Follow its generated README
to run Vivado in a bounded allocation and inspect final setup/hold/pulse, clock,
methodology, routing and utilization reports. Preparing an export does not run
Vivado or reproduce timing. The recorded export checks are source-only tests.

The clock remains 10.000 ns, loaded before synthesis. No false/multicycle path,
clock relaxation or invented board delays are part of this experiment. OOC I/O
is intentionally not board-qualified; missing parent interface constraints must
be resolved during integration, not waived into a full-system timing pass.

## Interpret the results

`python3 scripts/cu66-v109/summarize.py` regenerates the native comparison and
actual-receipt summary. A running trial is listed separately from completed
routes. Negative setup slack fails the 100-MHz component target. A nonnegative
candidate additionally needs a fresh RTL repeat before a reproducible component
clock claim.

`python3 scripts/cu66-v109/cycle_budget.py` summarizes actual regression counters
against the assumed one-million-cycle budget for strict 10 ms at 100 MHz. These
are component simulation fences, not calibrated validated-frame publication
latency. The production parent still needs the adapters and complete-top checks
listed in [integration-gaps.md](integration-gaps.md). Neither an OOC route nor
these regression workloads proves sustained hardware 30 fps or complete
validated decoding below 10 ms.
