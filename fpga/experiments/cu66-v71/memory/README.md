# V71 qualified SDR2 memory bridge

This is a new integration. Frozen v70 source and evidence remain unchanged.
`cu71_memory_system` retains v70 canonical tile and auxiliary scalar ports,
and adds the dedicated LCD BL8 interface below. It uses a byte-identical copy
of the locally selected SDR2 source-v004 controller: 100 MHz, read phase
274.5 degrees (7.625 ns), wait 4, posedge retiming and MRS `0x033`.
`controller-origin.json` binds the copied controller. This does not establish
full-system routed timing or physical throughput.

## Operations and ownership

All addresses are x16 **word** addresses. Existing v70 generated map constants
remain authoritative. Only the mapped 32 MiB chip is selected.

Canonical tile identity/validation and generation/bank/plane/index responses
retain the v70 interface. Canonical writes now submit eight four-word rows,
each through an aligned masked BL8 operation. Tile rows are four-word aligned
and cannot cross an eight-word block. Disabled neighboring words are preserved.
There is no speculative write acknowledgment: each row waits for actual
controller recovery before advancing. Tile reads retain scalar reads backed
by a private aligned eight-word cache.

Auxiliary scalar writes submit one aligned BL8 with exactly the requested
word's two bytes enabled. Their response follows actual controller recovery.
This is a functional bridge, not auxiliary write combining. The existing
one-word request/reply API cannot safely combine future requests by pretending
queued writes already completed. Auxiliary reads have their own BL8 cache.

The bridge contains independent request and response slots for canonical,
auxiliary and LCD clients. Held responses do not hold the controller arbiter.
Aliasing writes selectively invalidate both scalar caches before issue and
after recovery. Different clients are not globally ordered: a reader requiring
another client's new data must wait for that write's completion/fence. Root
generation/bank ownership must still prevent unauthorized concurrent mutation.

LCD service uses a two-LCD-to-one-background quota at completed controller
operation boundaries when both are pending. A bounded four-cycle lookahead
reservation allows the next prefetched LCD request to traverse its independent
wrapper; without it, every inter-burst bubble would immediately grant background
traffic even under nominal LCD priority. Canonical/auxiliary background choices
use round robin. The original one-to-one bridge is preserved in `variants/`.
Refresh and the current accepted operation cannot be preempted. This is bounded
grant fairness, **not a proven line deadline**. Client requests held outside
their independent slots and controller refresh/service time must also be counted.

## Dedicated LCD port

| Signal | Meaning |
|---|---|
| `lcd_req_valid`, `lcd_req_ready` | One accepted aligned BL8 read |
| `lcd_req_addr[23:0]` | Aligned x16 word address; low three bits must be zero |
| `lcd_rsp_valid`, `lcd_rsp_ready` | Full response held stable until consumed |
| `lcd_rsp_data[127:0]` | Lane `i` at bits `16*i+:16` is address `base+i` |
| `lcd_rsp_error` | Invalid/alignment error; no memory command issued for an invalid request |
| `lcd_abort_i`, `lcd_busy`, `lcd_aborted` | Stop new issue, drain any accepted operation, suppress canceled success, then pulse acknowledgment |
| `lcd_completed_reads` | Actual controller READ operations completed for LCD, including subsequently canceled client transactions |
| `lcd_max_wait` | Largest bridge-accepted LCD wait through controller data completion; excludes outer wrapper admission and held-response time |

One LCD operation is outstanding. The consumer may copy a response into a
local buffer and issue its next request while serializing that copied block.
All eight words must remain within one allowed map block.

Abort does not rewind physical writes. A canceled candidate remains private
and its allocation cannot be reused until all accepted operations drain.
Reset requires the root's coordinated adapter/controller/domain flush and a
fresh generation; this component campaign does not qualify arbitrary reset
in the middle of an SDRAM burst.

## Reproduction and evidence

From the worktree root:

```powershell
python scripts/cu66-v71/memory/prepare.py
python scripts/cu66-v71/memory/run.py --output fpga/experiments/cu66-v71/memory/evidence/new-fast --seed 7001
python scripts/cu66-v71/memory/run.py --output fpga/experiments/cu66-v71/memory/evidence/new-slow --seed 7002 --flight 3.768 --access 8.489 --hold 2.223
```

Use new output directories. The native Windows runner requires Icarus/vvp at
`C:/msys64/ucrt64/bin`. Locally copied model helpers and verification inputs
make model generation independent of the historical source workspace.
`prepare.py` can reuse its hash-checked controller copy when that workspace
is absent. It never mutates v70 files.

The test uses the actual non-`SIMULATION` controller path with functional
ODDR/IOBUF models and a full-address 32 MiB SDRAM model. CAS3 launch convention,
strict hold behavior, command/byte-mask timing and refresh checks derive from
the previously reviewed SDR2 helpers. Clock/access arguments are **lumped STA
terms**, not independent chip tAC or PCB flight measurements.

Each run retains compile/run commands, logs, copied inputs and source hashes.
Coverage includes all banks/highest word, plane/tile boundaries, independent
scalar layout readback, guards/masks, cache aliases, rejected requests,
backpressure isolation, LCD word ordering, and accepted read/write abort drain.
Failed compile attempts remain in `component01`/`component02`.

`component03` preserves the earlier one-word masked-write control.
`rowburst02` and `rowburst-slow01` qualify four-word canonical row writes.
`lookahead-fast01` and `lookahead-slow01` bind the current scheduler and all
eight accepted-beat abort positions for canonical writes, aux writes and LCD
reads; each passes 4,543 checks and 34 abort/drain probes. `verify.py` checks
both results against current RTL and generates `qualification.json`.
The complete test adds an explicitly labeled 480-word stress-line measurement
with two response-hold cycles and eight serialization-gap cycles per burst.
It is not a clean scanout deadline gate. Display-owned integration must measure
the actual prefetch implementation and native panel clock separately.

No target-fit, native routed timing, board playback, network transport, 30 fps
or under-10-ms validated-decoding claim is made here.
