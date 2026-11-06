# V91l 8-byte row write contract

This model joins the V91l plane/tile/byte stream to the single-owner write
adapter. It proves address arithmetic and exercises protocol schedules in
Python. It is not RTL, hardware, memory-controller, timing, throughput, or
performance evidence.

## Address and coalescing rules

The canonical input remains ordered as `(plane, tile, byte_index)`, with 64
bytes per tile and row-major order inside each 8x8 tile. For each byte:

```text
x = (tile % tiles_across) * 8 + (byte_index % 8)
y = (tile // tiles_across) * 8 + (byte_index // 8)
address = plane_base + y * plane_width + x
```

The plane tuples `(base, width, height, tile_count)` are `(0,720,480,5400)`,
`(345600,360,240,1350)`, and `(432000,360,240,1350)`. The executable model
enumerates every canonical byte, proves each plane's addresses form a full
bijection onto its raster extent, and checks each 8-byte group is aligned,
contiguous, and within one epoch/fid/bank/plane/tile identity. The bound HUD
stream contributes 42,240 ordered bytes, represented by aligned contiguous
8-byte rows. A partial group or a group crossing an identity or address gap is
rejected.

| Stream | Ordered bytes | 8-byte requests |
| --- | ---: | ---: |
| Canonical | 518,400 | 64,800 |
| Receipt-bound HUD | 42,240 | 5,280 |
| Total | 560,640 | 70,080 |

Thus the structural transfer comparison is 560,640 byte beats versus 280,320
16-bit payload beats for the same 560,640 ordered bytes. The row owner stores
one 8-byte payload plus metadata: epoch/token/bank/plane/tile identity, start
address, 4-bit fill count, and 3-bit delivery index. It owns one row at a time;
there is no second payload copy. The enclosing transaction retains fid and
generation context.

## Single owner and ACK behavior

The intended interface is `cu66_row_write_hash_join_v91l` with states
`IDLE(0)`, `FILL(1)`, `OFFER(2)`, `WAIT_ACK(3)`, and `DELIVER(4)`. It has one
8-byte gather owner and no overlap. `req_data[63:0]` carries the row and
`req_bytes[3:0]` is 8. Fill requires `index % 8 == 0` at the start, then the same
epoch/fid/bank/plane/tile with increasing index and contiguous raster address;
HUD rows require aligned contiguous addresses. `fill_count[3:0]` tracks filling
and `deliver_index[2:0]` serializes the eight successful hash deliveries.

The physical lease starts only when the memory side accepts an offered row.
The owner holds that lease until an ACK matches epoch, token, bank, and address.
A wrong ACK latches failure without releasing the actual lease. A matching
successful ACK releases it and starts delivery of the eight bytes in their
original order. A matching bus-error ACK releases the lease without delivering
any hash byte.

Warm cancel or reset clears partial fill, an unaccepted offer, and any
undelivered hash bytes. If a physical row is already accepted, its lease stays
owned through cancel/reset until its matching ACK drains. It cannot be reused
or retried while outstanding. If matching ACK and kill happen on the same
edge, the lease retires and no byte is delivered. Publication waits for the
complete expected hash streams, successful ACKs, no outstanding lease, and no
candidate error.

## Service-price assumptions

The model records the supplied deterministic workload arithmetic only. FAST
prices a byte request as one payload beat plus one overhead unit and a row
request as four x16 payload beats plus one overhead unit. SLOW prices each
request as its payload beats plus a seeded overhead from two through seven
units. The resulting service-unit counts are scenario inputs to a model; they
are not measured latency, throughput, or hardware results.

## Evidence and invocation

Run `python3 experiments/python-gamebub-v91l-rows/model.py` to enumerate the
full canonical address stream, validate the HUD/canonical row groups, exercise
ACK/cancel/reset/publication schedules, and write
[`model-results.json`](../../experiments/python-gamebub-v91l-rows/model-results.json).
The output deliberately makes no RTL, implementation, or speed claim.
