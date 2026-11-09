# V115 live validation/publication: initial, refined and final partitions pass

All three selected **actual RTL partitions pass**: initial V115; refined V115
with the 93b header preparation and 2b9 scratch slot; and final V115 adding the
4ffe held owner certificate and e5ca request-address/bounds boundary. Each completes the original keyframe under fast and stalled
finite service, with a real wrong-ACK owner-drain test and clean retry without
reset. The refined and final live partitions each bind the **same 18 producer source
origins** as their corresponding main proof and native input/preflight cards. This establishes
the simulated component-to-C2/HUD/seal boundary; native clock closure and the
physical ESP32/SDRAM/display system remain separate.

| Selection | Selected attempt | Raw receipt SHA-256 |
| --- | --- | --- |
| Initial live | `20261109T024515202542Z` | `0a4b07a9509a89100764f8d9c791a63bac8b53a2b5a9b38cc1646060e69e8663` |
| Refined live | `20261109T025332546787Z` | `0adb51afea00e03f76a9e1a61e51d1ca735e62f2a6d44fc01822556c51e9f95e` |
| Final live | `20261109T035631906906Z` | `1289e6c52144554531640c7f0c8dcc55bfc4be48c281b62ce080d1d44201743c` |

The source and cycle audit is
[`refined/live-performance.json`](../../experiments/python-gamebub-v115/refined/live-performance.json).
It rehashes 39 initial, 42 refined and 42 final current/snapshot source bindings,
plus 49, 52 and 52 retained artifacts respectively. Those are repeated bindings across proofs, not unique
file counts. It independently compares all 18 emitted canonical/accepted-bank/
qcache arrays against frozen vectors. It also checks the final root, HUD digest
and seal, all 1,025 hash-job records per frame, and exact initial/refined/final digest
and cycle equality. This is an author's audit, not an externally independent
review of every implementation file.

## Actual work and measured fences

Each of the six successful keyframes has:

- 518,400 exact canonical bytes and 42,240 decoded HUD bytes.
- 560,640 candidate write requests, matching tagged ACKs and hash deliveries.
- 1,025 actual RTL SHA jobs covering 10,298 SHA blocks.
- The original C2 root, HUD digest and seal; an atomically accepted candidate
  bank and the expected abstract front-bank identity.
- Exactly one actual wrong-token ACK before the successful retry. The wrong ACK
  retains its physical owner until the real matching ACK drains. Each test has
  one explicitly discarded staged coefficient, with cumulative
  `accepted = delivered + discarded` conserved.

Initial, refined and final variants have identical measured fences:

| Finite service | First accepted outer byte → commit | **Last accepted outer byte → commit (ROADMAP strict)** | Start → commit | Conditional strict time at 125 MHz |
| --- | ---: | ---: | ---: | ---: |
| Fast, seed115701 | 3,092,122 cycles | **3,062,014 cycles** | 3,100,226 cycles | **24.496112 ms** |
| Stalled, seed115702 | 5,772,781 cycles | **5,732,576 cycles** | 5,780,885 cycles | **45.860608 ms** |

The ROADMAP strict decode/validation gate starts at the **last accepted outer
byte**, when the complete packet has arrived, and ends at validated commit.
First-byte times (24.737/46.182 ms at an assumed125 MHz) remain useful streaming
measurements but are not this strict gate. All live fences use the original
explicit cycle differences, without an inclusive plus-one adjustment. They begin at the successful retry; the preceding
negative-test setup/drain is separately executed and excluded from these nominal
frame latencies. The separate refined and final component ledgers each have 48 matched
successful component/transport rows with **zero fence changes from initial
V115**. Its
local decoder-done fence excludes validation/publication and must not be confused
with the complete partition fence above.

The 125-MHz conversions are arithmetic assumptions for this larger partition,
not an achieved clock claim. Fast service fits a conditional 33.333-ms frame
interval; stalled service does not. Both ROADMAP strict last-byte measurements exceed the 1.25-million-cycle
budget for strictly under 10 ms at125 MHz. **Sustained hardware 30 fps and validated
complete system decoding under 10 ms remain unproven.**

## Boundary and preserved checks

The selected producer retains the same public port header as V91k. The actual
V91l ACK-coupled joiner, validator, SHA core and abstract bank controller remain
unchanged. The owned parent wrapper adds a registered **producer-local** fault
cancel to break the observed combinational masked-done/cancel loop. Parent
joiner/validator cancellation stays immediate; external abort and power/warm
reset remain direct. New input/cache/memory/reference request grants and their
ready inputs are masked during revocation. Accepted response channels remain
unmasked so real physical debt drains.

The bench derives reversibly from the frozen V114 shared admission/elasticity
bench and adds the existing V91l live-service oracles. All 117 original class
`need()` calls remain after hierarchy translation. The actual accepted bank
supplies references through a bounded canonical view, with original size checks
and added independent byte comparisons. `ELASTIC=1` keeps its original one-slot
owner/conservation checks active. The original `settle()` condition, including
`start_ready`, remains; its finite watchdog is extended to cover the actual
C2/HUD work. This initial campaign does not claim to rerun the historical live
delta and full negative suite.

Strict compilation retains `--assert -Wall` and owned C++
`-Wall -Wextra -Werror`, with no warning waiver. Every run rebuilds the RTL,
snapshots sources and vectors, uses finite watchdogs and preserves failures.
The refined and final drivers are reversibly derived from the frozen initial
driver; their receipts explicitly distinguish the initial bench/API reference
from each actual producer selection. Final main selection is
`b6e34c72919d15155ba47da43f50b86e750c4f290e936d0267e12ae0107872df`,
with raw receipt
`020a105b44c14f24dbd884f7684c6aed034179a8f6f9a7423034ffe32dd6c951`.
The final partition's pixels, decoded HUD bytes, qcache, root, seal, SHA records
and all three measured fences are checked against both the frozen original
vectors and the initial/refined observations.

## Retained failures

The three earlier attempts remain immutable FAIL results:

| Attempt | Classification |
| --- | --- |
| `20261109T015802849920Z` | Strict compile found the real combinational masked-done/cancel loop; no RTL runtime. |
| `20261109T021132736264Z` | Fast RTL bench passed; the host parser then incorrectly omitted explicit discarded-token ownership from cumulative conservation. |
| `20261109T023320111515Z` | Fast complete profile passed; the stalled fixture checked a wrong ACK before its scheduled response had actually been offered. |

[`failure-history.json`](../../experiments/python-gamebub-v115/live-parent/failure-history.json)
pins their raw receipts and stdout. No old flag or result was rewritten. The
corrected fixture holds the response, advances actual RTL clocks to its recorded
`due`, then requires valid/ready and exactly one wrong-ACK counter increment.
It does not fabricate ACKs, skip clocks or weaken the original physical-owner
checks. The current runner records `actual_RTL_run` and `simulation_started`
before invoking the model, retaining FAIL on a later assertion.

HUD semantic decoding and expected commitment extraction occur in actual C++
before start. Memories use finite abstract tagged services. There is no ESP32
execution, QSPI timing, physical SDRAM controller, RGB display conversion or LCD
scanout in this partition. The measured result is stronger than a leaf decoder
test, while remaining distinct from a complete physical streaming system.


The final six-alias composition now has fresh passing component and live
selections. Its measured latency is unchanged; this is functional/source
qualification, not a native clock or hardware throughput verdict. Native timing,
strict under-10-ms decoding and sustained hardware 30 fps remain separate.
