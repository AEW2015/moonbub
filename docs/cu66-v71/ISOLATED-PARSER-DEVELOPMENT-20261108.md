# Isolated parser timing development

The user requested continued isolated development after the overnight handoff. This phase supersedes the earlier no-further-builds note in `STB1-PARSER-NEXT-TIMING-PLAN-20261108.md`; it does not authorize device programming or Windows driver changes.

Branch: `feature/dy71-parser-stage-20261108`, based on `63b894057ae8d449c8f01b3386efb73a98410f27`. All working files and builds remain under `C:/moon`. The selected V028 release and JPEG/build50 recovery archive remain unchanged.

## Candidate and compatibility boundary

The candidate combines the previously reviewed HUD CE factor with one parser change: successful code-6 header validation enters a separate code-7 length-validation state before derived metadata capture. Existing state values 0–18 remain unchanged; state 19 is appended. Validation checks, error precedence, arithmetic widths, packet format, clocks, pins, external-memory timing and XDC exceptions remain unchanged.

Compared with the selected V028 sources, exactly two production RTL files differ. The receiver SHA-256 is `316123fb1db92d67a797b2a49263500314d5173561a2eff52ef451734f94deb9`; the parser SHA-256 is `39197a682b894f55d4a9a73ed039e58c0f3bed1aeb3a6cc24139c1c4d5325c56`.

The intended equivalence is qualified handshake/data behavior with one extra validation cycle. It is not exact cycle equivalence: provisional diagnostic fields can differ around abort, and the parent watchdog can win at a boundary where the previous parser would finish one cycle earlier. No timeout is widened. Existing V54/V55 custom-codec readers use qualified request/metadata state and do not depend on the affected provisional parser fields.

## Gates

1. Freeze exact source bindings and review the delta independently. Run focused boundary/error/abort/reset tests plus complete packet-handshake comparison, with direct metadata and every-qmap-byte assertions.
2. Replay actual V55 Rust/native code against the combined RTL and independent KEY/P image/HUD oracles. Require a runtime witness of the new parser state, so an accidentally stale parser cannot pass silently.
3. Synthesize one source-frozen build, inspect resources and local timing/CDC changes, then authorize place and route. Preserve all original constraints. A shorter parser cone alone does not establish whole-design closure.
4. Repeat the corrected twelve-frame full-system image/HUD comparison against the actual candidate. Preserve explicit simulation timing and memory-model assumptions; no simulated result is a physical throughput or stack-safety measurement.
5. Emit a distinct programming image only after positive routed setup/hold/pulse, complete routing, no DRC errors, exact source/constraint/identity checks and functional gates. Preserve failed attempts and the passing V028 fallback.
6. Publish evidence and remaining limitations on this separate branch. Hardware qualification remains a later step; no USB, JTAG, firmware update, driver installation or sender operation is part of this phase.

## Status

The frozen parser suite passes 57 complete packet comparisons, direct metadata assertions and 12,150 qmap-response comparisons per source. Focused candidate tests execute 68,053 checks. The actual receiver-control cutoff test confirms the documented one-cycle watchdog-boundary difference, with unchanged simultaneous-error precedence.

The actual V55 Rust/native plus combined RTL KEY/P replay passes: two accepted/presented, zero rejects/underruns, 42,240 actual HUD words written/read back, exact canonical/raster/HUD comparisons and exactly two runtime visits to the new parser state. Its 443.531-second host simulation duration is not target throughput. Full-system fault injection and radio/SPI/IDF behavior are outside that replay.

Synthesis passed against all 79 frozen inputs (31,593 LUTs, 31,264 FFs, 65 RAMB36, six RAMB18 and 37 DSPs). Clock definitions are unchanged and no internal endpoints lack constraints. The two inherited critical CDC endpoints remain; this is not a zero-critical CDC result. Corrected read-only cone inspection passed: all 48 plane-length capture FFs remain, with zero reference-tag startpoints/paths feeding their CE pins; reference-tag validation still reaches the parser state inputs. The earlier driver-query failure is preserved separately and is not counted as a passing query.

Placement/routing started at 12:54 UTC with the unchanged original implementation script. The complete twelve-frame replay passed: 12 accepted/presented, zero rejects/underruns, 253,440 HUD words written/read back, 6,220,800 canonical bytes and 4,147,200 video pixels checked exactly. Runtime state-19 visits equal 12; HX33 frames 0–8 followed by HU25 frames 9–11 pass, including the frame-9 reference to frame 8. Banks 0/1 are exercised; bank 2, poison memory, target heap/stack and physical throughput are not qualified by this run. Host simulation duration is 2,728.422 seconds with the documented model delays. Final routed closure, a candidate BIT and physical qualification remain pending. V028 remains selected.

The separate native-code diagnostic now reproduces the existing strict `-O2`/`-O3` warning in a reduced optional/custom-allocator lifetime example. Explicit value initialization produces the same diagnostics. No warning was suppressed and no firmware optimization change was selected; the cause remains unresolved. These compiler experiments do not establish a runtime memory fault or a false positive.

## Subsequent explicit driver approval

The user later approved one UAC prompt for the exact vendor-DFU node. Fresh associated-driver preflight V006 matched reviewed V005 apart from timestamp. The one elevated install returned successfully, then the helper's postcheck stopped because the Microsoft INF changed DeviceDesc to `WinUsb Device`. The original exit-1 error is preserved. Independent PnP inspection confirms the exact Rev0411 node has problem code 0, WINUSB service and Microsoft `winusb.inf`; the requested interface GUID is present. The install's reboot-required flag was not preserved and remains unknown.

A pinned read-only vendor probe then passed, followed by a full read-only backup of the 5 MiB factory slot, 192 KiB updater and 4 KiB partition table. The complete installed 3,504,688-byte V48 image matches its known BIN SHA-256. Raw backup bytes remain private under `C:/moon/backups/DFU-V48-READONLY-20261108-v001`. V54/V55 update plans were generated offline only. No flash write, reboot, FPGA programming or driver-install retry followed. Application composite/CDC return and actual update-write/reboot recovery remain separate unqualified gates; the handheld stays in DFU.
