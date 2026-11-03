# Iteration 12: resolution-preserving codec execution and selection

The primary requirement remains **720×480 coded video, 720×405 active game
content, and 30 distinct displayed frames/s**. This iteration measures four Python
prototypes at that canvas. It does not replace the requirement with a smaller
picture or lower frame rate. The paired research branch in both forks is
`handoff/gamebub-app-codec-v12-20261103`.

Two changes preserve existing GM01/HG01 bytes and decoded pixels: exact zero/DC
inverse-transform bypass and exact last-source encoder reuse. A separate RM01
candidate selector demonstrates why unconditional block search should remain
disabled. Controlled finite refresh experiments identify scheduling limits and
repair a late-ACK ownership issue in a new scheduler copy. No installed Sunshine
mode, ESP32 firmware or FPGA bitstream changes are included.

## Measured decoder improvement without changing the stream

The [sparse decoder study](../experiments/python-game-sparse-study/README.md)
caches quantization tables, bypasses zero blocks and computes DC-only blocks with
the exact two-pass signed Q14 rounding. All other blocks use the frozen inverse.
Both complete RGB output and immutable reconstructed YUV anchors remain exact.

| Native sample, 60 IDs each | Whole GM01 receive | Whole HG01 receive | Core reconstruction |
| --- | ---: | ---: | ---: |
| Combat | 23.36 → 20.72 ms | 26.05 → 23.32 ms | 6.18 → 3.78 ms |
| Second sample | 23.86 → 21.63 ms | 26.64 → 24.45 ms | 5.55 → 3.39 ms |

Whole GM01 receive improves 9.4–11.3%; whole HG01 receive improves 8.2–10.5%.
These are combined bypass/table-cache results, not isolated transform savings.
The core bypass covers 84.9% and 69.3% of blocks, respectively; that percentage
is not a target cycle or resource saving. Parsing, entropy and color conversion
still account for much of whole receive time. The benchmark executes 480 complete
receiver calls and 240 separately timed core reconstructions on identical bytes,
alternates baseline/fast call order and checks all pixels and YUV samples.

Five tests include exhaustive supported DC coefficient values/scales/plane types,
partial blocks, key/P/refresh references and atomic error rejection. Full host
arrays remain allocated; no BRAM, DSP, SDRAM bandwidth or native throughput claim
follows from this Python result. Porting the bypass to a native receiver is the
lowest-risk next implementation experiment because it needs no new wire syntax.

## Exact host reuse helps repeated sources, not every gameplay frame

The [memo encoder study](../experiments/python-game-memo-study/README.md) stores
one immutable RGB source, map and P payload on the PC. It reuses payload bytes
only with exact source/map equality and the same epoch, mode, geometry and ACKed
reconstructed key object/ID. Hits issue a fresh full header/CRC and consume normal
credit. They do not introduce a new reference, skip packet, approximate comparison
or smaller stream.

| Native sample | Hits / source IDs | Mean complete preparation |
| --- | ---: | ---: |
| Combat | 26 / 60 | 24.73 → 13.95 ms |
| Second sample | 0 / 60 | 24.89 → 25.25 ms |

On the combat hit subset, actual preparation falls from 25.07 to 0.215 ms with
zero forward transforms. The all-frame gain is 43.6%, but comes from repeated
source images. The no-hit second sample instead shows approximately 1.5% miss
overhead. This is a conditional optimization, not a promise for distinct 30 fps
gameplay. It is particularly relevant to paused menus and host captures faster
than the rendered game, without changing the application's picture size.

The campaign has 156 paired IDs, 312 encoded packets and 156 independent decodes,
including labeled flat/alternating/noise controls. All paired complete packets
are byte-identical; eight oversized noisy packets remain explicitly counted as
non-admitted controls. Five tests check equality, mutations, credit/generation,
key/expiry/session behavior and random repeated histories.

