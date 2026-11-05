# v67 hash, scanout and publication integration audit

This is a source review of the frozen Python contracts, not a new integrated decoder, FPGA simulation or hardware timing test. It reviews the [v67 handoff](gamebub-v67-hardware-research-handoff.md) and [research report](custom-codec-prototype-v67-2026-11-05.md) against the v48 tile receiver, v64 filtered scanout, v66 canonical-tag receivers and v67 tile hash component. Their individual proofs are useful implementation oracles; they do not establish that the components run together within one 33.33 ms presentation period.

The handoff's main boundaries are consistent with the source. The additional obligations below make buffer lifetimes, publication and error handling explicit before hardware work begins. No frozen runtime or result file was changed for this audit.

## Component contracts and remaining connections

| Component | Source-proved contract | Integration work still required |
| --- | --- | --- |
| [v48 tile receiver](../experiments/python-game-stream-rx-v48-study/receiver.py) | Arithmetic dispatches 5/6 only, one coefficient/inverse/prediction tile at a time; complete entropy consumption and frame/HUD checks precede API state publication | It still retains full reconstruction and normalized planes. It has not been connected to the v67 hash input or a timed bank controller; general v43 dispatches 0–6 are a broader compatibility path |
| [v67 tile hash](../experiments/python-game-hash-stream-v67-study/model.py) | Ordered, already normalized uint8 8×8 tiles reproduce each declared planar tag domain using one eight-row strip | Frame identity, expected-tag comparison, SHA input backpressure, write drains and bank publication are caller responsibilities |
| [v66 receiver](../experiments/python-game-canonical-tag-v66-study/receiver.py) | One canonical output fingerprint per new-profile receive, cached verified reference binding, all-or-nothing Python state update | Hardware ownership must keep the cached tag and its actual reference bank consistent; negotiation and physical memory fault handling are absent |
| [v64 filtered scanout](../experiments/python-game-filtered-scanout-v64-study/model.py) | Exact fixed display filter, chroma interpolation, RGB565 conversion and HUD-last rows from immutable canonical planes | A panel clock, bounded output queue, DDR arbitration, row prefetch and front-bank release fences remain to be implemented |

The v67 replay starts from full canonical planes decoded by the old receiver. It is a proof of tile-to-planar hash serialization, not an end-to-end connection to the v48 producer. In particular, v48 currently performs normalization after reconstructing full planes. A future streaming connection must apply the exact canonical hidden-sample normalization before feeding the hash, including boundaries and partially covered transform blocks.

## Hash order, strip ownership and storage

An 8×8 tile's bytes cannot simply be appended to SHA: the fingerprint specifies complete planar rows, not tile concatenation. `TileHash` accumulates one band of eight rows, drains rows in order, then advances to the next band. Planes are Y, Cb, Cr, with widths 720, 360, 360. Chroma serialization uses only the first 360 columns of the shared maximum-width strip; stale unused columns are not hashed.

One context retains **5,760 bytes** of logical uint8 strip data. The software additionally creates a serialized row of at most **1,440 bytes** for CS66's i16 domain or **720 bytes** for CU66's uint8 domain. SHA state, input FIFO, control, addresses and implementation temporaries are additional. The i16 zero high bytes can be generated during serialization; the larger preimage is not evidence of twice the DDR reads.

The Python `hash.update` call consumes a row synchronously. A physical SHA engine may stall. The strip cannot be overwritten by the next tile band until all eight prior rows have been accepted. Either stall the decoder at that boundary or provide explicitly costed buffering, such as a second strip and bounded FIFO. A single-strip result does not prove that simultaneous strip fill and drain are possible with the selected RAM ports and clock rates.

Select one declared profile per frame and keep its SHA context until completion or abort. The replay creates both domains simultaneously to compare them; two live domain contexts require two strips and separate SHA state. There is no implicit sharing merely because each individual proof uses one strip.

