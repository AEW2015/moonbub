# Reproduce V126

Use an isolated checkout when retaining published selectors. Requirements are
Linux, Python 3.10+, Git, Docker, the pinned simulation image and the existing
Vivado 2026.1/build6511674 tools/license configuration. Optional Python 3.14
Zstd support enables independent EDIF inventory in the terminal audit.
The standalone Verilator 5.020 flow remains the behavioral backend; this is
not a claim of Vivado-integrated Verilator support or ESP32 instruction emulation.

Reserve the resource slots and pressure thresholds from the [plan](plan.md)
before a heavy command. Keep proof-pinned files immutable once a run starts.
All selected source, fixture, runner, seed and artifact bindings matter; a
successful compiler exit alone is not a functional verdict.

## Preparation and focused checks

The preparers and default runner modes validate source/fixture derivations
without launching a heavy build. Refer to the selected producer fixture
contract and verification plan before executing them. The actual focus run is:

```bash
python3 scripts/cu66-v126/producer/qualify.py \
  --run --root-grant ROOT_V126_PRODUCER
```

Require the selected source-bound terminal PASS for scalar/generic/caller seed
pairs, strict active assertions and all original oracles. New prepared payloads
and owner bits cannot be forced. Prepared-domain extra writer/primer clocks
must be separate from unchanged natural public-cycle comparisons.

The independent Python model is a separate finite algebra/transition check:

```bash
python3 scripts/cu66-v126/producer_model.py
```

Its tested equations and transitions do not establish sequential RTL correctness,
timing, physical memory service or hardware frame rate.

## Complete functional qualification

After focused PASS, use at most two heavy study slots for the independent stages:

```bash
python3 scripts/cu66-v126/integration/peer.py --run
python3 scripts/cu66-v126/integration/spatial.py --run
```

Then execute the guarded parent and collect/audit the complete result:

```bash
python3 scripts/cu66-v126/integration/live_guard/qualify.py \
  --run --root-grant ROOT_V126_PRODUCER_PARENT
python3 scripts/cu66-v126/integration/collect_final.py
python3 scripts/cu66-v126/audit_functional_v3.py
```

The unified gate is `PASS_V126_PRODUCER_FULL_FUNCTIONAL`. All four stages must
actually execute against the same eighteen-origin composition, changing only
the producer from V125. Require exact 4/2/4 decoder/transport, peer and parent
raw stream comparisons, including the parent's complete twenty-four-file order.
Keep inherited V125 admission and earlier owner/rank/bounds/queue proofs intact.
The independent full-audit digest, exact index digest and stream counts are
direct requirements of both native launch and independent preflight audit.

The original frozen `audit_functional.py` remains with its failed transcript.
Its new summary tried to read the inherited cache-driver key `clock_edges`;
that unchanged record uses `edges`. The separately reviewed v2 changes only
that reporting lookup. Semantic checks, strict flags and RTL runs are unchanged.
The v2 full run then exposed a producer-specific four-input inventory check
misplaced inside the inherited five-input tile check. The separately reviewed
v3 moves only that check to the producer function, retaining both inventories
and every original oracle. Earlier code and failed transcripts remain recorded.
Use v3 above for the selected full evidence; v2 focused-only PASS remains valid.

## Fresh 125 MHz implementation

After the complete functional gate and independent review:

```bash
python3 scripts/cu66-v126/native.py prepare --mhz 125
python3 scripts/cu66-v126/audit_native.py PREFLIGHT_JSON --auditor REVIEWER_NAME
python3 scripts/cu66-v126/native.py run \
  --preflight PREFLIGHT_JSON --audit AUDIT_JSON --license-file LICENSE_PATH
python3 scripts/cu66-v126/audit_terminal.py --receipt RECEIPT_JSON
```

Substitute unique prepared files and the legitimate existing license path;
never include license contents in Git/logs. The unchanged V120 core recipe
loads 8 ns before fresh RTL synthesis on xc7a100tcsg324-1. Historical V120 log
markers retain their old names. Large checkpoints remain external to Git with
their hashes recorded. No prior checkpoint starts implementation, no clock is
relaxed and no guessed I/O delays or timing exceptions are added.

A global positive internal component result requires a separate fresh repeat
using `prepare --mhz 125 --repeat-of INITIAL_RECEIPT` with unchanged source,
tool and core recipe. Do not reroute an unchanged negative source. External
I/O, complete-parent timing, hardware 30 fps and silicon latency remain separate.

## Matched read-only queries

```bash
python3 scripts/cu66-v126/inspect_pipeline.py \
  --receipt V125_RECEIPT_JSON --label baseline-v125 --license-file LICENSE_PATH
python3 scripts/cu66-v126/inspect_pipeline.py \
  --receipt V126_RECEIPT_JSON --label candidate --license-file LICENSE_PATH
python3 scripts/cu66-v126/compare_observations.py \
  --baseline BASELINE_QUERY_RECEIPT --candidate CANDIDATE_QUERY_RECEIPT
```

The [recorded baseline](pipeline-inspection.md) uses the frozen V125 route.
Both observations retain old failing families and both sides of the new
producer registers, including width differences and explicit empty-path gaps.
Successful observation means report/checkpoint integrity, not timing closure.

## Final results and publication checks

After the terminal native audit, matched query comparison and finalized reports:

```bash
python3 scripts/cu66-v126/collect_results.py \
  --native-receipt experiments/python-gamebub-v126/native/20261110T152207460876Z/receipt.json
python3 scripts/cu66-v126/final_qa.py --final
```

The recorded V126 run is globally negative, so it has no repeated route. A
separate positive source trial must provide its fresh repeat receipt and audit
to the collector. Final QA checks source lineage, frozen controls, report pins,
Python syntax, local links and publication file sizes; its PASS is evidence
integrity and does not change the component's failed timing verdict.
