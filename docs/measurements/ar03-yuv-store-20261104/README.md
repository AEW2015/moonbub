# Owned private YUV storage: simulated baseline

Local experiment `fpga/experiments/ar03-yuv-store-20261104`.
Manifest SHA-256:
`2e51572f8e74b169836351e6fdecea7d71c2f17e9282978d79f0c5a634a021f5`.
Root independently verified all 76 local artifact hashes. These are selected
records; the complete experiment, images and simulator executables are not
distributed in this folder.

The selected owned wrapper checks full owner/epoch/frame before completion or
release reaches the private sink. Eleven directed jobs, six stale-identity
cases and two model bounds rejection checks pass. The original unqualified
boolean-only wrapper run remains preserved separately in the local manifest.

The full actual tagged decoder feeds the retained build50 BL8 packer/controller
through the new private byte sink and a bounded synthetic SDRAM model. It checks
joint hashing/storage acceptance and compares every stored model word with the
pinned expected YUV bytes.

| Owned full simulation | Result |
| --- | ---: |
| Cycles, start to held storage result | 4,865,759 |
| Nominal time at 100 MHz | 48.65759 ms |
| Canonical/hash byte transfers | 518,400 / 518,400 |
| Stored 16-bit model words | 259,200 |
| Ingress bytes | 48,203 |
| Competing read lines / words | 2,263 / 1,086,240 |
| Write bursts / refreshes | 32,400 / 6,377 |
| Sink-stall / SHA-stall cycles | 2,071,630 / 1,587,596 |

The tag is `855898f019ffddad10bef275ee7dc9c6`. The two stream-wait counters are
mutually exclusive at this interface (`hi` versus `!hi`), but overlap work in
other pipeline stages. They are not CPU time or independently attributable
delays to subtract from a different baseline. The uniform competing load requests a
480-word line every 2,140 core cycles after cycle 22,000; it approximates average
pressure rather than the real LCD active/blank schedule.

This already exceeds the 33.33 ms target interval before RGB/HUD rendering.
It is not a matched A/B against the ROM-only diagnostic. The next matched
experiment adds bounded owner-scoped elasticity while holding the fixture and
read schedule fixed, and reports FIFO high-water and real writer drain.

No RGB rendering, LCD presentation, P/reference publication, AF03, live network,
Vivado implementation or physical test is established. Aperture capacity is
explicitly synthetic; production memory mapping requires board-part confirmation.
Reset is power-on only; outstanding-write reset/rekey remains unqualified.
