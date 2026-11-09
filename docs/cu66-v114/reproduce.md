# V114 reproduction guide

Run commands from the repository root. Start with the [V114 overview](README.md), which describes the contracts and limits. Study commands using `--run` create new timestamped attempts and update the selected summary pointer; they do not overwrite historical attempt directories. Preserve failed receipts and logs as failures when investigating or recovering.

## Environment and portable evidence

Reading the reports and running `python3 scripts/cu66-v114/bundle.py --verify`
requires Python 3.10+ and the complete branch, including its frozen base files.
The Python helpers use the standard library. Building requires Linux, Docker,
and these **local** images; their hashes are identities, not registry pull URLs:

- `gamebub-cu66-v69-tools:20261105`, content ID
  `sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf`:
  Verilator 5.020, a C++17 compiler and make.
- `acorn-nexys4-ddr:2026.1`, content ID
  `sha256:dd51b5dd44148c23bb0059b929697243797022172d5efb01ffdd8b8dd7a89742`:
  the native runner also needs the external Vivado 2026.1 installation with
  `xc7a100tcsg324-1` support and a valid license. Tool binaries and license files
  are not included in this branch.

The commands below target the original host layout: build scratch space under
`/home/lori/gamebub-build/cu66-v69`, Vivado under
`/home/lori/acorn-nexys4-ddr/tools/2026.1/Vivado`, and the license path shown below.
These scripts are local, source-bound recipes, not a self-contained installer.
On another host, provision equivalent paths/tools or derive a new study recipe
and regenerate its source/proof/card/audit bindings. Existing receipts do not
qualify edited paths, images, tools or recipes as a new implementation.

This is a non-project RTL flow: relative source origins, exact source order,
XDCs, settings, Tcl recipes, source snapshots and reports are retained. There
is no `.xpr`, IP/BD export or generated-IP cache to preserve. Checkpoints and
external build trees remain outside Git. The optimized recovery retains its
specific executable and fixtures as evidence, but `optimized_resume.py` also
depends on its original failed build tree. For a new host campaign, run the
full `optimized_spatial.py --run` instead of that one-off recovery.

## Selected functional and syntax studies

| Study | Reproduction command | Current selected result |
| --- | --- | --- |
| Focused reserved-control proof | `python3 scripts/cu66-v114/control/prepare.py` then `python3 scripts/cu66-v114/control/qualify.py --run` | [control/results.json](../../experiments/python-gamebub-v114/control/results.json) |
| Paired scratch-prefetch proof | `python3 scripts/cu66-v114/prefetch/qualify.py --run` | [prefetch/results.json](../../experiments/python-gamebub-v114/prefetch/results.json) |
| Full primary composition and V97 transport | `python3 scripts/cu66-v114/spatial.py --run` | [spatial/results.json](../../experiments/python-gamebub-v114/spatial/results.json) |
| Python SR14 byte-cost study | `python3 scripts/cu66-v114/syntax/run.py --run` | [syntax/results.json](../../experiments/python-gamebub-v114/syntax/results.json) |
| Native SR14 packetizer parity | `python3 scripts/cu66-v114/syntax/run_native.py --run` | [syntax-native/results.json](../../experiments/python-gamebub-v114/syntax-native/results.json) |

The spatial command is the full canonical plus actual custom-transport campaign; `spatial.py` without `--run` only prepares/verifies its reversible adapter. The control preparation step writes the reversible top edit recipe before running the focused proof. Prefetch verifies its reversible recipe and adapters before it starts the paired run. Syntax and native-syntax `--run` commands execute CPU-bound container studies; the native syntax result validates C++/Python container and chunk byte parity, not image pixels or a full published parent.

Historical attempts remain under each study’s `attempts/` directory. Preserve a failed receipt as failed: the first V114 spatial attempt used the original immediate-diagnostics bench assumption and is followed by a recorded, reversibly adapted API retry; the early Python syntax attempt passed component work but failed host-side summary publication, and only the later exit-0 selected result is PASS. Recovery means a new pinned attempt, not rewriting an earlier status.

## Bounded native timing flow

Native timing is a separate, gated Root-owned dispatch. First prepare one allowed clock point after the required selected functional proof is PASS:

```sh
python3 scripts/cu66-v114/native.py --trial spatial-100
# or: python3 scripts/cu66-v114/native.py --trial spatial-125
```

Preparation prints the `PREPARED_NOT_RUN` card path. Save that exact path in `PREFLIGHT` and choose a new `AUDIT` path for the independent reviewer’s output; the values below are placeholders. An independent reviewer must inspect the exact card, source snapshots, recipes/tooling, functional evidence, clock/XDC, image, resource budget, unchanged constraints, and no-hardware/no-bitstream conditions, then write an audit JSON bound to that card SHA, policy SHA, and current native driver SHA. It must include a named auditor and all eight required checks. There is no command that substitutes for this independent review.

Only Root dispatches after that review and its heavy-job grant:

```sh
PREFLIGHT="<exact path printed by preparation>"
AUDIT="<path for independent reviewer JSON>"
python3 scripts/cu66-v114/native.py --run \
  --preflight "$PREFLIGHT" \
  --audit "$AUDIT" \
  --license-file /home/lori/acorn-nexys4-ddr/cache/vivado.lic
```

`PREFLIGHT` is the exact path printed by preparation; `AUDIT` is the independently reviewed audit JSON. Use `scripts/cu66-v114/native_optimized.py` only for the separately qualified optimized composition, with its own selected functional proofs and policy-bound audit. Do not dispatch from a copied/stale card or reuse an audit after source, driver, policy, clock, recipe, or proof changes. The driver enforces the prepared-card and audit pins, timing controls, source composition, shared budget, image, resources, license-file existence, and launch gates.

## Resource and claim boundaries

Get a Root heavy-job grant before starting a `--run` command. Root coordinates at most two heavy jobs globally, including simulation and native jobs. Each job is limited to two CPUs and Docker `--memory=8g --memory-swap=8g`: an 8 GiB combined memory-plus-swap ceiling, with no additional container swap. Respect the scripts' per-command watchdogs and host available-memory/PSI gates; do not start concurrent launchers independently.

That scheduler covers this study's workers. An independent Acorn simulation
became active outside it during the native runs; the
[host concurrency note](../../experiments/python-gamebub-v114/host-concurrency-note.json)
records that observation. Host pressure gates remained active, and no unrelated
job was stopped. Host wall time is not a calibrated target CPU-time measurement.

No command here programs hardware or creates a bitstream. The roadmap's canvas is 720×480; it is not a 720p claim. These component, focused RTL, packet-transport, and byte-parity results do not establish an integrated CS88/SR14 full-parent pipeline, C2/HUD/pixel publication, QSPI/ESP32/Sunshine integration, hardware frame rate, or validated full decode below 10 ms. The 30 displayed frames/s, 49,152-byte parent cap, and strict under-1,250,000-cycle target at 125 MHz remain system goals, not results of these studies.
