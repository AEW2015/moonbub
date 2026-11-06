# V80 reference integration components

`cu80_reference_path` connects the frozen V79 two-slot prefetch core to the
actual decoder tile interface. `cu80_memory_system` forks V74 only to arbitrate
the existing tile P0 requests with aligned prefetch BL8 requests. The V74 tile
adapter, V74 word bridge, V72 controller, and SDRAM model remain unchanged.
The system owner selects the exact original V74 memory system for the disabled
prefetch baseline and disables legacy tile reads for the enabled path.

A delta epoch captures monotonic generation, reference bank, candidate bank,
and reference frame ID. The system retains its reference-bank lease until
prefetch ownership and every held token drain. Key-frame writes bypass slot
retirement. New epochs wait for held write and reference tokens to clear.

The raw backend admits one prefetch command, receives the frozen bridge's
128-bit response snapshot, and emits eight ordered 16-bit beats. The accepted
P0 owner remains occupied through the final consumer handshake; `idle` includes
this ownership. The frozen bridge still services HUD and LCD clients while a
prefetch stream is held. Physical-command telemetry captures the owner at
bridge admission and reports the client on actual controller acceptance:
0 tile/legacy, 1 HUD, 2 LCD, 3 prefetch.

Candidate requests during an active epoch must match its generation and bank
and valid plane/index bounds. Invalid requests generate a local error without
reaching physical memory. Actual write completions must match all four fields
of the accepted candidate request before translation to the reference bank.
Successful completion is held until V79 accepts retirement. Hidden tiles use
the exact frozen `cu66_expand_tiles` predicate (256 Y, 19 U, 19 V). Visible
tiles require a two-entry served ledger, preserving an earlier tile's identity
when the decoder looks ahead to the next reference.

Abort or a prefetch fault cancels V79's held success response. The wrapper
preserves any accepted lookup identity and returns one held error response,
so both receiver and base pipeline clear their pending tokens. Interrupted
writes can similarly receive an error through `mem_write_aborted`. A mismatched
terminal completion produces an error carrying the accepted write identity;
it never retires a slot. The system must independently include physical tile
busy, raw backend busy, wrapper busy, and auxiliary drain in its drain decision.
It must never infer physical drain from the error token alone. Frozen core
faults remain visible until all wrapper/core work drains and `clear_fault`
acknowledges them. A subsequent key bypass and fresh delta epoch are supported.

Run the bounded component checks from the repository root:

```sh
python3 fpga/experiments/cu66-v80/integration/run_component.py
python3 fpga/experiments/cu66-v80/memory/run_memory.py
```

The wrapper runner uses strict Verilator `--Wall` and seven transactional cases:
full 8,100-tile replay (7,806 lookups, 294 unused retirements, 32,400 BL8
commands, 259,200 beats), two-entry lookahead, held reference cancellation,
all four terminal completion metadata mismatches, raw/aborted-write/held-done
fault drain, fault-clear/key/fresh-delta recovery, and four invalid candidate
request fields. This backend is transactional, not a physical SDRAM model.

The memory runner uses strict `--Wall` with the conventional testbench-only
`BLKSEQ` waiver at tAC 2 ns and 7 ns. Reference bytes enter through actual
controller tile writes, with no model backdoor initialization. It checks all
eight held stream beats, concurrent LCD/HUD progress, write/prefetch P0
arbitration, abort during stream delivery, invalid-address error drain without
a physical command, and exact command-client accounting. Each corner requires
12 physical write commands, two prefetch reads, one HUD read, and one LCD read.

These checks establish component behavior. Actual decoder canonical validation,
whole-system faults, source pacing, and latency claims require the separately
owned V80 system campaign. Component replay totals do not establish a frame
rate improvement or the strict validated-before-10-ms target.

## Separate P0 snapshot-release experiment

`cu80_overlap_memory_system.sv` is a separate fork. Its default
`P0_RELEASE_ON_SNAPSHOT=0` preserves the original V80 ownership behavior.
Mode 1 clears the P0 command owner when the prefetch snapshot is captured,
retains `stream_active` as its independent raw-response lease, and blocks
another prefetch until that stream drains. Candidate tile writes can use P0
while the old snapshot streams. Stream-final never clears a newer command's
owner in mode 1. The original `cu80_memory_system.sv`, reference wrapper, and
system source pins are unchanged by this experiment.

Three cumulative counters reset only with reset:

- `stream_candidate_wait_cycles`: `stream_active && t_valid`.
- `stream_idle_candidate_wait_cycles`: the same, with bridge and controller idle.
- `stream_write_accepts`: a P0 write admission while the raw stream is active.

Run `python3 fpga/experiments/cu66-v80/memory/run_overlap_memory.py` for both
modes at tAC 2 ns and 7 ns. Each invocation preserves exact source snapshots,
commands, build logs, and run logs in a timestamped `memory/overlap-attempts/`
directory. The qualified attempt is `20261106T030250Z`; its predecessor retains
a strict CLI bit-width warning caused by passing integer `1` to a bit parameter.
The runner now passes an explicit one-bit literal without warning suppression.

All four configurations pass through the frozen actual controller and SDRAM
model with identical traffic: 21 physical prefetch reads, 24 tile writes, one
HUD read, and one LCD read. Each checks 176 raw beats and reads back all 128
candidate words through physical memory. The directed cases cover a complete
candidate write while raw beat 0 is held, a second prefetch blocked against
snapshot overwrite, final raw beat coincident with both a new P0 write grant
and a tile response, and receiver-abort drain under the real system's contract
that accepted memory writes finish (`memory.abort_i=0`). Existing raw stream
abort and invalid-address checks also pass.

At both corners mode 0 records 140 candidate-stream cycles, 106 idle candidate
cycles, and no overlapping write admissions. Mode 1 records 46, 12, and nine,
respectively, with one final-beat/new-write coincidence and one
final-beat/write-response coincidence. These are directed concurrency coverage
results: the test intentionally holds streams differently to reach each case.
They establish overlap behavior and preserved data/ownership, and do not
establish comparable system latency or a frame-rate improvement. The frozen
V79 core still serializes its eight-beat response before its next raw request.