The component checks plane/y/x progression, sample dtype and geometry. It does not bind those tiles to an epoch, frame ID, bank generation or HUD. The frame controller must do so. `finish()` only returns a completed fingerprint; the caller must compare it with the expected output tag and complete every other frame check.

One error-handling detail deserves an integration test: a `feed()` after successful `finish()` raises, while an idempotent `finish()` can still return the earlier tag. The controller must treat any illegal input/closed-context exception as an aborted transaction. It must not ignore that exception and use the old completed tag to authorize a different frame.

## Scanout bounds and concurrent bank lifetimes

The display filter consumes **canonical, unfiltered** YUV. Filtered luma is display-only and must never be written into the prediction reference or passed to the canonical hash. RGB conversion follows filtering and chroma interpolation; the exact opaque RGB565 HUD words are applied last.

The v64 logical row-data bound is **7,200 bytes**:

| Item | Bytes |
| --- | ---: |
| Four cached vertical-filter Y rows | 2,880 |
| One pending corrected Y row | 720 |
| One returned Y row | 720 |
| Two raw rows for each chroma plane | 1,440 |
| One returned RGB565 row | 1,440 |

This bound assumes one outstanding returned Y/RGB row. Python callers can retain arbitrarily many returned arrays; a hardware or native integration must bound that queue and hold each line stable until consumed. The filter needs up to two rows of lookahead. DDR prefetch and arbitration must meet the actual panel deadline; pausing a pull iterator is not a pixel-clock or backpressure proof.

During overlap, the hash serves a provisional decode bank while scanout reads a published front bank. Their strip/cache lifetimes and access patterns differ. Count them independently unless a verified schedule establishes safe sharing. One hash strip plus one scanout context totals **12,960 logical data bytes**, or **14,400 bytes with the i16 serialized row / 13,680 with the u8 row**. These sums are bookkeeping, not measured peaks, minimum storage, BRAM fit or total SRAM use. Full banks, HUD, masks, SHA state, FIFOs, control, alignment and ports are excluded.

A valid 8-bit canonical YUV420 bank contains 518,400 logical sample bytes. Python i16 reference arrays occupy 1,036,800 data bytes instead. Hardware must choose and qualify its actual bank format rather than mix these sizes in a memory budget.

Reference acceptance and display-front switching are distinct events. A decoded P frame may become the next prediction reference before scanout reaches a safe vertical boundary. The old front bank can still be needed by scanout lookahead, outstanding DDR bursts or HUD composition. With two banks, the next decode may need to wait until that old bank is released; otherwise another bank or a different proven schedule is required. Do not overwrite a bank while any reader still owns a lease. Keep the HUD descriptor paired with the displayed bank until the same front-switch fence.

## Publication and recovery transaction

The future controller must complete the following transaction before publishing a candidate reference:

1. Validate the negotiated profile, epoch/IDs, geometry, envelope/CRC and reference binding against the currently owned bank descriptor.
2. Decode all entropy payloads with exact consumption/trailing-data checks; reconstruct and normalize all canonical samples. Tiles and bank writes remain provisional.
3. Complete the declared canonical fingerprint and compare the expected output tag. Validate HUD syntax, previous-HUD binding and reconstructed HUD output tag.
4. Drain candidate writes, ensure no late parser/entropy/HUD error remains, then atomically publish bank generation, reference ID, verified canonical tag and HUD state.
5. Switch scanout to the accepted descriptor only at its separate safe fence. Release the prior bank after all readers and outstanding accesses are done.

On a failure, discard the candidate/hash context and retain the prior published descriptor and HUD. Reset and epoch changes must also invalidate provisional work. Directed API tests establish unchanged Python state after late failures and recovery from an independent key. They do not implement a physical DDR write fence, bank lease or panel recovery mechanism.

## Profile negotiation and memory-fault meaning

