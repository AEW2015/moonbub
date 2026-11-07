# V91l shared physical-service ownership contract

This note freezes the logical ownership expectations for joining the live
candidate writer and RGB reader behind one SDRAM service. The source basis is
baseline commit `298961c64ae947c01eeb55ea1b0815a3e87a3fdb`; source pinning is
fixed to that revision and the model does not compare against the moving `HEAD`.
The V91l integration order and qualified source boundaries are recorded in
[`next-integration.md`](../cu66-v91l-burst-converter/next-integration.md).

## One physical owner

The arbitration clients covered here are candidate writes and RGB reads. A
request carries its operation, physical address, payload, and that bridge's
native identity. Acceptance creates one owner. An arbiter grant by itself is
not a physical acknowledgement.

The owner cannot change while any accepted physical work remains. A response
is not produced until the accepted work drains through the qualified bridge's
drain sequence, and the owner remains assigned until caller response ACK. The
writer traverses
one `WAIT_BUSY` fence edge, then waits for an observed `ctrl_idle` in
`WAIT_IDLE`; the reader captures all eight BL8 beats, then requires two
consecutive `ctrl_idle` samples. The response identifies its request and
remains bit-for-bit stable for as long as the caller withholds acknowledgement.
The current controller source does
not provide a physical write ACK, error, or byte mask; the integrated service
must define how completion and errors are produced without presenting the
controller's command acceptance as physical completion.

A candidate logical eight-byte write can comprise four x16 word writes. The
service may accept up to that four-word group, but it must drain all accepted
words before changing owner. An RGB BL8 read is eight x16 response beats; all
eight beats must be captured, then the reader's two-idle fence must complete
before ownership changes. With both clients continuously offering work, the
abstract model uses round-robin choice.

## Cancel, reset, and identity failures

- A cancellation before physical acceptance returns an error completion and
  emits no controller commands.
- Cancellation during physical work stops issuing the unaccepted remainder,
  drains every accepted word/beat using that bridge's qualified drain sequence,
  then holds an error reply until caller acknowledgement.
- Reset while idle applies immediately. Reset during physical work is deferred
  through the same drain and error completion. Reset while a response is held
  must preserve the reply and ownership until its acknowledgement. A cold power
  reset with an accepted controller owner still requires external quiescence.
- An invalid identity may still be granted and accepted by its bridge, but it
  must return a held error response without issuing a physical command. The
  owner remains assigned until response ACK. The writer requires nonzero epoch
  and treats token as an opaque 32-bit value (zero is valid and echoed). The
  reader requires nonzero epoch and generation.

The two bridges retain their native identity forms: the writer requires a
nonzero epoch and carries an opaque 32-bit token (zero is valid and echoed),
bank and byte address; the RGB reader requires nonzero epoch and generation,
bank and byte address. The adapter must preserve each tuple, while the root
live-frame lease correlates ownership across clients. Do not create writer
generation or ticket fields that its bridge does not carry. Any future ticket
requirement beyond the writer's opaque token needs separate interface
qualification.

These are interface requirements for integration. The finite model in
[`ownership_model.py`](../../experiments/python-gamebub-v91l-shared-service/ownership_model.py)
checks directed transaction sequences for them. It does not prove that any RTL
implements the requirements. Its invalid-identity scenarios model bridge
acceptance followed by an error held through ACK, with zero controller
commands; a separate scenario verifies that writer token zero is accepted as
opaque identity and echoed unchanged.

## Workload accounting only

For the current candidate payload, 560,640 bytes correspond to 70,080 logical
eight-byte writes and 280,320 x16 write words when every logical write uses
four full-word writes. The 32,400 RGB BL8 reads correspond to 259,200 x16 read
words. Together these account for 539,520 data words per frame.

This arithmetic excludes reference and scratch traffic, hashing reads,
commands, refresh, turnaround, row misses, and finite response backpressure.
It is workload accounting only; it is neither a latency estimate nor a closed
shared-service budget. Finite logical reference/scratch service and the C++
HUD semantic endpoint remain outside this physical-controller iteration.
There is no 30-fps hardware claim or under-10-ms claim here.

## Evidence boundary

`ownership_model.py --check` compares the deterministic abstract results with
the checked-in `model-results.json`; that JSON pins source file hashes from the
fixed baseline and the check does not inspect current source hashes, branch
state or `HEAD`. The result is a logical protocol reference only. It is not
RTL simulation, equivalence or formal proof, and it does not model real SDRAM
pin service, refresh timing, or shared physical throughput. The model's
fairness and held-response assumptions must be checked against the integrated
RTL interface when that interface is available.
