# V91l reference tile reader traffic contract

`reference_model.py` derives a read stream from the retained V91i2 BR88
operation tables and checks it against the original V91l canonical tile
vectors. Run `python3 experiments/python-gamebub-v91l-reference-reader/reference_model.py`
to regenerate the frozen result, or pass `--check` for a deterministic check.
The model pins baseline `380539d99164cc88b1b92b2620fcaca57ef2216c`, the
validation vector archive, actual operation tables, source RTL rules, and the
existing V91l packet-vector generator. It does not inspect Git HEAD at runtime.

## Tile request rule

The operation table uses `0=COPY`, `1=CONST/hidden`, and `2=RESIDUAL`. The
V91k `safe_hidden(plane,tile)` source rule marks 294 of 8,100 tiles as hidden;
these must be CONST and have no reference request. Visible key tiles are
RESIDUAL and make no reference requests. Every visible delta tile, whether
COPY or RESIDUAL, requests its same-position 64-byte tile from the accepted
reference frame. The three retained actual delta tables each yield 7,806
requested tiles and 3,752, 4,608, and 1,687 COPY tiles respectively.

| Delta row | Accepted reference | Requested tiles | BL8 reads | x16 words | Reference bytes |
|---|---|---:|---:|---:|---:|
| c0_f1 | c0_f0 | 7,806 | 31,224 | 249,792 | 499,584 |
| c0_f3 | c0_f2 | 7,806 | 31,224 | 249,792 | 499,584 |
| c3_f50 | c3_f49 | 7,806 | 31,224 | 249,792 | 499,584 |

Each requested tile is four aligned 16-byte chunks. The model concatenates
those four responses, checks the resulting bytes against the accepted source
tile, and checks COPY output tiles against that same source tile. A 64-byte
payload is the adapter unit for each tile. The physical address is
`plane_base + tile_index*64 + chunk_index*16`, with Y/Cb/Cr bases 0, 345600,
and 432000. The canonical physical bus carries 19-bit byte addresses; the
largest aligned 16-byte line start is 518384. The outer request identity
retains the full 64-bit publication generation alongside epoch, fid, plane,
tile, and chunk. The physical memory ticket is an independent nonzero 32-bit
nonce; it is not a truncation of, or substitute for, the outer generation.
The edge examples cover the last tile in all three planes. A high-generation
check confirms that two distinct 64-bit generations do not alias even when
their physical address is identical.

## Word accounting and limits

The established candidate/RGB payload count is 539,520 16-bit words per frame.
Adding one delta reference stream gives 249,792 more x16 words, or 789,312
payload words per delta frame. This accounting excludes scratch traffic,
commands, refresh, scheduling, and controller overhead. It is a Python traffic
model and byte-assembly check; it makes no memory-fit or latency-closed-budget
claim.

## Integration observations

The sibling `reference_tile_reader.sv` snapshots the accepted bank and request
IDs when it captures a descriptor. External accepted-bank hint inputs may
change afterward; the active transaction uses its snapshot. Invalid descriptors
produce an error response without issuing a physical command. While a physical
line is pending, cancellation keeps the transaction until the matching response
drains; a held logical response keeps its metadata and assembled bytes stable
until accepted. The 32-bit physical ticket is an independent nonce and remains
separate from the full 64-bit outer generation.

The caller must protect the captured source-bank contents from writes or reuse
until accepted reference traffic and the outer reply or cancellation drain
have closed. The adapter does not own the bank allocator or acquire this lease.
The existing native live path can establish that the old bank remains protected
until the new commit and that reference traffic completes before final outputs;
the adapter integration must preserve the same lifetime fence. This model does
not validate the RTL state machine, physical service behavior, or end-to-end
integration.
