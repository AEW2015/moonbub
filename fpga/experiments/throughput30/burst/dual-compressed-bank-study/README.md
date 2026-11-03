# Hypothetical two-bank compressed JPEG ingress

This is an isolated **Python ownership and timing model**, not a modified FPGA design. It compares the captured three-frame workload and synthetic 30 Hz producer from `../scheduled-30hz-model/` with a hypothetical second compressed-JPEG bank. No target firmware, production RTL, synthesis or hardware changes are made.

## Why the current core cannot overlap these operations

`fpga/rtl/moonshine_core.sv` has one `compressed` array, one set of frame metadata and CRC state, and a single `receiving/decoding/draining/pending` state. `ready_state` is false while any of these phases is active. The QSPI register interface exposes a single length, ID, expected CRC and remaining byte count; payloads written at `0x100` go to the one selected-by-global-state buffer. The firmware's `begin()` checks this ready bit before starting and `forward()` checks remaining compressed-frame capacity. The experimental CDC-credit endpoint also has a separate FIFO credit register; free frame bytes are not FIFO credits. Simply allocating a second array cannot make the current protocol accept the next JPEG safely while the first decodes or waits for vblank.

A real candidate would need explicit per-bank `FREE → RECEIVING → READY → DECODING/PENDING → FREE` ownership, independent ID/length/CRC/marker state, and atomic publish of a fully received, CRC-valid bank. The QSPI protocol would need an unambiguous bank/frame generation and separately specified frame-byte and CDC-FIFO credits. A stale write, duplicate, incomplete frame, oversize length, CRC error, overflow or abort must invalidate only the affected bank; old commands and late packets must never address a newly reused bank. The decoder must consume READY banks in a specified order, arbitrate memory bandwidth and release the compressed bank only after it can no longer read that bank. This study conservatively keeps the bank occupied until display publication; earlier release could be possible only after verified final read and ownership handoff.

Two compressed banks do **not** create a second decoder or a third display framebuffer. A READY frame may still wait behind the current decoder, SDRAM drain and display ownership/vblank. A receiving-bank abort must not accidentally cancel a different frame that is already pending; a lost or ambiguous abort ACK requires a defined quiesce/recovery path. The separate `../abort-study/` demonstrates an original-core abort coincident with vblank can publish the supposedly aborted frame, and its limited test-only priority candidate does not solve all stale command/CDC/ownership races. A dual-bank proposal must address that issue explicitly; this Python model assumes instantaneous successful per-bank abort and does not validate it.

## Rough Artix-7 block-RAM budget

The project handoff names `xc7a100tcsg324-1`; the connected board and actual memory population were not verified there. AMD's [7-series overview](https://docs.amd.com/api/khub/documents/2LByHkO~nSZXcei2D55fTg/content) lists the XC7A100T with 135 36-Kb BRAM blocks. The [7-series memory guide](https://docs.amd.com/api/khub/documents/9gZGbqBxtlKXxBfkBt~lAg/content) explains the 32-data-plus-4-parity-bit organization and byte-wide write options. The current array is a 32-bit-word, byte-write memory; a simple width-32 mapping without packing extra payload into parity bits gives the following **capacity arithmetic only**:

| Maximum compressed bytes per bank | Approximate 36-Kb blocks per bank | Two banks | Fraction of 135 blocks |
| --- | ---: | ---: | ---: |
| 32 KiB | 8 | 16 | 11.9% |
| 64 KiB | 16 | 32 | 23.7% |
| 256 KiB (current `MAX_BYTES=262144`) | 64 | 128 | 94.8% |

These figures exclude the JPEG decoder, line buffers, FIFOs, frame-control metadata, other RAM, placement constraints and parity packing; they are not actual synthesis or fit results. Two full current-size banks would leave very little nominal BRAM on the named part. A smaller bank would require an explicit protocol/encoder cap and a safe oversize drop **before any write**; the existing protocol allows up to 256 KiB. The three captured synthetic JPEGs are 26,159, 26,358 and 26,991 bytes and fit 32 KiB, but this small sample does not bound future game frames. External SDRAM-backed compressed storage is another architecture to study, but concurrent scanout/decoder/ingress arbitration, latency and physical SDRAM timing are unverified.

## Three-frame comparison

The model uses exactly the hash-verified guest-produced bodies and the **same synthetic producer, 30 Hz BEGIN schedule, 1.2 ms DATA spacing, assumed QSPI service, five-slot FIFO and fixed 33.97969 ms post-commit decoder/display delay** as the one-bank study. That delay was the maximum of one earlier finite RTL sample, not a hardware timing bound. The two-bank hypothetical uses 32 KiB per bank and one decoder, and keeps a bank until modeled publication. CPU, guest, network and abort execution time are not modeled. See `../scheduled-30hz-model/README.md` for the source/queue limitations and why frame 2's recorded event stream already overlaps a hypothetical fourth 30 Hz BEGIN.

| Modeled architecture | Presented IDs | Dropped IDs and reason | Maximum FIFO occupancy |
| --- | --- | --- | ---: |
| One compressed bank | 0, 2 | 1: BEGIN while prior frame pending | 1,039 bytes |
| Two 32 KiB compressed banks | 0, 2 | 1: recorded guest ABORT after accepted partial frame | 1,039 bytes |

In the two-bank model, frame 1 is admitted into the free bank while frame 0 is pending; its recorded guest ABORT arrives at 64.35333 ms while frame 0 presents at 66.19969 ms. The model keeps frame 0 intact. Frame 1's final datagram was deliberately corrupted in the earlier guest capture, so it cannot be an additional valid presentation in either model. **This trace therefore shows admission overlap, not an extra valid frame, improved throughput or 30 fps.** Modeled capture-to-publication ages for valid frames remain 66.19969 and 67.39969 ms in both cases. All input/drop/present actions are in `results.json`.

`OUTPUT=/tmp/repro.json ./run.sh` runs five directed checks and regenerates the result; the saved JSON reproduced byte-for-byte. The tests cover captured-workload state isolation and CRC, an oversize cap, FIFO overflow, and a separately constructed tiny synthetic control in which two READY/PRESENTING banks block a third BEGIN while preserving presentation order. None is RTL or physical timing proof. Next steps would include a bank-aware protocol and FPGA ownership specification, actual Vivado resource/timing checks on the correct part, directed abort/CDC/vblank tests and a valid multi-frame workload before claiming an advantage.
