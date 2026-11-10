# V124 portable endpoint probe

This bounded host experiment connects the actual Sunshine native `gamebub::msv1::packetizer_t` output directly to the actual Moonbub Rust `streaming::protocol` receiver in a separate host process. It does not invoke image capture, JPEG encoding, socket send, a Sunshine session, ESP-IDF, firmware task/session glue, CPU/Wi-Fi timing, DMA, QSPI, RTL, or hardware. Container wall time is not endpoint timing.

## Pinned inputs

The probe snapshots Sunshine at Git HEAD `3d49c6fe87753eb5b35d693991fdff0365e4bbbf` and Moonbub at Git HEAD `1d462803bf2a638f25c2d13bd2215ca08a30518d`, verifying each copied production file against its Git blob. It feeds the shared pre-encoded 720×480 JPEG and `receiver-pattern-msv1-packets.bin` fixture (frame ID `0x12345678`, capture timestamp `1234567890123`, 1024-byte payloads). The fixture files are byte-compared across both repositories and pinned by SHA-256 in each attempt receipt.

The C++ driver calls the actual Sunshine packetizer for 1024-, 100-, and 1-byte chunks; Python does not produce packets. The Rust wrapper includes the copied actual `protocol.rs`, calls `Header::parse`, `Receiver::accept`, and `feedback`, and commits reassembled JPEG bytes only after Rust reports `done`. Python only parses u16 framing, mutates native datagram output for fault cases, and independently checks IEEE CRC32 and recovered file bytes.

## Cases and bounds

The bounded attempt checks byte-for-byte equality of the native 1024-byte packet stream against the shared golden, successful reassembly at all three chunk sizes, and the Sunshine packetizer's empty/oversized frame, invalid chunk, and invalid offset guards. Fault sequences cover loss, reorder, duplicate, truncated final datagram, corrupt final payload, stale frame ID, uint32 frame-ID wrap, and recovery with a newer frame. Error names are emitted by the actual Rust `Error` enum; the harness checks the expected backend error and the actual completion/feedback records.

## Run control

The preparation command creates an immutable attempt snapshot and performs no compile/run:

```sh
python3 scripts/cu66-v124/endpoint/run.py --prepare-only
```

A native attempt requires the explicit root grant and immutable image ID already pinned in the script:

```sh
python3 scripts/cu66-v124/endpoint/run.py --run --root-grant ROOT_V124_ENDPOINT --attempt experiments/python-gamebub-v124/endpoint/attempts/<attempt>
```

The launch uses a network-disabled container capped at two CPUs, 8 GiB memory and 8 GiB memory-plus-swap, with finite watchdog and host memory/PSI checks. Every attempt retains source snapshots, exact compiler commands and versions, binary/output hashes, per-case receiver records, resource samples, and failures. It is a packetizer-to-parser control only; it does not join the endpoint to Moonbub's production session or hardware path.

## Selected attempt

The selected passing receipt is `experiments/python-gamebub-v124/endpoint/attempts/20261110T040425114351Z-6a1d1432/receipt.json` (SHA-256 `d7eba5bc52afc856344810bcb9ee544dc9d7a76c899520a349a4735b449fbfd5`); the direct receiver result is `out/result.json` (SHA-256 `f3870ed9802cb611645d597fdbfe2c0594ce6d29149126dceb80d98eaa2867ee`). A stable selected-result pointer is `experiments/python-gamebub-v124/endpoint/results.json`.

The native 1024-byte packet output is the exact 27,251-byte golden, 26 datagrams. All three chunk sizes recover the exact pinned 26,159-byte JPEG; the independent CRC32 value is `eceeb9c5`, and the C++ bounds probe passes six invalid-input cases. Fault tests retain Rust `Sequence` for loss/reorder/duplicate/stale ID, `Bounds` for truncation, and `Integrity` for corrupt final payload; newer-frame recovery and `uint32` max-to-zero wrap pass. Feedback bytes use the actual Rust `MSF1` helper and are checked against receiver `done` IDs.

The selected run used g++ 13.3.0 and rustc 1.99.1 in immutable image `sha256:e6e97e6db1c57d0f07530d7ae6912e455bb7079de7428f282a508a2fcca3fb5a`. Its approximately two-second container wall time is host compile/replay time, not ESP32 timing. The two earlier setup/compile failures remain preserved in their own attempt directories with logs.
