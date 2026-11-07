Direct fresh RGB to selected CS88
================================

`direct_cs88.DirectSender(dense_encoder, native_receiver, clip_id=...)` creates
one fresh q16 clip context. Its `send` method consumes a fresh uint8 RGB frame,
sequential frame ID, expected source hash, actual output path, and optional
authoritative control row/path used only after its packet is complete. No
historical coefficient, quantized image or packet is an encoder input.

`scripts/cu66-v99/run_direct.py --output NEW_DIRECTORY --synthetic32` runs the
four selected source clips at q16, 30 fresh frames each, then a separately
reported 32-frame deterministic synthetic cross-key control. The corpus,
native container, existing binary hashes, selected CS88 report, control frame
ledger, Python closure and frozen C++ closure are pinned. Code snapshots,
native/binary receipts, all newly produced packet bytes, phase measurements
and source/output hashes remain in the immutable output directory. The
completed 120-frame campaign writes `direct/index.json`. A bounded smoke uses
`--clip mass-effect-2600 --limit-frames 2 --synthetic32` and cannot produce a
complete-campaign index.

Fresh fixed-codec color conversion, forward DCT and q16 quantization produce
new coefficients. Hidden coefficients are zeroed. Reconstruction and
normalization use the unchanged frozen functions. Exact HUD encoding uses the
same fresh HU25/HX32/HX33 policy as the authoritative CU66-to-CS88 control.
Operations are computed directly from fresh coefficients: hidden CONST128,
visible all-zero P COPY, otherwise RESIDUAL. The fixed selected grammar is
key0/Pgroup3, QM87 key run2/P accepted-cache6, all BR88, block32 and C2 group16.
No AB38 encoding or CS38/CU66 packet wrapping is performed.

The sender retains its own exact normalized reconstruction. Every actual new
packet must fit 49152 bytes, equal the selected authoritative packet bytes for
the same real-source frame, and pass the independent unchanged CS88 receiver.
Native canonical, dense coefficient, HUD-word, RGB565 display, C2 root and C2
seal hashes must match both newly computed expectations and the authoritative
control. Only then are the sender reference, HUD state, C2 root, QM87 cache and
generation advanced. Any cap, byte-equality or native parity failure raises
and aborts the context; its produced packet remains as diagnostic evidence.

The synthetic control generates each fresh frame from a small deterministic
function with a moving rectangle and frame-counter blocks. Per-frame source
hashes and actual packet hashes are retained, without storing raw source
arrays. It requires independent native parity on all 32 frames, keys exactly
0 and 30, P31 referencing key30, QM87 key2/P6 and exact C2 seals across the key
reset. It has no historical packet oracle and is reported separately from the
120 gameplay-source frames. It tests causal key transition semantics, not
gameplay quality or physical frame rate.

The measured interval starts with prevalidated, already loaded RGB and ends
when the complete actual CS88 packet exists. Phases report color conversion;
forward transform/quantization/hidden operations; sender reconstruction;
fresh HUD construction; QM87; C2 tree/seal; BR88 IPC; and remaining mode/packet
assembly. The frozen BR88 helper includes an internal exact decode check, and
that work and persistent Docker stdio IPC remain paid in the BR88 phase.
The HUD path similarly retains the frozen codec's internal validation work.
Initial imports, source hashes, packet writes, expected display rendering and
hashes, authoritative byte comparison, and independent native ACK roundtrip
are outside packet-ready timing. ACK roundtrip is recorded separately and
includes IPC plus full native output verification; it is not isolated decoder
timing. The overall loop is unpaced host software processing with explicit
checks and I/O. It makes no capture-to-display, deployment, FPGA or 30fps claim.

The first bounded smoke produced two real-source packets byte-identical to
the authoritative q16 key/P packets and passed all 32 independent synthetic
native ACKs including the second key. Source code may subsequently be frozen
only after final receipt/hash checks; the root runs the full campaign.
