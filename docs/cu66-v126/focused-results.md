# V126 focused producer results

The selected fresh [attempt](../../experiments/python-gamebub-v126/producer/attempts/20261110T142915604891Z/receipt.json)
passes all six seed runs with all nine commands exiting zero. Its receipt SHA
is `b3a18c18b617bdd5085b86f90f15bae8208f4eafdb85752b830158ff43abe133`;
45 source inputs and 69 artifacts are retained. Wall time was 619.064 seconds,
including fresh compilation; this is host test duration, not FPGA decode time.

The unchanged production candidate is
`fpga/experiments/cu66-v126-producer/cs88_coefficients_v91k.sv`, SHA
`5dec7454e6bfae4f7a9d7f64ecfbef8568665ddaa2dc00d4a76de1167a3c7292`.
It adds 24 logical payload bits and no intended public cycle. Physical register
mapping and routed timing require the later native evidence.

## Executed domains

| Domain | Seeds | Result per seed |
| --- | --- | --- |
| Extracted geometry stages/table | 126501 / 126502 | 32,768 exhaustive full13/all-plane cases plus 65,536 random cases; 98,304 total; 1,190,177 clocks; 294,912 hold edges; 1,120 cancellation cases |
| Whole-producer prepared campaign | 126501 / 126502 | 534 contexts; 3,664 real fixture edges, including 1,428 primer and 2,236 other edges; all semantic checks pass |
| Actual controller pair | 126601 / 126602 | 11 vectors × two configurations = 22 cases; 12 directed checks; 4,058,368 dense comparisons plus 913,984 directed comparisons; no pending drain or request/ack imbalance |

The extracted scalar domain checks all thirteen tile bits and all four planes,
including modulo13 successor wrap and low11 cell truncation. Its arbitrary keys
and phase operations are not natural producer packet histories. The actual
producer campaign uses bounded planes 0–2, original PREP/MAP_REQ writers and
synchronous mode/scale reads. Neither new payloads nor verification owners are
forced. Primer edges are separately traced and counted.

Prepared producer checks include all lookup modes, concurrent reconstruction
arbitration, 555 consecutive skip advances crossing row/pair/table-bank
boundaries, 21 held-child edges, 96 nonterminal advances, 288 cancels, 48 bad-owner
cases, 72 stage overlaps, nine unowned bad-bound cases, three empty-plane cases
and three accepted-start cases. The odd luma tile 185 → 186 dispatch changes
the current cell from 47 to 48, distinguishing current from successor data.

All inherited cache/scale, V119 nonce/owner and V124 lane/error/debt oracles pass.
Their records retain 250,000 random nonce/owner cases, 466,944 lane wire cases,
65,536 full-width random lane cases and 8,192 state cases per seed. No existing
oracle or RTL assertion was disabled, removed or downgraded to obtain PASS.

The generic monitor checks the original current-cache invariant on all
275,334 observed edges, including 1,188 address captures and 672 cell consumes.
The actual-caller monitors check 10,222,021 / 10,220,622 edges, each with 104,824
address captures and 104,777 consumes. Caller held-owned edge counts are
8,062,225 / 8,061,224. Earliest mode2/skip responses and blocked/accepted starts
are observed. Public cycle changes and new payload/owner forces remain zero.

## Independent audit and retained failures

The [focused independent audit](../../experiments/python-gamebub-v126/audit/full-independent-focused.json)
passes with SHA `c4137c64b15b84dbce24f70ce6c6bac774e8ebbddde371fbce7dc5ca86eb083b`.
It rehashes the source/artifact chain and independently reconstructs scalar,
generic, caller, primer and terminal records. Inherited admission, owner, rank,
bounds and queue proofs remain separate source-bound controls.

The [attempt history](../../experiments/python-gamebub-v126/orchestration/focused-attempt-history.json)
retains three failed official attempts before this PASS:

1. A missing runner memory helper stopped execution before any Docker command.
   Restoring the frozen V125 helper changed no RTL or fixture.
2. Strict C++ warnings rejected ambiguous indentation in the new testbench.
   Braces clarified the conditional; its counter remained unconditional.
3. The new bad-owner fixture corrupted a selected child's own bank lease and
   tripped an unchanged reference scratch assertion. The corrected fixture
   instead mismatches original parent keys while keeping child state coherent;
   error 67 and every original assertion remain required.

Private-copy incremental diagnostics then exposed one omitted initialization
edge in the new auxiliary monitor's expected total. Independent loop arithmetic
and a diagnostic counter probe agree on **271,670 retained instrumented edges +
3,664 campaign edges = 275,334**. Strict equality was corrected; this is not an
added production cycle. Diagnostics are explicitly non-qualifying. The selected
PASS above rebuilt both executables freshly and reran every seed afterward.

The original independent auditor also retained a reporting-only `clock_edges`
lookup against the inherited `edges` field. A separate v2 fixes that one lookup;
the original code/failure, exact derivation and review are preserved. No RTL,
fixture or passing simulation was rerun or altered for this reporting repair.

## Limits

This finite two-state Verilator suite is not formal proof, CDC/reset electrical
qualification, a full Sunshine/ESP32 system, hardware frame-rate evidence or
silicon decode latency. The full decoder/transport/peer/parent regressions and
fresh global timing result decide their own gates. No 125 MHz timing, board
bitstream, sustained hardware 30 fps or validated hardware <10 ms follows from
this focused PASS.
