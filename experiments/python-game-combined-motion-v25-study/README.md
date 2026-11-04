# CP25 combined base/HUD protocol model

This laboratory model composes the frozen GM25 lossy base and exact HD25 HUD
component with legacy full HP01/HR01 patch alternatives. It implements actual
bounded CP25, HU25 and JA25 bytes. No firmware, RTL, hardware memory timing or
physical30fps claim follows from these Python tests.

`encode_hud` takes up to four original legacy patch byte strings. The original
legacy selection cost belongs to the caller. This wrapper validates the full
patches and builds every eligible HD25 alternative, retaining whichever actual
packet is smaller (full on a tie). The information dictionary reports
`encode_wall_ms` and complete HD25 candidate work, including losing candidates.
Motion is disabled by default; `motion=True` explicitly pays the stronger HUD
search. Patches outside HD25's bounded patch domain retain the full alternative.

```python
hud_packet, hud_work = encode_hud(legacy_patch_bytes, previous_decoded_hud,
    epoch=1, frame_id=fid, reference_id=previous_hud_id, motion=False,
    width=720, height=480)
pair = encode_pair(gm25_packet, hud_packet, epoch=1, frame_id=fid,
    source_slot=0, destination_slot=1, publish=True, key=False)
bare_yuv, current_hud, ack = receiver.receive(pair)
ack_metadata = validate_ack(ack, pair)
```

Keys use `reference=None, reference_id=NO_REF` for HU25, and CP25
`source_slot=255, destination_slot=0, publish=True, key=True`. Each accepted P
references an actual reconstructed base bank by slot, frame ID and content tag.
A published P writes the other bank; a nonpublished P requires
`destination_slot=255`. HUD references always bind the actual previous accepted
HUD tuple and its frame ID, independently of the older base-reference ID.
An independent HUD is also allowed. HUD pixels never enter the base references.

`Receiver(epoch=1,width=720,height=480)` exposes two immutable logical `Bank`
records, each containing `frame_id`, `tag` and read-only `planes`, plus `hud`,
`hud_id`, `hud_tag`, `last_frame_id` and `last_ack`. `receive` validates complete
caps/CRCs/hashes, coherent inner identities, source-bank content, every HUD
patch and both final reconstruction tags before committing any state. Modeled
`write_drained=True` and `vblank=True` are required. Any validation or gate
failure leaves all bank/HUD/presentation/ACK state unchanged. A repeated frame
or wrong epoch is rejected; a later independent key resets both logical banks.

ACK bytes bind the complete accepted pair hash and both output tags. Validation
requires the exact pair bytes and returns publication metadata derived from that
pair. This is a synchronous model of publication and acceptance; it does not
implement physical leases, DMA fences, asynchronous ACK delivery, retries,
thread safety, clocks or memory-port arbitration. Read-only NumPy arrays are a
trusted local contract, not an adversarial memory boundary.

The complete pair cap is49,152 bytes. CP25 adds60 fixed bytes; HU25 adds110;
each actual ACK is65 bytes and belongs to return-link accounting. There is no
diagnostic overcap admission. Source images, reference banks, prepared analysis,
candidate packets and receiver reconstruction arrays require additional memory.
Bitrate/quality/runtime results belong to the independent native-source campaign.

Ten tests cover actual packet sizes, key/P exact roundtrip, alternate/no bank
publication, exact HD25 selection and reference binding, caps/CRCs/replay,
write/vblank gates, atomic bad-HUD rejection after a valid base, wrong bank/HUD
IDs, forged ACKs, inner identity/hash binding, empty HUDs and unused-slot bounds.

```sh
python -m unittest -v test_model
```
