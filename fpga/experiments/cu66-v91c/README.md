# V91c: bounded complete BR88 packet control

`br88_packet.sv` accepts actual BR88 bytes through `in_valid/in_ready/in_data/in_last`. `start` latches the declared `packet_bytes`, external `blocks` binding, epoch, word width, and serial-parser control. It stores at most 49,152 bytes in byte RAM and computes reflected CRC32 while receiving the declared body (all bytes except the last four). It accepts exactly the declared packet size with `in_last` on the final byte; early or missing final markers fail. A producer that stops without a final marker leaves ingress waiting, and must abort or reset to recover.

After reception, the wrapper checks the CRC, BR88/version/flags, block/width/reserved bindings, widened length sum, raw bounds, and all four compressed stream descriptors. Stream checks cover parameter ranges, per-band event limits, exact byte/bit sizes, zero-event emptiness, and zero padding. Only after all metadata succeeds does it autonomously sequence DC and the three AC contexts through the unchanged V91b context decoder and V91 elastic Rice parser. It packs each stream into MSB-first 16- or 32-bit words preserving its exact final bit count. No CPU-parsed descriptors are input ports. Zero-event contexts still participate in completion.

Sparse outputs contain block, raster index, signed coefficient, and the latched epoch. RAW fallback emits every raster coefficient, including zeros, and checks the same inclusive [-2048,2048] range. Outputs are provisional until sticky `done`; the external consumer must discard the epoch on later error, abort, or replacement start. `done` requires successful CRC and metadata, all four context ends, and acceptance of the final output. The component provides no persistent coefficient store, dense coefficient RAM, clearing engine, or publication transaction. The consumer must implement implicit zeros for compressed sparse output.

Reset and abort clear control and sticky status without clearing packet RAM. Start replaces the active transaction. All three cancel controls combinationally gate ready/valid so an old transfer cannot be accepted at their active edge. Context decoding and output remain gated until the new packet overwrites its full declared extent and passes CRC and metadata. The counters include every edge after start through sticky completion or error, including ingress, CRC finalization, metadata, word replay, parser/context control, output stalls, and context transitions.

The error codes are 1=start bounds, 2=input end marker, 3=CRC, 4=header/descriptor/parameter/count metadata, 5=coefficient range, 6=run range, and 7=padding or exact coded bit consumption. Underlying Rice code 2 also denotes coded EOF, and code 3 would denote invalid replay word metadata; replay words are derived internally.

`tb_packet.cpp` checks the 16 retained packet fixtures (12 actual packets from four historical source frames, plus four synthetic coded/raw packets) in eight configurations: 16/32-bit replay, serial/word parser, and continuous/stalled transport. Each configuration must match all 84,389 expected output tuples and epochs. Per-case random schedules use the same seed and exactly two cycle-indexed draws for byte offers and output ready across every serial/word configuration; an offered byte remains stable until accepted. No-stall runs remain independent of the seed.

The 200 directed checks per seed cover malformed magic/version/flags/bindings, length overflow and extents, bit sizes and parameters, band counts, last-band validation before any output, CRC corruption, input truncation/late last/trailing data, final padding, coded EOF/range/run/tail errors, zero-event nonempty streams, raw field/range failures, all-zero raw writes, a full 49,152-byte staging extent, the largest raw packet under the cap (383 blocks), held-output stability and final acceptance credit, and reset/abort/restart during ingress, descriptor validation, replay, and held output. Invalid semantic streams may have earlier provisional output, which must be discarded. Metadata and CRC failures emit none.

Run from the repository root:

```sh
python3 scripts/cu66-v91c/run_rtl.py --seed 910232
python3 scripts/cu66-v91c/run_rtl.py --seed 910233
```

The runner uses the existing `gamebub-cu66-v69-build` container, fatal Verilator `-Wall --assert`, C++ `-Wall -Wextra -Werror`, and `-j 2`. Every invocation retains source snapshots, hashes, gzip oracle/index, commands, versions, compile and simulation logs, and a result receipt including failures. Compiled objects and binaries remain in `/build` inside the container. The latest selected receipt is `results.json`; both final seed receipts are independently retained under `attempts/`.

The CRC and header checks cover one BR88 residual-chunk packet. They do not validate the enclosing CS88 frame, HUD, cache state, or final frame publication.

The byte array currently supplies combinational `le32` header/descriptor reads, up to 32 indexed bit lookups for replay, and a two-byte RAW lookup. These imply many concurrent byte-array accesses. The reported cycles assume those combinational accesses; this is not a demonstrated one-read/one-write synchronous BRAM implementation. V100–V105 must bank, register, or schedule the actual RAM ports, then rerun cycle measurements and verify synthesis/memory mapping before using these counts for a physical implementation.

This is behavioral full-packet RTL simulation. It makes no claim about live network ingress, framegraph integration, persistent coefficient publication, whole-frame timing, synthesis, routed timing, memory fit, physical throughput, or hardware operation. The packet RAM alone is 49,152 bytes; external sparse coefficient-store and zero semantics costs must be accounted for separately.
