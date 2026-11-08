# V113 1/2/4-lane budget and service bounds

Status: **source-pinned Python ledger PASS**. Only one inverse lane is
implemented and behaviorally verified. Two and four lanes below are conditional
replication budgets. This study runs no synthesis or RTL jobs and predicts no
FPS or achieved clock.

The [generated ledger](../../experiments/python-gamebub-v113/lanes/results.json)
pins the selected 16-tile benchmark, its actual source hashes, the V112 routed
hierarchy/capacity/RAM reports, and the actual physical-source origins from
V112's native input receipt. Reproduce with
`python3 scripts/cu66-v113/lanes.py`.

The V112 `xc7a100tcsg324-1` report records **240 available DSPs**, 63,400 LUTs,
126,800 registers and 135 block-RAM tiles. The routed component uses 42 DSPs,
36,669 LUTs, 35,438 registers and 34 block-RAM tiles. Slice occupancy is
14,050/15,850. These component figures do not include a qualified board-parent
allocation or establish fit for replicated V113 control.

The shared coefficient/context path uses 17 DSPs: 16 in synchronous ingress
and one in `context_decoder` itself. The inverse lane maps eight dequantizer
and 17 IDCT DSPs. The conditional engine cost is therefore **17 + 25 × lanes**,
using the old mapped arithmetic modules; new dispatch, arbitration and owner
logic have no mapped cost yet.

| Compute lanes | Conditional engine DSPs / 240 | Candidate result slots | Result payload + full identities | Shared intake floor, cycles/tile |
| --- | ---: | ---: | ---: | ---: |
| 1, implemented inverse | 42 | 2 | 3,352 bits | 128 |
| 2, budget only | 67 | 4 | 6,704 bits | 128 |
| 4, budget only | 117 | 8 | 13,408 bits | 128 |

Each lane's two result slots contain 1,536 payload bits **each**, plus a
140-bit identity each: epoch/child/token (96), plane/scale (4), block (16),
tile (13), and qcell (11). Two state bits per slot and all remaining control,
coefficient banks, IDCT working/result registers and reorder/dispatch storage
are additional. The fixed-word result and coefficient banks are registers;
V112's transform maps no RAMB18/RAMB36. The table does not assign them free
BRAM ports.

DSP headroom is insufficient to qualify whole-device fit. As a diagnostic,
copying the **old V112 whole transform** linearly would yield 36,669 / 48,075 /
70,887 LUTs for 1/2/4 lanes; the last exceeds the part's 63,400 LUTs. V113 has
changed control/storage, so this extrapolation is neither a V113 resource
measurement nor proof of its eventual fit or failure.

The service sweep retains one shared upstream coefficient stream and the
current **aggregate acceptance of one coefficient every two decoder cycles**.
With 64 coefficients per tile, the steady intake lower bound is 128
cycles/tile for every lane count. The finite 1,024-coefficient accepted-event
span is at least `(1024−1)×2+1 = 2047` cycles. Alternating accepts between
multiple lanes to reach one coefficient per cycle would require an additional
dispatch/ownership architecture and is outside this sweep.

The [actual standalone comparison](../../experiments/python-gamebub-v113/inverse/benchmarks/20261108T205614490604Z/receipt.json)
streams 16 identical golden tiles with no source gaps:

| Workload / residual consumer | Frozen cycles | V113 inverse cycles |
| --- | ---: | ---: |
| Zero / always ready | 1,153 | 2,118 |
| AC positive limit / always ready | 3,329 | 2,434 |
| Zero / ready on 83 of every 257 cycles | 3,412 | 3,368 |
| AC positive limit / same bounded consumer | 4,175 | 3,411 |

The V113 zero/always-ready coefficient span is exactly 2,047 cycles; every
inter-input gap is two. Its observed mean tile-start separation across the
15 output intervals is 128 cycles, already at the retained intake floor.
AC/always-ready has a 2,216-cycle coefficient span and mean output-start
separation of 140 cycles. These are end-to-end observations. The receipt has
no independent per-job DQ-launch/IDCT-complete timing, and first-residual
latency includes intake, validation/commit, launch and result ownership.
It cannot supply a pure arithmetic service time for a multi-lane simulator.
No speedup is assigned to the two/four-lane budgets.

