# Overlay reset-enable proof and complete BRAM coverage

Read-only query of the sealed CANCEL-boundary routed checkpoint, parent manifest
`ac3ea38161c6f6ca69a9ecba7917b3a4cbdf1d5d2b975558c64480d734df8e3b`.
This resolves the specific overlay EN polarity uncertainty in v3; it does not
replace v2/v3 or qualify warm-reset content retention. No candidate or checkpoint
was changed. No synthesis, place, route, bitstream or hardware command was run.

## All 44 overlay read enables are forced low by reset

The query collected the actual ENBWREN driver and LUT input/INIT table for every
one of the 44 overlay RAMB36E1 cells. Every immediate driver is a LUT4 with I0
directly connected to `rstpixel_reg[3]/Q`. Its other inputs are registered read
address bank-selection bits. All LUT INITs have zero at **every odd truth-table
index**, so I0=1 forces ENBWREN=0 across all eight assignments of the other inputs.

The independent Python enumeration in `overlay-truth-v4.json` checks that exact
driver/I0 association and all eight values for each of the 44 pins. This is a
universal reset-asserted enable proof; it does not depend on assuming address zero
or retaining the initial address registers. The inspected reset fence is FDPE
with INIT=1. The unchanged top source keeps it asserted while panel MMCM lock is
low and releases through four pixel-clock edges after lock. The query did not
separately re-enumerate its PRE fan-in; the final successor must bind its own
actual reset fence and routed reports.

This means overlay is **not an additional EN-high-in-reset blocker** like the
fixture ROM. The 44 REQP warnings name the asynchronous reset source but do not
mean it necessarily drives the hazardous polarity. Reset assertion during an
already active read and possible prior corruption are separate questions; this
does not promise transparent or uncorrupted overlay after warm PLL loss.

## Recursive evaluator limitation is preserved

The copied general recursive evaluator reproduced the known-bad high-bank fixture
ROM EN=1 under core reset, but returned unknown (-1) for all overlay reset-only
and fresh-INIT evaluations. Those raw results remain in `overlay-enable.txt`.
They were **not** converted to PASS. The overlay conclusion instead uses the
independent, explicit direct-LUT enumeration described above. Unknown still
blocks any other positive gate unless its actual netlist logic is proven by a
separate valid method.

## The warning set covers every block RAM cell

GM's separate read-only parent checkpoint query produced exact sorted names for
106 RAMB36E1 cells and zero RAMB18E1 cells. A preserved copy and its query/log are
under `bram-coverage-reference/`. The independent comparison finds that this
106-cell set equals the unique cell set named by the 199 uncapped REQP warnings,
with no missing or additional cells. This confirms the v3 role classification
covers every RAMB36E1/RAMB18E1 cell in this routed parent. In particular there is
no unflagged quantizer-table BRAM; its source table does not add another immutable
BRAM to the identified fixture-ROM problem.

The exact proof remains bound to this parent checkpoint. A successor can map or
gate memories differently, so final startup proof and coverage must be rebound
to its actual netlist. External QSPI hold, warm reset, physical playback and AV
qualification remain separate open gates.
