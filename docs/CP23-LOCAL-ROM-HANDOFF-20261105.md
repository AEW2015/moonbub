# Restricted CP23 local-ROM simulation handoff

Latest status: see [morning handoff](OVERNIGHT-MORNING-HANDOFF-20261105.md) for the final actual-board setup failure, newer address-strength component, current source packages and proposed next hardware gate. Earlier checkpoints below retain their original scope.

The self-contained source package is `fpga/exports/cp23-rom-composite-source-20261105`, manifestSHA `574d42277b06e9fcf766fc6a82cb5f5fdf6211c70891d4e89bb136e83354234d`. Its92 included files/41 source bindings contain the actual RTL, fixed ROM, native golden assets, testbenches and compact executed records for eight modes. Python and Icarus are external prerequisites; no other GameBub checkout is assumed. The helper uses fresh external output paths and preserves all package bytes. A fresh copied held-LOAD cancellation replay passes with32 local compile inputs and all eight local runtime assets verified.

This is a local fixed-fixture composition, not a board image, firmware hook, network receiver or complete advertised CP23 profile. It runs exactly the authenticated17,412-byte epoch1/frame0 CP23 packet, SHA `3255ef9bbdb71f8678547aaadd72a41bf92991b7b09ee7cd88ad2a073df08107`. The selected format remains CP23/HC22/HD22; implemented scope is independent KEY with HC22 mode0 and HR01 INDEX_RUNS2. Predictive/reference/HD22 history modes remain unsupported.

## Executed path

The guarded ROM loader feeds real bounded staging; the actual outer CRC/component digests and base/HUD decoders check both computed tags. Guarded canonical storage, transpose, functional SDRAM controller/model and fresh private HUD RAM qualify a candidate only after real modeled writes drain. Native owned reads, RGB conversion and HUD overlay produce the independent composite oracle.

Full run:17,412 ROM bytes;518,400 canonical samples;21,120 HUD words;259,200 modeled physical words;691,200 native canvas pixels and1,440 actual latches over two complete refreshes. Zero pixel mismatches, missed latches or underruns;64,800 owned reads delivered. Qualification is cycle2,600,630 and first publication3,073,338 at nominal100MHz. This first-frame functional latency and repeating native canvases are not sustained unique FPS or physical playback.

Held/pulsed cancellation, pre-consumer cancellation, post-checked pending cancellation, physical accepted-burst drain and reset quarantine pass. A positive consumer-release indication joins actual component readiness and memory idle, never a byte count or timeout. The held loader abort request is adapted to one consumer cancel pulse; the loader still masks bytes and retains its own busy fence until positive release.

An INIT-only configuration fence prevents post-start logical reset from being mistaken for a fresh safe boot. The first configuration can bootstrap only from actual consumer/physical idle. A later reset requires reconfiguration; no warm-memory retention or safe interruption of arbitrary SDRAM writes is qualified. The immutable front's bank remains reserved after writer retirement; this is not a general reference-bank allocator.

## Verification and limits

From the package, use `python verify_source.py`; `python run.py --help` describes independent modes and fresh external evidence paths. All eight original mode records retain exact commands, source hashes, return codes and logs. Source and original complete local evidence are bound by parent manifest `8d55a9dc17c2f42259e84e11bcd83c8f864bcbda34a54a93cc90ac0070c31d06`.

Synthesis, routed board timing, CDC/I/O/reset qualification, bitstream and hardware execution are **NOT_RUN for this ROM composition**. Further resource/timing successors have separate gates and must not inherit these exact source results without their own checks. `refreshes` in the raw SDRAM-model log counts SDRAM refresh commands, not LCD frames.

The future CPL1 private board diagnostic is separately under development. Its post-read native RGB digest expectation is in `measurements/cpl1-expected-render-20261105.json`: IEEE CRC32 `4c5725e5` over345,600 RGB565 words, little-endian16-bit, column-major(x outer/y inner). This is expected fixture metadata, not a device measurement. Computed decoder tags alone are not physical SDRAM readback evidence; the planned observer also checks the actual rendered stream.

No new public transport or UDP port is allocated. Do not send CP23 data to JPEG/MSV1 ports or AKD1. Installed v30/build50 and SD/settings remain unchanged; a separately coordinated image/firmware/hardware window is required.
