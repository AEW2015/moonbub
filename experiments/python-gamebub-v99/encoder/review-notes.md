Read-only review of the V99 campaign harness
==========================================

The review did not modify the frozen encoder or running campaign. The seven
encoder unit tests previously passed, including actual cap rejection/reset,
fresh scene change, false-tag publication rollback, CRC rejection, native
zero-motion restrictions, supported qmaps, and compressed golden/component
serialization.

`scripts/cu66-v99/run_fresh.py` preserves one encoder record per fresh input,
counts cap failures, includes actual diagnostic packet bytes in offered-load
statistics, and exports only accepted packets to the independent native
ledger. The encoder clears both references after cap rejection and forces the
next attempted input to be a key; it never ACKs the rejected candidate. The
unchanged v66 receive must match the sender's fresh canonical reconstruction
and exact source HUD before reference advancement.

Quality uses the same V98 RGB565 display-domain metric and source-frame hashes.
Expanding exact RGB565 words to uint8 RGB and passing them through
`metrics.displayed` is idempotent. Comparing final RGB565 PSNR is meaningful,
with configurations disclosed: current CU66 has a separate exact source HUD
and previous-ACKed-frame reference, whereas the V98 GM01 control has no HUD
sidecar and retains a key anchor. Partial admission quality is explicitly
accepted-only, and the harness suppresses misleading temporal metrics across
missing input IDs. A complete sequence claim requires every input admitted.

Timing scopes differ. The fresh case field `encoder_prepare_ms` covers the
encoder's entire candidate-construction interval: source conversion, fresh
forward transform/quantization, full/compact AB38 trials, reconstruction and
tags, exact HUD generation, and real CS38/CU66 wrapper/adapter crosscheck. It
excludes later golden rendering/checks, receive/ACK, gzip and NPZ output. The
native CU66 timer ends after complete RGB565 publication. V98 standard
`decode_ms` measures only `AVCodecContext.decode`; its inverse conversion is
outside that fence. V98 `decode_call_start_to_rgb_ready_ms` includes the
canonical inverse conversion, but does not explicitly time RGB565 packing.
These are host software measurements with different fences, not calibrated
hardware or equal end-to-end decode measurements.

The fresh source closure pins loaded codec Python modules, unchanged color
arithmetic, the root harness, V98 metrics, and source manifest; the complete
manifest pins the compressed source NPZs. Native C++ is a separate receipt and
is intentionally not in the Python campaign's source closure. A read-only
snapshot audit found all 79 then-recorded source hashes matched both live code
and retained snapshots. A first-case record audit found all 30 records
accepted, matching actual packet SHA256, and gzip canonical/HUD/RGB565 goldens
of 518400, 42277 and 691200 decompressed bytes matching their recorded hashes.

Two findings were sent immediately to the CS88 adapter owner and root:

* The in-memory `components` branch read `normalized_planes` from
  `record['rtl_components']`, although the encoder exposes it at the record's
  top level. The persisted NPZ path has the required planes and is unaffected.
* The initial CS88 summary's `entire_sequence_49152_eligible` and
  `all_sequences_49152_eligible` ignored skipped CU66 inputs. Entire-sequence
  eligibility must also require zero skipped inputs and complete input
  coverage, or use an explicitly accepted-subset label.

CS88's 2MiB diagnostic chain may advance through oversized diagnostic packets,
provided it never claims that chain is physically eligible under the 49152-byte
cap. Its reference/root/QM87 state must advance only after independent native
acceptance. Its native parity and separate source closure are independent
gates from the accepted CU66 control.
