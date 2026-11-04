# Portable AR02/GF02/AF02 golden vectors

This is the first bounded native/FPGA interoperability fixture pack for the v15
application-specific codec. It exports complete real wire bytes plus canonical
reference/display arrays. It does not implement a native decoder or prove FPGA
fit, timing, compression quality, live capture or physical 30 fps.

## Results

- Three deterministic synthetic cohorts, ten complete AR02 frames: five GM01
  lifecycle frames, four actually selected SR01 lifecycle frames, and one
  720×480 SR01 key with an exact display patch.
- Twelve actual GF02 datagrams. The full-resolution packet is 2,664 bytes and
  uses three datagrams; flat synthetic content is not a gameplay rate estimate.
- Ten retained malformed/binding-negative vectors: eight receiver failures and
  two encoder feedback failures. Every failure leaves publication/identity state
  and read ownership unchanged; performed parser/reconstruction work is not free.
- Six UI frames select 128 original RGB565 words each: 768 exact selected words.
- Eighty-four content-addressed object files use 89,759 stored bytes. zlib is only
  offline fixture packaging, not the AR02 video codec or transport compression.
- Seven regression tests pass. Twenty-six repository source snapshots are pinned,
  including the frozen v15 codec dependency set and this pack's exporter/verifier.
  The conservative pin set includes v15 benchmark/test/verifier snapshots that
  are not themselves executed by every fixture replay.

The GM lifecycle is key 0 → ordinary P 1 → promoted P 2 → bank-1 P 3 → forced key
4. The SR lifecycle is key 0 → ordinary P 1 → promoted P 2 → bank-1 P 3. Each cohort
starts with empty banks and epoch 16. Full resolution is a separate empty-bank
cohort. All data are synthetic full-canvas fixtures; no 720×405 gameplay cadence
or quality claim is inferred from the full 720×480 fixture.

## Files and schema

`results.json` uses schema `gamebub-ar02-golden-v1`, specified in [SCHEMA.md](SCHEMA.md).
Every object descriptor names a relative content-addressed file, storage encoding,
raw length, raw SHA-256 and stored SHA-256. Raw wire packets are directly usable
`.bin` files; RGB888, RGB565 and signed int16 YUV arrays are zlib-packaged solely
to keep repository artifacts small. Arrays specify shape/dtype. RGB565 words and
int16 YUV samples are little-endian; YUV tag input is `<HH width,height>` followed
by C-order Y/Cb/Cr `<i2` arrays. A tag is the first 16 SHA-256 bytes. Display RGB565
is an output contract, not the reference bank representation.

Each positive row supplies original RGB888, scale map, complete AR02, ordered
GF02 datagrams, expected AF02, pre/post banks, decoded YUV, expected display
RGB565 and base/display hashes. Fixtures can be replayed without invoking the
encoder or exporter. The source generator is deterministic and source hashes
are checked in addition to the stored source arrays.

Each negative row declares its fresh cohort, positive prelude IDs and failing
entry point. Receiver negatives must be attempted with no active decode and no
external reader lease. Feedback negatives require fresh encoder key 0 pending
and unpublished; the original valid AF02 must still succeed afterward.

Malformed cases include outer CRC, truncated frame, independently invalid patch
CRC under a resealed outer CRC, truncated patch under valid outer framing,
overlapping patches, incorrect reconstructed-result tag, incorrect selected
reference tag and unsupported inner dispatch. Feedback cases have valid AF02 CRC
but incorrect outer-content binding or stored-YUV tag. Rejection is asserted
before publication, with canonical bank contents, last decoded identity, active
owner and reader count unchanged. Work counters may change during a failed
parse/reconstruction and are not included in rollback assertions.

## Reproduction

Use the project's NumPy/Pillow/PyAV Python environment from this directory:

```sh
python verify.py
python -m unittest -v test_vectors.py
```

The read-only verifier validates source pins, hashes all stored objects it uses,
reassembles actual GF02 bytes, reconstructs every positive frame and compares
all YUV/display/reference/feedback outputs. It independently recomputes the
canonical stored YUV tag. It also exercises abort/retry and a read-owned-key
replacement failure. Tests cover reordered/duplicate GF02 chunks, pinned complete
readers surviving conflicting duplicates, corruption clearing incomplete ingress,
and UI-independent YUV/tag identity at 720×480.

`export.py` regenerates evidence and object bytes and should be run only when
creating a new fixture snapshot. Its sources are pinned before export and checked
afterward. No timing gain is claimed. `failed-initial-tests.log` is retained as
history: legacy helpers changed `sys.path`, so a bare `import verify` selected an
older verifier. The test now loads its local verifier by explicit file path;
final source pins, export, read-only replay and all seven tests are freshly run.

For native implementation, reproduce the stored arrays and feedback using only
these packet bytes, implement the negative-vector failure boundaries, then add
cycle/memory instrumentation. Matching this pack establishes contract equivalence
on these fixtures; it does not constitute an independently implemented decoder
or complete interoperability/fuzz/real-time qualification.
