# V84 operation-map V2: make fixed application state implicit

V2 is an application-specific refinement of the [V1 metadata prototype](mode-map.md).
Its canonical operation array is identical for every native source, but it
avoids transmitting two facts already fixed by this profile:

- Hidden tiles always use CONST128; their positions come from the receiver's
  fixed, hash-bound mask.
- A key uses RESIDUAL on every visible tile and therefore needs no transmitted
  operation choices.

Only visible delta tiles need choices: COPY_REF versus RESIDUAL. The profile
has **7,806 visible positions**, so a packed bitset is at most **976 bytes**.
An independent parser reconstructs all 8,100 canonical operations, inserting
the 294 hidden CONST128 operations itself.

## Distinct binary profile

The header remains 20 bytes, big-endian `>4sBBBBHHHHI`, with magic `CM84`,
**version 2**, method, key flag, grouping 16, dimensions 720×480, canonical
tile count 8,100, body length and CRC32. V2's CRC covers the first **16 header
bytes plus the body**, excluding the CRC field itself. It detects accidental
changes in valid-valued header fields as well as body corruption; it is
unkeyed and does not authenticate a sender.

The fixed hidden mask SHA-256 is:

```text
e08b9861ae9a170c913c6425a5773ff42042a0abfe2fef8cd756cb505a8a8fa5
```

The encoder and parser require exactly this mask. This is local profile state,
not a transmitted mask accepted from a host. All 457 native inputs agree with
that fixed mask.

| Method | Meaning |
|---|---|
| 0: IMPLICIT_KEY | Key flag required; empty body; visible RESIDUAL, hidden CONST128 |
| 1: VISIBLE_BITS | Delta only; 7,806 choices packed MSB-first, 0=COPY, 1=RESIDUAL; exactly 976 bytes, low two final padding bits zero |
| 2: VISIBLE_RLE | Delta only; token high bit is COPY/RESIDUAL choice, low seven bits are run-length-minus-one, runs 1–128; exact visible coverage |

For a delta, choose the shorter complete bitset or RLE body; equal lengths
prefer the bitset. The full packet cap is **996 bytes**. The parser rejects V1,
unknown methods, profile or geometry changes, malformed lengths, CRC failures,
nonzero bit padding, visible-count gaps/overruns and non-implicit methods on keys.
It never calls the encoder. It accepts valid alternative delta representations
instead of requiring the shortest method.

As in V1, frame IDs, reference generations, accepted content roots and negotiated
capabilities still belong in the future complete outer envelope. The caller
can require a matching expected-key flag. This component alone cannot prove
reference correctness, valid residual coefficients or an authenticated frame.

## Native evidence

All **457 sources** round-trip to the same full canonical operation arrays as
V1. Selected methods are **20 implicit keys, 263 bitsets and 174 RLE maps**.
All 20 keys have zero-byte bodies. Every source uses fewer operation-metadata
bytes than V1 in this corpus.

| Metadata | Minimum | Median | Maximum | Total across 457 |
|---|---:|---:|---:|---:|
| V1 complete packet | 158 | 1,143 | 2,045 | 503,553 |
| V2 complete packet | **20** | **996** | **996** | **384,102** |
| Per-source reduction | 31 | 147 | 1,049 | **119,451** |

V2 reduces these metadata bytes by **23.72% versus V1**. Its bodies total
374,962 bytes versus 925,425 for a standalone 2-bit canonical map, a 59.48%
reduction in that metadata comparison. The evidence includes **28 checks** and
four exact packet-hex/SHA vectors: a key, delta, maximum-body case and a
distinct native RLE case containing a maximum-length 128-position run.
Malformed tests include V1 rejection, CRC corruption, valid-method/key header
bit flips, wrong fixed mask, key COPY representations, padding and run coverage.

## What this does and does not advance

This proves an actual bounded encoding/parser for operation metadata that uses
the application's fixed hidden geometry and key semantics. It does **not**
prove a streaming bitrate reduction: adding the map to unchanged AB38 adds
bytes. Existing adaptive/DC/AC dependencies still require decoding; a real
explicit-COPY codec needs residual reencoding or new context/partition rules.
Content/reference validation and recovery must be designed alongside that
change. No entropy-work or FPGA-clock reduction is credited to V2 here.

The parser's 8,100 returned operations are a logical bound, not a Python-object
RAM estimate or an ESP32 implementation. A hardware/firmware version needs a
packed or streaming output and finite buffering/handshake tests. Residual data,
HUD, transport, RAM ports and other decoder state remain outside this component.

## Retention and reproduction

```sh
python3 scripts/cu66-v84/prototype_mode_map_v2.py
```

The command refuses to overwrite retained results. The current source snapshot,
source/data hashes, per-frame records, tests and vectors are under
`experiments/python-gamebub-v84/mode-map-v2/`. The first research V2 run used a
body-only CRC; it passed native round trips and was then superseded by the
header-prefix-plus-body CRC before publication. Its exact source/results remain
under `historical-body-crc-v2/` with `final_selected=false`; they are historical
evidence, not the selected V2 wire definition. No V1 or entropy source changed.
The selected header/body CRC evidence was also regenerated to retain the real
RLE128 boundary vector; the previous three-vector source/results remain under
`historical-three-vectors/`. That evidence-only addition changes no encoding or
parser semantics.
