# V121 functional results

**PASS: the selected refill request cursor preserves tested Source B behavior
and public cycles.** This is finite RTL regression evidence, not formal proof,
physical timing or sustained gameplay performance.

The [functional index](../../experiments/python-gamebub-v121/integration/results.json)
has SHA-256 `bafb9950bbf740f0b3182f4d7f5f19875e1fbfa65b85d3c193282ceec748b689`.
The [independent audit](../../experiments/python-gamebub-v121/audit/full-independent.json)
recomputes selector/receipt, source, snapshot and artifact bindings and compares
the retained raw streams directly to V120 Source B.

## Selected change

Only alias `fpga/experiments/cu66-v91i2b/byte_refill_queue_v91i2b.sv` changes.
It selects [the V121 queue](../../fpga/experiments/cu66-v121-request/byte_refill_queue_v91i2b.sv),
SHA-256 `69b80d1210dcb17ad0eed0ba24cff68e31fbf213d5984b64ffc32ae213ac8e48`.
The other 17 source/include origins match Source B exactly, and all 18 original
Source B files remain unchanged in the checkout.

The prepared full32 address captures the start offset and advances only on
accepted reads. Source arithmetic still wraps modulo 2^32; the inherited assertion
still rejects an accepted overflowing request. A legal read at the final
unsigned address preserves the original unqualified wrapped next address.
See the [design contract](request-design.md) and [baseline audit](baseline-audit.md).

## Actual tests

| Stage | Fresh tested work | Result |
| --- | --- | --- |
| Focused queue | Two seeds; inherited 12 directed checks per seed; 40 legal boundary cases, 25 stalled full32 extrema and 2,048 random spans per seed | Exact pre/post-edge public pair and independent address/data/epoch/credit scoreboard PASS |
| Focused illegal wrap | Separately compiled original and candidate; starts at `0xffffffff` and `0xfffffffe` | Both reject the same accepted ordinal/edge with the unchanged overflow assertion |
| Complete decoder | Two seeds: 44 case profiles and 42 directed checks | Exact Source B stdout, events, values, cycles and independent canonical pixels |
| Actual V97 transport adapter | Two seeds; 12 successful profiles plus abort/reset retries per seed | Exact Source B event/cycle/canonical streams and bounded forwarding/accounting checks |
| Physical debt/peer | Two seeds; 14 canonical retries and six parent-pending cases per seed | Retained accepted read/write, cancel/reset, stale/replay and ownership checks PASS; raw Source B streams exact |
| Guarded parent | Four runs: byte/row × fast/bounded-stall | Six terminal dictionaries plus raw accepted/value/event/hash-cycle streams exactly match Source B |

The focused extensions cover 372,832 cycles and 193,910 completed bytes in
total. These are queue-test totals, not frame decode latency. All original
assertions and oracle statements remain; there is no nonfatal-warning override.
Executable C++ benches use `-Wall -Wextra -Werror`; Verilator uses `--assert`
and fatal `-Wall`. The separate V97 library-only model and its strict standalone
C++ adapter retain the original build contract.

The independent audit checks four spatial/transport stream sets, two peer sets
and four guarded-parent sets. Repeated profile outputs use the existing six
goldens; they are not new distinct gameplay captures.

## Cycle and coverage boundaries

The declared and observed public-cycle delta is **0**. The row parent retains
1,145,104/1,553,197 final-outer-byte → validated-commit cycles. At an assumed
complete-parent 125 MHz these are 9.160832/12.425576 ms; the stalled fixture still
needs 303,198 fewer cycles for strict <10 ms. The complete parent has not been
physically routed at that clock, and row service remains abstract.

Wrong-address rejection logic is unchanged and address-binding scoreboards
check accepted transactions, but this iteration adds no new directed corrupt
response-address injection. New focused faults include missing/unsolicited and
wrong-epoch responses, plus real response-on-revocation cases. These finite tests
do not establish all-state coverage, CDC, actual SDRAM service or RF behavior.

## Preserved orchestration failures

No failing functional oracle was changed to obtain PASS. The original metadata
collector incorrectly required executable C++ flags on the library-only V97
model. Its failed invocation/traceback and the separate reversible final
collector correction are retained under
[integration orchestration](../../experiments/python-gamebub-v121/integration/orchestration/failures.json).
All receipt-pinned collector/runner files remain byte-identical.

The first native preflight auditor resolved a full-copy selector's artifact
paths against the selector folder rather than its selected receipt folder.
[The failure record](../../experiments/python-gamebub-v121/audit/native-preflight-failure.json)
retains the command/error; the corrected independent audit passed before any
native tool was launched. A separate stopped watcher attempt never dispatched
a native job; its nested stderr was not retained, and its underlying cause is
explicitly unattested in
[the orchestration record](../../experiments/python-gamebub-v121/orchestration/watcher-preparation-failure.json).

Physical timing and mapped-path interpretation are separate from this functional
PASS. The qualified 100 MHz Source B handoff remains the independent hardware
control; production Sunshine/ESP32/custom-codec integration and the physical
30 fps/strict <10 ms milestones remain open.
