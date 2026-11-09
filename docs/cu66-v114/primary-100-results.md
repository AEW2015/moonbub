# V114 primary 100 MHz terminal result

Fresh RTL route completed with exit zero but **fails 100 MHz internal setup**:
WNS **−1.670 ns**, TNS **−3,466.342 ns**, **8,299 failing setup endpoints**.
Hold slack is **+0.040 ns**, pulse-width slack **+3.750 ns**, with zero hold or
pulse failures. All **68,616 routable nets** are routed with zero routing errors.
Successful routing and clean hold/pulse do not erase setup failure. The
positive-only policy permits no fresh repeat of this failed clock.

The [receipt](../../experiments/python-gamebub-v114/native/20261108T232847380696Z/receipt.json)
SHA-256 is `2ab4321ee00df9245578cc1de9e6cf67655dd37975909ae890dea3c0114cf141`.
The independent [terminal audit](../../experiments/python-gamebub-v114/audit/primary-100-terminal.json)
passes evidence validation while recording timing failure. All retained and
external artifact hashes, 18 source snapshots, prepared source/proof/recipe/tool
pins and raw-parser equality were verified against the exact audited card.
This reviewer performed no builds, native/MCP launches, source edits or hardware
actions.

Actual synthesis and routed clocks are `component_clk`, **10.000 ns**, waveform
**0/5 ns**. The pinned recipe reads the fixed clock XDC before the exact fresh
`synth_design` command. Vivado parses that registered XDC within synthesis;
this is not an after-route clock override. Before/after effective XDCs contain
only that clock and `current_instance`; there are no valid timing exceptions.
Vivado 2026.1 build 6511674, `xc7a100tcsg324-1`, Default synthesis by omission,
Default opt/route and ExtraNetDelay_high placement match the controls. There is
no checkpoint start, retiming option or separate physical-optimization stage.
Two CPUs/threads, 8 GiB RAM and equal memory-plus-swap, the 3,600-second watchdog
and host memory/PSI gates remained bound; no monitor stop occurred.

## Routed control family

The [worst setup path](../../experiments/python-gamebub-v114/native/20261108T232847380696Z/reports/route-setup-paths.rpt)
is `base_kill_owner_reg[3]/C` →
`coefficients/child/scratch/transfer_data_reg[34]/CE`: **15 logic levels**,
**11.380 ns** total, **3.071 ns logic** and **8.309 ns routed interconnect
(73.015%)**. It includes three CARRY4s in owner-tag qualification, then base-abort,
child/packet cancellation, context output and scratch write/transfer enables.
Mapped optimization names are not newly introduced RTL owners.

**48 of the 50 retained worst paths** start at that kill-owner register:

| Destination family | Reported paths |
| --- | ---: |
| Scratch transfer-data CE | 31 |
| Scratch request-epoch CE | 4 |
| Context consumed CE / available CE / output-value reset | 2 / 3 / 8 |

The other two paths are ingress fetch-byte → ingress state and fetch-index →
prepared request bounds. This is a top-50 sample, not a classification of all
8,299 failures. The synthesis-only owner-sequence and placed-only memory-enable
diagnoses are superseded by this actual routed family.

The first source net has **fanout one**, with 0.983 ns routed delay; the final
128-load transfer CE net contributes 1.336 ns. Broad unrelated nets include
scratch clear 7,146 loads, scratch reset 2,355 and coefficient fault-pending
2,229. Blind MAX_FANOUT or duplicating the first kill-owner register is not an
evidence-backed remedy. Inspect each tag-qualification/control segment and
locality. A future bounded registered local kill/command qualification must
preserve immediate public revocation on both valid and returned ready, coherent
owner tuples and all accepted physical response drains. Private flush is not
physical completion. No source change or new trial is proposed by this audit.
The historical prefetch cone is secondary to this measured routed family;
optional B requires its own actual route evidence. Complete production PCTL1
is **not implemented**.

## Mapping and comparison

Actual Series-7 primitives are **42 DSP48E1**, **32 RAMB36E1 and 12 RAMB18E1**,
equivalent to **38 BRAM tiles**. Routed utilization is **36,426 LUTs**,
**39,462 flip-flops** and **14,331/15,850 slices (90.42%)**. The part report gives
63,400 LUTs, 126,800 registers, 135 BRAM tiles and 240 DSPs. Spare DSPs do not imply
placement or extra memory-port capacity. This remains one compute lane.

The coefficient path uses 17 DSPs; inverse dequant uses eight and IDCT 17.
All 44 mapped RAM primitives have DOA_REG/DOB_REG zero; actual widths, write modes
and DSP AREG/BREG/MREG/PREG patterns are pinned in the audit. The 17 IDCT DSPs
have MREG=1/PREG=0, and eight dequant DSPs MREG=0/PREG=0. No register property is
silently changed to address warnings or add pipeline latency.

| Same-clock 10 ns result | WNS ns | TNS ns | Setup failures |
| --- | ---: | ---: | ---: |
| Count100 | −1.022 | −1,125.069 | 4,620 |
| V112100 | −1.034 | −2,028.748 | 5,607 |
| V113100 | −1.686 | −3,190.694 | 8,220 |
| V114 primary100 | −1.670 | −3,466.342 | 8,299 |

The 0.016 ns WNS difference from V113 does not establish timing closure or a
robust improvement; total negative slack and failure count worsened. An 8 ns
run must be compared with 8 ns controls, not this result.

## Methodology limits

Internal unclocked/unconstrained endpoints, loops, latch loops and multiple-clock
checks are zero. External OOC requirements remain missing for **1,101 inputs**
and **12,884 outputs**. Methodology reports SYNTH-6:28, TIMING-16:766 and
TIMING-18:1,000 warnings. DRC reports CFGBVS-1:1, DPIP-1:6, DPOP-1:27,
DPOP-2:14 and RTSTAT-10:1. No waivers or guessed IO delays were added.
The single-clock CDC report says all paths safely timed; it does not qualify
parent CDC, board memory, display, session or publication interfaces.
No achieved 100 MHz, hardware FPS, validated under-10-ms, bitstream or complete
parent signoff claim follows from this negative component result.
