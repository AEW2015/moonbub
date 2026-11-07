# V104: cached geometry and DSP product-register prefetch

V104 starts from published V103 commit
`1d0a702a758787522723ac52ff44a1bf220c39d1` and its selected **V102** RTL.
Discarded V103 arithmetic rewrites are not promoted. The CS88/all-BR88 q16
profile, 720×480 coded video, 49,152-byte packet cap, ports, diagnostics and
intended public cycle schedule remain frozen.

## Candidate contracts and focused results

The [control candidate](../../fpga/experiments/cu66-v104-control/cu66_reconstruct_stream_v91k.sv)
caches the expected quantization-cell index. Y column/row-parity recurrence
advances only on the accepted last output byte; plane transitions and
reset/start/cancel initialize it alongside the original tile state. The cache
drives lookup and residual validation. Existing owner/error/metadata guards
remain intact; the original geometry function remains a non-synthesis oracle.
This is a reachable, post-reset state invariant, rather than a replacement
for an externally driven arbitrary-domain function.

The [clocked control test](control-results.md) passes **2,445,067 clock edges**,
**7,335,201 low/high/low public comparisons**, two complete 8,100-tile frames
and 51 directed checks. Its independent Python replay verifies coordinate
advances, holds, resets and event ownership. A seven-edit source reconstruction
ledger limits the source changes. These checks are not machine-checked formal
equivalence of every possible history or four-state behavior.

The [DSP candidate](../../fpga/experiments/cu66-v104-dsp/cu66_dequant.sv)
prefetches group-zero products on the accepted input edge, then computes each
next group while the current group commits on its original MULTIPLY edge.
The product register can map into a DSP48E1 pipeline. Coefficient/product
widths, rounding, error/zero fast paths, held output and every partial packed
output cycle are preserved by the tested contract; no extra interface cycle
is introduced.

The [clocked dequantizer test](dsp-results.md) passes **579,794 clock edges**
under two seeds and **111,320,320 packed-element comparisons**, including
exhaustive legal coefficient values in six quantizer configurations, invalid
inputs, input noise, backpressure, resets and aborts. Independent Python
replay checks every retained row. Earlier host-pressure launch stops and one
strict testbench-formatting compile failure are retained and classified;
no RTL change or warning downgrade was used to bypass them.

The [baseline audit](baseline-audit.md) pins the selected source and actual
primitive configuration: eight dequantizer DSPs have AREG/BREG/MREG/PREG all
zero, while the IDCT already uses fifteen MREGs and one PREG. Native ledgers,
not the RTL declaration or a synthesis log sentence, decide whether new
register absorption occurs. Register use alone does not establish a timing,
power or frame-rate gain.

The separate [admission-coordinate model](admission-coordinate-model.md)
passes **137,343 bounded tile/delta transitions**, including all permitted
0–16 advances, holds, row crossings and end-only sentinels. It also checks
proposed epoch/owner invalidation rules. This is conditional coordinate math,
not a proof of actual admission-state reachability, RTL or timing. Admission's
existing 32-bit state/function is unchanged; its documented header-entry and
abort/drain obligations still precede an RTL recurrence implementation.

## Matched implementation and selection

The [vendor comparison](vendor-comparison.md) records actual synthesis and
routed stages, DSP48E1 register absorption, resource headroom and critical
paths. The [checkpoint JSON](../../experiments/python-gamebub-v104/summary.json)
binds selected functional/native receipts and qualification gates; the
[source selection](../../experiments/python-gamebub-v104/selection.json)
records the next-study source choice. The [source audit](audit.md) and native
audit verify provenance, strict terminal outcomes and retained artifacts.
Evidence-audit PASS does not mean timing or hardware signoff.

| Routed component | LUTs | DSPs | Dequantizer PREGs enabled | Setup WNS at 10 ns |
| --- | ---: | ---: | ---: | ---: |
| V102 selected control | 48,522 | 28 | 0/8 | −13.976 ns |
| V104 cached control only | 47,588 | 28 | 0/8 | −14.750 ns |
| V104 combined control + prefetch | 48,868 | 29 | 8/8 | −13.978 ns |

