# Integrated v70 receiver, memory, painter and LCD path

`cu70_system.sv` connects the actual receiver's packet/base decoder, canonical
memory clients, HUD processor control, RGB painter and descriptor-driven LCD
scanout. `cu70_system_sim.sv` combines it with the checked full32MiB SDRAM
command model. No native golden metadata or reference pixels feed this top.
The packet byte port remains an external immutable staging interface. The HUD
processor endpoint remains explicit software and must decode the original HUD
bytes, transfer real words and compute the readback tag before claiming drain.

`USE_STRIP=0` selects the baseline painter. Nonzero selects the strip painter
through the identical scalar interface; implementation and qualification for
that painter are owned by the display work package. The active baseline and
optimized branches use the same physical memory map and global frame owner.
`sources.json` records the simulation source list/includes/options. For a
hardware flow, exclude `cu70_system_sim.sv` and `cu70_sdram_model.sv`, omit
`SIMULATION`, and use the real board's top-level clocks/I/O/constraints. No
routed target or electrical result is supplied by this directory.

## Memory and completion routing

Canonical reads/writes connect directly between receiver and memory subsystem,
including bank/plane/index/generation identities and actual write completions.
The memory adapter is not canceled when the receiver aborts: it completes its
accepted operation normally so the upstream owner can consume it while draining.

A three-way round-robin scalar arbiter serves the external HUD writer, painter
and LCD reader. It buffers each accepted request and retains response ownership
until the selected client consumes the response. One stalled response can delay
all three clients; both this effect and cache thrashing must be measured. The
underlying auxiliary port has one eight-word cache for all three clients.

Frame `memory_drained` excludes separately leased front-buffer LCD reads; those
must not prevent every new decode or commit. Canonical tile work and candidate
HUD/painter transactions still fence frame completion. The receiver advances
its front/RGB leases using the scanout module's **actual presented descriptor
acknowledgment**, with matching generation/frame/slot, rather than an unrelated
raw vblank pulse. That acknowledgment means old descriptor readers have drained;
it does not require that future reads of the new front remain idle.

The system preserves the native LCD timing/line behavior, including black lines
on actual service underrun. Scalar request/response overhead may miss line
budgets even when frame-buffer contents are correct. Do not infer a clean panel
or30fps from frame-buffer readback or a descriptor switch.

## HUD writer restrictions

External scalar HUD requests carry generation/frame identity. They are enabled
only after the matching processor preparation handshake and target only the
current candidate's HUD allocation. Writes must cover words0..21119 in order;
readback may access any word in that allocation before sealing. Stale, idle,
wrong-frame, wrong-region, duplicate or out-of-order writes receive an error
without a memory command. Rejected requests do not poison the legitimate next
word. Data-write replay/partial updates are not part of this initial interface.

The system counts **completed** HUD writes and rejects a successful drain claim
unless all21,120 words completed, no accepted HUD write failed, and no HUD memory
transaction remains outstanding. The claim's tag must be computed by software
from actual readback words and canonical HUD geometry. This counter is a transfer
coverage fence, not an implementation of HUD semantic decode or SHA in hardware.
After a matching drain claim, the writer is sealed. Generation reuse still
follows the receiver's transaction-owner rules.

Painter memory errors drain to an explicit negative painter completion, avoiding
a wait for a completion that the painter never emits after an error. All reset
signals must coordinate memory, pixel-domain state and external response queues.

## Read-only simulation visibility

The simulation top exposes `peek_address`/`peek_data` solely for independent
scoreboard reads of actual modeled SDRAM. It provides no write backdoor and no
path from peek data to receiver, memory, painter or scanout. `model_*` counters
observe physical command-model operations. The write event sequence/address/data
likewise observes actual model write commands, rather than queued writer intent.
Neither peek throughput nor these simulation-only ports are hardware features.

For a C++ timed driver, context time is in picoseconds. With a10000ps memory
cycle and clock falling atT, drive read clock high atT+2750, memory clock high
atT+5000, read clock low atT+7750 and memory clock low atT+10000. Evaluate queued
Verilator events via `eventsPending()`/`nextTimeSlot()` between phase changes.
This reproduces the existing279-degree sampling phase and model flight/tAC
scheduling; `test_control.cpp` demonstrates the procedure. Pixel clock is
independent and explicitly declared by the bench, not derived from simulation
host speed.

## Qualified control smoke

```sh
python3 fpga/experiments/cu66-v70/system/run_control.py
```

Current `control-results.json` pins the full source list, fixture, commands and
logs. The Verilator timed test parses the actual retained key packet twice,
performs two legitimate HUD word writes and readbacks through the real memory
controller/model, denies seven forbidden writes, observes physical writes via
peek/events, drains an explicit abort and processor ABORT acknowledgment, and
rejects a falsely claimed complete HUD transfer with error0x71. It confirms no
accepted reference/front frame results from either partial transaction.

The result is an explicit `SYSTEM_CONTROL_PASS`:99,247 modeled memory clocks,
133refresh commands, two actual writes, two actual read commands and zero
accepted complete frames. This is **not complete-frame decode/render or panel
qualification**. The root integration work owns those full-packet and real
presentation tests separately. Historical pre-parameter records are retained
as `control-pre-strip.*`; their raw `.json.txt` result is not current qualification.