Added PC cache storage is one 1,036,800-byte RGB copy at this canvas, a map, P
payload/header and a reference pointer, excluding Python object overhead and
existing workspaces. No FPGA/ESP32 cache is allocated. The current optimization
overrides `prepare()` only: the finite rate controller invokes candidate APIs and
does not use it. Its measured preparation gain must not be added to finite link
results until preview/commit admission, paid rejection and expiry are integrated.

## Actual motion selection: bits saved do not justify blind search

The [rate/motion study](../experiments/python-game-rate-motion-study/README.md)
shares one canonical ACKed key between GM zero-motion and BM bounded-block
candidates. Both alternatives are actually prepared and charged; only the
selected packet consumes credit or commits state. The RM01 envelope adds 30
bytes to all compared modes. This is a separate experimental dialect, not a new
installed mode or a GM01-compatible body.

| Native sample | GM control → best actual candidate, mean bytes | Preparation, GM → selector |
| --- | ---: | ---: |
| Combat | 8,832 → 8,832 | 22.34 → 70.16 ms |
| Second sample | 12,056 → 11,741 (−2.61%) | 19.47 → 63.69 ms |

Combat chooses GM for all 60 frames; the second chooses BM for 38 and GM for 22.
Second-sample active PSNR changes from 35.203 to 35.132 dB, so equal maps do not
mean equal distortion. Held-out second-source savings are only 0.066%. Contrived
opposite motion saves 66.95%, demonstrating the mode works without establishing
a general gameplay gain. Nine noisy decisions reject after paying candidate work.

There are 462 decisions, 616 actual candidates, 453 admissions and nine paid cap
rejections. Nine tests and the stored verifier pass. Full search is not a default
recommendation. The next experiment must screen motion cheaply using current/
past source observations, then spend bounded search effort only where side bytes
and residual savings justify it. Every screened and rejected candidate must keep
its measured cost. Selection also needs a quality floor; smallest bytes alone
can choose a more distorted reconstruction.

## Controlled refresh scheduling, with a late-ACK repair

The [refresh study](../experiments/python-game-refresh-study/README.md) holds one
declared service table fixed across each policy group while causally generating
actual GM01/HG01 packets from the current ACKed reference. The table is pinned to
v11 stage means; it is not the measured cost of each newly generated packet.
Actual call wall times are recorded separately. Costs occupy independent virtual
servers, not a shared physical CPU. All policies pay the same source observation
allowance; failed noise preparation pays a fixed declared 120 ms.

The new scheduler rejects a matching ACK after timeout has already requested
expiry, even while a parser reader prevents physical reclamation. It pays parsing
and waits for reader drain. The frozen v11 scheduler could accept that late ACK;
its original evidence remains unchanged. The repair applies to every new policy
and is separately regression-tested, rather than credited to refresh removal.

All native cases schedule 60 IDs over two seconds, with a separate drain window.
Diagnostic cadence counts distinct presentations in the middle one-second window.

| Sample / profile | Periodic 30: strict / eventual / diagnostic | Initial-only: strict / eventual / diagnostic |
| --- | ---: | ---: |
| Combat / GM base | 54 / 55 / 28 | 56 / 58 / 30 |
| Second / GM base | 54 / 56 / 28 | 56 / 58 / 30 |
| Combat / exact UI | 49 / 51 / 24 | 51 / 53 / 27 |
| Second / exact UI | 40 / 42 / 21 | 42 / 44 / 23 |

Periodic 60 and initial-only have identical checked packet/event traces in these
short clean windows, because neither inserts a second key. That is not a long-run
refresh-policy qualification. Removing periodic-30 refresh adds two strict IDs
per group, yet **no case presents all 60 IDs within the strict window**. A declared
half-CPU-service UI scenario reaches 30 diagnostic IDs/s but only 57 strict and
59 eventual IDs. That ablation is a what-if, not measured accelerated execution.

