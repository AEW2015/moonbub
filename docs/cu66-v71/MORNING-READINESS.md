# Morning CU66 hardware readiness

Updated November 6, 2026, about 03:30 Denver. This record distinguishes
completed offline work from installation and physical qualification.

| Item | State |
|---|---|
| Installed application/FPGA | Last physically verified v32 / build50; unchanged overnight |
| Next ESP32 app | v36 built, packaged, independently audited; not installed |
| New direct-YUV board | DY71 implementation02 running; no qualified BIT |
| New complete KEY/P/P model | PASS, zero LCD underruns and exact canonical/HUD/display checks |
| v36/native on previous SYNCsafe/split RTL | PASS, two accepted/presented, zero rejects/underruns, 42,240 HUD readbacks |
| v36/native on final safe-staging/validation successor | Separate proof pending |
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

Current prospective DY71 board-source-v005 selects the unchanged actual CU66
codec, owner, grouped SDRAM path and SYNCsafe scanout, with three focused
successors: registered staging credit, explicit rejection of overlapping
discard/upload, and a one-work-cycle IDCT classification stage. It also uses
exact primitive-register C-to-D legacy bundle bounds instead of a broad
selector that matched a LUT. Numeric clock, I/O and SDRAM hold budgets are
unchanged. Selection SHA-256:
`84cc0f1e93f03f870207c68df2c33aac6a4a7a3cee8da87deab7900ec69daf76`.

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
