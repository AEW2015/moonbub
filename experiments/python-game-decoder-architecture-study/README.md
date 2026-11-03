# Game Bub decoder architecture parameter study

This is a standard-library Python arithmetic model for the
[HEVC/AV1 architecture investigation](../../docs/gamebub-hevc-av1-fpga-plan.md).
It evaluates storage, average shared-bus payload and dense-transform operation
counts. It does **not** decode HEVC/AV1, estimate LUT use, simulate a memory
controller, prove frame/line deadlines, or predict achieved FPGA clock rates.

Run from this directory:

```sh
python3 -m unittest -v test_model.py
python3 model.py
python3 verify.py
python3 verify.py --online
```

The last command only refetches the commit-pinned openav1 README and checks its
SHA-256; it executes no external code. Offline verification checks the retained
[results.json](results.json), source metadata and hashes of four existing local
inputs. [sources.json](sources.json) records access date 2026-11-03, primary
URLs, the pinned commit/date and README hash. It distinguishes author reports
from independent validation. No third-party RTL or software source is copied.

To run a different scenario, write an object containing any `Scenario` fields,
then run `python3 model.py --scenario-json /path/to/scenario.json`. For example:

```json
{"decode_fps": 30, "display_hz": 60, "references_stored": 2,
 "prediction_sources": 2, "efficiency": 0.4,
 "separate_color_conversion": false, "full_yuv_filter_passes": 1}
```

Unspecified fields retain their defaults. Stored-reference count changes
capacity; `prediction_sources` changes reads per predicted output. The latter
must not exceed stored references. `predicted_fraction` represents the fraction
of output using that reference-access pattern. The study does not choose a
codec's actual partition/motion distribution.

The checked-in [512×288 scenario](scenario-512x288-30.json) can be run directly:
`python3 model.py --scenario-json scenario-512x288-30.json`.
The retained sweep additionally covers 512×288@20, 480×270@30/20 and
320×180@30, with 720×480@60Hz display independent, plus an 800×480 display
alternative. It reports 1/2/4/8-reference storage and an 8×8 dense-transform
arithmetic example for every reduced profile. 512×288@30 is the proposed
first software-model baseline; 20 fps is a secondary tradeoff.

The retained workload is 720×480, 8-bit 4:2:0, 30 decode fps and independent
60 Hz RGB565 scanout. It assumes one current YUV reconstruction buffer plus
1/2/4/8 reference buffers and two RGB565 display buffers. That conservative
ownership layout is a choice; it excludes strides, padding, bitstreams, syntax,
motion vectors, filter scratch and ownership metadata. Aliasing frame roles
needs a separate lifetime proof. Full YUV images use 518,400 bytes, RGB565
691,200 bytes. SRAM's nominal 512 KiB leaves only 5,888 bytes after one YUV
frame and cannot hold one RGB565 frame.

This model's **two physical RGB output buffers** differ from the hybrid-link
finite model's **three metadata framebuffer roles**. The roles do not establish
the same physical allocation; combining the models requires an explicit
ownership and physical-buffer mapping. If three physical 720×480 RGB565 output
buffers are required, add 691,200 bytes (0.659 MiB) to the reported allocations:
512×288 with one reference then uses approximately **2.399 MiB**, rather than
1.740 MiB. Compressed storage, contexts and caches need additional space.
The two-buffer arithmetic does not prove that the actual whole pipeline fits
inside the existing 2 MiB functional-memory-model coverage; that coverage is
a verification limit, not an actual controller-capacity limit.

The default bus has a 200 MB/s raw data-cycle ceiling (100 MHz × 16 bits).
Efficiency is an unmeasured service assumption. Payload includes YUV
reconstruction writes, separate YUV→RGB read and RGB write, scanout, one
reference read and compressed staging read/write at 8 Mb/s. In-loop filter
passes default to zero so their cost remains explicit. Three naive full-frame
read/write passes add 93.312 MB/s; a line-streamed fused implementation can
avoid that particular external-memory pattern.

At 60% assumed service efficiency the default no-halo workload uses
110.864 MB/s with 9.136 MB/s average slack. Independent 16×16 luma/8×8
chroma fetches with illustrative 8/4-tap halos use 126.5375 MB/s, exceeding
that assumed service by 6.5375 MB/s. Halo fetches are an access-pattern example,
not a codec bound: caching and edge reuse lower them, while scaling, compound
prediction, bad locality, burst overfetch and rereads can raise them. Smaller
blocks amplify halos. Stored references do not all get read every frame.

`transform_budget` uses two dense NxN matrix passes: 2N³ MACs per block,
with each plane rounded up to full blocks. Fast butterflies and zero handling
reduce arithmetic; normalization, address generation, syntax, dependency
stalls and data movement add work. Abstract MAC lanes are not DSP slice counts.
100/150/200 MHz scenarios are requested clocks, with no Fmax evidence.

Validation: nine tests cover independently calculated frame sizes, source
count versus storage count, scanout independence, halo/partial-block arithmetic,
traffic accounting, reduced coded/display-size independence, padding, transform counts and invalid inputs. Tests and
the offline/online verifier passed on 2026-11-03. These checks validate the
parameter model and provenance consistency, not either codec or FPGA fit.
