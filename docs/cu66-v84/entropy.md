# V84 entropy primitive observations and arrival ordering

V84 exports **457 complete native sources / 1,371 coefficient planes** from the
original CU66 packets. A new native observer executes the four AB38 arithmetic
contexts in the interleaved order used by the frozen RTL: preload all four
contexts, prefetch one event from each AC band, decode a tile's DC value, consume
its AC events and fetch the next event, then emit that tile. It does not charge
an entire plane's band-major bulk decode before every tile, and does not assume
that COPY eligibility is available at time zero.

This observer counts primitive work. **It is not a measured clock trace or a
cycle-accurate RTL model.** The Python scheduling study chooses explicit costs
for these operations. It still needs true entropy/dequant arrival traces and
bounded-input backpressure before claiming target performance.

## Native correctness evidence

Every new interleaved coefficient array equals the frozen native bulk AB38
decoder's array exactly. Separately, the original complete native decoder
validates the packet SHA, canonical planes SHA, semantic HUD SHA and displayed
RGB565 SHA against the original fixture index. The Python collector compares
each identity/digest and all **3,701,700 zero-coefficient mask bits** with V82's
retained native data. Its independent retained-data verifier repeats those
mask/digest checks and checks the operation-count invariants.

There are **2,216,647 safe visible COPY tiles** across the delta sources. Their
classification is unchanged. The native corpus exercises dispatch 5 and 6 in
all three planes; all observed payloads use compressed AB38. A raw coefficient
fallback is implemented in the observer but absent from these 457 inputs, so
the evidence does not qualify that raw path.

## Fields and accounting

`experiments/python-gamebub-v84/entropy/data.py` exposes `iter_frames()`. A frame
contains native identity and digest metadata, the original `zero_mask` string,
plane dispatch/length metadata, and `tile_work`, exactly 8,100 dictionaries in
Y/Cb/Cr canonical tile order. Its fields are:

| Field | Counted operation |
|---|---|
| `decisions` | Arithmetic binary decisions |
| `renorm` | Arithmetic interval renormalization shifts |
| `stream_bytes` | Compressed bitstream byte-cache fills, with a separate cache for each context |
| `rice_values` | Decoded Rice values, DC or AC run/level |
| `events` | Decoded AC nonzero events, including lookahead |
| `raw_bytes` | Raw coefficient bytes; zero in this corpus |
| `header_bytes` | Extra parameter/padding-check fetches after the CRC scan |
| `crc_bytes` | Initial complete AB38 byte scan including its CRC trailer |
| `emits` | One canonical tile output, including hidden CONST expansion |
| `raw_bits` | All arithmetic raw bit reads, including preload and termination |
| `prob_init` | Initial probability-context entries, 352 per compressed plane |

The RTL captures its 42-byte AB38 header during `CRC_READ`; this is not counted
as an extra header fetch. It separately reads six parameter bytes and one pad
byte per stream, including when the bit count is byte aligned: **28 additional
fetches per compressed plane**. All four contexts preload 16 bits; each
finishes with two termination bits. Thus each compressed plane has
`raw_bits = renorm + 72`, and `rice_values = encoded_tiles + 2*events`.

Plane initialization, CRC scanning and initial AC lookahead are charged to the
first encoded tile. Work for fetching an AC event beyond the current tile is
charged to the tile that performs that necessary lookahead. A compact dispatch-6
hidden tile has zero entropy work and one canonical expansion emit. These are
explicit attribution conventions, not independent jobs that may all be removed.

Totals across the native corpus are:

| Primitive | Total |
|---|---:|
| Arithmetic decisions | 43,436,569 |
| Renormalization shifts | 35,844,140 |
| Compressed stream byte fills | 4,495,595 |
| Rice values | 13,671,373 |
| AC events | 5,042,343 |
| AB38 CRC scan bytes | 4,591,565 |
| Canonical tile emits | 3,701,700 |

The compressed retained trace is **7,366,109 bytes**. The loader verifies its
compressed SHA before use and raw SHA/record count at complete exhaustion.
Consumers that read only a prefix cannot claim that the final raw/count check
has executed.

## Why explicit COPY needs a new profile

A decoded all-zero tile can avoid inverse/reconstruction work, but the existing
AB38 stream must still be decoded to establish that property. Its adaptive
probability contexts, DC predictor and AC lookahead are shared across tiles.
Deleting the current tile's attributed work is not a valid optimization of the
unchanged byte stream. Initialization or a future AC event may also have been
attributed to a tile later classified COPY.

A future application-specific explicit COPY opcode can define reference-copy
semantics directly, with content/reference validation and capability negotiation.
It requires a host encoder, a defined envelope, an independent receiver and new
rate/quality/error tests. This primitive trace does not implement that codec and
does not predict its compressed size by subtracting attributed COPY work.

## Reproduction and retained attempts

The original data collection command is:

```sh
python3 scripts/cu66-v84/collect_entropy.py
```

It deliberately refuses to overwrite an existing retained `index.json`.
Compilation uses the existing `gamebub-cu66-v69-build` container, a unique
`/build/v84-entropy-*` binary, `g++ -std=c++17 -O2 -Wall -Wextra -Werror`, and no
container/package changes. Command arrays, compiler version, raw logs, binary
and source snapshots are retained per attempt. The first attempt failed three
misleading-indentation warnings promoted to errors; formatting-only fixes
produced the successful attempt `20261106T061440583775Z`. No failed data was
published as the successful corpus.

Verify retained data without rerunning compilation:

```sh
python3 experiments/python-gamebub-v84/entropy/verify.py
```

The verifier's PASS covers retained native work/count consistency and source
integrity. It is not FPGA timing, packet-ingress throughput, physical memory
arbitration, ESP32 execution, or sustained 30-fps qualification.