CS38/GS38 is the unchanged compatibility contract with its pre-normalization output tag. CS66/GS66 removes that inner 16-byte tag and preserves the old `<HH geometry>` + planar little-endian i16 canonical/reference domain. CU66/GU66 also removes the tag but explicitly changes those domains to validated planar uint8. CU66 validates integer type, exact geometry and 0–255 range before conversion. These are different profiles: do not silently reinterpret a legacy packet or truncate out-of-range samples.

The Python candidates are explicitly configured at fixed epoch 25 and 720×480 geometry. There is no implemented live capability-negotiation handshake. References here to a negotiated hardware profile are requirements for a future deployment, not a completed network feature.

The new profiles retain the canonical truncated SHA256 fingerprint and all required CRC/HUD checks. Their one full-frame canonical hash does not mean one cryptographic or integrity operation for the entire frame. New-profile calls were spied on all 577 receives per profile; the old 1,705-call total is calculated from the directed-test-validated schedule of two calls for each of 26 keys and three for each of 551 P frames.

A cached verified tag assumes the reference bank remains unchanged under its owner. Read-only NumPy flags and immutable tag bytes are an API ownership contract, not DDR ECC. A privileged visible-bank fault that changes the next canonical output is rejected by the tested receiver; a hidden or non-propagating fault can leave the canonical output unchanged and pass. That counterexample is retained deliberately. Define the actual hardware ECC/fault/ownership policy separately; these unkeyed fingerprints are not authentication.

The current Rust/FPGA path remains **JPEG-only**. None of CS38, CS66 or CU66 is deployable through it as a new decoder backend without capability negotiation and implementation. A chunk parser accepting arbitrary bytes marked with the JPEG codec ID is not evidence that those bytes can be decoded. Retain JPEG for hardware bring-up while a negotiated experimental backend is developed.

## Evidence and test scope

The [v66 README](../experiments/python-game-canonical-tag-v66-study/README.md), [v64 README](../experiments/python-game-filtered-scanout-v64-study/README.md) and [v67 hash README](../experiments/python-game-hash-stream-v67-study/README.md) identify the component results and logs. V66 independently replayed 577 old causal presentations and 1,154 new-profile receives; its producer and independent directed suites contain seven and eight tests. V64 replayed 96 later-window frames / 46,080 scanout lines with exact luma, RGB565 and HUD checks. The hash replay covers 457 canonical frames in both domains and deliberate caller pauses. These are retained-input functional proofs, not new live capture or hardware execution.

Reproduction entry points, from the repository root and using the pinned environment:

```sh
PYTHON=/home/lori/gamebub-streaming-prototype/.venv/bin/python
(cd experiments/python-game-canonical-tag-v66-study && "$PYTHON" -m unittest -v test_model test_verify && "$PYTHON" verify.py)
(cd experiments/python-game-filtered-scanout-v64-study && "$PYTHON" -m unittest -v test_model test_verify && "$PYTHON" verify.py)
(cd experiments/python-game-hash-stream-v67-study && "$PYTHON" -m unittest -v test_model test_verify && "$PYTHON" verify.py)
```

This audit reviewed those source contracts and retained verification scope; it did not rerun or rewrite frozen campaigns. It adds no new end-to-end test result. A hardware integration suite should additionally interleave decoder stalls, delayed SHA row acceptance, full write queues and scanout pauses; cross plane and frame boundaries; inject wrong identity/profile, late CRC/HUD failures and reset; and prove that rejected candidates and unreleased front banks are never published or overwritten. Check canonical/ref hashes before and after display filtering to catch accidental feedback.

Do not add CPU receiver ratios, inverse-product counts, scanout traffic estimates, SHA round-demand ratios and QSPI lower bounds into a 30 fps claim. The illustrative iterative SHA demand at 100 MHz—31.10592 ms for old P-frame passes, 10.36864 ms for one CS66 tag, 5.18464 ms for one CU66 tag—omits a real engine's feed/control and competing memory work. A system proof needs complete unique-presentation timestamps, bounded queues, shared-memory arbitration, worst-case entropy/HUD/hash load and panel/input/audio contention on the fitted hardware.
