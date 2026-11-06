# V84 finite staging credits and coefficient arrival

V83 bounded group-output ownership, but allowed all tile modes at epoch start
and did not enforce finite reference, inverse-result or coefficient staging.
V84's `credits.py` transforms the frozen V83 workload to make those assumptions
explicit. This is a Python scheduling model, not an RTL FIFO implementation.

## Admission and ownership contract

There is one sequential `entropy` resource. Each physical tile receives one
`entropy_tile` job whose duration is supplied by the caller. It waits for the
previous tile's entropy job and admission of its own output group. The tile's
map lookup waits for this mode/coefficient arrival. Thus reference reads,
inverse work and store decisions cannot use a tile mode before the modeled
front end has produced it.

Three independent FIFO credit rings reserve slots before production starts:

| Staging class | Bytes per slot | Producer reserves at | Slot released at |
|---|---:|---|---|
| Reference input | 64 | Four-BL8 reference-read start | Reconstruction finish, or COPY-ready for a COPY tile |
| Inverse result | 192 | Inverse-task start | Reconstruction finish |
| Coefficient/mode record | 128 | Entropy-task start | Inverse finish for residuals; map-lookup finish for COPY/CONST |

The signed 24-bit inverse interface is retained: 64 samples × 24 bits gives
192 bytes. Reference/inverse credits are reserved throughout production, not
only after a response arrives. Coefficient storage is conservatively retained
through inverse completion. COPY and CONST also reserve a coefficient-sized
slot before classification even though a later hardware implementation might
represent their mode more compactly.

For capacity N, producer i depends on completion of consumer i−N. All producers
are ordered by physical tile identity, and all previous-tile consumers precede
the new producer logically. The augmented graph is explicitly checked for
cycles. A stalled reconstruction can therefore backpressure inverse and
coefficient production instead of silently accumulating results in unlimited
software storage.

V83's existing group-reuse ring is unchanged. A group cannot be reused until
its physical stores, shadow map writes and any required leaf digest have
completed. Every original priced memory, map and hash operation is retained;
the wrapper adds admission/credit dependencies and entropy work, not store
elisions or a new pixel reconstruction rule. The final candidate fence also
depends explicitly on completion of the entropy stream.

## Logical storage budget

With four groups of sixteen tiles, output allocation is 4,096 bytes. Eight
reference, eight inverse and eight coefficient credits add
`8 × (64 + 192 + 128) = 3,072` bytes, for **7,168 bytes (7 KiB)** across these
four staging classes. Two of each require 4,864 bytes; 64 of each require
28,672 bytes. These are logical reservations, before RAM rounding or ports.

V83's conservative 20-KiB staging figure excluded coefficients. Including 128
coefficient bytes for each of its 64 admitted tiles makes the comparable
unrestricted-per-group reservation 28 KiB. Therefore 7 KiB versus 20 KiB is not
a like-for-like storage saving; the appropriate four-class comparison is
7 KiB versus 28 KiB, under the explicitly modeled admission contract.

The 71,547-byte g16 tree/maps budget, clone temporary, inverse working registers,
dequant staging, hashes, bounded command descriptors, transport buffers, control,
CDC and physical memory implementation are additional. The software graph still
contains all future tasks; real hardware must generate bounded streaming
control rather than store that complete graph.

## Verification scope

`scripts/cu66-v84/test_credits.py` passed **557 directed checks** across 42
scheduled cases: six synthetic histories using capacities 1, 2, 4, 8 and 64,
eight native workload records, zero-arrival controls and front-end/backpressure
cases. Tests independently bind each producer/consumer pair, inspect reuse
edges, retain V83 priced work, audit every declared timing dependency and check
all reservation high-water marks. Zero-cost, 64-credit key/delta controls match
the frozen V83 completion cycles in the tested native cases.

The module's lifetime audit measures reservations from producer start through
consumer finish, with half-open intervals so a completed slot can be reused on
the same clock. It checks capacity and reuse timing, while generic V83 timeline
auditing checks resource occupancy and declared dependencies. Directed tests
bind intended consumers; neither audit is an exhaustive proof that every
hardware dependency has been modeled.

Per-tile entropy durations are caller inputs. Native primitive counters can
inform them, but counter-to-cycle weights are conditional assumptions. No
current entropy RTL clock count, ESP32 forwarding rate, RAM-port timing,
physical 30-fps operation or under-10-ms decoder result follows from this model.
COPY-ready still moves/aliases reference data into group output with no
separately priced copy-port transfer; a real buffer/port implementation must
account for that operation.

No wire format changes here. A future explicit COPY opcode would require a new
negotiated encoding and independent parser/content checks; it cannot be treated
as permission to skip context-dependent decisions inside the existing AB38
stream without re-encoding it.
