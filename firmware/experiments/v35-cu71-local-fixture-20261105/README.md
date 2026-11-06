# V35 CU71 guarded local key/P firmware (offline)

This sealed successor of v34 adds an explicit USB `G` local fixture worker. It does not advertise CU66 networking or a streaming frame rate, autoprogram the FPGA, or modify SD/KVS settings. JPEG/AV/default features are retained. Its SDK configuration exactly matches v34: ESP193/IDF5.4.3, C++ exceptions enabled with1024-byte emergency pool, RTTI/PSRAM off. V32 remains installed; no hardware/flash/serial/JTAG access was performed here.

## Local operation

`G` first requires idle shared ownership, sufficient internal heap, CU71 magic43553731/ABI00010000/localcap7, a stable ESP programming epoch, idle command/staging state and fresh0accepted/0presented/0rejected counters. Other images are refused before writes. The explicit worker has a12288-byte stack; CPU-only `W` remains an8192-byte worker. Both are lazy and mutually excluded by existing ownership policy.

It uploads the two unchanged original CU66 key0/P1 packets from flash, checks actual stored byte count and CRC, seals and starts each allocation. It snapshots the typed HUD request by ticket, gathers the original HU through real PACKET_READ32 operations and compares the returned bytes with the original packet. The bounded native endpoint performs actual PREPARE and validates its decoded tag/identity. Every21120 candidate word is transferred through completed HUD_WRITE mailbox operations; everyactual SDRAM HUD_READ word is then compared with the native sealed candidate. Only after allwords match does firmware perform the native external-drain ACK and submit HUD_DRAIN using that verified candidate tag. Software COMMIT/ABORT commands execute the real endpoint operation with echoed and status-body identity checks. Completion additionally checks accepted/presented counts, accepted/front IDs and actual accepted canonical tag against the original packet. Physical RGB/video readback is not exposed by this ABI and is not claimed by this worker.

Mailbox fields are cached under the exclusive lease to avoid redundant writes. Sequence wrap refuses before mutation; command ACK/status/data, generation/frame/reference, packet span, candidate bank, tag and all read bounds are checked. Scalar mailboxes are a correctness path, not a throughput design. This profile requires the FPGA's explicit30-second lab owner watchdog; SDK observes through a40-second frame window. Deadlines are cooperative between bus calls; individual SPI WCET and target HUD CPU/heap/stack remain unmeasured.

## One-shot lifecycle and recovery

A successful fixture ends as **completed_held**, preserving the native accepted HUD cache and maintenance lease while FPGA accepted/front state remains valid. It reports reconfigure_required and parks without releasing paired state. Any ambiguous error after an attempted mutation additionally quarantines and parks with both endpoint and lease retained. There is no automatic clear/reset, no rollback after commit, no unsafe pending-operation recycling, and no assumption that a JTAG identity change establishes coordinated quiescence. A wrong-identity/no-write refusal can release its unissued guard.

This is deliberately one-shot. Reuse requires a confirmed paired firmware/FPGA reset or a future independently reviewed lifecycle fence; the current worker implements no resume/release command. A full handheld power cycle is the defined operator recovery for this diagnostic software. Merely restoring another FPGA image does not make the parked SDK context claim recovery.

## Evidence

- Twelve host tests execute the actual Rust driver and actual bounded native C++ endpoint through C ABI, against an explicitly modeled mailbox/SDRAM control peer. They verify both key/P readbacks, no writes on identity/freshness/sequence exhaustion, corruption preventing drain/commit, bounded missingACK handling, and actual native accepted-cache retention after lost postcommitACK and success. This is not an RTL/SPI cosimulation or physical result.
- Exception-enabled target check and release/link passed offline with locked dependencies. Production DFU parsing validates all13140 UF2 blocks and application-only Rev4 identity/ranges.
- Exact selected target ELF frames: localrun3104bytes, worker608bytes, USBcommand416bytes; individual frames do not prove fulltask headroom. Static shared SRAM130924bytes, unchanged from v34. New worker stack/TLS/TCB and dynamic allocations are additional.
- The existing native port's457history/20key byte-exact oracle campaign remains applicable to unchanged native source; its110730-byte host requested-allocation peak is not a target heap bound. CPU W and local G carry physical measurements for future testing.
- SDK observations record packet-complete, admission, HUD CPU/validated result, writes/readback/drain, software ACK and presentation-observed times on the same ESP clock. These are control-link observations, not FPGA first/last visible pixels or the full under10ms validated-decoding metric.

The old target-check/sourcev001 is preserved but hardware-ineligible because source review found nativecache drop on return. Sourcev002 repairs ownership; final sourcev004 additionally retains exact mailbox/readback failure context and is the packaged candidate. No physical fixture or30fps/under10ms result is established.

Final release: release-cu71-local-fixture-v002, ELF8dab6aed3ded35e4dc77c740caec08a8446d71e9deecb6c63efbd9e47a33ebc0; UF2ba43fc807a6d37d37fb89945708cbe60d920e2552077892bd55a5d737c5c3b5c. Images remain uninstalled.
