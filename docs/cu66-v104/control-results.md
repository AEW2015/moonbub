# V104 cached reconstruction geometry

The [candidate](../../fpga/experiments/cu66-v104-control/cu66_reconstruct_stream_v91k.sv)
starts from the selected V102 reconstruction source, preserved in V103 commit
`1d0a702a758787522723ac52ff44a1bf220c39d1`. Candidate SHA-256 is
`445e1b96fc931cf1a8a6cabbf7f111a199197264eb8ab35f9dde871ab010ecb8`.
The full public 72-port header is unchanged. Seven exact source edits in the
[edit proof](../../fpga/experiments/cu66-v104-control/edit-proof.json) recover
the complete candidate from its committed baseline. The original mode,
reference-owner, coefficient validation, output, error-priority and diagnostic
logic remains; the candidate adds derived coordinate register state.

## Recurrence and reachable-state contract

Three small registers hold an eleven-bit quantization-cell index, a seven-bit
Y column and Y row parity. They replace runtime `quant_cell` evaluation in both
the always-visible `lookup_cell` output and the residual qcell validation guard.
The original function remains unchanged as a non-synthesis assertion oracle.

For every initialized reachable state, the intended invariant is:

- Plane is 0–2, and tile is below 5,400 for Y or 1,350 for either chroma plane.
- For Y, column is `tile % 90`, parity is `(tile / 90) % 2`, and cell is
  `45*floor(tile/180) + floor((tile%90)/2)`.
- For chroma, column/parity are zero and cell equals tile.

Reset, start and cancel initialize the derived registers alongside the original
plane/tile assignments. The cache holds through every admission/mode/residual/
reference/math/output stall and every error. It advances only on the accepted
64th output byte, exactly when the original tile advances. Ordinary Y columns
increment the cell only when the old column is odd. At column 89, the column
wraps to zero and parity toggles: an even-to-odd row transition subtracts 44
from the cell; an odd-to-even transition adds one. A plane boundary resets the
cache/column/parity to zero. Chroma increments the cell once per completed tile.
The final plane-2 tile also resets to zero in `WAIT_DONE`, matching the original
tile wrap. These cases preserve the invariant by induction on clock transitions;
this is an engineering derivation, not a machine-checked formal proof.

The maximum reachable cell is 1,349, so eleven bits suffice. Column is bounded
to 0–89; no tile or public input width is narrowed. This candidate refines
reachable sequential state rather than replacing the original function for
arbitrary forced/internal plane/tile values. No hierarchical state force is
used by the focused test. Verification assertions check the original function,
coordinate ranges, column and parity on initialized, non-killed clocks.

The physical reference owner is untouched: `ref_pending` still survives warm
reset/cancellation until the matching response drains. No new interface state,
ready/valid bubble or accepted-frame cycle is inserted. Always-visible lookup
values are compared even when lookup requests are low.

## Actual RTL comparison

The [selected focused receipt](../../experiments/python-gamebub-v104/control/results.json)
records a strict Verilator 5.020/GCC 13.3 run, with `--assert -Wall` and C++
`-Wall -Wextra -Werror`; no warning or assertion downgrade is added. Both full
production modules are instantiated through exact body-preserving verification
adapters. All public outputs are compared at every low/high/low evaluation;
all verification coordinate outputs are compared too.

| Clocked focused evidence | Measured value |
| --- | ---: |
| Complete frames | 2 |
| Directed checks | 51 |
| Actual rising clock edges | 2,445,067 |
| Low/high/low public-output comparisons | 7,335,201 |
| Accepted canonical bytes, including directed setup | 1,037,120 |
| Coordinate changes, including kill/reset changes | 16,212 |
| Coordinate holds | 2,428,855 |

One key frame and one predicted frame traverse all 8,100 tiles each, covering
all 90 Y columns, 30 row pairs, plane transitions and final wrap. Predicted
mode selection exercises copy, residual and hidden tiles with delayed reference
responses. Input, mode, reference and output readiness have deterministic
random stalls. An independent pixel model checks every accepted byte; the two
complete frames account for 1,036,800 bytes, and directed setup adds 320 bytes.

The directed suite applies reset, cancel, start, reset+start and cancel+start in
original states 0–9, checking cache initialization and old reference drain. It
also injects a bad qcell and requires error 4. `WAIT_DONE` is held for seven
cycles in each complete frame before normal completion; this focused suite
does not claim all reset combinations in `WAIT_DONE`. The parent integrated
pipeline regression provides its separate protocol/error/epoch coverage.

The [independent Python replay](../../experiments/python-gamebub-v104/control/trace-audit.json)
verifies **112,409 retained rows**, including every geometry advance/control
pulse/state change and periodic holds. It checks row/column arithmetic and
successive coordinates independently of the hardware recurrence, plus source,
receipt and artifact SHA-256 values. It sees 16,205 non-killed advances, 214
control pulses and exactly two final-frame wraps. The larger C++ change count
also includes seven coordinate resets; the counts describe different events.
A rolling all-clock observation digest is retained; it is not substituted for
the direct SV output comparison or presented as a cryptographic proof.

## Retained resource stop and reproduction

The [attempt ledger](../../experiments/python-gamebub-v104/control/failed-attempts.json)
retains the first attempt, whose strict compile passed before a host memory
PSI gate denied the next checksum/simulation command. No RTL simulation or
mismatch occurred in that stopped attempt. The retry used unchanged production
sources and resource thresholds and passed. It is the selected receipt above.

```sh
python3 scripts/cu66-v104/control.py
python3 fpga/experiments/cu66-v104-control/audit_trace.py
```

Commands snapshot their inputs, retain transcripts and compressed actual traces,
hash the executable and declared artifacts, and use finite compile/simulation
watchdogs. Executables remain outside Git. The historical backend is a
**two-state model**; this is not four-state or formal equivalence, post-mapped
netlist proof, complete HUD/C2/shared-memory/display integration, an achieved
clock, hardware 30 fps, or validated full decoding below 10 ms. Native resource
and timing measurements belong to the separate parent comparison.
