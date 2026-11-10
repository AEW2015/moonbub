# Reproduce V123

Use Linux, Python 3.10+, Git, Docker and the pinned simulation image recorded in
the receipts (Verilator 5.020). Native timing uses Vivado 2026.1/build6511674,
the retained image and a legitimate locally available license. Python 3.14 or
the optional `zstandard` package additionally enables checkpoint EDIF inventory
in the terminal auditor. No board is contacted by these experiments.

Run from the repository root. Reserve at most two heavy jobs globally, each two
CPUs/eight GiB RAM with no extra swap allowance. Launch/runtime guards use
available RAM, full-memory PSI and combined RAM/swap consumption. An occupied
cold swap allocation alone does not prevent work.

## Functional gates

Validate the reversible preparation and focused sources first:

```bash
python3 scripts/cu66-v123/rank/prepare.py
python3 scripts/cu66-v123/integration/prepare.py
python3 scripts/cu66-v123/integration/contract.py
python3 scripts/cu66-v123/rank/qualify.py --run --suite all --root-grant ROOT_V123_RANK
```

Grant names are local resource-slot guards, not authentication credentials.
After focused PASS, run the peer and complete decoder/transport stages in
separate terminals only when two resource slots are reserved:

```bash
python3 scripts/cu66-v123/integration/peer.py --run
python3 scripts/cu66-v123/integration/spatial.py --run
```

Without an explicit source-bound pair-grant file, the spatial seeds run
sequentially. Once those stages pass, run the guarded parent and collect/audit:

```bash
python3 scripts/cu66-v123/integration/live_guard/qualify.py \
  --run --root-grant ROOT_V123_RANK_PARENT
python3 scripts/cu66-v123/integration/collect_final.py
python3 scripts/cu66-v123/audit_functional.py
```

Check the explicit terminal verdicts, selected receipt paths and hash closure.
Compiler exit zero alone does not pass a functional gate. Run fresh experiments
in an isolated checkout when retaining the published selectors and audits.
Do not edit proof-pinned scripts or RTL while a stage or native run is active.

## Fresh native timing

After all functional gates pass:

```bash
python3 scripts/cu66-v123/native.py prepare --mhz 125
python3 scripts/cu66-v123/audit_native.py PREFLIGHT_JSON --auditor REVIEWER_NAME
python3 scripts/cu66-v123/native.py run \
  --preflight PREFLIGHT_JSON --audit AUDIT_JSON --license-file LICENSE_PATH
python3.14 scripts/cu66-v123/audit_terminal.py --receipt RECEIPT_JSON
```

Replace placeholders with the unique preflight output, its sibling audit, your
existing license path and the resulting terminal native receipt. Keep license
contents outside logs and source control. The preflight pins the auditor itself
as well as selected proofs, source composition and the fixed core recipe.

The source clock is 8 ns before fresh RTL synthesis on `xc7a100tcsg324-1`.
V120 Tcl/report files and their historical `V120_*` log markers are reused
byte-for-byte. No checkpoint is used as an implementation starting point.
The receipt retains source/recipe snapshots, commands and reports; larger
checkpoints remain in its external build directory. No complete board bitstream
or guessed board I/O delays are produced.

A passing route requires a separately audited fresh repeat of the identical
source/tool/core recipe using `prepare --mhz 125 --repeat-of INITIAL_RECEIPT`.
A negative route is retained and is not rerun unchanged as qualification.

To query an existing route without modifying it:

```bash
python3 scripts/cu66-v123/inspect_rank.py \
  --receipt RECEIPT_JSON --label candidate --license-file LICENSE_PATH
```

The [inspection contract](rank-inspection.md) records explicit selection gaps,
mapped widths and individual path families. A successful query means observation
completed; it does not pass a failing clock or count as a fresh implementation.

## Python spatial prototypes

```bash
python3 scripts/cu66-v123/rank_model.py
python3 scripts/cu66-v123/overlap_model.py
```

The rank model supplies independent finite algebraic checks. The overlap model
uses retained canonical bytes and explicitly synthetic compute/memory/digest
service costs. It is a causal architecture prototype, not a calibrated physical
controller, RTL qualification or a measured latency/FPS improvement. Keep these
results separate from the exact-cycle decoder regressions.

The [qualified V120 100 MHz hardware export](../cu66-v120/handoff.md) remains the
remote board control. V123 cannot replace it without its own required timing,
repeat and complete-board qualification evidence.
