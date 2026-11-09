# V115 refined source preflight

Static and hash checks pass for the selected refined ingress and scratch focus receipts. At audit time the full refined spatial and control-peer attempts were in progress, so this audit leaves runtime qualification **pending**. The machine-readable audit records the source and artifact pins in [refined-source-preflight.json](../../experiments/python-gamebub-v115/audit/refined-source-preflight.json). Later runtime results appear in [selected status](status.md).

## Selected focused receipts

- Refined ingress selects `experiments/python-gamebub-v115/refined/ingress/attempts/20261109T020712236590Z/receipt.json` (SHA-256 `09a8b9ae…`). Its 25 frozen input sources and 34 listed artifacts rehash. It ran actual Verilator RTL with assertions retained, no warning downgrade, and reports two passing ingress seeds plus parser checks. The refined ingress source is `fpga/experiments/cu66-v115-refined-ingress/br88_packet_ingress_sync_v91h.sv` (SHA-256 `93b965d5…`); the parser alias remains pinned to `fpga/experiments/cu66-v115-ingress/br88_rice_elastic.sv`.
- Refined scratch selects `experiments/python-gamebub-v115/refined/scratch/attempts/20261109T021637391746Z/receipt.json` (SHA-256 `24872d24…`). Its 36 frozen input sources and 47 listed artifacts rehash. Both selected seeds pass with all 128 raw tile words compared and no new public cycles. Its refined scratch source is `fpga/experiments/cu66-v115-refined-scratch/packed_scratch_v91g2.sv` (SHA-256 `2b9dbaf7…`).
- The unchanged initial inverse selector remains PASS. Its current `results.json` SHA matches the proof pin in both initial V115 native receipts.

## Refined composition and source identity

The refined policy and `spatial_refined.py` agree on five candidate aliases: dequant, IDCT, ingress parser, synchronous packet ingress, and packed scratch. The running spatial and peer attempts each contain the same 18 ordered source-origin aliases, with every archived copy matching the expected source SHA and each other. The peer runner calls the refined spatial preparation routine, so it uses the same source composition. Its selected V115 peer testbench also matches the frozen initial peer receipt and the active peer source snapshot.

The spatial runner derives from the frozen runner with reverse verification. It retains the V113 benchmark file unchanged, including all 144 `need()` checks, and records the original functional oracles as retained. Its source specifies separate fresh component and transport-model compiles, strict assertions and warnings, no `-Wno-fatal`, finite memory/CPU/time bounds, and the 44-profile / 42-directed-check requirement. These are source-contract findings; they do not establish that the active spatial or peer runs completed successfully.

## Native flow and budget pins

`native_refined.py` differs from the initial native driver only in `AREA` and `FLOW`. The refined policy retains the same global budget SHA and the 10 ns / 8 ns target periods. The refined flow keeps the initial run script and both clock XDCs byte-identical; its report script adds only the eight requested register-name globs for local-predicate reporting. No new timing constraints or implementation directives were added.

The current active attempts have raw simulation output, but no current selectors at `refined/spatial/results.json` or `refined/control-peer/results.json`. Their final receipts and source/artifact pins must be audited after those selectors appear.
