# Literature-review brief after V90

Prepared 2026-11-06. This is a review protocol, a primary-source seed set and
an evidence-extraction template. **It is not a completed systematic review or
a reproduced performance comparison.** The seed screening read publication
metadata, abstracts, specification front matter and repository descriptions;
full architecture sections, resource tables and implementations remain queued.

## Questions raised by the prototypes

V88 measured actual AB38/Rice byte-versus-feedback choices. V89 joined actual
Rice operations with aliases and found that removing feedback need not shorten
a memory-limited frame. V90 evaluates all eight whole-plane representations
for four sources and prepares a full-corpus work-aware proxy. Keep those scopes
distinct from 457-frame timing or physical hardware results.

The selected key illustrates the policy issue: an absolute-cap mixed choice
uses 29,941 bytes and models at 8.12490 ms under HIGH costs, versus 10.08595 ms
for the earlier relative-15% choice. On the selected hard source, even the
exhaustive oracle remains above 10 ms. These are conditional model results,
not calibrated FPGA clocks. See [V90 results](README.md) and
[the exact candidate study](exact.md).

The review should answer:

1. Which bounded parser architecture removes the critical dependency at the
   lowest LUT/BRAM/port cost, rather than merely maximizing standalone symbols/s?
2. Which entropy representation gives the best complete bytes **and** validated
   publication latency when fetch, contexts, transforms and memory overlap?
3. Can context interleaving, a word window or finer mode selection help within
   finite buffers, without hiding table/restart/framing overhead?
4. Which physical layout/controller techniques reduce COPY, descriptor and
   display traffic while preserving reference, candidate and scanout leases?
5. What must a fair HEVC/AV1 baseline include, and what extra compression benefit
   would justify its decoder state, memory traffic and implementation effort?

## Primary-source seed queue

These links were checked during preparation. Publication dates below are
document dates, not search-engine crawl dates. No published throughput figure
is transferred to Game Bub.

