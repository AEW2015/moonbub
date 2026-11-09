# Optional V114 optimized 100 MHz terminal result

Fresh RTL route completed with exit zero but **fails 100 MHz setup**:
WNS **−0.965 ns**, TNS **−779.991 ns**, **3,032 failing setup endpoints**.
Hold slack is **+0.053 ns**, pulse-width slack **+3.750 ns**, with zero hold or
pulse failures. All **69,066 routable nets** are routed with zero routing errors.
No failed-clock repeat is permitted. Neither routing completion nor this improved
negative result establishes an achieved 100 MHz clock, FPS or under-10-ms result.

The [receipt](../../experiments/python-gamebub-v114/optimized/native/20261108T235409013074Z/receipt.json)
SHA-256 is `325d79fb5338ab57f84a5d01f81c11449df84eedcefdc4299ee0670917f293cc`.
The independent [audit](../../experiments/python-gamebub-v114/audit/optimized-100-terminal.json)
passes evidence validation while recording timing failure. All **97 retained**
and **72 external artifacts**, **18 source snapshots**, exact prepared card,
source/proof/recipe/tool pins, raw timing parser equality and bounded command were
verified. This reviewer performed no build, native/MCP launch, source/proof edit
or hardware action.

Only scratch differs from the primary A source composition: prepared prefetch
scratch `332da205…` replaces V113 scratch `efc3e61a…`; top controller remains
`9e6d2b88…`. Actual synthesis/routed clocks are **10.000 ns, 0/5 ns**. The same
fixed XDC is registered before fresh default synthesis; before/after effective
XDCs contain only that clock/current-instance command, and no valid timing
exceptions exist. Part `xc7a100tcsg324-1`, Vivado 2026.1 build 6511674,
Default opt/route, ExtraNetDelay_high placement, no separate phys-opt, image,
two CPUs/threads, 8 GiB RAM/equal memory-plus-swap and 3,600-second watchdog match
the audited method. There was no checkpoint start, explicit retiming option,
monitor stop, guessed IO timing, bitstream or hardware programming.

## Actual routed bottlenecks

The [worst path](../../experiments/python-gamebub-v114/optimized/native/20261108T235409013074Z/reports/route-setup-paths.rpt)
is ingress `band_reg[0]_rep__0/C` → `prepared_request_in_bounds_reg/D`:
**16 logic levels**, **10.912 ns** total, **3.502 ns logic** and **7.410 ns routed
interconnect (67.906%)**, including eight CARRY4s. The source net has 65 loads
and 1.362 ns routed delay; the next eight-load net contributes 1.523 ns. This is
band-selected full-width fetch/descriptor address arithmetic followed by request
bounds and ownership/control selection, not the primary A kill-tag path.

| Top-50 source family | Paths | Worst slack ns |
| --- | ---: | ---: |
| Band → owned request bounds | 1 | −0.965 |
| Context blocks → scratch metadata/count/used-bytes enables | 20 | −0.908 |
| Scratch read address → scratch state | 3 | −0.902 |
| Replay remaining bits → context output reset/control | 7 | −0.871 |
| Inverse math-bank select → dequant output enables | 19 | −0.778 |

No kill-owner path appears in this sample. That does not prove all kill paths
pass, and these 50 paths do not classify all 3,032 failing endpoints. A100's
measured tag-qualified control priority remains valid for A100; B100 requires
its own ranking. The pre-route synthesis/placement tag paths do not supersede
this routed result.

The next study should address coherent full-width ingress request address/bounds
preparation, near-worst metadata allocation/readiness, and inverse-bank/dequant
validation/zero-selection/output-enable control and locality. The dequant source
selects the owned coefficient bank before its global input-range/zero shortcut;
a bank-to-output CE path is not evidence that token validation can be removed.
Multiple independent families already fail, so cutting one worst path alone
cannot close the retained timing result. Blind fanout constraints or register
duplication do not establish a safe or sufficient cut.

Any future boundary must preserve complete address/bounds/kind/index/band/epoch
ownership, first and subsequent requests at the earliest legal response edges,
32-bit wrap and 17-bit 65,536-block semantics, coherent metadata and coefficient
bank payloads, held offers and error priority. Preparation needs a proven reachable
producer edge; no spare cycle is assumed. Immediate public valid and returned-ready
revocation and accepted physical scratch/reference drains remain mandatory.
No source change or further trial is performed by this audit. Complete production
PCTL1/session and publication ownership are **not implemented**.

## Same-clock result and mapping

| 10 ns run | WNS ns | TNS ns | Setup failures |
| --- | ---: | ---: | ---: |
| Count100 | −1.022 | −1,125.069 | 4,620 |
| V112100 | −1.034 | −2,028.748 | 5,607 |
| V113100 | −1.686 | −3,190.694 | 8,220 |
| V114 primary A100 | −1.670 | −3,466.342 | 8,299 |
| V114 optional B100 | −0.965 | −779.991 | 3,032 |

A/B use the same 10 ns recipe/image and differ only in scratch source.
B has **0.705 ns less-negative WNS**, **2,686.351 ns less-negative TNS** and
**5,267 fewer failing endpoints**. This is a measured fixed-recipe comparison,
not timing closure, a predicted Fmax, a standalone throughput gain or an isolated
causal attribution of all placement changes to one arithmetic expression.

B uses **36,052 LUTs**, **39,747 flip-flops**, **14,707/15,850 slices (92.79%)**,
**32 RAMB36E1 plus 12 RAMB18E1 = 38 BRAM tiles**, and **42 DSP48E1**.
Compared with A, LUTs decrease 374 and FFs increase 285, while slices increase 376.
Smaller LUT count or spare DSPs therefore does not imply placement space, extra
physical ports or additional implemented compute lanes. DSPs remain 17 in the
coefficient path, eight dequant and 17 IDCT. All 44 RAM primitives retain
DOA_REG/DOB_REG zero; exact configurations are pinned.

Native DSP register mapping is not identical to A: ten IDCT DSPs have
AREG=0/BREG=1/MREG=1/PREG=0 and seven AREG=1/BREG=1/MREG=1/PREG=0; A had all 17
with AREG=1. No retiming option was added, but the actual mapped properties must
be reported rather than copied from the unchanged IDCT source. DRC consequently
reports DPIP-1:16 versus A's six; DPOP-1:27, DPOP-2:14, CFGBVS-1:1 and RTSTAT-10:1
are also retained. No register property is changed to suppress these warnings.

The functional qualification honestly reuses completed 44/42 canonical and
first-seed 12/2 transport certificates from the exact resource-interrupted parent,
which stays FAIL. Only second-seed transport 12/2 newly ran during recovery;
qualified totals are 44/42 and 24/4. Exact-source executable/input pins, original
oracles and extra full-top peer proof remain bound. The native measurement itself
starts from fresh RTL, without a synthesis checkpoint.

Internal clock/unconstrained-endpoint/loop/multiple-clock checks are zero. External
OOC requirements remain missing for **1,101 inputs** and **12,884 outputs**;
methodology reports SYNTH-6:28 and TIMING-18:1,000 warnings. The absent TIMING-16
summary category does not negate the raw negative WNS. The single-clock CDC report
says safely timed, with no complete-parent CDC/IO qualification. Board memory,
display, firmware, complete session/PCTL1, sealed publication and hardware
performance remain open.
