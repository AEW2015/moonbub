# Moonshine / MoonBub prototype

Current product priority: **720×480 coded video at 30 fps**, with 720×405 active
16:9 game content. Lower-resolution/FPS results are diagnostic comparisons.
The [current plan](docs/gamebub-application-specific-codec-plan.md) prioritizes
compression, decoder service and refresh scheduling while retaining resolution.

The [v33 Python study](docs/custom-codec-prototype-v33-2026-11-04.md) adds exact
run-coded HUD packets with 35.77% / 17.75% fewer HUD bytes than v32. Shared
incumbent/band evaluation retains all tested packets with 32.97% less pair work.
Integer-grid motion reduces decoder prediction reads but trades bytes/quality;
guarded 32→16 refinement saves only 0.356% in a separate fixed-reference probe.
Its motion metadata consumes most residual savings. HEVC/AV1 receive the same
new HUD benefit and remain ahead in compression. Run
`python experiments/verify_prototype_v33.py`; native/physical 30 fps is unproved.

The [v32 specialization study](docs/custom-codec-prototype-v32-2026-11-04.md)
adds actual lossless HUD packets: 9.83% fewer HUD bytes on the harder window,
preserving every pixel. New coefficient shrink is rejected as a default; compact
wide-motion escapes save only 0.33–0.58% in a separate prospective probe. A
two-bank stage model projects 6.20/7.39 ms inverse service at an unclosed 100 MHz,
requiring actual RTL implementation. HEVC/AV1 with the same new HUD still use
about 37–40% fewer complete bytes at better sampled MSE. Run
`python experiments/verify_prototype_v32.py`; no physical 30 fps claim follows.

The [v31 RTL acceleration experiment](docs/v31-rtl-acceleration-2026-11-04.md)
adds an exact Q14 inverse/prediction-add/clip kernel with eight shared MAC lanes.
Verilator checks 33,054 blocks per case; generic Series-7 mapping uses 8 DSP48E1s
and no block RAM for the isolated kernel. Zero/DC shortcuts reduce measured
component cycles; 12.06–16.44 ms projections assume a future 100 MHz clock, not
routed timing or physical 30 fps. Run `python experiments/verify_prototype_v31.py`.
[ESP32 compact transport notes](docs/esp32-compact-transport-plan.md) are now saved;
that firmware change remains proposed and has not been flashed.

The [v30 study](docs/custom-codec-prototype-v30-2026-11-04.md) adds actual
block/band residual candidates with unchanged GM27 wire. Strict causal selection
saves 0.08–0.28% complete bytes with slightly lower measured MSE; a small-error
budget saves up to 0.63%. Full Python trial work roughly doubles, so these are
compression prototypes rather than deployment defaults. A separate exact
fixed-parameter local entropy oracle speeds equivalent recounts 21–25× after
setup. Run `python experiments/verify_prototype_v30.py`. Hardware 30 fps remains
unproved; the local oracle is not yet integrated into the full controller.

The [v29 study](docs/custom-codec-prototype-v29-2026-11-04.md) adds causal
quiet-block motion-search gating at unchanged resolution and exact HUD. Host
base-policy work falls 277→149 ms and 301→211 ms, with measured byte/error
trade-offs. An exact EC26 size counter is validated; its first guarded whole-plane
selector gives no gain and remains a negative control. All 384 accepted pairs
and 752 candidate encodes are retained. Run `python experiments/verify_prototype_v29.py`.
These are Python measurements; native/FPGA 30 fps remains unproved.

The [v28 study](docs/custom-codec-prototype-v28-2026-11-04.md) keeps GM27 wire
semantics and qualifies exact lazy entropy selection plus tap-aware prediction.
The exhaustive optimized controller reproduces all v27 packets/ACKs/pixels.
Mixed sampled search cuts measured base-policy work662/687→276/300ms at3.3%
more body bytes and small MSE increases. Predictor-only work improves2.46× with
50.22% fewer logical gathers. Run `python experiments/verify_prototype_v28.py`.
These are Python operating points; native/FPGA30fps remains unproved.

