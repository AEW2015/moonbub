# V114 restartable residual-chunk prototype

The [selected study](../../experiments/python-gamebub-v114/syntax/results.json)
runs a new Python encoder, an independent Python reader, and a native C++
container reader using the unchanged BR88 codec. It passes 48 real-data
configurations (six frozen CS88 packets × two container versions × four chunk
sizes), eight sparse/raw boundary cases, 784 malformed-input rejection checks
and 392 clean retries. Both compressed and raw BR88 forms execute. Every
Python-produced BR88 chunk equals the native encoder's bytes; both container
readers reconstruct the exact original coefficient arrays.

These are **packed residual-block chunks**, not image-row partitions. COPY and
CONST tiles are absent from that packed order. A future parent must map the
chunk ordinal through its actual operation map and bind the frame, epoch,
generation, plane and output ownership. No pixel, reference-generation, C2/HUD
seal or publication round trip is implemented by this experiment.

The standalone container applies a generic 5,400-block bound to every plane; it
does not itself enforce the 720×480 chroma-plane bound of 1,350 blocks or match
the admitted residual-operation map. Those checks belong in the future parent.
Empty coefficient planes are rejected here; omission/descriptor semantics for
an all-COPY or all-CONST plane also need a parent packet contract.

## Two explicit experimental versions

`SR14` is a research container, not an accepted production codec identifier.
The header is big-endian `magic[4], version:u8, plane:u8, chunks:u16,
blocks:u32`. A big-endian CRC32 closes the entire container. Chunk lengths,
ordering, exact closure, coefficient geometry and inner BR88 CRCs are checked.

- Version 1 has a 16-byte directory entry: first packed block, block count,
  byte offset and payload length, all u32. Each payload is a complete BR88 v1
  packet, independently restartable.
- Version 2 has a six-byte entry: block count:u16, BR88 raw flag:u8, zero
  reserved:u8, payload length:u16. Block and byte positions are implicit prefix
  sums. It omits BR88's constant 14-byte prefix and four redundant stream
  length fields. Those lengths are recovered from each stream's bounded bit
  count; raw length follows from the block count. The retained BR88 CRC is
  verified against the exactly reconstructed original header and payload.

Version 2 saves **40 bytes per chunk** relative to version 1: ten directory
bytes and 30 payload-header bytes. It changes no coefficient value, Rice
algorithm, transform or quantizer. The receiver needs a directory-prefix scan
or bounded descriptor cache before independent scheduling; those costs are
not free FPGA ports or an implemented dispatcher.

## Measured bytes and cap pressure

The largest frozen frame is `actual_031`, originally 47,960 bytes. The table
projects replacing its BR88 payloads with these containers while retaining the
existing outer directory size. It is not a constructed/decoded new CS88 parent.
Actual negotiation or parent-header changes could consume additional bytes.

| Blocks per chunk | Version 1 projected frame | Version 2 projected frame | Version 2 fits 49,152? |
| --- | ---: | ---: | --- |
| 32 | 62,510 | 54,790 | No |
| 64 | 54,929 | 51,049 | No |
| 128 | 51,023 | 49,063 | Yes, only 89 bytes spare |
| 256 | 49,080 | 48,080 | Yes, 1,072 bytes spare |

All six fixtures fit the projected cap with compact 128- or 256-block chunks.
That small corpus does not establish a robust rate-control margin. Choose
chunking/fallback before transmitting a frame; an oversize rejection must not
advance the committed reference or quantizer cache. The general timing
candidate retains the frozen CS88 q16/all-BR88 wire profile.

The report also balances actual coded bit counts over hypothetical 1/2/4 lanes.
This is a work ledger, not cycles, measured speedup, physical fit or decoder
latency. Parsing, CRC, ordered retirement, memory arbitration, reconstruction,
validation and display still need implementation and timing evidence. Spare
DSPs do not provide those services. No Pareto improvement in full hardware
throughput has been established, so this syntax is not adopted for hardware.

## Reproduction and retained attempts

```sh
python3 scripts/cu66-v114/syntax/run.py --run
```

Use a Root heavy-job grant: two CPUs, 8 GiB RAM with the combined RAM+swap
ceiling also 8 GiB, no network, a 600-second worker watchdog and host pressure
gates. The image content ID, native source/binary hash, source snapshots,
strict compiler log, metrics CSV, worker output and host completion are pinned.
The first attempt completed the codec checks but failed its summary write to
a read-only mount; its nonzero host completion is retained. The runner now
writes its selection from the host. Later full executions, including the
compact format and raw/sparse checks, have normal exit code zero. Only the
selected final source/receipt pair describes the current study.

A separate [native packetizer study](../../experiments/python-gamebub-v114/syntax-native/results.json)
executes a C++ encoder for the **entire** SR14 container, including its directory
and checksums. All 48 real configurations and eight sparse/raw cases match the
Python packet bytes exactly; coefficient round trips and the 784 negative checks
also pass. Reproduce with `python3 scripts/cu66-v114/syntax/run_native.py --run`
under the same heavy-job grant and resource gates. This closes native container
serialization parity; it does not add a Sunshine capture hook, ESP32 transport,
FPGA parser or accepted production format.
