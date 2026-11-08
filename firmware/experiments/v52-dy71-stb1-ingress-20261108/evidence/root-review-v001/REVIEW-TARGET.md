# Independent V52 STB1 target/firmware review ? 2026-11-08

PASS for the isolated firmware source/build/package candidate. No blocking supported-contract defect found. This is not a hardware qualification or a claim that the paired FPGA passes routed timing.

## Exact sources and package

All592 entries in final-source-bindings.json match current frozen candidate files. Compared V48 source trees: native is byte-identical; handheld/src changes exactly the eight reported files (local.rs, local_usb.rs, mod.rs, network_driver.rs, network_usb.rs, newstb1.rs/tests.rs and diag_pages.rs). SDK defaults, Cargo.toml and target config are unchanged. V49 canonical Huffman, V50 READ slicing and V51 free-only probe optimizations are absent; V52 is an ingress comparison againstV48.

Target build receipt passes with no source/native changes. Built and published ELF match SHA285bc4953afd5c2dffc220bf512c33105642f18ed1f3ed4a1afa2080d7c48473. UF2 is pinned in bindings.json (prefix06f56805); release production parser reports13704blocks, Rev4/app-address/BIN-roundtrip pass. Static shared SRAM132076bytes remains below163840guardrail. Initial README/V52-READINESS.json source-only/pending-target prose is historically stale relative to these later root target/release receipts; use exact receipts for current build state, not those early status strings.

## Admission, bounds, ownership and errors

Actual network worker requires exactDY71 ABI3/caps3f, HBU1 and STB1 identities before Wi-Fi/native allocation or FPGA writes. The network driver repeats identity, fresh owner/counters and the STB snapshot checks before BEGIN. Legacy ABI2 is refused, with no automatic fallback. The separate legacy profile retains its old capability meaning and refusal tests.

Driver operations require bounded absolute deadlines and at most4096polls. Only Contended is retried and the actual Adapter can return it only when Device::try_lock failed before any SPI operation. Epoch is captured on read, then checked under the same lock as each descriptor/raw SPI write. SPI errors retain Io ambiguity, poison the ingress driver, and enter existing mutation-retained/quarantine behavior. Writes mark the MaintenanceGuard and counters before the SPI call; no silent resetting, reprogramming, taking another lease or releasing a failed endpoint was added.

The existing16384-byte network worker stack,98304-byte arena,8192-byte reserve and pre-Wi-Fi/native free/largest thresholds are unchanged. Native reserve/free sampling and failure diagnostics are unchanged. The new pure ingress object introduces no heap allocation; HU Vec allocation already exists and is not claimed removed. SDK/DMA internals may still allocate/copy.

## Payload representation and aperture safety

PacketBuffer is exactly1024bytes aligned4, replacing the existing input array. There is no second1KiB payload or u32[256] bounce buffer. Source HU caching and source CRC occur before in-place per-word byte reversal. At most3padding bytes are saved locally; all valid source/padding bytes are restored on every returned payload result, including bounded contention/deadline/short/epoch/owner/Io errors. This guarantee covers Rust Result returns, not process abort/panic or lost power.

Actual staging payload borrows the caller's transformed slice, uses one16MHz Bits32/no-swap/autoincrement SPI transaction atE0000C00, and checks exactC00, nonempty multiple4, aligned4 and<=1024 BEFORE locking. Driver stage_chunk rejects valid>1024 before descriptor creation/write. Valid final tails pad to<=1024. Metadata is one20B transaction; reads use at most24B. Prefix ACKs require exact native committed CRC/prefix, generation/ticket, empty/unarmed/unblocked/fault-free status and native faults0; final SEAL/START/HUD/commit/presentation verification remains.

This cap matters because the selected FPGA endpoint forwards12-bit core addresses and does not drop an overlongE0001000wrap. Exactly256payload words stop atFFC; no257th completed word means no wrap-write. Supported driver cannot cause it. Hardware hostile-host aperture isolation is not claimed.

## Explicit new boundary receipt

Per root request, added only fresh test-harness/evidence adapter-shim04, leaving all application/final-source hashes untouched. The actual candidate Adapter impl is text-identical to its SDK-shim include. Eight SDK-mock tests pass, including aligned1028-byte raw payload rejected before Device lock, read/write/transaction counters, guard marking or SPI; the same aligned buffer's exact1024-byte slice then succeeds in one transaction with original pointer. A source-extracted actual STB driver plus original model tests passes24cases: added valid1028 stage_chunk must failBounds before any descriptor, rawwrite or snapshot read, restore storage and poison the driver. These are extra reviewer gates, not included in the original201count.

## Offline test accounting and stack limits

Original final host receipts contain201Rust executions, not201independent newcases:104existing regressions +23STB tests repeated in4crates +3integrated profile tests +2rerun legacy-boundary tests. The seven original SDK-shim03 cases are separate; shim04 reruns/extends them as described above. Host source-check reports unchanged192inputs. Pure zero-allocation instrumentation covers actual identify/bind/stage/finish with pre-reserved model transport storage; it does not prove SDK allocation behavior or physical DMA.

Independent target disassembly shows network_usb::worker static entry5200bytes and monomorphizedrun_sequence_mode entry4000bytes, both identical to exactV48. Prologues are retained alongside this report. This checks only those function frames, not the maximum nested call chain, interrupt/SDK demand or runtime low-water; physical V52 stack/memory remain unproven. Do not infer safety solely from the old physical2904-byte low-water.

Paired STB1 full-system/pin evidence is separately retained under staging-burst-v1-20261108. Synthesis maps the FIFO toBRAM, but root owns active P&R; final routed setup/hold/CDC/DRC, exact new image identity, firmware/image pairing and controlled physical regression are still required before hardware readiness. No liveCU66 encoder,120-secondMassEffect playback or30uniqueFPS is established here.

Reviewer did not edit frozen firmware/native/RTL, rebuild the target, touch shared build outputs, access hardware or launch Vivado. Only reviewer reports and explicitly authorized fresh offline harness/evidence were created.
