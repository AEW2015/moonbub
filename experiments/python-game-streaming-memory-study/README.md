# Bounded streaming memory and scanline service

This Python prototype advances v16's average memory budget to an explicit
request-level schedule. It keeps **720×480 coded / 720×405 active** and an
independent **800×480 RGB565 panel at 60 Hz**. It does not implement a decoder,
SDRAM command engine, fitted panel, native/FPGA clock or physical 30 fps proof.

## What is actually exercised

Three retained native GM packets from v16 supply real packet/CRC/UI byte counts
and decoded coefficient classifications per eight-row Y/Cb/Cr stripe. The
coefficients, not a guessed all-dense ratio, determine inverse work. The campaign
uses fresh model IDs over a repeated traffic pattern: initial key demand,
ordinary-P demand and promotion demand every 16 IDs. It **does not replay valid
AR02 reference identities or decode 30 distinct gameplay pictures**. Only three
related source frames anchor these workload templates.

Eight principal scenarios cover one-second/30-ID capture windows with 250 ms
of continued scanout/drain. Four short phase cases repeat six-ID/200 ms demand
windows with 100 ms drain and vary refresh/stall alignment. They are not new
native samples or long-run hardware qualification.

## Bounded storage and causal service

There are two compressed ingress slots, one latest waiting frame, one decoder,
three physical full-panel RGB565 buffers, two retained packed8-bit YUV banks and
one private reconstruction buffer. New capture replaces only an unstarted waiting
frame; accepted bus work and active decoder state drain before reuse. A private
reference publishes by pointer swap after all its requests and compute finish.
Expired completion does not publish. Readers pin their selected physical bank.
This proves ownership only in this model; no packet contents/tags are validated.

The memory address map is byte-based, padded/aligned to 1,024-byte rows, and
selects one chip/bank. Full-frame coefficient storage uses external memory in
`baseline`; `streaming` retains one coefficient strip instead. External ranges
are checked against an **assumed 8 MiB implemented window**. The current 2 MiB
functional-model window is explicitly rejected before timing. This is not the
board's physical capacity and does not qualify new addresses on real hardware.

Every read/write becomes bounded BL8 requests. Unaligned entropy reads pay head
and tail overfetch. A grant contains at most eight bursts. Row changes, direction
turnarounds, refresh debt and configured non-preemptible stalls consume cycles;
refresh/stall debt does not disappear while a grant is active. The nominal
assumptions are read15/write13 serialized cycles, eight row-change cycles, two
turnaround cycles and 12 refresh cycles per 780 cycles at 100 MHz. Those are
conditional request service settings, not a JEDEC/part timing proof.

A bounded 1 KiB preflight pass pays CRC/UI work before reconstruction. Entropy
reads are a second bounded pass. Actual total entropy bytes are apportioned by
coefficient block count to stripes; this is an offline release oracle, **not an
implemented CP02 token parser**. Both profiles use this same two-pass preflight
architecture. The baseline parses/writes full-frame coefficients, then reads
strips back; streaming parses directly into one strip. Each reconstruction strip
reads its prediction, pays inverse/dequant/clip issue cycles, then writes private
YUV. Staging buffers for these steps are counted explicitly.

Baseline publication hashing rereads packed YUV through a bounded strip and
widens it into canonical int16 SHA input. Streaming applies the exact v16 inline
ordering contract to its produced stripe. **SHA work is unchanged**. No full tag
input is silently staged locally. The subsequent color pass reads each Y/Cb/Cr
sample once using a two-row Y and two-row-per-chroma cache, computes pairs of
RGB rows, and writes their centered 720-pixel regions in a full 800-pixel pitch.
Panel border pixels are preinitialized black in all three output buffers.
The local allocation includes coefficient/prediction/reconstruction strips,
parser FIFO, canonical SHA block, color pair buffers, UI words and metadata.
The metadata reserve also covers a 16-byte response/overfetch skid register.
It is not measured BRAM packing or total process memory.

## Scanout consistency and deadlines

Scanout has a bounded line-buffer FIFO. The observation starts from a black
front buffer and a prefilled FIFO; startup/prefill cost is outside the measured
window. A future panel epoch chooses only an already-complete pending framebuffer
when its first prefetch is issued. That framebuffer and model source ID are
immutable for all 480 lines of the epoch. Old epochs and accepted read requests
keep physical reader pins until they drain, even across an early front choice.
No prefetched old-front line is reinterpreted as a new image.

This is an **early prefetch commit boundary**, up to FIFO depth lines ahead of
vertical blank. A frame completing after that choice waits until a later epoch;
it cannot replace prefetched rows in place. Every served line asserts its epoch's
buffer index and source ID. A clean panel appearance is recorded only after all
480 line deadlines succeed. Late or absent line data increment underruns even
when the front-pointer source-ID cadence still reaches 30/s.

`deadline_rr` gives background work bounded grant opportunities when scanout is
not urgent; urgent display reads take priority. There is no promise of background
progress if service is physically oversubscribed. Reported arbitration waits
cover display-grant blocking, not a whole-system maximum stall contract.
Scanout consumes a whole prepared line at its uniform deadline; pixel-clock
blanking, actual portrait/landscape timing, electrical FIFO/CDC and physical
watermark behavior are not simulated.

