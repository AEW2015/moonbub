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

At creation, source review and initial focused/sequential tests passed; strengthened packet checks, full-system replay, synthesis and routing are pending. No candidate BIT or new physical result is claimed.
