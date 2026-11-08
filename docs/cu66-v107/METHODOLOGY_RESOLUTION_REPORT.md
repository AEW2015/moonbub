# V107 methodology resolution report

Design: `cs88_pipeline_v91k`, component out-of-context on `xc7a100tcsg324-1`.
Tool: Vivado 2026.1 build 6511674. Selected measured frontier: `threshold-runtime`.

The unchanged comparison clock is **10.000 ns / 100 MHz**. Routed WNS is
**-2.333 ns** with **21,433 failing setup endpoints**.
Hold slack is +0.096 ns and pulse-width slack +3.750 ns.
The decoder timing target is NOT MET.
The evidence audit verifies reports; it does not waive negative slack.

## Native reports and constraints

The [selected receipt](../../experiments/python-gamebub-v107/native/20261108T081254078678Z/receipt.json) and
[comparison](vendor-comparison.md) bind read-only source snapshots, input map,
Tcl/XDC, exact tool command, logs, stage reports and final checkpoint hash.
The native source list and 10 ns constraint load before synthesis. There are
no valid decoder timing exceptions. Board input/output delays remain open
because the component comparison has no external board timing contract.
No clock, path or endpoint was excluded to manufacture a timing pass.

Report commands include `check_timing`, `report_timing_summary -delay_type
min_max -report_unconstrained`, setup/hold paths, `report_clocks`, clock
interaction, exceptions, CDC, DRC, methodology JSON/text, routing status,
utilization, memory primitive configuration and high-fanout/control sets.
Both slow and fast timing corners are enabled in the timing summary.

## Findings and disposition

| Finding | Disposition |
| --- | --- |
| Setup timing / TIMING-16 where reported | OPEN. Exact RTL rewrites, tuple staging and mapped table changes target actual reported cones. Negative setup remains unresolved. |
| TIMING-18: missing input/output delay | OPEN parent integration requirement. No guessed board delay or waiver was added to the OOC decoder. |
| SYNTH-5: distributed RAM mapping | Inspect actual inferred primitives, fanout and route delay. The table candidates use actual mapped/UNISIM checks; this advisory is not automatically waived. |
| SYNTH-6: potentially suboptimal RAM timing | OPEN where retained; inspect actual RAM read/write/output registers and collision behavior before changing structure. |
| DSP DPIP/DPOP advisories | OPEN where retained. IDCT/dequant remain exact. A pipeline change needs full tuple, cancellation and canonical qualification. |
| CFGBVS | OPEN board-level electrical configuration. The OOC component has no board configuration-voltage contract. |
| OOC HD.CLK_SRC/PARTPIN or routing advisories | Retained as reported; no invented clock location or board constraint was supplied. Complete routable-net status is independently checked. |
| Single-clock decoder CDC report | Applies only to this component. It cannot establish production board CDC/reset signoff. |

Actual selected route rule counts:

### methodology

- `SYNTH-6`: Warning, 39 reported.
- `TIMING-16`: Warning, 1000 reported.
- `TIMING-18`: Warning, 1000 reported.

### drc

- `CFGBVS-1`: Warning, 1 reported.
- `DPIP-1`: Warning, 40 reported.
- `DPOP-1`: Warning, 12 reported.
- `DPOP-2`: Warning, 16 reported.
- `RTSTAT-10`: Warning, 1 reported.

## Separate CDC repair and remaining integration

The isolated reset-safe CDC experiment routes with WNS +2.078 ns, hold +0.027 ns
and pulse +2.000 ns. Per-FIFO synchronizer notification and synchronous local
RAM address/control reset remove the observed CDC-11 fanout hazards and
REQP-1839/1840 asynchronous RAM-control findings. Its actual Gray crossings use
bounded datapath and bus-skew constraints, without blanket clock groups that
would override those bounds. Remaining generic Gray CDC-6 warnings and the
reset-combination finding require parent review; this is not metastability or
board signoff. See [CDC source/rate and native evidence](cdc-sync.md).

The production parent still uses legacy JPEG. CU66 transport/reference/memory,
publication, LCD buffering and real interface contracts are not implemented
in the new experimental fabric. The pixel FIFO repair delivers only 0.5 word
per receiving clock; it is not a sufficient direct native-scanout replacement.
Preserve the existing related DDR capture clock and qualify actual clocks,
reset recovery/removal, external delays and electrical configuration at parent
integration.

## Resolution boundary and next work

The selected decoder source is a measured implementation frontier. A clean
repeat, full parent fit, real clock/interface qualification, sustained hardware
30 fps and complete validated decoding below 10 ms remain open. No Fmax is
inferred from a negative or single routed slack. Follow the measured remaining
cones rather than adding timing exceptions or launching an unbounded strategy
sweep.

Source receipt SHA-256: `8a24372a70162d2968e255f2c0175e15d4bed9d86e7e5578f7cc84e1a38acd47`.