The single residual output can transfer at most one value per cycle. An
always-ready consumer therefore imposes at least 64 cycles/tile. The actual
bounded consumer allows 83 transfers per 257-cycle period, imposing an
asymptotic floor of `64×257/83 = 198.169` cycles/tile at every lane count.
Finite startup, stalls and drain add to these bounds; an unbounded consumer
stall gives no finite completion bound.

The physical-port ledger retains these constraints:

- V112 maps 32 RAMB36E1s as two 16-primitive packet memories, all TDP with
  one-bit A/B primitive widths. Each logical packet read is shared by parser
  and replay with explicit priority; bit/depth slices are not independent
  compute-lane read ports.
- Mode and scale each use one RAMB18E1, mapped with A/B read widths 2/2 and
  9/9. Their source exposes one current lookup interface. The two context
  RAMB18E1s have read widths 18/0. TDP configuration grants no additional
  independently scheduled metadata requests in the existing interface.
- Scratch has one 128-bit request/response channel and one physical
  outstanding ledger. Reconstruction has one reference request/response owner
  and a 512-bit pixel response. Replicated math does not multiply these ports.
- The board top has one physical 16-bit SDRAM DQ bus. A 128-bit scratch payload
  needs at least eight data beats; 512 reference bits need at least 32, before
  commands, refresh, turnaround, other clients and CDC. Actual requests per
  tile and calibrated memory service are absent, so no memory-cycle or frame
  rate is inferred.

The meaningful checks enforce the source/receipt pins, DSP capacity boundary,
full identity sizing, the measured 2,047-cycle acceptance span, unchanged
shared-intake bounds across the sweep, and the bounded consumer's 83 ready
slots per period across six phases. All pass. Additional lanes still need
measured independent arithmetic service, an owned dispatcher and ordered
retirement, metadata/scratch/reference arbitration, and fresh complete-source
resource/timing evidence before a throughput or 125-MHz claim.

## Actual routed V113 one-lane mapping

The subsequent full-composition native runs now provide actual **one-lane**
resource measurements. Both fail setup; these resource counts grant no clock
qualification or positive-repeat eligibility.

| Actual component target | LUTs | FFs | BRAM tiles | DSPs | Slice occupancy |
| --- | ---: | ---: | ---: | ---: | ---: |
| 100 MHz / 10 ns | 36,367 | 39,212 | 38 | 42 | 91.31% |
| 125 MHz / 8 ns | 36,976 | 39,225 | 38 | 42 | 92.56% |

Both map 32 RAMB36E1 plus 12 RAMB18E1 primitives: 38 tile equivalents,
**four more than the V112 ledger's 34**. Both retain the actual 17 shared and
25 transform DSPs. The [100-MHz](spatial-100-final.md) and
[125-MHz](spatial-125-final.md) terminal audits retain the negative timing,
primitive, clock and ownership scope.

These measurements are an appended one-lane observation. The frozen Python
ledger/results and its conditional 2/4-lane calculations still use the
explicitly pinned **old V112 mapping**; they have not been replaced by these
numbers or promoted into a multi-lane implementation. With more than 91% of
slices occupied, unused DSP capacity does not imply placement room, spare
logical memory ports, full-parent fit, timing margin or additional throughput.

The exact raw report pins, independently checked against each terminal
receipt's retained-artifact hashes, are:

| Target / raw report | SHA-256 |
| --- | --- |
| [100-MHz hierarchy](../../experiments/python-gamebub-v113/native/20261108T213634749593Z/reports/route-utilization.rpt) | `88f9570c84573760f6ccb7e48f6f64ca80a1c363e42109ab0eef9b2044b4bcb0` |
| [100-MHz capacity](../../experiments/python-gamebub-v113/native/20261108T213634749593Z/reports/route-capacity.rpt) | `a84bd90bf6cb92d79da55a99ecda06f63af9549733562430f08271dcbcd8c003` |
| [125-MHz hierarchy](../../experiments/python-gamebub-v113/native/20261108T213919828839Z/reports/route-utilization.rpt) | `ca82b8006e619745196f5957d55fb2783de26d15a9814fbcc2ad523ced5f22fc` |
| [125-MHz capacity](../../experiments/python-gamebub-v113/native/20261108T213919828839Z/reports/route-capacity.rpt) | `9a083c90a2c7248ff58a736069618ad9dc6a529357b27f9329f7e45b1bc916fd` |
