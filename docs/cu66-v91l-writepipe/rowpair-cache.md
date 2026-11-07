# Tile-row retention for display conversion

The [Python model](../../experiments/python-gamebub-v91l-writepipe/rowpair_cache.py) checks a concrete way to retain the reference-read advantages of 8×8 storage without repeatedly fetching the same tile rows for raster conversion. It preserves the existing 720×480 Y / 360×240 Cb / 360×240 Cr bytes. It does not change the encoded stream, quality, resolution or frame rate.

In 8×8 tile-major storage, a 16-byte physical BL8 read contains eight pixels from each of two adjacent rows of one tile. A 16-byte raster request usually needs two such bursts from neighboring tiles. The simple gather discards each burst's other row, then fetches that data again when the next raster row is requested.

Retain those unused eight-byte fragments in a next-row buffer. Serve the current row from the physical burst, and serve the following row from that buffer. The Python experiment processes every aligned 16-byte logical request in canonical plane order and compares every returned byte with both native goldens. It proves a bounded data-retention property for that declared schedule; it is not a new implementation of the converter.

| Tile8×8 conversion model | Physical BL8 reads/frame | Physical read bytes/frame | Overfetch |
|---|---:|---:|---:|
| Independent requests, discard unused rows | 64,800 | 1,036,800 | 518,400 bytes |
| Sequential next-row retention | 32,400 | 518,400 | 0 |

The retention model observes at most 728 pending data bytes for luma, and 368 for either chroma plane. A proposed implementation reserves 720 bytes for next-row RAM, 16 bytes for a physical-burst scratch register and 16 bytes for the logical response: **752 data bytes**, excluding tags, valid bits, control and other existing converter buffers. Each physical burst is fetched once, and both full reconstructed planes match their existing SHA-256 goldens. The 360-wide chroma rows and 16-byte logical requests that straddle their row boundary are included.

The Python dictionary, full-frame byte arrays, inverse mapping and fetched-burst set are verification storage. They are not an FPGA memory allocation or evidence of synthesis fit. The candidate requires a small indexed row RAM with validity/ownership tags; its RTL storage ports and timing still need to be designed and simulated.

## Promotion requirements

1. Preserve the independent-gather control. Implement a bounded row-retention reader with explicit request/response backpressure and stable held responses.
2. Preserve an immutable bank lease and generation/epoch tags. Invalidate every pending fragment on reset, cancel or lease change; drain accepted physical reads before reusing ownership. Random request order must use an explicit fallback or reject the unsupported schedule.
3. Adapt to the actual converter's chroma-prefill order. This model intentionally uses monotonic canonical plane order, whereas the existing converter preloads chroma rows around luma consumption. Decide whether existing chroma row storage can absorb retained fragments and use a separate bounded luma cache; do not assume the schedules are identical.
4. Recheck complete canonical/HUD-to-RGB565 output, plane boundaries, chroma interpolation and cancellation using the live shared controller. Include refresh, hash/reference/candidate traffic and continuous scanout in one finite arbitration schedule.
5. Measure whole-design resource/timing and hardware cadence. The address-only 2,352 row activations for this derived traversal are neither a timed controller result nor frame latency.

This candidate is a local codec/memory optimization, not a HEVC/AV1 coding-efficiency comparison. Sustained hardware 30 fps and complete validated decoding below 10 ms remain unproven.
