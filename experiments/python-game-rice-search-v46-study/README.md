# V46 bounded actual-byte Rice parameter search

The existing AB38 wire already carries Rice parameters. This sender-only pilot
tries each baseline parameter and its legal ±1 neighbors, then chooses the actual
shortest arithmetic stream, keeping the baseline on byte ties. DC has one parameter;
each AC band's run/level parameters form a bounded local Cartesian menu. Streams
still use exactly the frozen arithmetic primitive, CRC and decoder grammar.
There is no new receiver profile, context model or mathematical inverse.

The declared cohort is the first six v40 frames from each of four clips: 24 causal
frames and both full/compact alternatives for every plane. All 2,917 attempted
stream encodes are paid and archived; independent stream decode checks coefficients,
Rice parameters, decision/renormalization counts, padding, termination and actual
byte winners. Three focused tests pass. Baseline streams and packets reproduce
frozen AB38 byte for byte before search.

| Accounting boundary | Before | After | Saving |
| --- | ---: | ---: | ---: |
| All 144 full/compact components, including losers | 451,605 B | 449,785 B | 1,820 B |
| Actual 24 complete CS38 frame packets | 395,448 B | 394,546 B | 902 B /0.2280957% |

Complete framing chooses among the actual original selected plane payload and
both searched full/compact candidates. Among 72 decisions, searched full wins11,
compact wins30 and old payload remains31. Every old fallback is a byte tie. All
maps, HUD, checksums, tags and complete component lengths are included. The two
component choices must not both be counted as transmitted data.

Independent complete-frame replay verifies exact coefficients, reconstructed
references, future causal state, HUD words, display tags and unchanged source
quality. The per-cohort complete savings are 278 /250 /138 /236 bytes. This is a
small compression result on reused short prefixes, not a large advance toward
HEVC/AV1 efficiency or an independently held-out corpus.

Old source CS37/CS38 generation is externally paid; every candidate search is
additional host work. These are not optimized sender/FPS measurements. The
complete-frame proof still uses the frozen adapter's old-entropy reserialization;
V43 separately qualifies direct receive. No native FPGA/ESP32 port, new bitstream,
physical frame rate, globally optimal Rice search or standards superiority is
claimed. The bounded candidate menu can be considered only if its actual byte
benefit justifies its measured host work in a native sender.

```sh
python -m unittest -v test_model
python benchmark.py
python verify.py
python frames.py
python verify_frames.py
```
