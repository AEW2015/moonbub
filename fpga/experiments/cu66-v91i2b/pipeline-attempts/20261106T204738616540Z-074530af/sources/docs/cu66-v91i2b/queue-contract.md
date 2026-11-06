# V91i2b bounded registered-read refill queue

V91i2b models the packet-byte refill between the unchanged V91i2a admission
fork and its frozen V91h child. Compile-time mode 0 preserves V91i2a's
REQ/WAIT/SEND sequencing. Mode 1 adds two physical FIFO byte slots and a
registered read-response owner. A response reserves FIFO capacity when its
read request is accepted, so the total queued plus pending ownership never
exceeds two bytes.

## Byte ownership

For each chunk, the source address is chunk_offset + issued_count. A read
request is accepted only while the chunk is active, the address is inside the
chunk, and queued_count + pending_owner - pop < 2. The read request captures
the address, frame epoch, and final-byte bit. Its byte response arrives exactly
one edge later. The pending owner moves into the FIFO only after response
address and epoch match the captured request. There is no response-to-child
bypass.

The child pops only when the FIFO is nonempty and child_ready is asserted.
The head byte, address, epoch, and last remain stable while the child is not
ready. Pop advances the head and sent count; response push advances the tail;
request issue advances the source address. Same-edge pop, old-response push,
and next request issue may all occur when the reservation formula allows it.
The byte, address, frame epoch, child epoch, and last travel together.

At chunk completion, every byte has been issued, responded, and popped in
order, and the queue and pending owner are empty. The final emitted byte alone
has last=1. Reset, accepted-frame start, cancel, and refill failure take
priority over local queue operations and clear queued and pending owners.
External accepted scratch writes retain their original owner through ACK; that
drain path is outside this refill model.

## Independent model

[queue_model.py](../../experiments/python-gamebub-v91i2b/queue_model.py)
reads all 11 pinned V91i2 rows, verifies the case TSV and packet/span hashes,
and models the mode-0 and mode-1 byte transfer. It reuses exact bytes and
absolute offsets from existing vectors. Rows rejected before BR88 refill and
the all-COPY zero-residual row issue no read. Five admitted all-BR88 rows
provide 15 chunks and 76,087 byte transfers.

The deterministic synthetic child-ready schedule forces initial stalls and
repeated backpressure. The model checks exact output bytes, source addresses,
frame and child epochs, one last byte per chunk, request/response/pop
conservation, no overread, total ownership bound, and head stability under
stall. It exhausts 2,560 small symbolic traces over payload lengths 0 through
4 and all 8-bit ready schedules. Directed traces cover a full stalled queue,
simultaneous pop/push with a new request, cancellation at three ownership
points, reset, refill failure, and replacement with new epochs.

The generated
[queue-results.json](../../experiments/python-gamebub-v91i2b/queue-results.json)
records source pins, per-chunk byte hashes, queue high-water marks, and modeled
cycle counts. Both modes emitted exactly the same 76,087 bytes as the retained
spans. Mode 1's maximum total ownership and FIFO occupancy were both two.
Its aggregate model cycle count was 104,724 versus 279,044 for mode 0 under the
same deterministic ready schedules. These are abstract cycle-step counts for
this Python model only; the schedule is not measured service, and the result
does not establish RTL correctness, hardware throughput, frequency, or
30-fps performance.

Reproduce the artifact with:

```sh
python3 experiments/python-gamebub-v91i2b/queue_model.py
```
