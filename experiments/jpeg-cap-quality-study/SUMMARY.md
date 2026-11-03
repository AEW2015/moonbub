# q90 vs q80 48 KiB retry image-quality study

**Offline only:** 1,493 native-25 fps samples. PSNR compares decoded JPEG to the same upscaled 720×480 canvas.

| Policy/population | Frames (finite / exact) | Mean PSNR dB* | p5* | Median* | p95* | Min* | Max* | Over cap / dropped |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Fixed q90, theoretical all frames | 1490 / 3 | 45.637 | 43.336 | 44.959 | 49.758 | 41.020 | 74.052 | 503 |
| Drop-only q90, frames sent | 987 / 3 | 46.593 | 44.540 | 45.583 | 51.268 | 43.380 | 74.052 | 503 |
| Fixed q80, all frames | 1490 / 3 | 43.251 | 41.150 | 42.822 | 47.428 | 39.400 | 69.913 | 0 |
| q90 then one q80 retry, frames sent | 1490 / 3 | 44.890 | 41.150 | 44.959 | 49.758 | 39.400 | 74.052 | 0 |

*Finite PSNR statistics exclude exact pixel matches: PSNR is mathematically infinite when MSE is zero. Exact-match frame counts are shown separately.

The retry policy used q90 on 990 frames and q80 on 503 q90-over-cap frames; it dropped 0. On retried frames, q80 minus q90 PSNR mean was -2.213 dB (min -2.412, max -1.536); 0 exact-match pairs have undefined delta.

These measurements quantify distortion versus an already-compressed, low-resolution source after upscaling. They do not establish perceptual quality or gameplay acceptance. Oversized q90 frames in the theoretical distribution are not sendable under the cap; the drop-only row excludes them and reports their count separately.

No transmission or hardware was used. See `README.md` for source details and reproduction.