Both V104 implementations route with zero routing errors: all 71,894
control-only routable nets and all 73,363 combined routable nets are routed.
Hold slack is +0.067 ns and +0.098 ns respectively. Cached control saves
934 LUTs but its setup slack is worse. Combined preserves all eight local
PREGs through routing, costs 346 additional LUTs and one additional global
DSP, and has essentially the same worst setup slack as V102. The reported
2-ps difference is a single-run result, not a statistically established
regression or improvement. Global IDCT mapping accounts for the additional
DSP; dequantization itself still uses eight.

The [recorded selection](../../experiments/python-gamebub-v104/selection.json)
**retains V102** because neither new implementation demonstrates the required
strict routed setup-slack gain. The new variants remain isolated, bit-true
research options. All three native attempts completed successfully; no V104
build remains running. None closes the 100-MHz comparison timing target.
The remaining worst paths are in admission indexing, so the conditional
coordinate model needs an actual owner-safe state/RTL proof next.

The next matched matrix should test admission recurrence alone, with V104's
verified reconstruction cache, and with both cache/product prefetch. Retaining
V102 as the control does not discard these building blocks: removing one
geometry cone can leave the other as the worst path. Their joint effect still
needs actual RTL and native timing measurements.

All native comparisons use Vivado 2026.1 build 6511674,
`xc7a100tcsg324-1`, the same 10-ns clock loaded before synthesis, Default
directives, two threads and unchanged public diagnostic visibility. V104
pipeline state may increase area: selection requires a physically fitting,
error-free route, nonnegative hold/pulse slack, exact workload-cycle parity and
strictly better setup WNS than selected V102. Prefer best WNS, then lower
resources; otherwise retain V102. Report resource increases explicitly.
This next-study choice is not production or hardware promotion.

Parent clock-buffer location, component boundary locations and genuine
external I/O timing remain unknown. Native warnings, methodology findings and
incomplete full HUD/C2/frame-seal/shared-memory/display/ESP32 integration stay
open; no invented pins/delays, timing waivers or false paths hide them.
No achieved Fmax follows from an abstract OOC clock or negative setup slack.

## Reproduction

```sh
python3 scripts/cu66-v104/control.py
python3 scripts/cu66-v104/dsp.py
python3 scripts/cu66-v104/regress.py --variant control --mode canonical
python3 scripts/cu66-v104/regress.py --variant dsp --mode fresh
python3 scripts/cu66-v104/regress.py --variant dsp --mode canonical
python3 scripts/cu66-v104/regress.py --variant combined --mode canonical
python3 scripts/cu66-v104/build.py --variant dsp --synth-only --run
python3 scripts/cu66-v104/build.py --variant control --run
python3 scripts/cu66-v104/build.py --variant combined --run
python3 scripts/cu66-v104/audit_sources.py
python3 scripts/cu66-v104/audit_native.py
python3 scripts/cu66-v104/summarize.py
python3 scripts/cu66-v104/bundle_manifest.py --verify
```

Commands create fresh attempts. Both baseline and candidate compilations
start from V102's selected memory/predicate sources; only named V104 sources
are substituted for candidate runs. Reconstruction is absent from the fresh
V91j closure, so combined fresh has the same changed closure as DSP fresh.
Historical Verilator 5.020/GCC 13.3 strict checkers remain in use. Vivado MCP
returned `Transport closed`; the source-pinned native batch runtime uses the
existing installed tools and legitimate license read-only. Executables and
checkpoints remain in external build directories; hashes/reports are retained.

Launch heavy jobs only with at least 8 GiB available RAM and memory PSI full
avg10 below 1, with at most two heavy jobs. Native containers have an 8-GiB hard
limit, no extra swap, two CPUs/threads and finite watchdogs; the shared
Verilator container keeps its existing 4-GiB limit. Stale swap occupancy alone
is not the gate. Do not remove stopped attempts or relax checks to manufacture
a pass.

Sustained hardware 30 fps and complete validated decoding below 10 ms remain
open. Cycle-preserving experiments do not reduce the existing fresh-key
1,386,271 component cycles: even at a qualified 100 MHz that would exceed
10 ms before missing whole-path work. No board is programmed in this study.
