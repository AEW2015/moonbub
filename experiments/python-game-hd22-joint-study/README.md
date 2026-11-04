# V23 actual HD22 joint codec

This Python model replaces v22's full-pair HD22 byte projection with actual
versioned **HC22/HD22 → CP23 → private decode → JA23** bytes. It retains
720×480 coded /720×405 active content, all four exact RGB565 HUD regions and the
49,152-byte whole-pair cap. It does not modify the frozen v20–v22 modules or
install a native Sunshine, ESP32 or FPGA endpoint.

## Actual grammar and dispatch

HC22 keeps the existing bounded four-region cache identity: epoch, frame,
generation, destination, confirmed reference bank/frame/generation/tag, new
whole-HUD tag, four patch lengths and four patch dispatch values. LEGACY=0
retains actual HP01/HR01 full patches; DELTA=1 now requires the actual HD22 grammar,
including minimum-byte short-gap span packing. The existing full encoder and
HD22 candidate both run before the smaller complete patch wins. HD21 is rejected
rather than silently dispatched as HD22.

The cache envelope is 79 header bytes plus four-byte CRC =83 bytes; HA22 is
50+4 =54 bytes. CP23 is a 53-byte pair header plus four-byte CRC =57 bytes. It
binds each component's bytes, epoch/frame, lengths and SHA256[:16]. JA23 costs
33-byte header +43-byte AF03 +54-byte HA22 +4-byte CRC =134 bytes. The new magic
values use profile version1. Old HC21/HA21/CB21/JA22 parsers reject the new bytes;
these profile tags are **not an implemented negotiation handshake**.

AR03 inner video grammar and reconstructed YUV references remain unchanged.
Exact display patches never enter a YUV predictor or its canonical publication
tag. All complete packet, patch, reference and feedback validation remains paid.
CRC/hash tags are consistency checks, not authentication/encryption.

## Transaction API

`JointSender.build` prepares private HUD bytes and tries one to four declared
legal ROI/background maps. Only a complete fitting pair can be committed. Failed
maps are discarded and paid without issuing video identity, HUD generation or a
reference. Source leases survive until commit/discard. Private metadata forks
share published arrays rather than copying full banks.

`JointReceiver.prepare` validates the fixed 720×480 profile and privately decodes
both components. Explicit `mark_writes_drained(candidate)` and
`present(candidate, vblank=True)` calls are required before the logical state
changes. An invalid fourth patch, wrong profile/epoch/tag, bad frame geometry,
stale candidate, held destination reader or failed gate cannot publish a partial
base/HUD image. JA23 binds both exact component ACKs to the complete pair.

Sender/receiver state is stop-and-wait. `retry()` retransmits only the exact
outstanding pair; `retry_ack()` returns the same last-published JA23 without
presenting a second frame. Eight bounded unique reader descriptors protect
banks; duplicate release cannot drain another owner. Increasing local epoch
resets require drained owners. Lost reset negotiation, rekey and one-sided reboot
recovery remain outside this model.

The source APIs match the v22 joint model:

```python
sender = JointSender(base_encoder_class=None)  # frozen C.Encoder by default
candidate = sender.build(rgb, frame_id, force_key=False, promote=False,
                         profiles=None, now_ms=0, deadline_ms=None)
packet = sender.commit(candidate, now_ms=0)
task = receiver.prepare(packet)
receiver.mark_writes_drained(task)
ack = receiver.present(task, vblank=True)
sender.ack(ack)
```

`base_encoder_class` accepts a drop-in encoder. If it supplies
`begin_source(rgb, frame_id, force_key=..., promote=...)` and `end_source()`, a
source context is opened once after HUD preparation and before the map loop.
Every accepted/rejected/exception path closes that context; its lease is gone
before semantic snapshots while a winning candidate retains its own lease.
Preparation and cleanup remain inside the outer build timer. After cleanup,
JSON-safe `last_source_info` (or `last_shared_info`) is copied to
`candidate.info['source_analysis']`. No global frozen encoder is patched.

## Retained tests and evidence boundaries

Twenty-five tests cover all v22 transaction gates plus actual HD22 spans with
interior zero words, full frozen native-display equality, cross-profile rejection,
HD21 payload rejection after private base decode, and encoder context hook
cleanup on acceptance/rejection/exception/reset. The native fixture test observes
an actual selected HD22 span with merged zero words, rather than merely testing
new header magic.

```sh
python -m unittest -v test_model.py
```

Root-owned `benchmark.py` and `verify.py` qualify complete source sequences,
map choices, display/reference equality, wire bytes and source pins separately.
All new protocol overhead is determined from serialized structs, not assumed
eliminated. Existing JPEG and frozen earlier custom profiles remain separate.

This is a synchronous trusted-local Python contract. Owning NumPy arrays can
have their write flag deliberately reenabled; readonly flags are an API contract,
not an adversarial immutability/security boundary. Metadata tuple assignment is
not a threaded/native memory-order proof. Write-drain, vblank and caller time are
injected functional events, not measured DMA, CDC, scanline or real-time service.

The reference retains int16 YUV, full RGB/output and parser/transform arrays in
addition to HUD banks/staging and packets. Pointer sharing and named ndarray byte
counts do not establish total heap, mapped external memory, ESP32 SRAM/DMA/RF/QSPI
service, FPGA LUT/BRAM/DSP/Fmax, physical FIFO/line deadlines or sustained30fps.
