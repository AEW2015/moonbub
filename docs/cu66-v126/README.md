# V126: producer successor pipeline

**V126 is complete as a bounded experiment; 125 MHz timing still fails.**
The producer split passes all functional checks with zero public-cycle change.
Its targeted cursor-to-cache path improves **−1.224 → +0.246 ns**, but global
WNS regresses **−1.224 → −1.867 ns**, with **10,868** failing setup endpoints.
This candidate is not promoted and was not rerouted unchanged.

| Gate | Measured result |
| --- | --- |
| Focused scalar/generic/caller | Six seed runs PASS, all inherited assertions/oracles retained |
| Full decoder/transport, peer, byte/row parent | PASS; exact 4/2/4 raw-stream comparisons against V125 |
| New address → ROM-result / result → cache | +0.256 / +4.802 ns |
| New address-stage enable | −0.086 ns; local control still fails |
| Global 125 MHz | WNS −1.867 ns; TNS −4,427.979 ns; 10,868 setup failures |
| Hold / pulse / routing / internal coverage | PASS; zero failing hold/pulse, routing errors or unconstrained internal endpoints |
| Routed area change from V125 | +322 LUT, +110 FF; BRAM/DSP and 1,252 control sets unchanged |
| Whole-parent 125 MHz / hardware 30 fps / hardware <10 ms | Open |

See [functional results](functional-results.md), [routed timing and all selected
families](timing-results.md), the [machine-readable result](../../experiments/python-gamebub-v126/results.json)
and the [next timing proposal](next-timing.md). The independent native audit’s
PASS means evidence integrity; it separately records `design_timing_pass=false`.

## Implemented cut

V126 changes only the producer alias relative to the frozen V125 eighteen-file
composition. It adds a 13-bit prepared successor address and an 11-bit prepared
cell result. It uses existing writer and MAP_REQ edges, preserving the original
current-cell cache and public-cycle contract.

```mermaid
flowchart LR
    T[Old tile value before advance] -->|"wrapped t+2 on original writer"| A[Prepared successor address FF]
    A --> R[Original quant_cell ROM]
    R -->|"existing MAP_REQ edge"| C[Prepared successor cell FF]
    C -->|"original skip or nonterminal dispatch edge"| K[Original current-cell cache]
```

PREP establishes tile0/current-cell0 and successor-address1. On a tile advance,
the old t+2 address is the successor of the newly current t+1 tile. MAP_REQ
captures its ROM value; mode2 maps the old current cell while preserving the
successor through stalls. A nonterminal completion copies the staged result
on its original edge. NEXT_PLANE retains its direct current-cell recompute,
including empty planes. Full 13-bit wrap, all four plane encodings, full owner
keys, accepted/rejected start, first-error and physical-debt contracts remain.

Production source SHA is
`5dec7454e6bfae4f7a9d7f64ecfbef8568665ddaa2dc00d4a76de1167a3c7292`.
Twenty-four added logical payload bits do not imply exactly twenty-four physical
FFs after optimization/replication. Verification-only owners are not intended
to exist in the mapped hardware. No public port, wire syntax, quality, synthesis attribute,
placement directive or clock-constraint change is part of this RTL experiment.

See the frozen [design](producer-design.md), [verification plan](verification-plan.md),
[experiment plan](plan.md) and [focused results](focused-results.md). The
[independent Python model](producer-model.md) checks geometry equations and
finite transitions; its scope is separate from sequential RTL and silicon.

## Evidence chain

The fresh official focused run passes all scalar/generic/caller seed pairs.
The [focused report](focused-results.md) retains source/artifact hashes, actual
writer/primer counts, full-width and wrap cases, old canonical/debt oracles,
earliest responses, held ownership and the diagnostic/repair history. All
production RTL remained unchanged throughout the runner and test-fixture fixes.

Complete decoder/actual V97 transport, peer and byte/row-parent runs also pass
the separate full functional gate with exact canonical/event/terminal streams.
Fresh internal component implementation uses the unchanged V120 recipe, Vivado 2026.1/build6511674 and xc7a100tcsg324-1
with 8 ns loaded before synthesis. The retained reports cover global setup,
hold and pulse, internal clock coverage, routing, methodology and both new
register boundaries.
A positive route requires its own fresh identical-source/tool/recipe repeat.
An unchanged negative source is not rerouted to seek a favorable result.

The [read-only baseline](pipeline-inspection.md) captures V125 with the same
expanded query. A shorter old endpoint alone is insufficient: the prepared
address and cell D/CE/Q paths, scratch return, admission coordinates, RAW and
queue families all remain in the comparison. Missing paths or register names
remain explicit gaps. The [independent query review](../../experiments/python-gamebub-v126/audit/candidate-query-review.json)
passes all 25 checks while retaining the negative clock qualification.

## Remaining product gates

Qualified [V120 B100](../cu66-v120/handoff.md) and its eighteen original files
remain the control for independent remote board work. This study does not
create a qualified board bitstream or perform board programming.

Retained row fixture counts are 1,145,104 / 1,553,197 cycles from final accepted
outer input to validated commit. At an assumed complete-parent 125 MHz, that
is 9.160832 / 12.425576 ms; the stalled profile needs at least 303,198 fewer
cycles for strictly below 10 ms. The byte control is slower and is reported
separately. These abstract fixtures do not establish full-parent clocks,
physical SDRAM service, calibrated ESP32 Wi-Fi/QSPI/CPU behavior, distinct
displayed 30 fps or validated hardware <10 ms.

The [V126–V130 plan](../gamebub-v126-v130-timing-streaming-plan.md) carries those
gates forward, including cycle reduction, actual custom endpoint negotiation,
complete-parent constraints and the remote frame-rate/latency campaign. The
[next timing proposal](next-timing.md) is grounded in the actual
V126 routed families. [Reproduction instructions](reproduce.md) retain the
strict backend, finite watchdog, two-job resource and source-freeze policies.
