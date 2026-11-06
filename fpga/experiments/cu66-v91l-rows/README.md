# Eight-byte tile-row candidate-write experiment

`cs88_rows_v91l.sv` is generated from the frozen live wrapper. Static
`ROW_WRITES=0` uses the unchanged byte adapter, with its eight-bit request
normalized to a 64-bit bus and `candidate_req_bytes=1`. Static `ROW_WRITES=1`
uses `cu66_row_write_hash_join_v91l` with eight payload bytes and
`candidate_req_bytes=8`. Parser, entropy, inverse transform, reconstruction,
C2/HUD/seal hashing and publication implementations remain unchanged.

The coalescer has exactly one 64-bit payload register. It gathers eight
contiguous bytes from one canonical tile row, or eight contiguous semantic HUD
bytes, then owns one external request until its matching epoch/token/bank/address
ACK. Only successful acknowledgment permits serial delivery of those bytes to
hashing in their original order. No new row can be collected while the old row
is offered, awaiting acknowledgment or being delivered. Canonical metadata must
retain the same plane/tile and increment byte index; HUD metadata preserves the
first input's fixed fields (zeros in the frozen wrapper). The final stream marker
is retained only on the eighth input and appears only on the eighth output.

States are IDLE=0, FILL=1, OFFER=2, WAIT_ACK=3, DELIVER=4. `fill_count` and
`deliver_index` expose bounded ownership for verification. Counters count inputs,
outputs and drops in bytes, and requests/ACKs in eight-byte rows. Error 0x83
rejects an invalid first byte (including zero epoch, unaligned address/index or
early last); 0x84 rejects an invalid continuation. Error 0x81 poisons but retains
a wrong-ACK lease until the matching response; 0x82 retires a matching bus-error
request and suppresses hash output. Warm reset/abort discard partial/local bytes
but preserve an accepted request until its matching ACK drains. Cold power-on
reset requires external quiescence; tokens increment across warm reset.

## Fair declared service and physical scope

The comparison explicitly charges x16 payload transfers: one data beat per byte
control write, four beats per eight-byte row. FAST adds one response-overhead
cycle per accepted transaction; SLOW adds a seeded overhead of two through seven
cycles. These formulas are identical for both widths. Request acceptance,
scratch/reference service and hash backpressure remain finite. Seeded stall
rules are shared, not necessarily the same absolute stall trace as work schedules
differ. Only candidate writes receive this x16 payload pricing. Frozen 64-byte
reference and 128-bit scratch transactions remain separate logical services;
the experiment does not account for total physical x16 memory traffic. The byte control under these rules is a new control measurement; old
one-cycle-FAST response counts are historical evidence, not its comparison.

This is a logical eight-byte service model, not a physical SDRAM command bridge.
The current `fpga/rtl/moonshine_sdram.sv` uses mode `13'h233` (BL8, CAS3,
write-single) and 16-bit word writes. A physical row bridge must either charge
four single-word commands and their waits/refresh/arbitration, or implement and
qualify appropriate burst-write support. Four priced x16 payload beats do not
establish that one existing-controller command writes the row. No physical
controller, mapped frequency, full shared memory/display service or target
30-fps/under-10-ms result is claimed.

## Live verification and receipts

`tb_compare.cpp` is generated from the frozen live bench, retaining its exact
coefficient/transform/canonical scoreboards and accepted-bank/qcache history.
Each static binary runs the c0/f0 key and c0/f1 delta under FAST/SLOW service,
checks all actual candidate writes, all 1,025 RTL SHA jobs per frame, publication
and retained recovery cases. A matching bus error deliberately changes a prefix
of the provisional write (four row bytes or one control byte); the accepted
key bank remains byte-exact, no failed bytes enter hashing, and retry retains
proper ownership. This does not assume a failed write had no side effects.

Nominal bus receipts are fixed 32-byte little-endian records with Python format
`<BBBBIIIIQI`: kind (0=request, 1=matching ACK, 2=actual hash byte), profile,
bank, byte count, fid, epoch, token, address, 64-bit little-endian payload value,
and cycle. Hash bytes have length one and token zero. Nominal request/ACK/hash
streams can be replayed independently to prove byte-address and ordering parity.
Directed failures run with detailed nominal tracing disabled; their evidence is
pinned self-checking RTL/C++ assertions and named verdict entries, not independent
negative bus replay. Actual output TSVs contain canonical output, full accepted
canonical+HUD banks and captured qcache vectors for each nominal frame/profile.

HUD semantic decoding remains native C++ before timed RTL start. Its transfer,
write acknowledgment and hash are timed in RTL. Header preparation, qcache
preload, RGB conversion, HUD overlay, ESP32 and shared scanout remain separately
reported or excluded. Reproduction and audited totals belong in the experiment's
higher-level results documentation.