The [v27 study](docs/custom-codec-prototype-v27-2026-11-04.md) combines fractional
prediction and EC26 coefficients in actual GM27/CP27/JA27 transactions. The
fixed-history control saves another7.0–9.8% with identical v26 pixels; the causal
path uses2.620/5.978Mb/s with a small primary-MSE tradeoff. Syntax-only MV parsing
and metadata-only binding remove receiver-side encoder search and duplicate
entropy parsing. Run `python experiments/verify_prototype_v27.py`. The static
profile descriptor supports handoff; native negotiation/FPGA30fps remain open.

The [v26 study](docs/custom-codec-prototype-v26-2026-11-04.md) proves exact RDO
bit counting with9.06× faster paired Python encode-prepared work and identical
packets. New sparse-band coefficient coding cuts complete bytes another7.8–9.5%
without changing pixels; a separate compact fractional-vector/SSE-guarded path
saves6.1–8.1% while improving measured mean error. The two codec gains have not
been merged. Run `python experiments/verify_prototype_v26.py`; no native/FPGA or
physical30fps result follows. Historical verification commands below apply to
their frozen study branches.

The [v25 study](docs/custom-codec-prototype-v25-2026-11-04.md) adds exact HD25 HUD
coding, reconstructed-reference GM25 motion/SKIP and actual CP25/JA25 replay.
One fixed policy reduces complete bytes31.3%/33.3% at better measured mean MSE,
preserving all HUD words and resolution. HEVC/AV1 with the same improved HUD
still use about1.8–1.9× fewer bytes; Python encoding and physical30fps remain
open. Run `python experiments/verify_prototype_v25.py`. This is an offline study,
not a new native Sunshine/ESP32 mode or FPGA bitstream.

The [v24 study](docs/custom-codec-prototype-v24-2026-11-04.md) adds actual HEVC/AV1
software comparisons on the same source frames. With the same exact HUD, selected
native-codec hybrids use roughly half the body bytes at equal or better measured
MSE; this does not prove a Gamebub standards decoder. Owned/lazy analysis retains
identical custom packets while reducing repeated source guards. Functional reset
agreement is also tested. Run `python experiments/verify_prototype_v24.py`.
Native/RTL/transport timing and sustained physical30fps remain open.

The [v23 Python study](docs/custom-codec-prototype-v23-2026-11-04.md) now sends and
decodes actual integrated HD22 profile bytes, confirming1.55–2.07% complete-byte
savings at unchanged images. Its shared-analysis host encoder removes repeated
forward transforms with byte-identical results; measured build work improves3.90%
on the complex window but regresses3.23% without retries. All288 joint decisions
retain exact requested HUD words. Run `python experiments/verify_prototype_v23.py`.
These remain Python contracts and host measurements, not native/RTL or physical 30 fps.

The [v22 Python study](docs/custom-codec-prototype-v22-2026-11-04.md) adds functional
joint video/HUD admission and publication, with 192 sequential source-frame
decisions, whole-pair ACKs and explicit write/vblank gates. A separate HD22 gap-span
codec saves another 3.27–4.07% of HUD bytes at equal quality; joint integration
is still a projection. The adaptive joint policy can instead spend headroom on
better backgrounds. Run `python experiments/verify_prototype_v22.py`. These are
Python proofs; native/RTL timing, memory and sustained physical30fps remain open.

The [v21 Python study](docs/custom-codec-prototype-v21-2026-11-04.md) adds acknowledged
exact HUD COPY/XOR updates with the existing full-patch fallback. On two reused
gameplay windows, complete bytes fall 4.67–5.42% including binding overhead, while
all requested HUD words and ten full-display goldens remain exact. The complex
30-ID/s forward projection still needs 10.876 Mb/s before radio/retry costs;
this does not close the decoder/physical-30-fps gap. See
[integration tasks](docs/v21-display-cache-integration.md) and run
`python experiments/verify_prototype_v21.py`. This extension is a study; the
frozen v20 branches below remain the hardware-development baseline.

