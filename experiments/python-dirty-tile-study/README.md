# DT01 exact-source dirty-tile experiment

This new Python-only format asks whether static HUD/menu content can avoid
transform decoding. A 32×32 tile is SKIP only when its current RGB source bytes
exactly equal the host's **ACKed original** tile. Otherwise it is independently
encoded as FT02 at the declared quantizer. The receiver copies the previous
reconstructed tile for SKIP. There is no motion search, approximate change
threshold, future source, or unacknowledged reference. This is an alternative
to the temporal residual codec, not an integrated mode or an optimized sender.

## Format, state and bounds

DT01 has a versioned outer header with epoch/frame/reference IDs, even geometry,
fixed tile32 and quantizer, a one-bit dirty map, per-changed-tile lengths, nested
FT02 CRCs and an outer CRC. At720×480 there are345 tile positions and44 bitmap
bytes (ceil345/8), plus the outer header/CRC and changed-tile descriptors/data.
The last column is16 pixels wide. All dimensions, map padding, tile frame
geometry/quantizer, lengths and raw worst-case bounds are checked before
reference publication. An independent key must transmit every tile. Replay,
missing exact reference, wrong epoch and malformed/corrupt payloads are rejected.

The encoder permits one outstanding transaction. Matching epoch/frame ACK
publishes its original/reconstructed snapshots. Abort clears the reference and
forces a new key. A geometry or quantizer change also forces a key, so static
coarse tiles cannot silently survive a requested quality restoration. The
receiver rejects a non-key quantizer change. ACK serialization, authentication,
network loss/reordering, physical DMA/read drain and target memory service are
not implemented here. Original input and returned RGB mutations cannot modify
retained snapshots.

The host retains both original and reconstructed uint8 RGB, each1,036,800 bytes
at720×480, plus pending copies/temporary work. The receiver retains reconstructed
RGB and builds another output. For a hypothetical RGB565 implementation, a skip
copy requires reading old pixels and writing the back buffer; it does not make
SDRAM service free. Each decoded record reports logical skip reads and full
frame writes, not real bus transactions or a physical framebuffer allocation.

## Results: useful only for restricted content

`benchmark.py` compares12 consecutive held-out native frames from each related
Mass Effect clip plus two separately labeled procedural12-frame sequences.
Each frame is actually encoded/decoded and checked against host reconstruction,
then immediately ACKed before the next. Whole-frame FT02 and MA01 immutable
anchor controls use the same source capture and q8 but reconstruct different
pixels; this is not equal-perceptual-quality or finite transport evidence.

| Input12 | DT01 mean bytes | Whole intra | Immutable anchor | DT01 packets >48 KiB |
| --- | ---: | ---: | ---: | ---: |
| Combat |21,507|39,155|9,709|3 /12|
| Second clip |53,465|25,764|15,635|7 /12|
| Synthetic static HUD + moving actor |7,456|21,483|7,135|1 /12|
| Synthetic scrolling + fixed HUD |74,078|32,043|31,646|12 /12|

The simple static synthetic tail (excluding the initial key) averages1,210
bytes versus21,490 intra and5,838 anchor bytes. But its initial tiled key exceeds
48 KiB, so the small tail **does not establish a bootstrappable48 KiB stream**.
All over-cap packets are retained and decoded for algorithm comparison; they
are failures under that receiver cap, not admitted transmission successes.

Combat skips3,427/4,140 tile opportunities (82.8%), partly reflecting repeated
native content. Its rate saving must not be generalized to camera motion. The
second clip skips1,514/4,140 yet loses badly to both whole-frame controls because
independent small tile headers, repeated coding context and lost spatial context
cost more. Scrolling skips506/4,140 and every packet exceeds48 KiB. DT01 mean
wire demand at hypothetical30 captures/s is5.51/13.69/1.92/18.97 Mb/s across the
four scenes, including68 application/IP/UDP bytes per1,024-byte chunk. These
are byte-demand estimates; they are not delivered FPS or measured link rates.

Global active RGB565 PSNR differs slightly from intra due to independently
padded tile/chroma boundaries; the format can create seams. Mean pooled PSNR
is35.54/35.95/37.24/34.64 dB versus intra35.54/35.97/37.25/34.58. Neither small
PSNR differences nor source-equality skips establish visual/HUD acceptance.

**Selection:** do not make independent dirty tiles the gameplay base codec.
Keep immutable-anchor residual coding as the better measured general candidate.
Consider exact copy only as a future bounded mode for known static UI regions,
after reliable key/refresh delivery and real copy-memory service are qualified.
No dirty-tile FPS, decoder-time saving, target fit or physical display result is
claimed.

## Reproduce

Use the existing pinned Python/NumPy/Pillow/PyAV environment and source media:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v
/home/lori/gamebub-streaming-prototype/.venv/bin/python benchmark.py
```

Six tests cover ACK/epoch gating, exact source skip, mutable alias protection,
changed tiles, abort/key recovery, replay/CRC and map/geometry rejection, edge
sizes, quantizer refresh and raw packet bounds. `results.json` binds executed
sources, native PTS/source/image hashes, synthetic generator and every packet.
Source rates25/29.88 fps and repeated images remain explicit; immediate-ACK
eligibility does not prove a30 fps or finite feedback schedule.
