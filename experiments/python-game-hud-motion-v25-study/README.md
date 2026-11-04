# HD25 exact component/motion HUD coding

This isolated Python experiment preserves original RGB565 words while testing
byte-plane runs, bounded component-delta Rice coding and integer motion against
the frozen HD22 and legacy full-patch compressors. It has no native endpoint,
FPGA RTL/fit, packet scheduler, radio or physical frame-rate claim.

The 50-byte HD25 envelope binds geometry, exact reference/current content and CRC.
It includes RAW/COPY/HD22-span fallbacks, byte-plane literal/zero/repeat coding,
R5/G6/B5 signed component deltas, and independent direct/left prediction.
Each Rice channel chooses k0..5 by actual encoded bit count. Rice unary/value,
component-domain, padding, geometry and output-tag bounds are checked on decode.

Optional motion searches integer offsets within ±4 pixels, globally and per16×8
tile. Edge refetches clamp within the same patch. The host ranks all81 vectors
using a declared component Exp-Golomb-length proxy, evaluates three global
vectors and one tile field, then constructs actual span/byte-plane/Rice residual
bytes. The selected packet is no larger than the unchanged-HD22 alternative.
This is not globally optimal motion/entropy coding. The receiver uses bounded
refetch, XOR or component add/prefix-add, simple byte RLE and Rice bit parsing.

`encode(current, reference=None)` returns immutable HD25 bytes; `decode` returns
a fresh uint16 array and does not mutate inputs. `encode_with_info(...,motion=False)`
is the non-motion ablation. `inspect(packet)` validates bounded grammar and
metadata; temporal content/tag verification additionally needs its exact reference.
Modes with `independent=True` require no reference, including new intra modes.

The campaign uses fixed already-ACKed source-word histories from the prior HUD
fixtures. Every legacy, old/new and losing candidate is actually encoded; separate
no-motion and full-policy timings are retained without double-charging the
ablation. The 83-byte future cache wrapper is only accounting until integrated.
RGB565 fixture-to-RGB canvas rebuilding, correctness/export and source acquisition
are outside encoder timers. Search counts are logical operations, not measured
memory bus traffic or native speed. Source snapshots include conservative frozen
code and fixture objects, not exclusively executed source lines.

```sh
python -m unittest -v test_model.py
python benchmark.py
python verify.py
```

Use the project environment with NumPy/Pillow. Retained verification needs no
external gameplay videos. Native regression windows and synthetic controls are
reported separately in `results.json`; they do not prove fresh live30fps capture.

## Retained results

All original HUD RGB565 words are exact, including the first independent frame.
Each native window contains 48 source updates; rates below project those updates
at 30/s and include the same 83-byte wrapper on every update. These are HUD-only
rates, not complete streamed-video bitrates.

| Native window | Legacy + HD22 | HD25 without motion | HD25 with motion | Full saving |
| --- | ---: | ---: | ---: | ---: |
| mass-effect-2600 | 2.139830 Mb/s | 1.580725 Mb/s | 1.520095 Mb/s | 28.96% |
| mass-effect-7200 | 4.906925 Mb/s | 3.281315 Mb/s | 3.096090 Mb/s | 36.90% |

The full policy reduced complete projected HUD bytes from 427,966 to 304,019 and
981,385 to 619,218. The non-motion policy captures most of that saving. In one
Python timing trial, full-policy encode took about 53–56 ms/update versus
20 ms without motion and 9–10 ms for the old policy. These host timings exclude
correctness/export and do not establish live 30 fps; all losing candidates and
legacy selection work are paid. Decode time is also retained per selected patch.

Static and random-noise synthetic controls retain the old minimum byte count;
the reused small-change control improves 14.37%. Separate artificial translation
controls exercise small motion packets, while independent random scene changes
fall back to RAW. They are not native gameplay wins. The scalar verifier checks
528 source-patch decisions / 2,787,840 words, 24 additional controls, 16 retained
goldens, and 16 CRC-negative cases. The 13 unit tests cover malformed lengths,
vectors, coverage, padding, references and component-domain rejection.
