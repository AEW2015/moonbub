# Bounded reference-tile read grant

`tile_reader_mux` preserves the frozen per-line memory protocol and adds one
optional scheduling policy: a reference turn may retain ownership across up
to four successfully retired 16-byte line reads in one aligned 64-byte tile.
`REF_LINES=1` retains the old round-robin policy. `REF_LINES=4` enables this
candidate. The current profile uses `GAP_CYCLES=8`. Only metadata and counters
are added; no payload buffer is added.

A tile reservation starts only with a legal 64-byte-aligned reference line.
A legal 16-byte line that does not start a tile is serviced as a standalone
turn. A continuation must have the captured epoch/bank, the next contiguous
16-byte address within the same tile, and the next nonzero physical ticket.
The 32-bit ticket wraps UINT32_MAX to one. Full 64-bit outer frame identity
remains in the unchanged reference tile reader.

Each line remains owned until its matching response is acknowledged and the
actual lower bridge is idle with no held response. Successful line ACKs consume
the four-line credit. Wrong-tag replies cannot consume the owned credit or
release the owner. Error, owned reset/cancel, changed continuation metadata,
or exhausted credit ends the reservation after accepted physical work drains.
An already held response remains unchanged; an unrelated client's cancellation
cannot cancel the owner.

If the next reference offer is absent, the reservation waits at most eight
sampled clocks. A mismatched offer is blocked combinationally and causes a
yield; it must take a fresh round-robin turn. A matching offered request held
behind lower-port backpressure retains its request credit. The wait bound is
for a missing next offer, not for an arbitrary lower-port/response stall.
After the four-line turn, a continuously eligible display receives the next
reader-arbiter opportunity. Fairness is bounded in reference credits under
responsive clients; no wall-time bound is claimed while a response is held.

Yield reason receipts use `0=normal/credit`, `1=owned cancel/reset`, `2=error`,
`3=mismatch`, and `4=missing-offer timeout`. Counters report groups started,
accepted continuations, yields and each terminal reason. `batch_display_wait`
start/end receipts measure actual eligible display clocks without request
ready, including lower-port stalls; they are observational metrics rather
than a latency guarantee. Wait maxima reset at cold reset.

The wrapper `tile_grant_shared_timed` changes only the reader mux in the frozen
scratch/reference/physical-controller wrapper. Candidate writes, scratch
arbitration, reference assembly, timed memory and the SDRAM controller remain
unchanged. This wrapper includes a pin model and delayed clock and is a
simulation top, not a board-ready design.

## Directed verification

`tile_mux_unit.sv` instantiates the unchanged old mux beside the new mux when
REF_LINES=1, asserting cycle-by-cycle equality of every original ordinary
output. Both instances emit identical old `mux_*` receipts: their exact pair
is intentionally retained and must be normalized only after verifying that
both copies are identical. `batch_*` receipts belong only to the new mux.
The four-line unit has one ordinary mux receipt stream.

The abstract lower memory returns deterministic full 128-bit payloads with
owned response backpressure and explicit post-ACK busy drain. Tests cover:

- Four credits followed by a waiting display and a fifth reference line.
- Ticket rollover, short producer gaps and the eight-clock absent-offer bound.
- Epoch, ticket, bank, address-step and tile-boundary mismatches.
- Legal non-tile-start standalone requests, the final legal tile boundary and
  invalid initial epoch/ticket/bank/address metadata without reservation.
- Held and wrong-tag replies, unrelated cancellation and late owned cancel.
- Accepted reset drain, error termination, offer withdrawal and lower stalls.

The selected strict Verilator runs pass 1,022 control and 1,034 candidate check
entries. These are directed check entries, not exhaustive coverage. Unit
memory is abstract; actual controller/tAC behavior is checked by the separate
native key/delta campaign with the unchanged timed physical memory path.
Cold-reset boundaries in this unit are identified by its verified
`cold_owner_idle` checks. No hardware, routed timing, fixed source cadence,
whole-device fit or complete validated under-10-ms claim follows.

```sh
python3 fpga/experiments/cu66-v91l-tile-grant/generate_wrappers.py
python3 scripts/cu66-v91l-tile-grant/run.py
```