## Results

| Profile | External bytes / local bytes | Line misses | Logical IDs/s | Clean epoch IDs/s | Eventual clean IDs |
| --- | ---: | ---: | ---: | ---: | ---: |
| nominal_baseline | 4,997,120 / 82,624 | 0 | 12.0 | 12.0 | 12 |
| nominal_streaming | 3,959,808 / 88,384 | 0 | 20.0 | 20.0 | 21 |
| fast_baseline | 4,997,120 / 82,624 | 0 | 26.0 | 26.0 | 27 |
| fast_streaming | 3,959,808 / 88,384 | 0 | 30.0 | 30.0 | 30 |
| fast_streaming_one_line | 3,959,808 / 83,584 | 0 | 30.0 | 30.0 | 30 |
| fast_streaming_stall_4lines | 3,959,808 / 88,384 | 3689 | 30.0 | 0.0 | 0 |
| fast_streaming_stall_8lines | 3,959,808 / 94,784 | 0 | 30.0 | 30.0 | 30 |
| current_2MiB_window | 4,997,120 / 82,624 | rejected | — | — | — |

“Clean” here means every modeled row arrived on time with the same immutable
framebuffer/source-ID token throughout the panel epoch. It is not a pixel-correct
image assertion: no output image is computed by this scheduler. The four short
phase cases record 0, 0, 1 and 0 line misses; their six model IDs can still obtain
clean appearances on later repeated panel epochs. Phase and full line deadlines
must therefore accompany aggregate rates.

The fast scenario is hypothetical read8/write8, 16 MAC issue lanes, eight entropy
bits/cycle and four sample/paired-chroma positions/cycle at 100 MHz; nominal uses
8 MAC lanes, four entropy bits/cycle and two sample positions/cycle. MAC issue
lanes are not demonstrated DSP48 counts. Both charge actual stripe block counts,
CRC/UI, dequantization, inverse, color and full canonical SHA work. Clock mapping,
signed widths, parser stalls, RAM ports and resource fit remain unproved.

The 200 µs stress is one non-preemptible 20,000-cycle stall every millisecond.
It is a declared adversarial service case, not a measured SDRAM behavior. More
FIFO lines can absorb that bounded pause only under the rest of this scenario's
service assumptions. A real arbiter needs a measured/verified maximum-stall
contract. Average/front-pointer cadence alone cannot prove clean scanout.

Baseline and streaming have different explicit storage/pass architectures; these
results are not v16 timing numbers with gains added. V16's average traffic did
not charge external coefficient scratch I/O. This baseline does, and both new
profiles pay a bounded two-pass input preflight. The conditional streaming gain
requires a real bounded parser and producer, not just changing an allocation
constant. Color-YUV reads remain; no reconstruction/color fusion is credited.

## Reproduction and limitations

```sh
python -m unittest -v test_model.py
python verify.py
python analyze.py --check
```

Use the project NumPy/Pillow/PyAV environment. `benchmark.py` regenerates this
deterministic architecture evidence, not target timings. Sources are pinned
before the final campaign and rechecked afterward. The verifier repeats all
12 scenarios from retained stripe counts and checks conservation, ownership,
served-line/underrun accounting and source snapshots. The regression suite has
twelve passing tests (nine frozen model guards and three supplemental boundary guards). `initial-probe.log` is historical: it predates aligned-overfetch,
clean-epoch accounting and explicit local-stage-buffer refinements, and is not
used for final claims.

No network/ESP service is charged: a complete compressed packet is available
upstream at capture, and a bounded request producer supplies its staging writes.
It is not assumed to reside in an uncounted local FPGA full-frame array. The
input/latest ownership model is bounded, but the actual QSPI producer and its
backpressure must be integrated with the separate paced-gateway study. Do not
add rates from independent models. This campaign neither hashes/decodes pixels
nor validates AR03/AF03 behavior, actual capture rate, fitted SDRAM, DSP mapping,
scanline hardware, target memory capacity or physical 30 fps.

`epoch-boundaries.json` is an explicitly untimed reconciliation bound to both
the frozen result and `analyze.py` hashes. It separates actual panel-epoch starts
from full-epoch finishes. Strict logical counts use epoch start `< capture_end`;
strict completed-clean counts require epoch finish `< capture_end`. A finish
exactly at the endpoint is excluded. Eventual clean counts require full epoch
finish `<= horizon`; partial final epochs are excluded. The stored validation
point is the last line's deadline, and the reconciliation checks that timestamp
against the exact rational panel schedule. The main scenarios have full-epoch
horizons, so no retained eventual clean appearance is lost at that boundary.
For fast streaming, 29 logical starts and 29 completed clean panel epochs
fall strictly before the one-second endpoint; all 30 finish within drain. Both
start-based and finish-based interior [250,750) ms windows contain 15 model IDs
(30/s), while the 200 µs/four-line-FIFO stress still has zero clean appearances.
No early prefetch commit is counted as visible presentation.
