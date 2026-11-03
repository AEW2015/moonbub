# RG01 application-priority quantization prototype

RG01 is an actual Python independent-frame codec with an explicit spatial
quality map. It tests a first application-specific decision: preserve more
detail in declared HUD/text rectangles while spending fewer bytes elsewhere.
It is not an installed Sunshine/ESP32/FPGA mode, temporal format or HUD detector.

## Syntax and reconstruction

Each16×16 luma /8×8 chroma macroblock selects scale8/16/32 using a2-bit map.
The map covers all three planes; scale8 is finest. Frozen Q14 color, DCT, inverse,
quantization rounding and upsampling remain unchanged. Three actual CP02
coefficient payloads carry the frame. The RG01 version/flags/geometry/map/plane
lengths and whole-frame CRC are bounded and checked; nested CP02 CRCs, coefficient
limits, map codes/padding and exact length are checked before return.

At720×480,45×30 map entries cost338 bytes. The outer header plus CRC costs34
bytes, and each CP02 plane retains its own header/CRC. Compared with uniform
FT02, RG01's uniform-map packet is318 bytes larger overall because envelope and
plane descriptors differ. The338-byte map alone costs0.08112 Mb/s at hypothetical
30 frames/s before transport overhead. No map-compression or free metadata is
assumed. Uniform maps reproduce the frozen uniform codec pixels exactly.

## Declared policy and matching byte budget

The fixed rectangles are `(16,48,192,80)` and `(160,352,400,80)` in the720×480
canvas. They cover47,360 active pixels; they are declared priorities, **not
verified real-game HUD coordinates**. Two synthetic fixtures put text/health/
ammo elements there. Real frame analysis cannot establish that these particular
rectangles are the regions a player wants preserved.

Six fixed profiles compare uniform8/16/32, ROI8/background16, ROI8/background32
and ROI16/background32. A seventh offline selection holds ROI8 and mixes
background16/32, ordering coarsening by current-source luma activity. It actually
encodes/decodes up to eight midpoint candidates plus two charged endpoints,
choosing the best observed feasible packet under that same frame's uniform16
packet length. This uses current-frame activity/bytes, not future frames or a
quality-metric oracle. The benchmark records no formal causality proof, and its
manifests lack explicit future/oracle metadata declarations; the independent
audit reports that gap rather than treating absent metadata as a guarantee.

The reference uniform16 is **a size-comparison budget**, not a48 KiB storage/link
limit. Search is bounded but size versus coarsened-block count is not proven
monotonic; the candidate can be suboptimal. Decoded-error metrics are used for
evaluation after selection. They are not the selection criterion.

## Recorded rate/quality tradeoff

The benchmark uses eight predeclared native indices `(0,2,4,6,8,10,12,14)` from
each existing4-second Mass Effect window plus two seeded synthetic HUD images.
The16 real inputs are related precompressed footage with native25/29.88 fps;
content may repeat. Each actual packet is decoded and checked against independent
arithmetic reconstruction. There are126 selected/fixed profile records and252
actual encode/decode candidate evaluations, including paid search candidates.
Raw media remains outside Git with source/PTS/rendered hashes in the result.

All18 selected packets fit their same-frame uniform16 reference; utilization
is recorded per frame. Pool MSE by pixel area before computing PSNR:

| Input | ROI PSNR gain | Background PSNR change | Active PSNR change |
| --- | ---: | ---: | ---: |
| Combat8 |+2.51 dB|−0.46 dB|−0.08 dB|
| Second clip8 |+1.47 dB|−0.93 dB|−0.60 dB|
| Synthetic HUD2 |+2.75 dB|−0.06 dB|−0.04 dB|

ROI luma-edge gradient error also decreases on these fixtures. This is an
objective regional-fidelity tradeoff, not OCR accuracy, visual acceptance,
perceptual optimality or a free global quality gain. Fixed-quality ROI profiles
and their complete byte costs are retained, not just the favorable selections.

Two synthetic selected packets exceed48 KiB (largest91,513 bytes), despite
meeting their reference-size budget. They **fail** the separate packet cap.
The16 real selected packets fit that cap, but this is not a sustained admission
or worst-case size guarantee.

The reference-plus-candidate encode work averages253.79 ms/combat frame,
237.63 ms/second-clip frame and395.06 ms/synthetic frame. Candidate decode,
metrics, ordering, source capture/scale and other work add cost. These are actual
Python observations under uncontrolled host load, not a real-time algorithm or
a passed30 fps deadline. A practical policy must reuse transforms and select
maps with at most a small bounded trial budget, then measure its full cost.
No timing from this offline search should be substituted for sender service.

## Reproduce and verification

Use the common pinned Python/NumPy/Pillow/PyAV environment:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v
/home/lori/gamebub-streaming-prototype/.venv/bin/python benchmark.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python analysis.py
```

Seven tests cover uniform/frozen pixel equality, nonuniform reconstruction,
CRC/nested CRC, map/length/padding/range checks, exact uniform-format metadata
cost, and a real small-frame paid candidate search with a preserved priority
region. `analysis.py` pools areas, verifies source/result hashes, counts cap
failures and reconciles every charged encode candidate. Tests and source hashes
are not a target-fit, memory-service, hardware decoder or long-run video proof.

Next combine the map with immutable-anchor residual prediction in a **new
versioned profile**, retaining exact reconstructed references, ACK/drain and
cap rules. Keep the existing JPEG path as the hardware control. Implementing
the new map in the parser/dequantizer and measuring physical reference/scanout
traffic is required before deploying the custom format.