The latest application-specific hardware-development handoff is
[`handoff/gamebub-app-codec-v20-20261103`](https://github.com/AEW2015/moonbub/tree/handoff/gamebub-app-codec-v20-20261103).
Start with the [hardware kit](hardware/gamebub-v20/README.md),
[team prompts](hardware/gamebub-v20/TASKS.md), [acceptance gates](hardware/gamebub-v20/ACCEPTANCE.md),
and [v20 results](docs/custom-codec-prototype-v20-2026-11-03.md). The matching
[Sunshine handoff](https://github.com/AEW2015/Sunshine/tree/handoff/gamebub-app-codec-v20-20261103/tools/gamebub/v20)
carries identical wire/development contracts and host-port instructions.
V20 supplies a portable C11 inverse oracle and golden packets/tiles for native/RTL
work. All 96 mandatory-policy frames preserve all requested HUD words within cap;
inline tags match reconstructed vectors and save modeled bank rereads. All 34
tests pass. Background quality, bandwidth and timing remain explicit gates:
complex-scene forward data projects to 11.376 Mb/s and native inline planning
profiles miss 33.33 ms. No full decoder bitstream or physical 30 fps is supplied.
Run `python experiments/verify_prototype_v20.py` for retained checks. Prior branches
remain frozen and installed firmware remains MSV1 JPEG.
V11 integrated temporal exact565 UI patches with actual GF02/GA01 software
replay, tests bounded block prediction and512×288 at30/20fps, and adds a
[HEVC/AV1 FPGA decoder investigation](docs/gamebub-hevc-av1-fpga-plan.md).
These remain software studies; sustained30fps and target decoder fit are unproved.
The baseline build and timing results below do not qualify the experimental
dual-bank, SDRAM staging, gateway, or host candidates for hardware use.

Source attribution and component licenses are listed in [NOTICE.md](NOTICE.md).

An isolated Game Bub Rev4 Wi-Fi video prototype: PC JPEG sender → ESP32-S3
Rust/ESP-IDF firmware → existing quad SPI framing → FPGA JPEG decoder → SDRAM
double buffer → native LCD. The firmware extends the existing Slint interface
and preserves the copied controller, USB and LCD changes. This is experimental
standalone test-source mode; Sunshine pairing and JPEG negotiation are not yet
implemented.

The source panel is **800×480 landscape** (480×800 scanout), rather than the
720×480 native panel assumed in the brief. The transmitted 720×480 canvas is
centered inside it. A 1280×720 source becomes 720×405 content with 37/38 black
rows. Existing native panel timing and the stock overlay mapping are retained.
The prototype does not provide the stock dock output.

Final build/check status and artifact hashes are in [evidence/manifest.json](evidence/manifest.json).
The offline prototype gate passes. The final FPGA has +0.031 ns setup slack,
+0.014 ns hold slack, zero failing timing endpoints, zero routing errors and
zero DRC errors. All 345,600 pixels of the 720x480 JPEG fixture match the
fixed-point software reference.
Physical streaming FPS and latency have **not** been demonstrated. The recorded
PC localhost rates are not Game Bub results. No hardware has been programmed.

## Files and build

- [Firmware setup/build](firmware/README.md),
  [application UF2](firmware/release/moonshine-rev4.uf2).
- [Streaming screen preview](firmware/evidence/ui-streaming-preview/streaming-view-focus.png)
  and [desktop UI verification](firmware/evidence/ui-streaming-preview/README.md).
- [FPGA bitstream](fpga/build-final/moonshine-rev4.1.bit),
  [register protocol](fpga/PROTOCOL.md) and `fpga/rtl/`.
- [PC sender setup](host/README.md), [wire protocol](host/PROTOCOL.md),
  [codec/Moonlight audit](host/CODEC_AUDIT.md).
- [Integration decisions](docs/integration.md) and the original
  [requested prototype](docs/requested-prototype.txt).

Firmware builds with the installed ESP193 toolchain and ESP-IDF 5.4.3:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File firmware/build.ps1 -Package
```

The FPGA uses Vivado 2025.2 and XC7A100T-CSG324-1. Use the final build command
in the FPGA documentation. The delivered bitstream passed a second, post-route
physical-optimization step using `fpga/scripts/close_timing.ps1` and its included
source-bound routed seed. `build.ps1` regenerates the initial synthesis/route;
that initial route has a small timing failure and needs the separate closure
step. Earlier attempts and failed logs remain available for review.

The snapshot includes the existing modified Game Bub application and the
selected FPGA framework sources. It does not require the original Linux paths
or an assumed checkout inside this workspace. The derivation is recorded in
`firmware/source-snapshot.json`, `fpga/vendor/` and `evidence/source-before.json`.
Dependencies/tool installations are separate from source snapshots. The original
`C:/Users/lavat/codex/gamebub` workspace remains separate and unmodified.

## Repeat verification

```powershell
python -m pip install -r host/requirements.txt
python -m unittest discover -s host/tests -v
python scripts/integration_checks.py
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/test_firmware_protocol.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/test_qspi.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/test_transport_overflow.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/test_lcd.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/test_overlay.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File fpga/scripts/test.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File fpga/scripts/test_memory.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File fpga/scripts/test_pipeline.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File fpga/scripts/test_pipeline64.ps1
python host/build_cmodel.py
python host/compare_decoder.py --require-fixed-exact
```

The full-resolution JPEG test checks 345,600 unique pixels and an exact match
to the software model using the RTL color arithmetic. The independent Pillow
comparison remains available: its default chroma interpolation differs from the
core. LCD tests exercise independent refresh, buffer changes, delayed lines,
whole-line underrun handling and recovery. SPI tests use the actual pin parser
and CDC bridge. SDRAM model tests are functional simulation, not board timing
qualification. Each saved log identifies its scope.

## Device setup and recovery

Place `moonshine.cfg` on microSD using the firmware example and copy the final
Moonshine bitstream as `/moonshine.bit`. Firmware loads it into volatile FPGA
configuration when Connect needs it; the standard system/core files are not
replaced. Configure the host IPv4 and Wi-Fi in that file or the Streaming screen.
Start the standalone PC sender as described in `host/README.md`. View video hides
the UI through the stock transparent game screen; Home returns to its menu.
Disconnect/exit releases remote controls and coordinates receiver teardown.

Before first installation, retain the currently working application UF2 and its
hash. This project's UF2 updates only the application partition; it does not
include the updater, NVS, or system-data FPGA images. Game exit restores the
normal boot image; a normal restart reloads the existing standard boot core.
To revert the application, use the retained known-working Rev4 UF2 with the
normal Volume-minus power-on USB updater procedure. No recovery artifact is
described as hardware-verified merely because it was named in historical notes.

## Remaining physical verification

Identify the connected board and preserve its current image before deployment.
Then verify local pattern, known JPEG, Wi-Fi→QSPI concurrency, real moving game
footage, queue age, drops and control response. The first performance target is
720×480/30; 60 fps is a later measured goal. The 40 MHz quad data clock gives a
calculated 20 MB/s wire ceiling before overhead; it is not measured throughput.
ESP32 memory is bounded to datagrams/DMA chunks, not a decoded framebuffer.

Sunshine negotiation/pairing, an explicitly negotiated JPEG extension, audio,
and stock dock support are subsequent work. Audio is absent from the standalone
capture/protocol. Optional Windows keyboard injection is explicitly enabled
by `--inject-keys`; automated tests mock it and do not inject desktop keys.
