# Reproduce the V110 evidence

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
in `experiments/python-gamebub-v110`.

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
python3 scripts/cu66-v110/canonical.py --variant busy --run
python3 scripts/cu66-v110/canonical.py --variant combined --run
python3 scripts/cu66-v110/dequant_canonical.py --variant combined --run
python3 scripts/cu66-v110/ready_canonical.py --variant combined --run
python3 scripts/cu66-v110/prefix_canonical.py --variant combined --run
python3 scripts/cu66-v110/cursors_canonical.py --variant combined --run
python3 scripts/cu66-v110/address_cursors_canonical.py --variant combined --run
python3 scripts/cu66-v110/count_domain_canonical.py --variant combined --run
```

Run only after the corresponding focused proofs pass. Each invocation retains a
new attempt and checks both original seeds against the frozen V109 FETCH actual RTL (it matched V108)
stdout, events and raw canonical pixels. Each complete pair has 44 case profiles
and 42 directed checks. This reuses an actual baseline run; it does not pretend
that the original control was newly rerun. The native read-order body containing
three admission modules is split losslessly for compilation, with independently
checked fragment hashes. The split is not an RTL replacement.

Respect the global limit of two heavy jobs and available-RAM/pressure gates.
Do not run these commands concurrently. Failures remain evidence, including
the four retained readiness-fixture attempts and their separately recorded repairs. A PASS must refer to a terminal actual run.

## Fresh physical replay

Native study runs use Vivado **2026.1 build 6511674**, Artix-7 support and
`xc7a100tcsg324-1`. A legitimate license is required. The existing study runner
mounts the supplied license read-only; no license contents or host identifiers
are altered. The study ledger rejects duplicate trial tags and enforces its
bounded trial policy. Use the portable exporter for an independent replay:

```sh
python3 scripts/cu66-v110/export_replay.py \
  --preflight experiments/python-gamebub-v110/prepared/EXACT_TRIAL/preflight.json \
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

`python3 scripts/cu66-v110/summarize.py` regenerates the native comparison and
actual-receipt summary. A running trial is listed separately from completed
routes. Negative setup slack fails the 100-MHz component target. A nonnegative
candidate additionally needs a fresh RTL repeat before a reproducible component
clock claim.

`python3 scripts/cu66-v110/cycle_budget.py` summarizes actual regression counters
against the assumed one-million-cycle budget for strict 10 ms at 100 MHz. These
are component simulation fences, not calibrated validated-frame publication
latency. The production parent still needs the adapters and complete-top checks
listed in [hardware-gates.md](hardware-gates.md). Neither an OOC route nor
these regression workloads proves sustained hardware 30 fps or complete
validated decoding below 10 ms.

## Offline hardware-evidence checker

[hardware-evidence.md](hardware-evidence.md) defines a proposed JSON/JSONL trace
format and calibration/provenance requirements. Run its stdlib self-tests with:

```sh
python3 -m unittest discover -s scripts/cu66-v110/tests -p test_hardware_evidence.py
```

Synthetic success tests validate only the checker. They cannot attest that a
board produced a trace or qualify hardware; those flags remain false offline.

## Conditional same-source synthesis comparison

[default-method.md](default-method.md) describes the separately bounded
Default-versus-RuntimeOptimized experiment. The original policy and receipts
remain frozen. Its driver refuses preparation until all five original V110
routes are complete and negative, then requires the control with the highest
final WNS and identical current 18-source/canonical/focused bindings.

```sh
python3 scripts/cu66-v110/native_default.py --control PATH_TO_CONTROL_RECEIPT
```

This only prepares inputs. Dispatch additionally requires the independent
preflight audit and current resource gates. Generated Default receipts live
in `experiments/python-gamebub-v110/default-native`. A positive Default result
requires `native_default_repeat.py --control PATH_TO_CONTROL_RECEIPT --repeat-of
PATH_TO_DEFAULT_RECEIPT` followed by its own audited dispatch; that repeat
executes fresh RTL with Default synthesis again. The [repeat-only driver](default-repeat.md)
binds the actual tool-emitted synthesis command and complete log SHA; an omitted
directive need not produce a separate directive-info message. It preserves a
missing message as `None` and does not alter the parent receipt. Never use a RuntimeOptimized
repeat driver for a Default result. The global positive-repeat budget is one.

## Later source compositions

The [private-cursor](cursors.md) comparator keeps every public/invalid/debug and
noncursor observation exact. It compares private cursors while either side has
a live owner, and deliberately allows retired values to differ until the next
owner restores them. This is not an all-private-state equivalence claim.

The [count-domain](count-domain.md) generic context defaults to all original
checks. Only the validated synchronous caller enables the specialization. Its
conditional unit comparison is paired with unchanged generic tests, an actual
caller-start count assertion, and complete-ingress packet/error comparisons.
Do not enable it in a new caller without discharging that count precondition.

Use [export_current_replay.py](../../scripts/cu66-v110/export_current_replay.py)
for source-only replay of later preflights. It records the declared synthesis
mode, observation scope and actual 2,400- or 3,600-second watchdog from the pinned
input card. The [current export checks](export-current-checks.md) are preparation
and path-resolution checks; they did not run Vivado again. No original DCP is
required by these fresh-RTL exports.


## Count-domain native gate

The source/method control is the actual address/cursor Default route, not its
Runtime predecessor. The new count-domain policy permits one initial trial
with exactly two source deltas (context and its synchronous caller), and one
globally shared positive-result fresh repeat. Generic context behavior remains
unconditional; specialization requires the owned count-domain precondition.

```sh
python3 scripts/cu66-v110/native_count_domain.py
# After independently auditing the exact generated preflight:
python3 scripts/cu66-v110/native_count_domain.py --run \
  --preflight EXACT_PREFLIGHT --audit EXACT_AUDIT
# Only if the actual final routed receipt passes all internal clock checks:
python3 scripts/cu66-v110/native_count_domain.py --repeat-of POSITIVE_RECEIPT
```

Each preparation and dispatch rechecks all source/proof/recipe/policy pins.
The repeat must retain the same sources, Default command, 10-ns clock and full
method; its new preflight needs its own independent gate. Recorded trial and
repeat reservations intentionally prevent silently redispatching historical
commands. Source-only exports allow a separately allocated fresh implementation
without mislabeling old native receipts as new.

The repaired preparation driver differs from its retained predecessor only in
the Python path join. The previous preparation failed before any preflight or
native dispatch; [the repair receipt](../../experiments/python-gamebub-v110/count-domain-preparation-repair.json)
preserves the failed code and records the added actual-qualification guard.
