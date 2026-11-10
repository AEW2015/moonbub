# Reproduce V124

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
python3 scripts/cu66-v124/owner/prepare.py
python3 scripts/cu66-v124/integration/prepare.py
python3 scripts/cu66-v124/integration/contract.py
python3 scripts/cu66-v124/owner/qualify.py --run --root-grant ROOT_V124_OWNER
```

Grant names are local resource-slot guards, not authentication credentials.
After focused PASS, run the peer and complete decoder/transport stages in
separate terminals only when two resource slots are reserved:

```bash
python3 scripts/cu66-v124/integration/peer.py --run
python3 scripts/cu66-v124/integration/spatial.py --run
```

Without an explicit source-bound pair-grant file, the spatial seeds run
sequentially. Once those stages pass, run the guarded parent and collect/audit:

```bash
python3 scripts/cu66-v124/integration/live_guard/qualify.py \
  --run --root-grant ROOT_V124_OWNER_PARENT
python3 scripts/cu66-v124/integration/collect_final.py
python3 scripts/cu66-v124/audit_functional.py
```

Check the explicit terminal verdicts, selected receipt paths and hash closure.
Compiler exit zero alone does not pass a functional gate. Run fresh experiments
in an isolated checkout when retaining the published selectors and audits.
Do not edit proof-pinned scripts or RTL while a stage or native run is active.

## Fresh native timing

After all functional gates pass:

```bash
python3 scripts/cu66-v124/native.py prepare --mhz 125
python3 scripts/cu66-v124/audit_native.py PREFLIGHT_JSON --auditor REVIEWER_NAME
python3 scripts/cu66-v124/native.py run \
  --preflight PREFLIGHT_JSON --audit AUDIT_JSON --license-file LICENSE_PATH
python3.14 scripts/cu66-v124/audit_terminal.py --receipt RECEIPT_JSON
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
python3 scripts/cu66-v124/inspect_owner.py \
  --receipt RECEIPT_JSON --label candidate --license-file LICENSE_PATH
```

The [inspection contract](owner-inspection.md) records explicit selection gaps,
mapped widths and individual path families. A successful query means observation
completed; it does not pass a failing clock or count as a fresh implementation.

## Algebra and native endpoint studies

```bash
python3 scripts/cu66-v124/owner_model.py
python3 scripts/cu66-v124/endpoint/run.py --prepare-only
```

The owner model provides finite independent algebraic checks, not clocked RTL
proof. The native endpoint probe compiles actual Sunshine serializer/Rust
receiver snapshots, using its separately pinned dependency image and the
existing read-only Rust toolchain mount. Follow [its source/image/command
contract](endpoint-results.md) and explicit endpoint heavy-slot grant. It does
not change the FPGA native image or execute ESP-IDF, Wi-Fi or QSPI.

The endpoint preparer checks the pinned V123 HEAD as well as source bytes.
After publishing V124, use the [detached-worktree instructions](endpoint-reproduce.md)
for a fresh endpoint attempt; do not rewrite the selected receipt. The selected
proof can be re-audited without compiling or running:

```bash
python3 scripts/cu66-v124/audit_endpoint.py
```

For the separately reviewed native-packet-file QSPI/JPEG replay, reserve one
heavy slot and check the [replay contract/results](jpeg-wire-results.md) and
review hashes before execution:

```bash
python3 scripts/cu66-v124/jpeg_wire/qualify.py --run \
  --root-grant ROOT_V124_JPEG_WIRE
```

This reuses actual QSPI/CDC/guarded-JPEG RTL at its existing clocks; it does not
exercise the custom CS88 component's 125 MHz clock. See the explicit
[full-harness boundaries](harness-boundaries.md).

The additional QSPI/JPEG file replay, when qualified, has its own bounded runner
and source/fixture/endpoint-receipt binding. It is separate from the custom
CS88 component, so it cannot substitute for its functional or timing gates.

The [qualified V120 100 MHz hardware export](../cu66-v120/handoff.md) remains the
remote board control. V124 cannot replace it without its own required timing,
repeat and complete-board qualification evidence.
