# V123 timing: measurable improvement, 125 MHz still open

The APPEND-prepared rank mask improves the complete component and its targeted
RAW/scratch paths, but **fails 125 MHz setup and is not promoted**. The
[fresh native receipt](../../experiments/python-gamebub-v123/native/20261110T024415819812Z/receipt.json)
and [independent terminal audit](../../experiments/python-gamebub-v123/audit/native-independent.json)
bind the actual source, fixed recipe, tool, reports and checkpoints. All 1,063
integrity checks pass; the independently parsed design-timing verdict is FAIL.

## Complete-component comparison

| Routed metric | V121 | V122 control | V123 |
| --- | ---: | ---: | ---: |
| WNS | −1.347 ns | −1.949 ns | **−1.086 ns** |
| TNS | −3,248.192 ns | −4,597.575 ns | **−1,709.649 ns** |
| Setup-failing endpoints | 9,407 | 11,866 | **6,724** |
| Hold slack / failures | +0.069 ns / 0 | +0.028 ns / 0 | +0.028 ns / 0 |
| Pulse slack / failures | +2.750 ns / 0 | +2.750 ns / 0 | +2.750 ns / 0 |

Against V122, WNS gains **0.863 ns**, absolute TNS falls **62.81%**, and setup
failures fall **43.33%**. V123 also improves on V121 by 0.261 ns WNS and
2,683 fewer failing endpoints. These gains do not meet the required zero-failure
setup gate. All 73,287 routable nets are routed, routing errors are zero, and
all internal clock/coverage checks pass. External OOC limits remain 1,101 missing
input delays and 12,884 missing output delays; this is not a full-board result.

The new worst path is `scratch/emit_bank_reg/C` → `scratch/busy_owned_reg/D`:
9.034 ns data delay, eleven levels including three CARRY4s and six LUT6s.
Logic contributes 2.380 ns and routing 6.654 ns. The measured return cone selects
bank epoch/block, checks ownership in the coefficient parent, returns readiness
and releases the final tile owner. See the [source trace and next experiment](next-timing.md).
Do not attribute the carries to one arithmetic operation from net names alone.

## Matched read-only queries

Separate [V122](../../experiments/python-gamebub-v123/request-inspection/baseline-v122-20261110T015803000902Z/receipt.json)
and [V123](../../experiments/python-gamebub-v123/request-inspection/candidate-20261110T031036800243Z/receipt.json)
queries verify unchanged routed-checkpoint hashes. They use identical explicit
source families, endpoint selections and 50-path bounds. Rows are each family's
worst returned path, which can move to another endpoint or replicated register.

| Family | V122 slack | V123 slack |
| --- | ---: | ---: |
| RAW mode → all endpoints | −1.949 ns | **−0.891 ns** |
| RAW mode → scratch state | −1.949 ns | **−0.852 ns** |
| RAW position → all endpoints | −1.696 ns | −0.916 ns |
| Previous position → all endpoints | −0.417 ns | −0.089 ns |
| New rank mask → all endpoints | Absent | **+0.159 ns** |
| New rank mask → scratch state | Absent | +0.198 ns |
| Scratch phase → all endpoints | −0.992 ns | −0.783 ns |
| Record-view bank → all endpoints | −0.148 ns | −0.093 ns |
| Admission cursor → state | −0.250 ns | −0.040 ns |
| Admission cursor → all endpoints | −0.250 ns | **−0.427 ns** |
| Refill prepared address → all endpoints | −0.318 ns | +0.567 ns |
| Refill prepared address → RAM enable | +0.284 ns | +0.636 ns |
| Refill issued → RAM enable | +0.234 ns | +0.959 ns |

The RAW-mode all-endpoint family improves 1.058 ns and goes from eighteen to
ten logic levels. Its new worst ends at `busy_owned`, with 8.839 ns data delay;
the scratch-state subset has 8.701 ns data delay and ten levels. The prepared
mask has positive local slack, while the RAW family remains negative.

The unchanged admission cursor/state subset improves, but its all-endpoint
worst regresses to `fetch_addr_reg[1]/CE`. This explicitly prevents describing
admission as closed. The selected refill subsets improve; unqueried paths and
the complete component still require the global signoff gates.

## Mapping and methodology

| Routed resource | V122 | V123 |
| --- | ---: | ---: |
| Total LUTs | 33,686 | **33,308** |
| FFs | 43,134 | 43,515 |
| RAMB36 / RAMB18 | 32 / 12 | 32 / 12 |
| DSP blocks | 42 | 42 |
| CARRY4 | 4,214 | 4,215 |

The 64 logical mask bits map to **63 FFs** in both synth and route. The selected
`previous_position` family maps to sixteen FFs versus twenty-two in V122;
scratch's overall FD inventory rises from 4,830 to 4,865. Global FF changes also
include other mapping/replication effects and must not be attributed solely to
the new mask. Register trimming/naming is an observation, not an arithmetic
proof; the RTL retains full32 semantics and the independent tests cover them.
The unchanged queue retains 32 prepared-address FFs and no old offset FFs.
Global carry usage rises by one; the gain is control decomposition/locality,
not global carry elimination. No KEEP/DONT_TOUCH forces these observations.

The fresh routed methodology report has TIMING-16=**2** large-setup entries,
down from V122's 800 and V121's 125. SYNTH-6=28, TIMING-18=1,000 reported entries,
and ULMTCS-1=1 remain. The control-set warning reports 1,252 sets. RAM output
register and missing OOC-delay limitations remain explicit; no warning was waived.
The auditor uses fresh methodology outputs rather than cached timing-summary
counts. A low TIMING-16 count does not mean all setup failures disappeared.

The run uses the unchanged V120 Tcl/report/8 ns recipe, clock before fresh RTL
synthesis, default synthesis by omission, fixed ExtraNetDelay_high placement
and Default routing. Part is `xc7a100tcsg324-1`; tool is Vivado 2026.1/build6511674
in the retained image. Two threads/eight GiB caps and resource guards remain.
Runtime was 1,497.283 seconds, exit 0, with no monitor stop. No constraint relaxation,
exception, directive sweep or checkpoint-based implementation was used.

There is no unchanged negative reroute, positive qualification repeat, qualified
125 MHz handoff or board bitstream. Preserve qualified Source B100 for the
remote hardware team. The unchanged row cycles still conditionally project to
9.160832/12.425576 ms at an assumed complete-parent 125 MHz; sustained hardware
30 fps and validated hardware decode <10 ms remain open.
