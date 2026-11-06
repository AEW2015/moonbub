# V81 observer, path events and immutable system attempts

`monitor.hpp` and `monitor_tb.cpp` are byte-identical to the frozen V79 observer
and unit proof. The nine synthetic observer tests pass under the V81 runner;
these are unit tests, not hardware fault injection. The main replay preserves
canonical-plane readback, full canonical hashing, semantic HUD write/readback,
per-generation native full-raster obligations, continuous health observation,
fixed packet release timestamps, queue accounting and lost-ACK reconciliation.

## Explicit modes

`run_system.py` accepts `--prefetch 0`, `1`, `2` or `3`, or matching `--variant`
values `baseline`, `prefetch`, `overlap` and `wide`. The explicit V81 default is
mode 3. Mode 2 remains the V80 snapshot-overlap control. Neither the default nor
a clean compile establishes that the experiment improves latency.

Each source emits the inherited `SYSTEM_PREFETCH`, `SYSTEM_COMMANDS`,
`SYSTEM_STREAM`, `SYSTEM_FRAME_PASS`, `SYSTEM_TIMING` and raster-deadline rows,
plus `SYSTEM_PATH`. The latter reports first offered reference lookup validity,
accepted raw prefetch requests, accepted bridge snapshots, successful wide-block
commits and actual backend write completions before wrapper retirement.

For a successful mode-3 delta, the path counts must be 7,806 first offered
lookups, 32,400 raw requests, 32,400 snapshots, 32,400 successful block commits
and 8,100 backend tile-write completions. Each tile must have exactly four
blocks at addresses `tile_base + block*8` x16 words, with exact generation,
reference bank, plane and tile identity. Snapshot must follow its accepted
request and block commit must follow its snapshot. Candidate backend completion
must match a previously accepted write. A keyframe has no reference lookup or
prefetch blocks and still has all 8,100 backend write completions.

Raw-request/snapshot/block events are instrumented only for mode 3. Their zero
counts in controls have `raw_snapshot_block_instrumented=0`; they do not claim
that control memory work is absent. First offered reference validity and
backend completion are instrumented in the controls as well. The legacy mode's
backend completion is its direct receiver-facing memory completion.

## Event CSV semantics

The optional trace retains the same 11-column header:

```text
cycle,ps,frame_generation,event,owner_generation,client,write,address,bank,plane,tile_index
```

`ref_first_valid` emits once per source/tile when offered valid is first observed,
including a cycle where ready is low. It is distinct from accepted
`ref_request`. The new events are `prefetch_raw_request`, `prefetch_snapshot`,
`prefetch_block_commit`, and `backend_write_done`. Their path metadata is the
captured owner identity; prefetch address is the captured block word address.
A successful block commit is distinct from consuming or discarding an aborted
response. Physical `command` events still use unknown owner generation zero;
trace-window generation is not substituted for transaction ownership.

Tile and path handshakes are sampled before the numbered memory rising edge;
cache-fill counter changes and epoch completion pulses are sampled after it.
The trace is bounded to at most four selected sources and two million rows.
Raw CSV is deterministically gzip-compressed after the attempt, preserving both
raw and compressed hashes, raw byte count and event counts.

## Build and attempt identities

Each attempt gets a unique UTC/UUID directory before source/build validation.
The result records exact RTL/spec/bench/runner and complete immutable fixture
hashes; mutable V81 bytes are also archived in a source tarball. Build and run
commands, return status, time bounds, logs and executable SHA are retained.
Completed failures are preserved separately from running checkpoints, whose
initial status fails closed. `V81_SYSTEM_PASS` requires a unique terminal
`SYSTEM_PASS`, no `FAIL`, complete canonical/HUD/raster proof, path accounting,
and unchanged producer sources throughout the attempt.

Builds use one compiler job and separate mode/TAC build directories. The build
identity is immutable: `--skip-build` requires matching source pins and the
existing executable SHA. To rebuild, preserve the published package and archive
both the old identity JSON and its object directory in a separate reproduction
workspace; never rebuild a binary used by an active run.

Functional correctness, packet-complete-to-ACK 33.333-ms budget, strict
packet-complete-to-validated-ready below 10 ms, and physical sustained throughput
remain separate verdicts. Validation includes admission queue time. Native CPU
HUD/control still consumes zero modeled time and the memory clock is assumed
100 MHz; these simulations do not establish ESP32 transport cost, FPGA fit,
routed timing, CDC or physical display qualification.
