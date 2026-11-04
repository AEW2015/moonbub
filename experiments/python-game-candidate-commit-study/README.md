# AR03 candidate construction, transport admission and commit

This Python prototype splits expensive AR03 construction from codec publication
state. It preserves v17's AR03/AF03 version 3 wire bytes, GM/SR coding, full-frame
cap, exact display patches and bank-local refresh. It adds no installed firmware,
new compression syntax, physical performance or end-to-end FPS claim.

## API and ownership

```python
candidate = encoder.build(rgb, frame_id, scale_map=map, promote=False)
if candidate.accepted and transport_accepts(candidate.packet):
    decision = encoder.commit(candidate)
else:
    encoder.discard(candidate)
```

`build()` accepts the frozen `prepare()` keyword arguments: `scale_map`,
`quant_scale`, `force_key`, `promote` and optional `reference_bank`. It returns an
owner-bound frozen `Candidate` with `packet`, frame/reference/publication fields,
`service_ms`, recursively immutable `info` and `source_lease`. `accepted` means
complete bytes fit the codec cap, not transport admission or decode success.
`plain_info(candidate)` copies metrics into JSON-safe containers.

One candidate may be building/ready per encoder. `active_candidate` exposes that
ready object; `can_build`/`can_prepare` returns false while it exists. `commit()`
performs its own validation and must not be gated by `can_prepare()` while a
candidate is active. Recursive callback builds are rejected. This is a serialized
Python interface, not a native concurrent lock implementation.

Building performs the actual one analysis/three forward transforms, GM and any
selected SR candidate work, promotion/key reconstruction and tag, UI encoding
and validation, all lengths/CRCs and complete-cap testing. A non-key source is
protected by a transient typed read lease through construction and admission.
It does **not** consume `last_issued`, geometry, pending transaction credit or
publication destination. Work counters and valid UI-cache state still change.
Transport rejection does not make that expensive work free.

`commit(candidate)` validates exact object/owner, immutable recorded fields,
configuration, frame identity/window, exact current source bank object/ID/tag and
destination availability. It ignores unrelated-bank ACK/expiry changes rather
than invalidating every candidate on a global generation change. The candidate's
own source lease is excluded only from its destination check when source and
promotion destination are the same bank; every other destination reader blocks.
Only after all checks does it release its source pin, add pending bytes, reserve
the publication bank, lock geometry and advance frame identity.

Commit returns the normal AR03 `Decision`; its internal `service_ms` covers the
commit phase only, with `info.build_service_ms`/`commit_service_ms` also recorded.
The `prepare()` compatibility helper builds then commits and totals those internal
ranges. For full caller-level timing, measure actual outer build/commit calls:
small Python return/bookkeeping work may fall outside the internal fields.

`discard()` releases the private recorded source lease and candidate ownership,
leaving frame/reference/publication state unchanged. A cap-rejected build retains
one rejected candidate object for explicit discard, but releases its source pin
before returning and cannot commit. Exceptions during building unwind pins and
allow another build. Failed commits leave the candidate active for explicit
cleanup/retry; foreign objects, replaced objects, double use, configuration
changes and caller field tampering are rejected atomically. The known candidate
can still be discarded after public-field tampering without trusting its fields.

After commit, reference ACK/expiry and receiver validation remain the frozen AR03
rules. Packet-consumed credits do not publish reconstructed YUV. The host must
retain committed work until physical transport/decode owners drain before timeout
expiry, as required by the finite pipeline. This component does not implement
those physical-drain events itself.

## Actual component results

The campaign makes 48 native full-720×480 candidates from twelve distinct source
frames in the already used Mass Effect 4-second regression region. Modes GM and
exact-SR each run an all-commit control and a profile that discards IDs 0, 3 and 5.
The latter exercises discarded initial keys, refresh keys and promoted frames.
It then continues coding against only actually committed/acknowledged references.

- **42 commits** match a frozen AR03 encoder's complete packet bytes, returned
  RGB pixels and AF03 bytes exactly, under matching committed ID histories.
- **6 expensive native candidates** are discarded with unchanged banks, pending
  state, identity, generation and geometry. The source read pin is released.
- **887,040 selected RGB565 words** are checked exactly: 42 × 21,120, all four UI
  patches per committed native frame, zero selected-word mismatch.
- **4 paid over-cap P candidates** record complete attempted bytes above 128,
  preserve semantic state and reuse the same unconsumed ID. Their source pins
  are already released before return.
- **13 tests pass**, including full-resolution GM/exact/UI byte equivalence;
  discard/retry; owner/double-use/tampering; same-bank promotion source pin;
  destination readers appearing after build; unrelated ACK/expiry; stale source;
  changed configuration; geometry; exception and recursive-callback unwinding.

Forty-two source/dependency snapshots are pinned before the retained run and
checked afterward. These include conservative v17 ancestry, not exclusively
executed files. The complete component campaign takes 5.15 seconds on this host;
that duration is not an input rate, target clock or achieved streaming FPS.
The source is offline precompressed 29.88 fps footage, BOX-scaled before component
clocks; it is reused regression material rather than independent validation.
Map/source construction and expected-image/error oracles are outside component
clocks. Outer measured build, discard, commit, receive and ACK times are retained.

## Limits and next integration

The encoder owns at most one active candidate, but caller-retained old Candidate
objects can retain packet bytes and a released lease's Bank/arrays. Store plain
metrics/hashes and drop objects after resolution. One-candidate ownership is not
peak process memory, native heap, BRAM or DMA fit. Key/promotion candidates also
hold reconstructed int16 YUV; reference pools, pending packets, transforms,
source/RGB/UI cache/output and copies are additional.

Frozen dataclasses and validation prevent supported API misuse; they do not
provide isolation against arbitrary mutation of encoder private internals or
NumPy buffers through Python reflection. Reference arrays follow the existing
read-only interface. CRC/tags identify content, not authentication.

No packet pacing, network/ESP32 firmware/CPU/RF, decoded-frame deadline, SRAM/SDRAM
service or panel scanout is modeled here. The actual joined pipeline must charge
candidate rejections and commit/discard work, preserve source-read ownership
through paid completion, stage ACK/publication, handle lost feedback without
inventing references and decode the real accepted packet bytes. These component
results must not be added to v17's separate FPS/bandwidth estimates.

```sh
python -m unittest -v test_candidate.py
python verify.py
```

Use the project NumPy/Pillow/PyAV environment. `benchmark.py` regenerates timed
component evidence and needs the external clip. `verify.py` checks retained counts,
state equality, source pins, exact-control hashes and source coverage without the
external video. No old source or result was modified.
