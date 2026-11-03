# Actual selective HG01 / GM01 over GF02 and GA01

This Python experiment connects the frozen v11 hybrid selector to actual GF02
chunks, bounded ingress and serialized GA01 feedback. It copies the v10 charged
service scheduler into a **new** folder and extends its codec adapter; old codec,
transport and model files remain unchanged. BM01 is not in this link model.
No live Sunshine mode, target firmware/RTL or physical30fps result is supplied.

## Actual codec/transport path and identity

A bounded controller first prepares a cap-respecting GM01 temporal base, then
selects actual HP01/HR01 patches using the hybrid policy. Its full call pays base
analysis/maps/candidates/key reconstruction, fast header/map/CRC preflight, every
attempted patch mode, rejected work and wrapper assembly. The selected packet is
actual HG01, or byte-identical GM01 when no patch is selected. Both share exactly
the same reconstructed YUV prediction anchor; display patches never become refs.

`DecoderState` exposes the underlying GM01 semantic state for delayed publication
in the finite oracle. Full decoder validation occurs before stateful commit. An
independent cloned receiver reconstructs the expected complete display and base
hash after the preparation timer; this verification work and its extra arrays
are not decoder or encoder service. Sender packets are local until encode_done;
receiver state/publication and delivered read pins wait until decode_done.

GF02 carries the **complete selected outer packet**. Its epoch/frame must match
the nested GM01 identity. GA01 binds epoch/frame and CRC32 of the outer body,
excluding the outer CRC footer: UI bytes participate in the acknowledgment.
The same frame's inner-GM-only tag cannot ACK its HG01 output. The immediate
functional adapter verifies this with actual bytes. CRC is not authentication;
peer negotiation/security and host/target resource scheduling remain separate.

The inherited finite model charges actual BOX preprocessing, packetization,
every reassembly feed, full HG/GM receive, feedback construction/parsing, wire
serialization and assumed QSPI/propagation/vblank service. These are independent
serialized virtual servers, not one measured shared CPU. Defaults retain ideal
8Mb/s forward/reverse links,160Mb/s payload QSPI,10ms feedback propagation and
60Hz vblank. Payload pools have two49,152-byte slots per side, two GM credits,
three framebuffer metadata roles and bounded CPU/feedback descriptors. Source/
patch/output/oracle/reference arrays and packet copies are extra host storage.
No physical DMA, memory fit, SDRAM service or LCD timing is modeled here.

## Reduced resolution and FPS cases

The main twelve cases contain720 capture-policy events,670 actual preparations
and669 hash-checked decodes:231 GM01 and438 HG01. All data/feedback/CPU owners,
credits, waiting inputs and metadata roles drain. Every reconstructed selected
region matches original RGB565 words; this is not losslessness relative to
RGB888. A missing initial HG01 key chunk prevents one decode. ACK loss can decode
an independent key but does not create an ACKed sender reference.

|Coded canvas / requested IDs/s|Policy|Combat strict / eventual / diagnostic|Second clip strict / eventual / diagnostic|
|---|---|---:|---:|
|720×480 /30|GM base|54 /55 /28|54 /56 /28|
|720×480 /30|Adaptive exact UI|49 /51 /25|40 /43 /21|
|512×288 /30|GM base|59 /60 /30|59 /60 /30|
|512×288 /30|Adaptive exact UI|58 /59 /29|58 /59 /29|
|512×288 /20|Adaptive exact UI|60 /60 /20|59 /60 /20|

Strict windows are `[0,2000)`ms at30 and `[0,3000)` at20. Eventual includes a
separate1,000ms drain. Diagnostic is `[500,end−500)` with distinct presentation
IDs divided by its exact duration; it is not strict count or all-frame delivery.
These short windows, native25/29.88fps precompressed sources and repeated combat
frames cannot prove native30-distinct-frame acquisition or sustained30fps hardware.
The same60 native frames are scheduled at20 or30 IDs/s; this is not a real-time
capture/decimation experiment. Key refresh remains every30capture IDs, changing
its wall-time interval at20fps. Different host timings/reference histories can
change selected subsets; this is not an isolated one-factor speed ablation.

Smaller images are BOX resized directly from native RGB. Priority rectangles are
projected from the720×405 active window into512×288. Their selected area/content
alignment changes; per-canvas PSNR/MSE is not a matched cross-resolution quality
comparison or proof of legible text. Display events are metadata: no native-panel
upscaler, its arithmetic/line buffers or full display-sized writes are charged.
The separate architecture model includes explicit display-sized traffic assumptions;
its two-buffer allocation is not this scheduler's three-role physical-memory proof.

The second-clip512×288 UI loss cases remain visible: initial chunk loss gives
53strict/54eventual; initial key ACK loss51/52. Both reach29 diagnostic IDs/s after
recovery. Lost/duplicate packets and feedback pay actual nominal IPv4/UDP bytes:
GF02 is31header+payload+28IP/UDP, GA01 is24+28. Neither RF/framing nor retransmission
is modeled. Configured later fault IDs can be skipped; use observed events.

## Separate refresh diagnostic

`refresh_probe.py` deliberately disables periodic refresh for two2-second512×288
UI runs. Both diagnostic windows reach30IDs/s. Combat has58strict/59eventual with
one startup replacement; second59strict/60eventual. The main periodic-refresh
baseline remains29, and all its failures are retained. Probe source IDs are the
same but preparation/receive costs are remeasured. This indicates refresh/key/ACK
bubbles are worth investigating, not proof that disabling refresh alone guarantees
30fps or should become the default. No long motion/scene-cut/cap/refresh-recovery
qualification was performed with this probe. Reference age and future residual
byte demand can grow without periodic replacement.

`comparison.json` derives operating points and common-ID byte/error comparisons
without re-encoding. It separately lists identical inner-base packets: common
source IDs alone do not imply equal reference histories. Probe data adds120capture
policy events,119preparations and119decodes; it is not folded into the main counts.

## Tests, provenance and reproduce

Twenty tests include fourteen inherited charged-stage/ownership regressions and
six actual hybrid-link tests: HG chunks/outer feedback, identity mismatch, valid
transport with a corrupted nested patch, delivered conflict/read-pin retention,
mixed GM/HG immutable refs and finite key-ACK loss recovery. Invalid inputs cannot
install the GM key. All new checks use real small codec/transport bytes.

Use the study's pinned Python/NumPy/Pillow/PyAV environment, then from this folder:

```sh
python -m unittest -v
python benchmark.py
python refresh_probe.py
python analyze.py
python verify.py
```

Results pin executed sources, native inputs/PTS/hashes and versions; packet,
resize and feedback hashes plus display identities are retained. Full display
hashes are checked during the run rather than stored per decoded frame. The verifier checks
stored CPU/read/publication causality, conservative release, wire totals, cap,
format/selected-area/fallback identity, frame outcomes and both probe cases.
It is read-only by default; `--write-summary` deliberately regenerates its summary.
Direct `model.run` callers must supply in-bounds base and patch priority
rectangles for their chosen canvas; `benchmark.run_case` performs the documented
projection. External media can be absent for stored checks and are listed separately. Neither
verification nor30 diagnostic IDs/s in this short model is hardware qualification.
