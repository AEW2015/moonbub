> Historical proposal snapshot before refined execution. Runtime-pending and
> no-owner-candidate statements below describe that cutoff only. The completed
> [refined route audit](native-refined.md), [final composition](final.md), and
> generated [status](status.md) supersede them.

# V115 route-driven refined five-body draft

The initial V115 native routes identify ingress-header preparation and scratch tile-write control as the next RTL cuts. The refined draft updates those two candidate bodies and keeps the other three initial V115 bodies. An owner-sequence/top-level cut is deferred: no owner-sequence path appears in either routed top-50 setup-path report, so no owner-cut RTL is emitted.

## Routed causes and selected cuts

| Trial | Routed WNS and critical path | Consequence for the next source cut |
| --- | --- | --- |
| 100 MHz, 10 ns | WNS `−0.645 ns`; `synchronous.ingress/fetch_bytes_reg[27][0]` → ingress `state_reg[0]/D`. 481 setup endpoints fail. | Refine early coherent header-length preparation in the synchronous ingress while preserving its public protocol and ownership behavior. |
| 125 MHz, 8 ns | WNS `−2.688 ns`; scratch `read_band_reg[0]/C` → `tile_reg[1][62][0]/R`. In the top 50, 30 paths end at tile `R` and 18 at tile `CE`; 33,790 setup endpoints fail. | Add one private tile-write slot with same-edge visible forwarding to cut the scratch read-band control fanout. |

Receipt and top-50 report pins: 100 MHz [`receipt.json`](../../experiments/python-gamebub-v115/native/20261109T013326592134Z/receipt.json), SHA `38e525cdc031e417bf862a59d47f943751513238999a35edce5b05b9c274343e`; [`route-setup-paths.rpt`](../../experiments/python-gamebub-v115/native/20261109T013326592134Z/reports/route-setup-paths.rpt), SHA `f18aa98e164206bc73a134e98ba731e4a2c0df91cb23688f9802bc36e11261bf`. 125 MHz [`receipt.json`](../../experiments/python-gamebub-v115/native/20261109T013313799994Z/receipt.json), SHA `79362f96a56b9d69cdd2046f6c822e71abbc3b69173575bc6e38fef011a81368`; [`route-setup-paths.rpt`](../../experiments/python-gamebub-v115/native/20261109T013313799994Z/reports/route-setup-paths.rpt), SHA `05b97fc7483aa4ecde5543bb7da14a5313ee42b8ee42b5da6e8baf24f607dc4b`. Neither report’s 50 setup paths contains an `owner_sequence` path. Both native runs are component-route evidence with signoff open; neither timing target passed.

## Refined source and proof plan

- The five candidate aliases remain dequant, IDCT, Rice parser, synchronous packet ingress, and packed scratch. The inverse pair and Rice parser reuse the initial V115 bodies. Only the ingress and scratch aliases move to new proposed bodies: `fpga/experiments/cu66-v115-refined-ingress/br88_packet_ingress_sync_v91h.sv` and `fpga/experiments/cu66-v115-refined-scratch/packed_scratch_v91g2.sv`.
- The top remains the existing CS88 component top. There is no sixth owner-top alias or owner-top candidate in this plan. The revised functional contract is IV115.3: early coherent exact 34-bit header-length preparation and one private tile-write slot with same-edge visible forwarding, while retaining initial V115 public edge/value/owner/drain behavior and the existing E/E+1 command API.
- The root-owned [`spatial_refined.py`](../../scripts/cu66-v115/spatial_refined.py) overrides exactly these five aliases, writes to `refined/spatial`, and selects the existing initial inverse proof plus `refined/ingress` and `refined/scratch` focused proofs. The refined peer proof is `refined/control-peer/results.json`. All these new source bodies and proofs remain source-dependent and unqualified.
- [`native_refined.py`](../../scripts/cu66-v115/native_refined.py), SHA-256 `9f8329af265baf20e5229d213ff8e8a3f31d8444c920304fb81a4df600b7fdb8`, differs from its initial driver copy by the refined `AREA` root and the refined flow path. [`cu66-v115-refined-flow`](../../fpga/experiments/cu66-v115-refined-flow/derivation.json) is a report-only derivative of the initial flow: `run.tcl` and both clock XDCs are byte-identical; `report.tcl` adds only the eight `NAME` globs `*tile_pending*`, `*tile_event*`, `*tile_payload*`, `*header_length*`, `*header_pair*`, `*header_total*`, `*header_expected*`, and `*header_size*` to the existing local-predicates report query. Synthesis/place/route commands, clocks, timing constraints, cell attributes, and strategy are unchanged. This adds source register survival/mapping visibility for the ingress and scratch cuts; the refined flow has not been run. The current refined policy [`study-policy.json`](../../experiments/python-gamebub-v115/refined/study-policy.json), SHA-256 `6554a7f504e551ec2dfd615d7e1594874052a7937ddd24e243aa7025ed9daabd`, retains the shared global budget, 100/125 MHz clocks, matched V114 receipts, directives, 2 CPU / 8 GiB resource bounds and no-hardware/no-bitstream rules.

The refined full spatial proof, three focused source proofs, fresh peer proof, actual negative native route and source-pinned card audit are all pending. The initial V115 PASS and its native routes are the baseline evidence only; they do not qualify either proposed source cut. No RTL, proof, card, or native result is created by this planning note.
