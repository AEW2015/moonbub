# V25 independent audit checklist

This is a checklist for reviewing the v25 retained artifacts. It is not a claim
that the proposed codec is hardware ready or sustains 30 fps.

## Pairing and quality

- Confirm both regression windows use the same retained source frames, coded
  geometry (720x480 with 720x405 active), source hashes, and frame IDs as the
  selected v24/custom reference baseline.
- Compare only matching source IDs and matching acknowledged reference IDs.
  Report any reference-policy change and its impact as a confound.
- Independently recompute active RGB565 expanded-channel error sums, sample
  counts, pooled MSE/PSNR, exact HUD word mismatches, and body bytes from retained
  objects. Require exactly 21,120 HUD words/frame and zero transmitted-profile
  mismatches.
- Recompute the no-compression color floor. Keep its difference from custom
  and motion outputs visible; it is a diagnostic, not a theoretical lower bound.
- State whether each result is a measured operating point, its threshold, and
  the number of windows. Do not present two windows as a universal result.

## Decoder evidence and information boundaries

- Replay each v25 packet using only its transmitted bitstream, decoder state,
  and ACKed reconstructed reference banks. Do not use original source frames,
  encoder search candidates, or future frames to reconstruct the output.
- Compare the independently decoded native planes and exact HUD output against
  the retained native decoder output, checking full hashes and actual pixels.
- Verify all transmitted mode, vector, map, entropy, header, CRC, and frame/ID
  fields, including malformed/truncated/negative controls where retained.
- Confirm reference-bank contents are reconstructed from decoded output and
  promotions/refreshes follow ACKed control messages. Flag aliasing, rollback,
  future-reference, or original-source dependencies.

## Rate and implementation accounting

- Derive video/base bytes, HUD bytes, binding, frame controls, ACK/reverse
  controls, headers, checksums, and any transport/framing bytes separately and
  as complete body bytes. Reconcile totals to the rate table at the stated
  nominal 30 IDs/s; do not turn that projection into a throughput claim.
- Price motion-compensation reads, reference-bank accesses/promotions, retained
  coefficient arrays, encoder candidate/search work, and decoder work. Report
  bytes and operation counts when possible; do not assume dedicated/free GPU,
  DSP, or host-search capacity.
- Keep same-source/same-reference-ID comparisons paired. Separate body-rate
  from combined goals and explicitly mark cases that miss either byte or MSE
  thresholds.
- Treat every profile that crosses 49,152 bytes as rejected. A later row's
  component trace cannot be presented as an accepted timeline after a rejected
  frame; keep the over-cap bytes and sealed parser-rejected packet as diagnostics.
- For standards comparisons, show the frozen v24 old-HUD target and separately
  recompute each standards stream with the actual new HU25 bytes plus CP25
  binding. Do not imply the old-HUD gap is closed by a different HUD policy.

## Reproducibility and independent checks

- Freeze the final source/artifact identities before running `audit.py --check`.
- Run the independent checks and all 8 retained tests; inspect test log for
  actual pass/fail and identify the exact artifacts covered.
- Rehash retained inputs and verify JSON descriptors, raw/stored lengths, CRCs,
  and hashes. Confirm the audit does not import the implementation's metric or
  decode functions as its oracle.
- Record exact command, environment, output, and limitations. Hardware fit,
  physical 30-fps operation, Wi-Fi airtime, and endpoint integration require
  separate evidence.
