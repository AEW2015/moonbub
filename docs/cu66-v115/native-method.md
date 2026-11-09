> This records the initial driver's design and authoring cutoff. References to
> missing proofs or reserved future drivers below are historical. Current
> [status](status.md), [refined routes](native-refined.md), and
> [final composition](final.md) identify the later source-bound runs.
> `native_final.py` uses the same refined flow and shared budget with six
> aliases and `PASS_V115_FINAL_SPATIAL_CANONICAL`; it additionally requires the
> actual owner-certificate focus and final peer proof.

# V115 source-bound native timing method

`scripts/cu66-v115/native.py` prepares and launches the initial five-body V115
composition only. No native job was launched while authoring it. At this stage
the complete spatial and actual-composition peer proofs are prerequisites, not
synthetic PASS placeholders.

## Fixed sources and evidence gates

The frozen V114 B125 receipt is the 18-origin baseline:
[`521daae4…`](../../experiments/python-gamebub-v114/optimized/native/20261108T235739184089Z/receipt.json).
Exactly five aliases may change: dequant, IDCT, synchronous ingress, Rice parser,
and packed scratch. The V114 reserved-control top, eleven other bodies and one include
remain unchanged. New focused proofs bind both inverse files, both
ingress files and scratch directly to their chosen source hashes. A separate
peer proof must pin all 18 sources. The V114 control proof is retained as an
inherited prerequisite, not counted as newly executed V115 evidence.

The full proof must be `PASS_V115_SPATIAL_CANONICAL`, with fresh candidate model
compilation and no candidate/canonical reuse: 44 canonical profiles, 42 directed
checks, 24 actual V97 transport profiles and four abort/reset retries across
seeds 107601/107602. Both raw stdout verdicts and accepted canonical bytes are
checked against the frozen V113 reference. The original bench API derivation is
reversed back to the unmodified V107 oracle; the V114 harness remains unchanged.
The admission source's existing lossless compile-fragment manifest is verified
by source bytes and fragment hashes. Component and V97 models are both rebuilt,
and the owned adapter uses strict C++17 warnings. No old partial resource-recovery
branch is accepted for a new V115 candidate.

The three matched controls are V114 A100, B100 and B125. Their five raw report
hashes, actual clocks, timing and routing are reparsed before a card is prepared.
They are retained negative controls, not fresh runs.

## Actual clock and flow

Allowed initial trials are `integrated-100` (10.000 ns, waveform 0/5) and
`integrated-125` (8.000 ns, waveform 0/4). The clock XDC is registered before
fresh `synth_design`; there is no checkpoint-read branch. The fixed part is
`xc7a100tcsg324-1`, with Vivado 2026.1 build 6511674. Default synthesis by omission,
Default optimization/routing and ExtraNetDelay_high placement match V114. No
retiming option, separate physical optimization stage, timing exception, I/O
delay guess, KEEP/DONT_TOUCH or fanout directive is added. Normal placer register
optimizations still operate and must be observed in the actual reports.

Each stage retains clocks, setup/hold/pulse summaries and paths, methodology,
DRC, CDC, exceptions, high fanout, control sets, utilization/congestion, DSP
AREG/BREG/MREG/PREG, RAM modes/output registers and selected local predicates.
Before/after effective XDCs are kept. A missing required report fails the flow;
optional methodology JSON failure is recorded explicitly. The native parser
requires the actual period/waveform, zero setup/hold/pulse failures, no
unconstrained internal endpoints or clock/logic loops, and complete error-free
routing. Missing external I/O delays remain an explicit OOC/full-parent gap.

## Scheduling, immutable cards and launch

The shared budget allows six initial routes across up to three source
compositions and one positive fresh repeat, preferably at 125 MHz. Each
coordination root may measure its one composition once at each clock. Dispatch
records bind an identity computed from all 18 alias-to-source hashes: renaming
paths cannot authorize an unchanged-source/clock retry. New composition roots
require changed source bytes. This is a guard plus Root review of the actual
source changes; it is not permission for a strategy or whitespace search.

The initial driver implements only its `experiments/python-gamebub-v115/coordination`
root. The `refined/coordination` and `final/coordination` roots are reserved for
future separate drivers and policies; they are not selectable with this driver.
After a measured result motivates an actual RTL change, Root must adjust both
the derived driver's `AREA` and its literal reservation roots, while retaining
the shared budget, alias-to-source identity and cross-root duplicate guard.

Root serializes dispatch decisions and grants at most two controlled heavy jobs
across all study workers. The driver is not an atomic scheduler for independently
invoked launchers or unrelated host projects. Each native job has two CPUs,
8 GiB RAM and an equal combined RAM-plus-swap ceiling (no extra container swap),
2,048 PIDs, two Vivado threads and a 3,600-second watchdog. Launch needs at least
8 GiB available RAM, full-memory PSI avg10 below 1 and combined RAM/swap use below
85%. It stops below 4 GiB available, at PSI at least 5 twice, at combined use at
least 90%, or at the watchdog. All gates remain active during the run.

Preparation and launch both verify sources, proofs, budget, tool image and
recipes. A card binds the live policy, driver/tooling, source snapshots and exact
clock. A named independent reviewer must finish and declare its audit stable
with all eight checks before Root launches. The validated audit and preflight
are read atomically and retained byte for byte as launch snapshots, alongside
source and recipe snapshots. A late file rewrite cannot silently replace the
bytes that were validated. The existing legitimate license and tools are
mounted read-only; host networking is retained for that license, without hostid
or MAC changes. License contents are never read into evidence.

```sh
python3 scripts/cu66-v115/native.py --trial integrated-125
# After the exact card receives its FINAL/STABLE independent audit and Root grant:
python3 scripts/cu66-v115/native.py --run --preflight CARD --audit AUDIT
```

Missing selected proofs print `PREREQUISITES_NOT_READY` and create no card or
build. Once the first card is prepared, Root freezes the policy, shared budget,
flow and driver. A positive repeat must start from fresh RTL with matching
sources, policy, tools, recipes and clock; a negative result authorizes no repeat.
No simulation or tool exit alone establishes timing closure, hardware 30 fps,
validated full decode below 10 ms, or full-parent integration.

## Author checks

Before any card, 13 read-only/local checks passed: the three actual retained
controls parse identically to their receipts; a 100-MHz report is rejected as a
125-MHz result; scheduler fixtures cover first/second clocks, source changes,
source mutation within one root, copied-source roots, duplicate runs, exhaustion
and invalid positive-parent locations. Those scheduler fixtures are synthetic
unit checks, not positive timing evidence. The complete-proof prepare command
currently rejects the missing full/peer prerequisites. Root performs the final
independent review after those real proofs complete.
