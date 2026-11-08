# V113 terminal 100-MHz component audit

The fresh RTL route completed with exit zero, but **fails the 100-MHz internal
setup gate**: WNS **−1.686 ns**, TNS **−3,190.694 ns**, **8,220 failing setup
endpoints**. This is a negative terminal result. No failed-clock repeat is
permitted by the positive-only repeat policy. No 125-MHz result is inferred.

The [terminal receipt](../../experiments/python-gamebub-v113/native/20261108T213634749593Z/receipt.json)
is SHA-256
`5c4cebfc6c444d50ef404e6252adbe8560554af59f271a2f55fc7f2087e06023`.
The [independent audit](../../experiments/python-gamebub-v113/audit/spatial-100-final.json)
passes evidence validation while explicitly recording timing failure. All 97
retained artifacts, 72 external build artifacts, 18 source snapshots/origins,
prepared recipes, tooling and proof pins match. No build, source change,
Vivado/MCP execution or hardware action was performed by this reviewer.

The native parser and independent raw checks agree on the exact receipt
result. The route marker, actual synthesis command, tool settings and bound
fresh-RTL recipe agree: `xc7a100tcsg324-1`, Vivado 2026.1 build 6511674,
Default synthesis by omission, Default opt/route and ExtraNetDelay_high
placement, two CPUs/threads, 8 GiB RAM and an equal RAM-plus-swap ceiling.
No explicit separate physical-optimization stage was selected; Vivado's
internal placement Physopt messages do not constitute an added strategy sweep.
There was no checkpoint start, retiming, bitstream or hardware programming.

## Actual clock and constraints

The actual routed clock is `component_clk`, **10.000 ns**, waveform **0/5 ns**.
The clock-before-synthesis recipe and settings are bound; before/after
effective XDCs contain only that clock plus `current_instance -quiet`.
The exceptions report finds no valid timing exceptions. No guessed I/O delays
were supplied. There are zero unclocked or unconstrained internal endpoints,
loops, latch loops or multiple-clock checks.

Hold WNS is **+0.071 ns**, pulse-width slack **+3.750 ns**, with zero hold or
pulse failures. All **68,602 routable nets** are fully routed with **zero
routing errors**. Successful routing and clean hold/pulse do not erase setup
failure.

The OOC interface still has **1,101 missing input delays** and **12,887 missing
output delays**. Methodology reports **1,000 TIMING-18 checks** for missing I/O
requirements. These are external-interface gaps, not waived internal setup
paths or board timing qualification. The single-clock CDC report says all
paths safely timed; it does not qualify the complete parent's physical CDC.

## Routed critical family and next priority

The [worst raw setup path](../../experiments/python-gamebub-v113/native/20261108T213634749593Z/reports/route-setup-paths.rpt)
is `transform/fault_pending_o_reg/C` →
`coefficients/child/packet_decoder/synchronous.ingress/fetch_index_reg[2]/CE`:
**12 logic levels**, **11.433 ns** total, **1.944 ns logic** and **9.489 ns
routed interconnect (82.996%)**. The raw report SHA-256 is
`5e2f3dead5db97e51de5c273abaffdcc4b146d359ba9a1a4a8f7466f598d99cb`.

Of the 50 retained worst paths, **45** start at this fault register, with
slacks from −1.686 to −1.210 ns. Their endpoint families are:

| Fault-source destination family | Reported paths |
| --- | ---: |
| Ingress fetch-base CE | 18 |
| Prepared request address / bounds CE | 9 |
| Fetch-index CE / buffer-byte CE | 6 / 6 |
| Fetch-count CE / return CE | 3 / 1 |
| Admission scale-memory write / packet-memory enable | 1 / 1 |

The remaining five paths include fetch-kind to prepared bounds, fetch-byte to
ingress state, raw-mode to scratch state and two lengths-to-sizes enables.
This is a top-50 sample, not a full classification of 8,220 endpoints.

The **first fault-pending net has fanout one** and 0.403-ns routed delay.
Blind MAX_FANOUT constraints or duplicating that register are not supported by
this evidence. The long cone traverses base abort/readiness, accepted-start
qualification, local running/refill/queue eligibility, ingress input and fetch
continuation logic. Inspect each segment and physical locality. Mapped names
in the report are not newly invented RTL owners.

