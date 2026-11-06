# V81 tagged 128-bit reference fill

V81 changes the reference fill response from eight accepted x16 words to one
held 128-bit block. It preserves the V80 decoder-facing interface, two 512-bit
slots, monotonic epoch generation, immutable reference-bank lease and
candidate-write completion authentication. Canonical tile ordering, encoded
packets, hidden-tile profile, SDRAM controller, word bridge, CPU HUD transfers
and LCD arbitration are unchanged.

## Request, block and ownership contract

`cu81_reference_prefetch` issues the same four BL8 addresses per tile. Alongside
each request it supplies generation, reference bank, plane, tile index and block
number. `cu81_memory_system` captures that complete identity on the accepted
request, captures the bridge's full 128-bit snapshot, releases its physical P0
command owner, then holds the data, identity and error stable until acceptance.
The saved block and a concurrent candidate write have independent ownership;
a block's acceptance never clears a newer write owner. A second prefetch cannot
overwrite the saved block before it drains. HUD and LCD service remain through
the frozen word bridge/controller.

The cache authenticates the returned generation, bank, plane, index and block
against the pending slot and accepted request. Data bits `[16*i+:16]` contain
word `i` of the old x16 stream. It updates exactly one 128-bit slice once per
successful block, and publishes FULL only after the fourth successful block.
An error or tag mismatch consumes the accepted response, faults the epoch and
never publishes its data as a successful reference tile.

Abort blocks new requests and lookups immediately. An accepted physical command
and held response retain the lease until consumed; a missing response retains
ownership rather than synthesizing success. A block accepted on the abort edge
is drained once without committing its payload. As in V79/V80, an aborted epoch
pulses both `epoch_done` and `epoch_aborted`. Reset is a joint cache/backend reset,
not an abort substitute.

`cu81_reference_path` retains the V80 two-entry served ledger and candidate
completion shim. Only a completion authenticated against an admitted candidate
write can translate its bank into the captured immutable reference bank and
retire a slot. Accepted lookups canceled by abort receive one held exact-identity
error so the receiver can drain its own token. Existing hidden retirement rules
continue to apply to 294 coordinates.

The diagnostic `prefetch_read_beats` increments by eight for each consumed
128-bit response. It counts equivalent x16 words, not eight new response
handshakes. Physical SDRAM commands/words must be measured from the actual
controller/model, separately from this logical counter. Component synthetic
backends are explicitly distinguished from actual memory-model tests.

## Instrumentation

The core exposes `block_commit` and `block_commit_address`; commit excludes
abort, drain and fault/error responses. The memory exposes internal
`snapshot_valid`, `snapshot_address` and captured `owned_generation`,
`owned_bank`, `owned_plane`, `owned_index`, `owned_block`. Snapshot means the
accepted bridge response, before the saved block is consumed. Raw request,
snapshot, successful block commit, first-offered decoder lookup and actual
backend write completion are separate events in the system experiment. They
must not be substituted for one another when attributing latency.

## Component evidence

Run:

```sh
python3 scripts/cu66-v81/run_components.py --case all
```

The runner uses the established Verilator 5.020 behavioral backend in
`gamebub-cu66-v69-build`, one compiler job and unique `/build/v81-components-*`
directories. Each attempt retains its exact mutable and frozen source bytes,
SHA-256 pins, command arguments, bounded timeout, log digest and result. The
pointer [`component-results.json`](../../fpga/experiments/cu66-v81/component-results.json)
binds the latest completed attempt; old attempts are not overwritten.

The final supplemental attempt is
[`20261106T040243383900Z-2bf0a5a5`](../../fpga/experiments/cu66-v81/component-attempts/20261106T040243383900Z-2bf0a5a5/results.json),
status `PASS_WIDEFILL_COMPONENTS`:

- Direct core: four groups. One epoch checks all 8,100 full 512-bit payloads and
  the complete 32,400-address block walk under deterministic request/response
  backpressure, including coordinates hidden by the wrapper profile. A separate
  epoch retires all 8,100 tiles as unused without lookups. The two-slot bound,
  held reference payload/identity, stale/wrong lookup and retirement identities,
  early unused retirement and simultaneous lookup/unused priority are checked.
- Decoder wrapper: nine groups. Its full replay checks 7,806 visible payloads,
  294 unused retirements, 32,400 logical blocks and 259,200 equivalent x16 words.
  It also checks the two-entry lookahead ledger, held cancellation, invalid
  candidate requests, all four bad candidate-completion fields, physical-write
  cancellation, fault-clear/key bypass/fresh-delta recovery, six block error/tag
  cases, and abort coincident with accepted block response. Missing-response
  tests retain ownership before delivery resumes.
- Actual SDRAM model at `tAC=2 ns` and `7 ns`: identical 21 physical prefetch,
  24 physical write, one HUD and one LCD command. There are 176 equivalent
  x16 response positions: 168 valid payload words compared (including 128
  candidate words read back through the same physical path), plus eight error
  positions in the invalid-address response. HUD and LCD payload checks are
  additional. The held
  128-bit payload and all tags survive delayed acceptance, candidate-write
  service, HUD and LCD service, and a blocked second prefetch. Directed final
  response/new-write grant and final response/write completion coincidences
  each occur once. Eight candidate-write accepts happen while the old response
  is held. Invalid address returns an error without a physical command.

These component checks are functional evidence, not a frame-latency comparison,
FPGA fit/timing/CDC result, live ESP32 transport test or physical 30-fps proof.
End-to-end claims require the actual compressed decoder, canonical/HUD fences
and continuous native display campaign owned by the main system experiment.

## Retained failed attempts

Two first wrapper attempts,
`20261106T035727056416Z-797061d2` and
`20261106T035757995133Z-7b758500`, timed out after one retirement because a copied
component helper changed lookup identity then checked stale combinational
`ready` before evaluating it. With the faster wide fill, the next tile could
already be FULL: its first wait tick accepted the lookup, then the helper
waited for ready while the reference response was held. Evaluating combinational
logic before checking the predicate fixes the stimulus race without changing
production RTL or weakening a handshake check.

`20261106T035829127984Z-eb57da6b` passed the wrapper but failed memory-test compile
on missing spaces between a hexadecimal literal and ternary `?`.
`20261106T035904247921Z-8978f058` passed the wrapper but failed strict memory-test
lint on two unsized division operands and an unused seed half. Explicit widths
and a stimulus seed range check corrected those verification-only errors.

`20261106T035926785699Z-98f0727b` then passed the nine wrapper groups and both
actual-memory corners. A subsequent supplemental attempt, `20261106T040101204047Z-9d3d5acc`, added the
direct-core all-payload/all-unused suite and repeated the wrapper and memory
checks. The final attempt strengthens both coincidence checks to compare all
eight words and all response tags, then repeats the complete component suite. All
source snapshots and failure logs remain retained. Production SV is unchanged
between the initial and final component attempts.
