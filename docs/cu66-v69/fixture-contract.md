# CU66 v69 shared native/RTL fixture contract

Status: fixed first-integration contract. Native CU66 decoding and the listed RTL components now have retained passing evidence; see [component matrix](component-matrix.md). The connected base-layer top uses externally qualified packet metadata and a separate HUD boundary; it does not yet implement the complete packet-to-panel interface described below. Shared fixture bytes and core semantics remain source-pinned.

## Frozen wire/profile scope

Use the already defined **CU66/GU66** profile from `experiments/python-game-canonical-tag-v66-study/protocol.py`; do not invent a new on-wire form for the first cross-implementation comparison.

- Outer magic `CU66`, inner magic `GU66`; current V66 adapter format uses a 76-byte outer header and 60-byte inner header, each with its existing CRC. The exact packed field definitions, lengths and CRC coverage are authoritative in the frozen `protocol.py`/`receiver.py`, not a C struct cast.
- CU66 profile ID is `16c998527276c7c5249e96c75931494b` for the frozen rectangle profile and 720×480 geometry.
- Canonical output/reference tag is `SHA256(le16(720) || le16(480) || Y_u8_planar || Cb_u8_planar || Cr_u8_planar)[:16]`. Plane shapes are Y `[480,720]`, Cb/Cr `[240,360]`; require integer samples in `[0,255]` **before** conversion to bytes. Do not truncate, reinterpret signed values, or mix the older i16 domain.
- Keep full header/body/CRC, reference IDs/tags, qmap, motion-vector, coefficient, and mandatory HUD checks in the path under test. The UI remains display-only and cannot affect canonical reference samples or tags.
- Geometry is fixed at 720×480 coded / 720×405 active; chroma is 4:2:0; epoch/profile/rectangle declaration comes from the pinned fixture manifest. No capability fallback or CS38/CS66 autodetection is allowed; reject unsupported/cross-profile bytes.

## Minimum paired fixture

Native and RTL owners share one archived, actual converted CU66 key packet plus its following causal CU66 P packet from the same V40 source history. The first pair must include the source-packet SHA, converted packet bytes and SHA, original accepted reference tag, canonical decoded-plane SHA per plane, output tag, exact HUD words SHA, and displayed RGB565 SHA. Pin the exact V40 row IDs, packet offsets/object hashes, parent V66 source pins and conversion script/version in a `fixture.json`; never identify fixtures only by frame number or directory order.

The P packet must use the immediately preceding accepted key's exact bank/tag/ID. Advance the reference only when both implementations accept and independently verify the complete frame. A parse/CRC/plane/tag/HUD/display failure leaves the published reference unchanged. A key-only smoke may be useful for bringing up ports, but cannot satisfy the causal key+P fixture gate.

The fixture is deliberately narrow: two frames from the known Mass Effect source family, not new gameplay captures or a general codec benchmark. Preserve all mandatory HUD payloads in these fixtures; do not simplify them away to make RTL easier. More motion patterns, clipping boundaries, packet faults, and full 457-frame qualification remain later gates.

## Native-to-RTL boundary

The boundary uses explicitly packed binary artifacts, never C ABI layout or host endianness:

1. `fixture.json` describes exact input packet hashes/lengths, profile/domain IDs, source ancestry, expected outputs, and each file's SHA-256.
2. Input is the complete CU66 packet byte stream with `valid`, `ready`, `data[7:0]`, and `last`. A transfer occurs only on `valid && ready`; bytes/last remain stable while stalled. `reset`/`abort` cancels a private frame transaction and must not publish any partial state.
3. The top-level result carries `frame_id`, `accepted`, `error_code`, `reference_id`, canonical output tag, and an ordered Y/Cb/Cr sample stream (plane ID, sample coordinates, `valid/ready`, final-sample marker). Stable frame/plane/coordinate/data are required through stalls. The testbench records both the canonical sample stream and RGB565 display result; overlay is downstream and display-only.
4. For a first implementation that stops at inverse transform, use a separate versioned *decoded-block* test interface rather than claiming full CU66 ingress: block identity/plane, row-major 64 signed dequantized `int32` coefficients, prediction block, and ready/valid; compare 64 signed residuals, then exact prediction-add/clamp and emitted canonical bytes. Label this as a transform component test, not a CU66 packet receiver.

Keep each external memory client separate in the fixture contract: input packet staging, verified canonical reference bank, provisional output bank, SHA stream, HUD storage, and display RGB565. A simulation may use arrays as external models, but its report must state which arrays are testbench-owned versus RTL-owned. Never turn a testbench array into a BRAM-fit claim.

## Required result records

For every command, save a machine-readable result and log with: repo commit; exact source-pin hashes; fixture manifest and object hashes; tool/container identity and version output; command/seed; native C stdout/exit status; RTL simulator version/build log; testbench/RTL hashes; pass/fail and failure frame/plane/coordinate; accepted/rejected transaction counts; exact canonical/HUD/display hash comparisons; resource reports only when an actual synthesis command produced them. Keep these independent gates:

- frozen Python/C oracle agreement;
- native implementation agreement;
- RTL simulation agreement under stalls, reset, malformed profile/CRC/tag/HUD and causal reference reuse;
- synthesis/resource/timing evidence;
- physical SDRAM, QSPI/ESP32, panel and end-to-end throughput.

No gate can be inferred from another. Existing JPEG route/tests remain the compatibility control and are not CU66 pass evidence.
