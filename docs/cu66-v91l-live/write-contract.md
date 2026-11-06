# V91l live producer and write-ACK contract

This note defines the next integration boundary after frozen V91l. V91l already
checks the CS88 header commitments, actual ordered canonical bytes, the native
HUD semantic receipt and stream, and the content root/frame seal. Its bank gate
atomically updates accepted metadata only after validation, matching producer
completion and drained writes. The V91k reconstruction contract defines actual
canonical pixels from the frozen parser/coefficients and accepted reference.
This join connects those contracts; it does not change their reference data or
claim evidence from RTL that has not yet been run.

## Live canonical stream

The V91l validator consumes 518,400 bytes as `plane, tile, byte-index`:

- Y: 5,400 8x8 tiles, tile IDs 0 through 5,399.
- Cb: 1,350 8x8 tiles, tile IDs 0 through 1,349.
- Cr: 1,350 8x8 tiles, tile IDs 0 through 1,349.
- Within each tile, byte indices run from 0 through 63 in row-major tile
  order. Each token carries the current frame epoch and its exact tuple.

The token order is tile-major, not raster row-major. The write address is
computed from the tuple, so writes land in raster memory without reordering the
hash input:

```text
x = (tile % tiles_across) * 8 + (index % 8)
y = (tile // tiles_across) * 8 + (index // 8)
address = plane_base + y * plane_width + x
```

`plane_width` is 720 for Y and 360 for Cb/Cr; bases are 0, 345600 and 432000
bytes. The Python model checks stream ordering and address mapping at plane and
tile edges. A raster-order producer must tile/reorder before it can satisfy the
V91l validator's exact `(plane,tile,index)` handshake.

## One-byte write ownership and ACK

The planned adapter has one owned byte at a time. It holds the byte, tuple,
transaction context and address while the downstream memory request is stalled.
Once accepted by memory, it retains a physical-write lease until the response
matches **epoch, token, bank and address**. The wrapper owns `fid` and
`generation` as transaction context; those are not ACK match fields in the
adapter interface. Only a matching successful ACK may retire the lease and
forward that exact byte to the V91l hash input. A matching bus-error ACK retires
the physical lease but must not forward the byte. A wrong ACK latches a failure
and cannot retire the outstanding lease. A later matching ACK is still needed
to drain/release the lease. This prevents a stale or misrouted response from
being counted as completion for a current candidate write.

Abort and warm reset stop accepting new producer tokens and discard bytes that
have not acquired the physical write lease. An already accepted physical write
remains owned until a matching response drains it. Candidate bank ownership
therefore remains held across abort/reset while any accepted write is pending;
retry cannot reuse that bank early. Cold power-on reset still requires external
quiescence of the write owner. Accepted reference metadata survives a warm
abort/reset. Failed candidates do not update accepted root, HUD digest, seal,
generation, or reference-bank pointer.

The HUD byte stream shares the adapter after canonical bytes. Its 42,240 bytes
retain V91l's receipt-bound `(epoch,fid,refid,generation)` identity and stream
order. The native decoder/receipt remains the V91l software endpoint; this join
does not claim RTL HUD decoding.

## Required validation and publication order

A candidate may commit only when all of these are true for the same epoch and
candidate bank:

1. V91k producer output completed in exact plane/tile/index order. Key frames
   use the key predictor; deltas use the currently accepted reference snapshot.
2. Every canonical write received a matching successful ACK before its byte
   entered the V91l root hash. The HUD bytes likewise follow the actual bound
   native semantic receipt and successful write/ACK path.
3. V91l consumed exactly 518,400 canonical bytes and 42,240 HUD bytes, checked
   the computed root and semantic-HUD hash, then matched the frame seal.
4. Producer completion is asserted with the active epoch, no producer/decoder,
   memory, ACK, root, HUD or seal error occurred, and no physical write lease
   remains outstanding.
5. The existing bank control accepts one atomic commit edge. Accepted metadata
   and reference-bank selection move together; a failed or late-failing frame
   leaves them unchanged.
6. Presentation remains pending until both `vblank` and `scanout_drained` are
   true. Acceptance alone must not move the front-bank selection.

Backpressure applies end to end: the producer cannot advance a byte until the
adapter can own it, and the validator cannot hash it until its memory write has
succeeded. Producer `done` is not a substitute for outstanding ACK drain. The
Python model includes wrong-epoch producer completion, wrong-epoch ACK, reset
with a write pending, late failure, commit-before-drain, vblank hold and
scanout-drain hold schedules.

## Initial evidence scope

The independent model at
[`model.py`](../../experiments/python-gamebub-v91l-live/model.py) checks this
protocol contract and writes compact results to
[`model-results.json`](../../experiments/python-gamebub-v91l-live/model-results.json).
It does not run RTL, reconstruct image payloads, prove memory behavior, or
measure speed. The initial live RTL cohort should be the actual c0f0 key and
c0f1 delta chain. c0f1 must consume the bank/reference metadata accepted for
c0f0. The other V91l primary frames are not a contiguous producer chain without
their intermediate live decoded frames, so they must not be presented as live
coverage by replaying only their endpoints.

Promotion evidence should retain self-checking directed cases for producer
backpressure, token order and address, stale/wrong ACK, bus error, ACK drain
after abort/reset, late canonical/HUD/seal failures, clean retry, metadata
preservation, and front-bank hold/release. These are design requirements until
captured from the integrated RTL runner; the Python model is not that evidence.
