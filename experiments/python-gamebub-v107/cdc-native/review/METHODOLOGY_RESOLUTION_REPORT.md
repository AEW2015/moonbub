# Methodology and CDC review

The routed isolated v107_cdc_fabric completes its explicit synthetic unit timing constraints (WNS +2.025 ns, WHS +0.097 ns, pulse-width slack +2.000 ns), but CDC, reset and parent interface signoff remain open. No waiver is created.

| Finding | Actual cause / evidence | Disposition |
| --- | --- | --- |
| CDC-11 (8 critical) | Equivalent source-domain up registers merge in synthesis. One startup flag drives multiple independent synchronizer chains in a destination clock. RTL sets each up flag to 1 after local reset, and channel ready/fetch gates remain separate. | Scoped startup-fanout review only; parent owner/reconvergence and reset distribution unqualified. Future architectural sharing or preserved channel-local logic requires behavioral/native revalidation. |
| CDC-6 (10 warning) | Multi-bit Gray pointer synchronizers. All40 bits have launch-period max-delay bounds and10 bus-skew constraints with positive routed slack. | Physical bounds verified; no formal CDC/metastability/primitive proof. |
| LUTAR-1 (1 warning) | v107_cdc_fabric coordinated_reset OR of4 external request bits drives asynchronous reset-release chains. | Clean glitch-free reset source assumption remains; do not waive or infer real board reset generation. |
| SYNTH-4/6 (7 each) | Explicit shallow8-word dual-clock block RAM, seven mapped primitives. | Resource/timing advisory retained; no LUTRAM replacement or collision claim. |
| TIMING-18 (558) | Synthetic unit has279 input and279 output delay omissions. No real parent budget exists here. | Follow TIMING-18 guidance by retaining missing requirements; no fabricated delays or blanket false paths. |
| REQP-1839/1840 (at least20 each) | Async-reset pointer/control flops feed BRAM address/enable pins. Default static timing does not qualify reset assertion effects. | Requires technology reset/enable/address proof or new implementation; report counts capped (CHECK-3). |
| CFGBVS-1 | Unit has no actual board configuration voltage. | Parent board contract required. |

The initial source-name-only template misses a synthesized Gray MSB alias. A separate actual-driver template then incorrectly uses Q pins as constraint startpoints; Vivado reports path segmentation and invalid false-path startpoints. Both receipts are retained unchanged. The corrected candidate derives the actual sequential driver from each exact first-stage D net, validates its source/bit/clock, and uses that sequential C pin as the timing startpoint. This retains C->Q arcs; each40bit path's requirement and explicit MaxDelay datapath-only exception is checked at synth/place/route. Ten Gray bounds and ten single-bit first-stage false paths show100% source/destination coverage, with zero ignored exceptions. No clock group or reset cut is introduced.

The methodology warning counts in the completed unit are573; no completed pre-repair methodology baseline exists because earlier attempts stopped during constraint application. Those warnings are not reclassified as resolved by the corrected constraint syntax. No RTL changes occur after behavioral PASS. The raw asynchronous reset input remains unconstrained by a real external source, while local synchronized-release recovery/removal paths remain timed.

Original constraints: fpga/experiments/cu66-v107-cdc/constraints.tcl (rejected historical template). Working separate constraints: fpga/experiments/cu66-v107-cdc-flow/mapped-checked/constraints.tcl. Synthetic clocks: fpga/experiments/cu66-v107-cdc-flow/mapped-checked/unit-clocks.xdc. Full evidence and independent audit: experiments/python-gamebub-v107/cdc-native/native-audit.json. Full parent integration obligations: docs/cu66-v107/cdc.md.
