# Targeted methodology / CDC repair review

The separate synchronous-control prototype removes the original unit's eight critical CDC-11 findings and its capped REQP-1839/1840 BRAM asynchronous-control findings. These are actual mapped report changes, with no waiver or constraint relaxation. Whole-parent/hardware qualification remains open.

| Check | Original mapped unit | New mapped unit | Evidence / reason |
| --- | --- | --- | --- |
| CDC-11 | 8 critical | 0 | Ten dedicated DONT_TOUCH notification FDCEs survive. Each actual Q drives only its own first peer-up synchronizer D. |
| REQP-1839 / REQP-1840 | At least 20 each, report caps reached | 0 / 0 | Staged read/write enables and addresses are synchronous local state. Forty mapped RAM issue/address registers are FDRE; no asynchronous reset drives these controls. |
| CHECK-3 | 2 warning (report limits) | 0 | No masked/capped BRAM-control finding count. |
| CDC-6 | 10 warning | 10 warning | Gray bus semantics remain an explicit review requirement; all 40 bits have valid C-to-first-D source-period bounds, 10 positive-skew constraints and 100% exception coverage. |
| LUTAR-1 | 1 warning | 1 warning | Common reset-request OR still needs a clean physical source and pulse/clock contract. |
| SYNTH-4 / SYNTH-6 | 7 / 7 | 7 / 7 | Shallow 8-word BRAM and timing advisories retained. |
| TIMING-18 | 558 | 558 | 279 input and 279 output ports lack real parent delays. None fabricated. |
| CFGBVS-1 | 1 | 1 | Actual board configuration voltage unspecified in the isolated screen. |

Three-source behavioral PASS precedes native implementation; all RTL bytes stay identical through the route. The new synchronous controls reserve eight RAM slots including the write stage plus one output slot. Write Gray publication occurs only on physical RAM write; read ownership advances only on physical capture. A dedicated asynchronously cleared notification is required for a stopped peer; making that flag synchronously reset would leave stale up=1. It stays 0 during the local three-edge release hold. Its only crossing endpoint is a first synchronizer D, outside every RAM control cone.

The recipe and synthetic clock files are byte-identical to the original mapped-checked Gray/clock constraints. Actual per-bit REQUIREMENT and MaxDelay datapath-only exception checks pass at synthesis, placement and route. All 10 Gray bounds and 10 peer-up exceptions have 100% endpoint coverage; no ignored exceptions or path segmentation. The same nominal 5/10/10/16.667-ns synthetic unit clocks are not actual board relationships.

Routed result: WNS +2.078ns, WHS +0.027ns, pulse slack +2.000ns; no setup/hold/pulse violations; 568/568 routable nets, no routing errors. Resources 107 LUT / 527 FF / 3 RAMB36 / 4 RAMB18 / no DSP: +16 LUT / +331 FF over the original unit. One route screen is not a robustness demonstration. OOC HD.CLK_SRC and HD.PARTPIN_LOCS warnings leave actual clock/input/output boundary timing unqualified; no locations were invented.

Measured no-stall unit delivery is one word per two output clocks, with 6–13 equal-test-clock latency. The actual panel-clock nominal ceiling would therefore be about 14.681 million pixels/s if used as a direct pixel FIFO, below a 720×480 60-Hz active-pixel demand. This is a targeted reset/BRAM-control repair, not a selected streaming optimization or complete LCD integration.

No warning is waived. Next work is the actual parent reset/epoch/clock contract and line-bank/full-burst service architecture, preserving memory/LCD timing and measuring whole-system cost. Raw reset distribution, glitches, physical clock stability and metastability remain device/integration obligations.
