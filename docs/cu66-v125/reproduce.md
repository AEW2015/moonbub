# Reproduce V125

Run from the repository root in an isolated checkout when retaining published
selectors. Requirements are Linux, Python 3.10+, Git, Docker and the immutable
simulation image recorded by the receipts. Behavioral tests use the established
standalone Verilator 5.020 flow; this is not a claim of Vivado-integrated Verilator
support. Native implementation uses the pinned Vivado 2026.1/build6511674 image,
installed tools and a legitimate existing license. Optional Python 3.14 Zstd
support enables the terminal auditor's additional EDIF inventory.

Reserve at most two study heavy slots and account for known outside jobs.
Every build uses two CPUs and 8 GiB RAM/8 GiB combined RAM-plus-swap, without
additional swap allowance. Preserve available-memory/full-PSI/combined-use gates
and finite watchdogs. Never edit proof-pinned source or scripts while a run is
active; failed attempts stay in their own directories.

## Preparation and focused execution

```bash
python3 scripts/cu66-v125/tile/prepare.py
python3 scripts/cu66-v125/tile/prepare_verification.py
python3 scripts/cu66-v125/integration/prepare.py
python3 scripts/cu66-v125/integration/contract.py
python3 scripts/cu66-v125/tile/qualify.py
```

Preparation/default qualification does not compile or simulate. Check reversible
source/fixture/runner recipes, full-module versus three-fragment byte identity,
the exact eighteen-origin order and final source hashes before the heavy grant.
The fixed-source focused execution is:

```bash
python3 scripts/cu66-v125/tile/qualify.py --run --root-grant ROOT_V125_TILE
```

Require the selected terminal PASS and hash closure for scalar, generic and
actual-controller seed pairs. Generic prepared keys are not natural packet
histories: original semantic clocks, additional real-writer primer clocks and
natural packet cycles have separate ledgers. No new predicate/owner bit may be
forced, and no original assertion or oracle may be disabled to obtain PASS.

## Full functional gates

After focused PASS, reserve up to two slots for these independent stages:

```bash
python3 scripts/cu66-v125/integration/peer.py --run
python3 scripts/cu66-v125/integration/spatial.py --run
```

The spatial stage retains its serial seed policy unless a separate explicit
source-bound pair grant is used. Once both stages pass, run the parent, collector
and independent audit:

```bash
python3 scripts/cu66-v125/integration/live_guard/qualify.py \
  --run --root-grant ROOT_V125_TILE_PARENT
python3 scripts/cu66-v125/integration/collect_final.py
python3 scripts/cu66-v125/audit_functional_v2.py \
  --output experiments/python-gamebub-v125/audit/full-independent-v2.json
```

The expected unified status is `PASS_V125_TILE_FULL_FUNCTIONAL`. All candidate
stages must actually execute and remain source-bound; ten raw decoder/transport,
peer and byte/row-parent stream sets must equal V124 exactly. Historical passing
receipts remain comparison controls and do not replace fresh candidate execution.

The original frozen `audit_functional.py` is retained with its failed transcript:
it incorrectly compared the parent's complete 24-file list to the 18-file core
list. The separately derived/reviewed v2 auditor checks both the core eighteen
and each full stage's pinned V124 order, substituting only the admission path.
The parent keeps six unchanged wrapper sources. This auditor-only correction
did not change or rerun the passing RTL, fixtures, scripts or selected receipts.

## Fresh physical measurement

Only after complete functional qualification and independent audit:

```bash
python3 scripts/cu66-v125/native.py prepare --mhz 125
python3 scripts/cu66-v125/audit_native.py PREFLIGHT_JSON --auditor REVIEWER_NAME
python3 scripts/cu66-v125/native.py run \
  --preflight PREFLIGHT_JSON --audit AUDIT_JSON --license-file LICENSE_PATH
python3 scripts/cu66-v125/audit_terminal.py --receipt RECEIPT_JSON
```

Replace placeholders with the unique prepared files and your existing license
path. Keep license contents outside logs and Git. The unchanged V120 core recipe
loads 8 ns before fresh RTL synthesis on xc7a100tcsg324-1; no prior checkpoint
starts implementation, no clock is relaxed and no guessed I/O delays or timing
exceptions are introduced. Larger DCPs remain in the external build directory;
their paths, sizes and hashes are retained in receipts.

Global setup/hold/pulse/coverage/routing gates decide the internal component
result. A positive result requires a separate fresh same-source/tool/core-recipe
repeat using `prepare --mhz 125 --repeat-of INITIAL_RECEIPT`. Do not reroute a
negative source unchanged as qualification. Missing external I/O delays remain
an explicit out-of-context limit, not full-board timing.

Read-only matched observations of an existing completed route use:

```bash
python3 scripts/cu66-v125/inspect_tile.py \
  --receipt RECEIPT_JSON --label candidate --license-file LICENSE_PATH
python3 scripts/cu66-v125/compare_observations.py \
  --baseline BASELINE_QUERY_RECEIPT --candidate CANDIDATE_QUERY_RECEIPT
```

The same frozen query includes the old owner/RAW/rank/refill families and both
sides of all three new predicate registers. An empty selection/path is a gap,
not a timing pass. A successful observation is not a new implementation or
positive repeat. The [preflight comparison](tile-inspection.md) records the
separate V123/V124 baseline runs performed before candidate production edits.

The completed route exposed a producer cursor → cell-cache worst path. A
separately derived, bounded read-only query measures that family in both V124
and V125, without changing the frozen tile query or rerouting either source:

```bash
python3 scripts/cu66-v125/inspect_producer.py \
  --receipt V124_RECEIPT_JSON --label baseline-v124 --license-file LICENSE_PATH
python3 scripts/cu66-v125/inspect_producer.py \
  --receipt V125_RECEIPT_JSON --label candidate --license-file LICENSE_PATH
python3 scripts/cu66-v125/compare_producer.py \
  --baseline BASELINE_PRODUCER_QUERY_RECEIPT \
  --candidate CANDIDATE_PRODUCER_QUERY_RECEIPT
```

The [producer comparison](../../experiments/python-gamebub-v125/producer-observations.json)
retains all selected register-width differences and missing-path gaps. The
unchanged producer RTL has different mapped path delays across these two
complete physical implementations; this observation does not establish an
isolated producer RTL regression.

## Independent algebra

```bash
python3 scripts/cu66-v125/tile_model.py
```

This standard-library finite model checks full-width equations and key ownership,
including an abstract verifier parse token. It does not execute RTL or ESP32
firmware, calibrate Wi-Fi/memory service, or establish physical FPS/latency.

The optional `scripts/cu66-v125/boundary_model.py` checks a proposed owned
unit-step hidden-boundary identity. It is algebra only; no boundary-update
hardware was selected, simulated or implemented in V125.
