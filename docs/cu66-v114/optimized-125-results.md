# V114 optimized 125 MHz terminal result

The fresh optimized RTL route completed with exit zero but **fails 125 MHz
setup**: WNS **−2.696 ns**, TNS **−29,584.469 ns**, and **33,428 failing
endpoints**. Hold slack is +0.100 ns and pulse slack +2.750 ns, with zero
hold/pulse failures. All 68,835 routable nets are routed without routing errors.

The [terminal receipt](../../experiments/python-gamebub-v114/optimized/native/20261108T235739184089Z/receipt.json)
SHA-256 is `521daae4a0f1ddc8c119a116c71eaee523cc3bf7c8295fe9b7a9e5ba5c7de1b1`.
The independent [audit](../../experiments/python-gamebub-v114/audit/optimized-125-terminal.json)
passes evidence validation while recording setup failure. It verifies 97
retained and 72 external artifacts, all 18 B source snapshots, source/proof
pins, recipe copies and tooling. Synthesis and route both report the actual
8.000 ns clock, waveform 0/4 ns; the fixed XDC precedes fresh Default synthesis.
Default opt/route, ExtraNetDelay_high placement and no physical-opt stage match
the controls. No retiming, timing exceptions or guessed I/O delays were added.
The restored launch audit still matches its original `840de943…` receipt pin;
the separately retained trim and restoration history preserve the same decisions
and build inputs. This reviewer ran no builds or hardware actions.

The worst path is dequant output bit 172 → IDCT DSP48E1 A[28]: **17 levels**,
**10.250 ns**, comprising **12 CARRY4s/five LUTs**, 2.790 ns logic and 7.460 ns
wire delay (72.781%). The endpoint already has AREG/BREG/MREG/PREG = 1/1/1/0.
This measures an input-preparation/validation/selection cone feeding a DSP,
not multiplier propagation or a missing AREG. Mapped rounding names cross
hierarchy; no exclusive RTL-expression cause is inferred.

| Actual top-50 path family | Paths |
| --- | ---: |
| Dequant output → IDCT DSP A input | 13 |
| Parser cached remaining → reservoir CE | 16 |
| Ingress band → offsets/sizes/k0s CE | 12 |
| Scratch read address → state D | 5 |
| Replay remaining → parser output-value reset | 4 |

There are zero kill-owner sources in this sample. It does not classify every
failure; the A100 tag-first diagnosis cannot be copied to this result.

| Same-clock 8 ns result | WNS ns | Setup failures |
| --- | ---: | ---: |
| Count125 | −3.264 | 34,864 |
| V112125 | −2.844 | 33,323 |
| V113125 | −3.303 | 44,277 |
| V114 optimized125 | −2.696 | 33,428 |

Resources are 36,883 LUTs, 39,522 FFs, 42 DSP48E1s and 38 BRAM tiles; occupied
slices are 14,479/15,850 (91.35%). IDCT uses 17 physical DSPs, dequant eight and
the coefficient path 17. All 44 RAM primitives have output registers disabled.
Spare DSPs do not establish extra lanes, ports or parent placement capacity.

Internal unconstrained endpoints, missing clocks and loop checks are zero.
External OOC delays remain missing for 1,101 inputs/12,884 outputs. Methodology
reports SYNTH-6:28, TIMING-16:1,000 and TIMING-18:1,000; these reported warning
counts do not replace the full failure/port counts. Parent I/O/CDC, memory,
publication, hardware 30 fps and validated under-10-ms decoding remain open.
This negative result permits no positive fresh repeat or adoption claim.
