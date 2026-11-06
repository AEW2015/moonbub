# V91i2b bounded registered-read refill queue

V91i2b models the packet-byte refill between the unchanged V91i2a admission
fork and its frozen V91h child. Compile-time mode 0 preserves V91i2a's
REQ/WAIT/SEND sequencing. Mode 1 adds two physical FIFO byte slots and a
registered read-response owner. A response reserves FIFO capacity when its
read request is accepted, so at most two byte-valid owners exist across the
FIFO and pending response. This is an ownership bound, not a claim that only
two physical byte-storage elements exist in the complete memory path.

## Byte ownership

The caller prevalidates chunk offset and length, including 32-bit wrap, before
starting refill. For each chunk, the source address is chunk_offset +
issued_count. A read request is accepted only while the chunk is active,
issued_count is below the validated length, and queued_count + pending_owner -
pop < 2. The read request captures the address and frame epoch. Its byte
response arrives exactly one edge later. The pending owner moves into the FIFO
only after response address and epoch match the captured request. There is no
response-to-child bypass.

The child pops only when the FIFO is nonempty and child_ready is asserted.
The physical FIFO stores byte data and last. The pending response owner stores
the request address and frame epoch. Queued address/order follow from the
immutable chunk base and the issued/sent counters; child epoch is maintained
by the parent wrapper and is not a FIFO or helper-port tag. While the child is
not ready, the physical head byte and last remain stable. Pop advances the
head and sent count; response push advances the tail; request issue advances
the source address. Same-edge pop, old-response push, and next request issue
may all occur when the reservation formula allows it. The Python model carries
address, byte, last, frame epoch, and child epoch together as logical ownership
metadata for checking order; that tuple does not describe per-entry RTL
registers.

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