| Seed | Source and screening level | Question for full reading |
|---|---|---|
| S1 | [ITU-T H.265 (01/2026)](https://www.itu.int/rec/T-REC-H.265-202601-I/en), official standard item page | Establish the compliant low-delay baseline, reference state and required decoding processes; select explicit encoder settings. |
| S2 | [Approved AV1 specification PDF](https://aomediacodec.github.io/av1-spec/av1-spec.pdf), front matter identifies v1.0.0 with Errata 1 | Extract entropy, reference, filter and buffering requirements for a stated profile. The [companion HTML](https://aomediacodec.github.io/av1-spec/) labels itself a working document, so use the approved PDF as the normative seed. |
| S3 | [Duda, ANS, v2 (2014)](https://arxiv.org/abs/1311.2540v2), author abstract/version | Price decoder tables, state, model metadata and short-block overhead on our actual residual distributions. |
| S4 | [Giesen, Interleaved entropy coders (2014)](https://arxiv.org/abs/1402.3392v1), author abstract/version | Examine state interleaving, stream order and finite input storage; test whether parallelism survives consumer backpressure. |
| S5 | [Moussalli et al., No-Stall Golomb-Rice Hardware Decoder, FCCM 2013](https://www.cs.ucr.edu/~najjar/papers/2013/FCCM-2013.pdf), author PDF abstract/introduction | Adapt word-window and boundary handling to BR88's capped unary plus literal escape; extract actual area, buffers and stall assumptions. |
| S6 | [CCSDS 121.0-B-3 (August 2020)](https://ccsds.org/Pubs/121x0b3.pdf), official standard cover/metadata | Study block adaptation, sample mapping and coding-option metadata. Do not equate its syntax with BR88. |
| S7 | [ryg_rans](https://github.com/rygorous/ryg_rans), author repository availability | Pin a commit, inspect ordering/state/framing and reproduce a bit-exact component experiment. Availability is not a reproduced benchmark. |
| S8 | [FiniteStateEntropy](https://github.com/Cyan4973/FiniteStateEntropy), maintainer repository availability | Pin a commit and charge table construction/transmission, reset frequency and finite decoder storage. |
| S9 | [PaGoRi, DDECS 2024](https://portal.fis.tum.de/en/publications/pagoria-scalable-parallel-golomb-rice-decoder/), author-institution abstract/metadata | Extract parallel parsing ideas and explicitly assess the change from neural-network weights to video residuals and this FPGA target. |

The [machine-readable source log](literature-review-source-log.json) records
versions, screening depth and one failed primary-PDF fetch excluded from the
screened set. It contains no claim that these nine sources exhaust the field.

## Search and selection protocol

Search IEEE/ACM publisher records, author/institution archives and arXiv. Start
with the source log's recorded queries, then follow references and citations.
Run separate searches for parallel Golomb-Rice/escaped codes, interleaved
ANS/rANS/tANS hardware, low-delay video entropy paths, bounded memory/display
scheduling, and decoder-complexity-aware encoding policies. Record query,
database, search date, duplicates, exclusions and reason for each decision.

Include primary sources with an explicit algorithm/format or inspectable
architecture and stated experiment conditions. Standards belong in the
requirements lane, not the performance-ranking lane. Include CPU and ASIC work
as possible design ideas, but label it separately from FPGA implementation
evidence. Keep inaccessible full text as pending; do not infer missing resource
or latency data from an abstract. Avoid ranking by popularity or a headline
throughput value alone.

For each candidate, fill [the extraction matrix](literature-review-matrix.csv).
Use evidence levels: **P** normative specification, **A** algorithm/abstract,
**S** software reproduction, **R** RTL simulation, **I** implemented timing/fit,
**H** hardware measurement. A paper can supply several levels; retain the
conditions for each result rather than assigning its best level to all claims.

Extract the target device/process, clock, LUT/FF/BRAM/DSP use, memory ports,
input/output buffers, tables, resets, average and worst symbol lengths,
backpressure, malformed-input recovery and latency fences. Record whether a
reported rate is peak, sustained, input compressed bits/s, output bytes/s or
symbols/s. Do not convert it to frame decode time without the source's actual
operation counts and excluded work.

## Fair comparison contract

- Use identical uncompressed host captures, timestamps, crops, chroma and bit
  depth. Existing CU66-reconstructed pixels are already quantized; encoding
  them again cannot establish rate-quality superiority on the original game.
- Retain two comparison lanes: exact reconstruction of the current quantized
  picture for entropy/layout experiments, and matched perceptual quality from
  common raw captures for complete codec comparisons. Include HUD/text quality
  and scene transitions instead of relying on one scalar quality metric.
- Pin software commits, build flags, presets, low-delay/GOP settings and host
  capture/encoder device. Keep host encoding, entropy-only, full validated
  decode, transport and display latency separate. CPU decoder timing is not
  FPGA latency; synthesized estimates are not measured hardware.
- Count complete headers, tables, masks, validation and transport overhead.
  Reproduce both the 49,152-byte target admission policy and sustained queue
  behavior. Do not silently compare a payload-only stream against CS88 frames.
- Report minimum, median, p95, p99 and maximum with source identities and sample
  counts. A four-source exhaustive oracle is not an online encoder or a
  sustained-run result. Add independent scenes and held-out game captures.

## Review deliverables and next experiment gate

Produce a source matrix with access/evidence gaps, a compatible-architecture
shortlist and a reproducible common-input benchmark plan. For each shortlisted
method, state the needed syntax change, memory/table budget, parser/port cost,
host work and predicted failure mode, followed by a small falsifiable prototype.
Prefer the method that improves complete validated latency under the actual
resource/transport contract, rather than the best isolated entropy result.

Before claiming a hardware win, close target device/revision and memory-port
facts, calibrate the parser and transform RTL, and include physical controller,
HUD, continuous display and ESP32 ingress costs. Preserve the 60-second then
600-second distinct-source 30-fps hardware milestones and the separate strict
under-10-ms validated decoder criterion. The review is preparation for those
experiments, not evidence that they have passed.
