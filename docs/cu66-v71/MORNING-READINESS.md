# Morning CU66 hardware readiness

Updated November 6, 2026, about 06:00 Denver. This record distinguishes
completed offline work from installation and physical qualification.

| Item | State |
|---|---|
| Installed application/FPGA | Last physically verified v32 / build50; unchanged overnight |
| Next ESP32 app | v36 built, packaged, independently audited; not installed |
| New direct-YUV board | Final v008 `dy71i03` completed; setup -0.834 ns, native directory errors retained; no qualified BIT |
| New complete KEY/P/P model | PASS, zero LCD underruns and exact canonical/HUD/display checks |
| v36/native on previous SYNCsafe/split RTL | PASS, two accepted/presented, zero rejects/underruns, 42,240 HUD readbacks |
| v36/native on final safe-staging/validation successor | PASS: two accepted/presented, zero rejects/underruns, all 42,240 HUD readbacks |
| v36/native on exact final v008 board core | PASS: two accepted/presented, zero rejects/underruns, all 42,240 HUD writes and readbacks |
| Exact final v008 KEY/P/P | PASS: three frames, exact panel/canonical/HUD checks, 5,452 clean LCD lines, zero underruns |
| Physical CU66 playback | Not run |
| 30 unique displayed fps | Not established; three-frame model interval 46.10029 ms |

Keep the existing JPEG/build50 setup for the separately coordinated **25 fps
test first**. Freshly check receiver mode/address/allowed sender, exact
identities, counters and camera/recorder before that network test. Historical
`.157:5533` accepting `.47` is not a fresh readiness check.

The selected v36 UF2 SHA-256 is
`20cdbd6db030b0e99f363f93d0b081d2ca1f718c5e6dc6cb4d5d7edeff52ed97`.
It adds explicit local USB `G` for CU71 and `Y` for DY71; mismatches reject
before writes. No CU66 network capability or new UDP port is offered.
The effective SDK is byte-identical to v35. Its static SRAM is 130,916 bytes;
runtime heap, task high-water and first-exception checks are still physical
gates, not conclusions from ELF prologues.

Current prospective DY71 board-source-v008 retains the CU66 arithmetic contract,
grouped SDRAM path, safe staging and SYNCsafe scanout. Focused successors pipeline
parser length sums, entropy header/DC checks, dequant and IDCT validation; remove
proved-impossible feedback terms from tag/metadata qualifiers; and retime the
diagnostic event-ring storage with immediate read bypass. The actual combined
KEY/P/P and v36 native-HU/CSR/SDRAM replays pass on this exact composition. It uses
exact primitive-register C-to-D legacy bundle bounds instead of a broad selector
that matched a LUT. Numeric clock, I/O and SDRAM hold budgets are unchanged.
Selection SHA-256:
`3e5760ca6da2d593febe00655cb0a343d6d675f02db2ea8d1e9623df0fef6ba8`.
Core manifest SHA-256:
`15cc325a837720ae4f54dbb98b30d457d76271f416b7ef1576c198a68fde4b69`.

The completed full implementation is `C:/mb70/dy71i03`. Its console contains
three `Common 17-1257` directory-creation errors despite short private TEMP/TMP.
Its native Vivado log omits those console errors. Preserve both transcripts;
neither a zero process status nor positive timing can waive this open gate.
The reports are complete: routed setup -0.834 ns, hold +0.023 ns, pulse
+2.000 ns, all 49,051 nets routed, and 4,696 setup endpoints failing. The
environment discrepancy is still being investigated. No BIT was generated.

Its placed checkpoint reports setup -1.120 ns and hold -0.098 ns (pre-route,
not final signoff). The worst reported path crosses command state, parser
request qualification, arbitration choice and staging RAM address. A separate
bounded registered-request experiment is being developed without changing this
selected build. Its actual v36/native KEY/P pairing also passes. Final routed
worst timing now targets event-overwrite counter enable. Separate event-counter,
entropy address, SHA payload-enable and cache read-address experiments remain
unselected pending their component and combined proofs.

This first DY71 image is a local video diagnostic: fixed native panel timing
and 40-column landscape borders, rather than build50's adjustable margin13;
its audio outputs are disabled. Existing JPEG/AV/margin controls remain the
separate build50 path. Verify actual placement and stability during the local
fixture instead of assuming the previous optical adjustment transfers.

The discard/upload edge case was reproduced through the public CSR interface.
The current bridge cannot emit the consecutive core writes needed to trigger
that schedule, and v36 also waits for acknowledgments. It was not reproduced
physically. The successor explicitly closes that interface hazard for future
bridge changes; normal loader behavior remains separately compared.

Implementation01 is an earlier diagnostic build with the old stager and
invalid broad legacy endpoint selector; do not qualify its BIT. The older
RGB-based implementation06 completes at setup −1.177 ns, hold +0.013 ns,
pulse +2.000 ns, with all 50,600 nets routed. It still fails setup.
Unplaced positive leaf/OOC estimates do not close full-board timing.

After the baseline network test, require the final source/firmware pairing,
positive routed setup/hold/pulse, complete routes, no DRC errors, reviewed
CDC/exception coverage, and the final BIT hash. Then perform the known
physical app-only USB update step, verify the installed ELF identity and run
the CPU exception probe plus one local KEY/P under USB/camera/counter capture.
Retain build50 rollback and the qualified paired-reset procedure; do not
guess a command to release an accepted native endpoint/maintenance lease.

Next speed work is evidence-led: P2 reference blocking is 16.00631 ms of
admission behind previous canonical writeback and 19.02676 ms accepted/inflight,
plus transfer edges. Reservation overlaps those waits and is not additive or
a promised saving. Preserve PHY/map/quota while evaluating bounded DMA
lookahead and reference/writeback overlap. More arithmetic lanes alone do not
address the measured bottleneck. See the profiling reports for exact bindings.

The **ESP32 control link also needs its own throughput work**. V36 intentionally
uses scalar typed CSR commands and complete HUD readback for first-fixture
correctness. Its numeric-CSR model report is 583,945 virtual microseconds for
two frames, with 787,090 accesses and HUD CPU time excluded. That is neither
physical playback rate nor a 30 fps transport result. At 30 fps, 21,120 HUD
words imply 1.2672 MB/s of actual pixel data in each write/readback direction,
before command overhead. Measure physical upload, native HUD CPU, write,
readback and presentation timestamps first; then coordinate bounded bulk HUD
transfer/readback with exact generation/ticket/tag/drain semantics. A faster
FPGA alone does not close this scalar diagnostic protocol's streaming gate.
