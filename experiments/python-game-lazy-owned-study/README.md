# Owned capture and lazy retry analysis

This v24 Python component replaces v23's borrowed-source SHA guards with an
actual immutable private snapshot. It moves analysis from eager context opening
to the first actual map build. Selected CP23/JA23 bytes, reference state and
display reconstruction stay unchanged. Installed Sunshine/ESP32 code, FPGA RTL,
and all frozen earlier studies remain unchanged.

## Ownership before HUD and video

`CapturePool.capture(rgb)` executes one actual `tobytes(order='C')` copy. Its
returned RGB ndarray is backed by immutable Python bytes, so normal NumPy writes
and reenabling its writeable flag fail. Both HUD preparation and base analysis
receive this same snapshot. A change to the caller's original array after that
copy cannot split HUD and video content. A test deliberately mutates the original
inside the HUD callback and still obtains the pristine control packet.

The pool has exactly two slots and at most eight unique reader descriptors.
Each descriptor binds pool identity, local epoch, slot, generation, token and
exact view. A live slot cannot be replaced. Duplicate/foreign release and stale
view reuse reject. Last-reader release clears the slot's retained payload;
external Python references may still keep immutable bytes alive, so clearing a
slot is not a measured heap-free event. Token/generation exhaustion fails closed
until a later drained local epoch reset; no counter wraps into a stale identity.

This snapshot is a synchronous host API operation. The caller must keep its input
stable during the copy. It is not a native capture DMA fence, atomic concurrent
producer snapshot or security boundary against deliberate raw-memory writes.

## Lazy source work

`OwnedJointSender` subclasses the frozen v23 joint API and supplies `LazyEncoder`.
Its outer `build` takes the private snapshot **before** calling the parent's HUD
or video preparation. Snapshot creation, ownership checks and release are inside
the outer paid build clock. Elapsed snapshot work is also added to the parent's
deadline origin; it is not hidden outside admission timing.

`LazyEncoder.begin_source` records identity/ownership and, for P frames, a source
bank hold. It allocates no prediction/DCT analysis. The first actual `build`
computes one analysis/three plane transforms. Only a real retry reuses that
result; every map quantization, entropy attempt, reconstruction/tag, serialization,
complete-cap check and losing discard still executes. The first attempt reports
one analysis/three forwards, later attempts zero, in addition to cumulative actual
encoder counters. No global module function or frozen class is patched.

The prepared arrays must remain available until the first map's admission result
is known. Their first-build peak is therefore not eliminated. A one-map winner
ends the context immediately after admission; a rejected map reuses it for the
next bounded attempt. No future-frame or fit oracle chooses whether to compute.

Each attempt validates the live capture descriptor and source/config/reference
identity rather than rehashing every RGB byte. Arbitrary borrowed arrays cannot
open this context. A referenced context still requires an additional bank-reader
descriptor alongside the ordinary candidate hold, as in v23. Native immutable
capture ownership and concurrency must be implemented separately.

The parent ends analysis before returning its candidate. The snapshot lease is
then released; the winning candidate still retains its separate reference-bank
lease until semantic commit/discard. Callback failure, cap rejection, deadline
expiration and pool pressure preserve all external readers and issued codec
identities. Local capture generations may advance on rejected preparations;
these are not transmitted codec frame/reference generations.

## Actual storage/cost contract

At 720×480, one snapshot is **1,036,800 host bytes** copied once per non-expired
preparation. Maximum two pool snapshots is 2,073,600 retained pixel bytes before
descriptors/allocator overhead. The normal serialized sender uses one slot.
`capture` records actual copied bytes, measured copy time, pool peak, owner identity
and reader/pixel counts after release. Parent benchmark timing must use the outer
`OwnedJointSender.build`, not just `joint_inner_service_ms`.

The prepared analysis still names 5,184,000 bytes: 1,036,800 int16 prediction and
4,147,200 int64 raw coefficients. It is computed lazily and retained through the
current decision/retries. `owned_capture_array_bytes` and
`retained_source_copy_bytes` name the same physical snapshot counted by
`capture.copied_bytes`; do not add them as separate allocations. Hash/copy
temporaries, new coefficients, reference banks, display/HUD arrays, packets,
interpreter state and caller references are additional. These are named host
objects, not measured heap peaks, ESP32 SRAM allocations, BRAM fit, bus traffic
or physical frame-rate results.

## API and verification

```python
sender = model.OwnedJointSender()
candidate = sender.build(rgb, frame_id)
# Normal v23 commit/private receive/write-drain/vblank/pair ACK follows.
```

The module exports frozen joint API as `m`, and `CapturePool`, `CaptureLease`,
`LazyEncoder`, `OwnedJointSender`. Generic `LazyEncoder` tests use 64×64 inputs;
the full joint sender retains 720×480 fixed geometry. Its CP23/JA23 format is
unchanged and remains a laboratory custom profile without installed endpoint
interoperability or capability/reset negotiation.

Sixteen tests pass, covering immutable bytes backing, slot/reader pressure,
generation/epoch/token invalidation, duplicate release, exact K/P/promote and
GM/exact/pruned retry parity, failed caps/ID reuse, stale ownership/configuration,
callback cleanup, end-before-commit, source mutation, deadline and complete
joint output/ACK equivalence.

```sh
python -m unittest -v test_model.py
```

The parent campaign measures plain, v23 eager and owned/lazy controllers on
identical native-source windows. This component claims no speedup until those
measurements exist and no native/RF/QSPI/RTL/DMA or physical 30-fps proof.
