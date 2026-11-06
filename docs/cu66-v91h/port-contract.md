# V91h staging-port contract

The executable abstract model is
[`staging-port-model.py`](../../experiments/python-gamebub-v91h/staging-port-model.py);
its frozen run is
[`staging-port-results.json`](../../experiments/python-gamebub-v91h/staging-port-results.json).
The RTL reference is `fpga/experiments/cu66-v91h/br88_packet_ingress_v91h.sv`.

## Staging RAM ownership and timing

The packet staging array has an 8-bit receive write port and an 8-bit
synchronous read port. Receive writes are accepted only in `RECEIVE`. Once the
whole packet has arrived, the parser fetches bytes through `FETCH_REQ` and
`FETCH_WAIT`; the scheduler does not overlap staging reads and writes. A read
request samples its addressed byte and epoch at its request edge. The registered
response is available on the following edge, where the parser checks both the
response address and epoch. Staging reads and writes use distinct physical
ports, but the current FSM serializes their use. The model asserts that
read/write overlap is excluded.

Reset or abort has priority over start in the RTL control branch. Start, reset,
and abort suppress the current local RAM response and clear the local pending
response state. A late response tagged with a different epoch cannot populate
the new transaction's registers. The staging array itself is not reset. This
local on-chip staging port is separate from the outer packed-store memory bus;
that bus's accepted request retention and physical hazard are outside this
contract.

Packet bytes remain immutable after receive completion until the transaction
finishes or is cancelled. Header and CRC validation starts only after complete
receive. The 46-byte register cache holds the 42-byte header and the trailing
four CRC bytes; the CRC fetch uses the packet tail, not the bytes immediately
after the header. Once header fields have been copied into metadata registers,
the cache is reused for one six-byte descriptor plus a seventh byte. That final
fetch reads the last stream byte for a nonempty extent and repeats the last
descriptor byte for a zero extent. `buffer_bytes` stays bounded by 46 in the
RTL; descriptor, replay, and RAW assemblies use only their needed small
prefixes.

## Assembly and backpressure

Little-endian header fields and RAW signed 16-bit values are checked with
independent byte slicing/indexing in Python. Coded replay places up to four
bytes in the high end of a 32-bit word and visits bits most-significant first;
unused low bits in the final partial word stay zero. A separate
`int.from_bytes(..., "big")` byte-slice oracle checks the word assembly,
including non-byte-aligned and partial final words. RAW fetch assembles one
two-byte little-endian pair at a time. Scenarios cover zero replay bits,
1/7/9-bit unaligned extents, 31/33/63-bit partial words, and 64 RAW pairs.

Receive valid data stays at the current packet byte until accepted. Output
payload stays fixed while the consumer is not ready. A directed check keeps a
child output word held while the staging port fetches the next word. Consumer
stalls use a deterministic seeded schedule; input and fetch stalls are also
deterministic. The model checks packet immutability after receive and requires
every accepted staged read to have one following-edge response.

## Evidence and limits

The model runs nine bounded scenarios: eight coded replay extents and one
single-block RAW packet. It records the model source SHA-256, scenario and
directed-check requested/actual counts, required event kinds versus observed
event coverage, read/write event totals, and restart counts. The implementation
uses deliberately small packet/address bounds and synthetic bytes/CRCs.

This is an abstract port and byte-assembly contract, not RTL equivalence,
cycle-accurate end-to-end timing, a codec correctness check, or a formal proof.
It does not verify full metadata/descriptor error recovery, decode arbitrary
context syntax, or model concurrent packed-store/tile ownership. The modeled
one-edge read response follows the functional RTL contract; it does not show
that synthesis infers a BRAM primitive or establish device fit, physical
latency, clock frequency, or routed timing. Those require the separate RTL
simulation and implementation evidence.
