# Independent final review: V54 and V55

Reviewed the curated candidates against their frozen originals, target build records, release manifests, selected static analysis, source composition records, and preservation bindings. This is a read-only audit; no build, installation, or hardware operation was performed.

## V54 failure diagnostics

The V54 delta over V52 is four modified tracked files (`diag_pages.rs`, `cu66/mod.rs`, `cu66/network_io.rs`, `cu66/network_usb.rs`) plus the new `cu66/stb_failure.rs` module. The selected path is called only when the network run returns an error. On success the lazy context closure is not evaluated and it adds no CSR reads or diagnostic log lines.

On failure, the observer attempts at most thirteen reads from 0x700 through 0x730, once each, under the existing retained guard and epoch-checking Adapter. Its 20,000 microsecond budget is checked before each call; it is not a hard deadline because one SDK SPI call can overrun it. There are no writes, retries, or yields. Four STBF1 records carry masks/error state, independent progress/current-identity context, and a CRC; the maximum payload is 186 bytes. Sampling is post-failure and non-atomic. Prefix/CRC words can be masked while the FPGA fence is false, and best-effort log delivery does not establish failure-onset time or complete RF receipt. V54 preserves STB1/ABI3/caps3f and the prior wire, error, native, and HBU1 state transitions.

## V55 composition and guards

The V55 composition proof records PASS and limits its delta over V54 to these seven files: `local.rs`, `local_usb.rs`, `network_driver.rs`, `network_usb.rs`, `diag_pages.rs`, `native/endpoint.hpp`, and `native/hud.hpp`. The source pins select V49 Huffman arrays, V50 bounded READ slicing, V51 revision 2 free-only callbacks, and V53 HBU status batching. Six other native files remain exact V48. The V54 STB1 wire and failure-observer guards are recorded as preserved.

Reviewed guards remain: 16,384-byte network worker stack; initial heap admission of free >= 114,688 and largest >= 24,576; 98,304-byte native arena; and 8,192-byte reserve. Raw 512/1024-byte bounds remain critical, with no new defense against arbitrary oversized raw QSPI transactions. The 64-bit native arena test peaks (95,053 bytes for the 12-frame case) do not measure ESP32 fragmentation or prove available physical heap.

The V55 target memory report counts 132,076 bytes of static shared SRAM against its 163,840-byte guardrail, and passes that build guard. The report states the data-cache option is 16 KiB while IDF configures 32 KiB and returns 16 KiB to heap. The compiled configuration enables the FreeRTOS stack canary, while compiler stack-check mode is NONE. PSRAM support appears as SoC capability; these records do not demonstrate enabled or available PSRAM at runtime. No runtime free/largest heap, reserve headroom, task high-water mark, canary event, or physical stack margin was measured.

V55's captured target `.su` file is hash-bound in `target-stack-v001`; it reports `cu66::huffman` at 752 bytes and `cu66::channel33` at 160 bytes. V49's recorded control/candidate `.su` comparison is 192->752 bytes for Huffman (+560) and 144->160 for channel33 (+16), a +576-byte local frame change. Read-only disassembly of the selected V55 ELF showed `entry a1, 0x2f0` (752 bytes) for Huffman and `entry a1, 160` for channel33. These are individual static frames, not a complete worst-case call-chain or runtime stack measurement. Runtime stack safety remains UNKNOWN; no physical stack-safety claim is justified.

## Target image and source integrity

Both copied target build records report return code 0, empty source/native change lists, and `hardware: false`. I independently compared every path in each `source-before.json` and `native-before.json` with the corresponding curated source tree: zero mismatches for both variants. For V54 and V55, the release ELF, BIN, and UF2 hashes match `hashes.json`, the UF2 metadata, and the per-file preservation manifest. Release verification records show successful image generation, image inspection, UF2 parsing, and memory guard commands. This verifies artifact identity and packaging only; it does not mean either image was installed.

## Qualification state and limits

V54 has a target-built package, but its historical README and readiness document predate the subsequently recorded target build and still say the target build is pending. The later target/release evidence is the controlling artifact record. V55 likewise has a selected target image and static SRAM guard pass despite historical README/readiness strings describing the earlier pre-target state. Preserve those historical records as-is; a separate current-status document should explain the chronology.

Both package metadata records say hardware was not tested. The copied target build results say hardware false. Installation and runtime are therefore NOT_INSTALLED / UNKNOWN. V55 retains an explicit Huffman stack-growth risk. There is no physical comparison, runtime stack proof, measured performance result, or new hardware qualification in this review.

## Evidence index

`bindings.json` gives exact paths, sizes, and SHA-256 for the reviewed release images and manifests, target records, source/native bindings, V55 composition and stack evidence, V49 comparison frames, and relevant source files. The curated `preservation.json` files bind every copied file back to its origin.