Separate broad nets remain: scratch clear **7,141** loads, scratch reset
**2,359**, coefficient fault-pending distribution **2,230**, and IDCT-related
enables **1,538/1,537/1,536**. Their presence is not proof that duplicating the
worst-path source fixes the path. The global control-chain/ingress ownership
cut and locality assessment take priority over the historical prefetch cone.

The next safe architectural study is reserved admission credits, coherent
registered commands, and tagged local kill/flush ownership. Preserve immediate
public revocation on both valid and returned ready; keep accepted physical
scratch/reference requests until matching completion. A delayed abort that
admits an extra transfer, sampled readiness without reservation, or private
flush treated as physical drain is unsafe. The full production PCTL1
supervisor/session protocol is **not implemented** by V113. This requires a
new contract, independent event oracle and actual measurements, not a source
edit during the frozen trial. The [prefetch/continuation proposal](next-scratch-cut.md)
now explicitly ranks its synthesis-only cone as secondary.

## Resources and actual primitive mapping

| Routed component | LUTs | Registers | RAMB36 / RAMB18 | DSPs |
| --- | ---: | ---: | ---: | ---: |
| V113 100-MHz top | 36,367 | 39,212 | 32 / 12 | 42 |
| Coefficient/context path | 20,218 | 21,472 | 32 / 12 | 17 |
| Context decoder | 1,991 | 678 | 0 / 10 | 1 |
| Scratch | 4,656 | 3,731 | 0 / 0 | 0 |
| Transform | 11,561 | 13,835 | 0 / 0 | 25 |

The part has 63,400 LUTs, 126,800 registers, 135 block-RAM tiles and 240 DSPs.
This component occupies **14,473/15,850 slices (91.31%)**, 38 RAM tiles and
1,169 control sets. LUT percentage alone does not express placement headroom.
The primitive table includes 39,037 FDRE, 173 FDSE, two FDCE, 5,145 CARRY4,
42 DSP48E1 and the stated RAM primitives. Hierarchical LUT sums may differ
because of cross-hierarchy combining.

The actual DSP table records eight dequant DSPs with AREG/BREG=1, MREG/PREG=0;
17 IDCT DSPs have AREG/BREG/MREG=1 and PREG=0. All 25 transform DSP PREGs are
disabled. The remaining 17 shared DSPs include 15 with PREG enabled and two
disabled. DRC reports **6 DPIP-1**, **27 DPOP-1**, **14 DPOP-2**, one CFGBVS-1
and one RTSTAT-10 check. These are real mapping opportunities/gaps, but no DSP
lies on the measured primary fault-to-ingress path; changing DSP registers
requires its own latency/owner proof and does not establish a fix here.

All **44 block-RAM primitives** have DOA_REG/DOB_REG=0. The 32 RAMB36s are TDP
with A/B read widths 1/1; the RAMB18s comprise eight at 18/0, two at 18/18,
one at 2/2 and one at 9/9. These primitive widths are physical mappings, not
new logical ports available to compute lanes. Methodology's **28 SYNTH-6**
checks record nonmerged RAM output registers. It also reports **248 TIMING-16**
large setup checks, which are real internal failures. The JSON and text
methodology summaries agree. RTSTAT-10/loadless-net observations are distinct
from zero routing errors and are not routed-net failures.

## Same-clock retained controls

Only actual **10-ns** controls are compared, both reused rather than rerun:

| Source | WNS ns | TNS ns | Setup failures |
| --- | ---: | ---: | ---: |
| Count100 | −1.022 | −1,125.069 | 4,620 |
| V112100 | −1.034 | −2,028.748 | 5,607 |
| V113100, fresh | −1.686 | −3,190.694 | 8,220 |

V113 WNS worsens by **0.664 ns versus Count** and **0.652 ns versus V112**;
setup failures increase by **3,600** and **2,613**, respectively. These are
source-bound OOC observations, not statistical route-quality estimates or an
isolated causal attribution to one of the three edits. This run supplies no
clock promotion, complete-parent/I/O/memory/panel qualification, sustained
hardware 30 fps or complete validated decoding below 10 ms.