In the second-source initial-only UI case, P-credit waiting totals 647.13 ms and
encoder waiting 440.67 ms. These are exclusive waiting intervals, not an additive
causal explanation of dropped frames. P sender slots remain held 88.71 ms on
average. UI processing, credit lifetime and reference scheduling all need attention;
raising the frame cap or reducing only inverse-transform cost will not resolve
every limit. The bounded scene heuristic does not improve the synthetic cut case.

The campaign has 17 cases, 1,020 capture-policy events, 892 actual preparations,
886 hash-checked decodes and six paid noise rejections. Nine tests cover timing
table isolation, causality, ownership, post-expiry feedback and actual small-packet
fault recovery. A 150 ms decode-age gate plus the next vblank is not a strict
150 ms optical-latency proof.

## Progress toward the application-specific codec

The coherent custom profile remains GM01 prediction/transform/entropy with optional
HG01 exact RGB565 patches, carried through GF02 and outer-bound GA01. Keep JPEG
as a hardware control. None of these experiments is HEVC/AV1 conformant, and shared
transform/motion primitives do not provide a standards decoder.

Next, in order:

1. Port the exact decoder bypass/table cache to native code and compare complete
   packets against the retained RGB/YUV outputs, including negative rounding and
   malformed streams. Profile entropy, color, memory traffic and full receive;
   derive a cycle/resource budget before adding a complex FPGA decoder.
2. Add exact-source reuse to the real preview/commit rate controller. Cache by
   source/map/ACKed-key identity, pay comparison/copy work, reject over-cap output
   before commit and test loss/expiry/key drain. Then rerun the full finite model.
3. Prototype a causal, low-cost motion shortlist and rate/distortion gate. Compare
   bounded block search, zero motion and block skip on held-out cuts, pans and UI.
   Explicitly charge losing transforms/search and motion side bytes.
4. Add acknowledged reconstructed-P references only as a separately versioned
   profile with content-bound reference IDs, protected reference storage and loss
   recovery. A newer reference can reduce long-key residuals, but reference
   bandwidth, credit lifetime and publication ownership must be proved first.
5. Integrate exact-UI change detection and a bounded patch work budget. Preserve
   spatial resolution; define which HUD regions require exact words and retain
   current behavior for unselected pixels. Do not assume configured rectangles
   are verified game HUD locations or call an approximate patch exact.
6. Compare the complete candidate with JPEG, HEVC and AV1 on the same longer,
   distinct-frame 720×405-in-720×480 corpus. Require cap/deadline/age distributions,
   quality and state/fault results, then implement the selected native/RTL path.

DSP-oriented work should follow this evidence: time-share a fixed-point transform
and residual/reconstruction datapath, bypass zero/DC work exactly, and provision
reference/output memory traffic. Entropy, parser bounds and feedback ownership
remain first-class costs even when arithmetic is accelerated. No new HLS/RTL fit
or synthesis result is supplied in this iteration.

## Reproduction and limits

Each study contains retained results, executed-source pins, tests and a read-only
verifier. The [independent audit](../experiments/python-game-audit-v12-study/README.md)
rederives accounting and separates measured costs from declared scenarios. Run
`python experiments/verify_prototype_v12.py` for the snapshot checks. The parent
manifest also pins the paired Sunshine laboratory README. There are 38 passing
component and audit tests: 5 sparse, 5 memo, 9 rate/motion, 9 refresh and 10 audit.

Native inputs are two related precompressed 25/29.88 fps clips, not live 30 fps
game capture. The 120 decoder source IDs contain 92 distinct per-clip RGB images.
Scaling uses BOX with fixed 720×405 active content. Standalone stage timings
exclude acquisition/resize and verification; finite scenarios include their
declared resize/transport costs. Host load was uncontrolled. No new native codec,
Renode/Verilator hardware timing, Wi-Fi/ESP32/QSPI transfer, shared SDRAM service,
physical scanout or sustained 30 fps claim is established here.
