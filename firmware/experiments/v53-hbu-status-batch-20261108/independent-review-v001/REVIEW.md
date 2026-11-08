# Independent review: V53 HBU1 status batching

Review date: 2026-11-08

## Finding

The V53 implementation is consistent with the reviewed V48 HBU1 contract. The application change adds one `Bus::hbu_status_words` method whose default implementation retains the four scalar reads, while the concrete USB/FPGA adapter overrides it with one 20-byte read beginning at `0xe0000608`. It decodes big-endian words 0, 2, 3, and 4 into the same four values used by the previous checks. Word 1, `packed_loaded`, remains observational. The driver keeps the existing flags mask, mode bit, completion count, packed count/offset, and ticket comparisons.

The concrete adapter uses the existing 16 MHz, 32-bit, no-byte-swap, incrementing SPI command and the existing `Fpga::spi_read` implementation. That implementation emits one SPI transaction with the command/address, its normal dummy read bytes, and the requested 20-byte read buffer. The helper returns `Contended` before counters or SPI on a failed device lock, checks the established programming epoch before the transfer, increments read accounting by five words and transaction accounting by one, and maps a SPI failure to the same I/O error. The driver still checks its deadline and yields/retries on contention around the bus operation.

This review found four application-source differences against the exact V48 tree: `diag_pages.rs` changes the diagnostic variant label; `local.rs` adds the backwards-compatible trait default; `local_usb.rs` adds the physical one-transaction override; and `network_driver.rs` calls the helper while retaining the old validation expressions. No changes were found in the eight native source files, `handheld-dfu/src`, `handheld/tests`, or the remaining handheld application source. The one additional test-file difference is limited to canonical fixture paths in `tests/network_driver.rs`; it relocates references to `C:/moon/publish/host/dy71-sequence-v3` and does not alter test logic.

## Evidence reviewed

The V53 host run at `C:/moon/builds/v53-host02` records 24 compile/test steps, all with return code zero. Its Rust test logs total 104 passing tests. `source-check.json` reports 189 hashed source and fixture inputs unchanged during the run. The earlier `v53-host01` network driver compile failed because a relocated test tried to resolve `../../../../host/dy71-sequence-v3/frame3.cu66`; V53 changes those test fixture references to the canonical published path, and host02 passes.

The adapter shim at `evidence/adapter-shim01` extracts and compiles the actual `hbu_status_words` method from `local_usb.rs`. All six tests pass. They check the one 20-byte SPI call and four-field mapping, ignored packed-loaded word, busy lock, missing/mismatched epoch, and I/O failure accounting. This shim verifies the concrete helper's request configuration and response mapping with a fake FPGA object; it does not execute the ESP32 SPI driver or physical hardware.

The V027 pin experiment at `C:/moon/dev/experiments/hbu1-status-span-20261108/attempt04` passed four cases using the actual installed Xilinx `RAMB18E1` model. It compares the original four scalar status values against one contiguous five-word QSPI read after successful command 23 ACKs for read/write modes and counts 1, 17, 256, and 128, with phase, clock-rate, stall, payload-readback, and post-ACK fault coverage. This verifies the selected RTL-side sequential address span and stable values in those exercised cases. It complements the adapter shim; it is not a complete hardware run of the Rust adapter.

The release package hashes match `release-hbu-status-v001/hashes.json`: ELF `023158630c563e3619394b6efd70ac88a39ccd785720c35a82f6af1931e2b734` and UF2 `9701ad4c20d5a50896cfe45c0066f7d8e595b15c7c7e6add5949e5116e55c20a`. The recorded release build uses locked offline Cargo release settings and records no source or native changes. The target-run01 result agrees with the packaged ELF hash. The package checks ELF-to-image generation, image information, UF2 generation and parsing, and memory budget.

## Limits

The RTL evidence and source reasoning support equivalence for the tested sequential reads after successful command 23 completion under exclusive ownership and the tested conditions. They do not establish a general atomic snapshot property. No firmware was run against the physical board, and no runtime throughput improvement was measured. The offline pin test uses synthetic owner/AUX memory; the adapter shim mocks `spi_read`; hardware and full decoder/SDRAM behavior remain outside this review.

## Bindings

`bindings.json` records baseline and candidate file hashes for every changed application/test file, aggregate hashes for reviewed source areas, the host and adapter evidence identifiers, the selected V027 pin experiment, and release artifact hashes. It also records the source-hash manifests that establish the full V53 host run inputs.
