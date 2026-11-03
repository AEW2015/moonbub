# Bounded stop-and-wait replay specification

This isolated Python experiment wraps the adjacent tagged bank model with a
single-request replay cache. A request must carry the current epoch and next
sequential request ID. An exact retry of the immediately preceding accepted
request returns its historical ACK without repeating the operation; a changed
retry is rejected, and any other old or future ID is rejected.

## Request validation and ACK/sequence behavior

The wrapper accepts unsigned 64-bit epochs, request IDs and integer fields,
ASCII operation names up to 16 bytes, `Token` objects with bounded integer
fields, and immutable `bytes` payloads up to **1,024 bytes**. Only the six
protocol fields (`token`, `frame_id`, `length`, `crc`, `offset`, `payload`) are
accepted. Booleans, mutable values such as `bytearray` or lists, arbitrary
objects, extra fields, oversized operation names, and oversized payloads are
rejected before the core or replay cache is accessed.

A well-formed current-epoch request with the expected ID consumes that ID even
if the core returns an operation-level failure such as `INVALID_BEGIN`,
`BAD_DATA`, or `UNKNOWN_OP`; the ACK is retained for an exact retry. Wrapper
rejections (`INVALID_REQUEST`, `REQUEST_TOO_LARGE`, `STALE_EPOCH`,
`OUT_OF_ORDER`, `REQUEST_ID_CONFLICT`) do not consume the next ID or replace the
cached ACK. Invalid request ID types/ranges raise `ValueError` without state
changes. Request validation precedes stale-epoch checking, so malformed stale
requests receive `INVALID_REQUEST` and valid stale requests receive
`STALE_EPOCH`.

The exact most recent accepted request and ACK are retained; the underlying
model's history is cleared after each operation. This bounds wrapper-owned
request storage: at most one 1,024-byte payload, six bounded fields and a
16-byte ASCII operation name. The core retains at most `capacity` data bytes in
each of its two banks. The request is single-threaded; callers must allow at
most one outstanding request and wait for its ACK before sending the next.

Python IDs do not wrap; after the maximum unsigned 64-bit ID is accepted, no
further valid ID can be supplied. Epochs are also unsigned 64-bit values and
reset requires a strictly larger epoch. Reset explicitly discards the replay
cache and all ownership; it must follow an independently verified quiesce and
drain sequence. The underlying bank model allows two concurrent receives even
though the current experimental RTL does not.

Run `python3 -m unittest -v` in this directory. Tests cover lost-ACK retries,
conflicting retries, out-of-order requests and ID expiry, reset cache
invalidation, bank reuse, operation-level failures, malformed mutable values,
oversized payloads, the exact 1,024-byte payload limit, and 5,000 sequential
operations with empty underlying replay history.

This is an executable protocol model, not production firmware, a physical drain
or CDC design, a pipelined QSPI protocol, a throughput estimate, or proof of
hardware correctness.
