# `gamebub-standard-compare-v24`

`source_sha256` maps repository-relative helper/reference paths to exact SHA256.
`inputs` has two48-frame source sequences. Each row retains the v23-matching RGB
source hash, an original RGB565 canvas object, common YUV420input object/hash,
actual HC22sidecar object, source preprocessing costs and uncompressed-color
roundtrip bare/hybrid metrics.

Every object descriptor has a safe relative `path`, exact `raw_bytes`,
`raw_sha256` and `stored_sha256`. Objects are bounded zlib byte streams.
Original RGB565 is contiguous little-endian `<u2`, shape480×720,691,200 raw bytes.
Common YUV input is concatenated uint8Y(480×720),Cb(240×360),Cr(240×360):518,400
bytes. HC22 contains real serialized metadata, patch bodies and CRC.

`custom_baselines` has fixed-v20-map/adaptive v23 controls for each scene, with
actual bare AR03 and full CP23bytes and independently rederived image metrics.
`cases` has20 native encoder/parameter/scene streams. Each `reference` retains
all elementary packets plus extradata blobs, actual PTS/DTS/key flags, requested
options, per-call emission and host timing records. Each row records the full
initial-extradata-inclusive access-unit bytes, bare and actual-composition hybrid
image hashes/metrics, and prospective transport counts. Hybrid complete bytes
include the actual HC22 length and a hypothetical57-byte future binding.

Metrics retain active RGB565 expanded-channel squared-error sums and sample
counts, derived MSE/PSNR, plus exact HUD word mismatch and channel-error counts.
All means use pooled error/sample sums. JSON`None`PSNR denotes zero error.
Summaries separate elementary/body rates from hypothetical lower-layer rates,
maximum frame bytes and the 49,152-byte cap fit count.

`operating_points` preserves each custom target's bare/hybrid MSE threshold and
the smallest measured native point meeting that threshold, plus the nearest
measured MSE point. `sampled_quality_range_covers_target` only means target MSE
lies within the sampled min/max; no monotonicity/interpolation/equal-quality
claim follows. `counts` records96 source acquisitions,960 actual native outputs,
192 custom reference outputs and 20 native cases. `versions` and`scope` state the
native codec, color, timing, byte-accounting and target-hardware boundaries.
