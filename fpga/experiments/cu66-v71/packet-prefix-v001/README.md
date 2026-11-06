# Isolated checked-prefix parser successor

`cu71_packet_prefix.sv` preserves the parent packet parser's ports, validation predicates, error ordering, arithmetic widths, abort/drain and metadata/commit/qmap semantics. It adds two private successful inner-header states to register prefix sums and then payload addresses. All existing debug-state codes are retained; new states are10/11. Successful parsing adds two clocks before byte136 is requested. Packet reads and committed metadata bytes are unchanged.

Parent SHA-256: `20d761a514073e8e5212eb70861f843441bc8d8f32b81bf7f02925cd202ae5a2`.

Candidate SHA-256: `b4c8dcb002adf8c3522a73a73f06bd928acb5bf83c953883647577486a9a8b1d`.

This is an isolated option following an actual first-DY final setup report identifying header→metadata-prefix/enable paths: `board-implementation01/setup-paths.rpt` reports header[56][6]→metadata_plane_addr[2][4]/CE at−1.439ns (16levels,8CARRY) and header[52][3]→plane_start[0][12]/CE at−1.420ns. That image had invalid legacy IO bounds and was not hardware-qualified. These are measurements of that frozen image, not timing for this candidate or v005. The v005 selected source remains unchanged. See [design and evidence distinctions](../../../../docs/cu66-v71/PACKET-PREFIX-TIMING-OPTION.md).

## Functional gates

- `evidence/focused02`: native Icarus four-state PASS18,090 checks. Checked-header injection covers1003 legal key/P prefix cases, exact code6-before7 and width/boundary errors,10,000 independent full-width modular arithmetic vectors, both new states' abort/reset/retry, and no early read/metadata/commit/qmap visibility. This gate is not a byte-RAM or canonical decode proof.
- `evidence/controls02`: actual Verilator byte-RAM baseline/candidate A/B, seeds6910/6911. Each checks12 native metadata-qualified packets plus23 structural rejections and five metadata-valid semantic-deferred packets,389,466 RAM reads and24,300 qmap results. Every structural case's exact error code matches the unchanged parent. Metadata, qmap, delayed-response/stall/held-commit and old three abort scenarios pass. Semantic-deferred cases are aborted, not falsely counted as decoded frames.
- `controls01` is a retained failed harness attempt: generated CRLF `cases.tsv` left a carriage return on the last path under Linux. LF generation fixes controls02 without a DUT change.
- `focused01` is the original command-recorded focused run; focused02 repeats the same frozen proof through the checked-in runner with a structured result.

`evidence/ooc01` completed matched unplaced exact-part synthesis: baseline−1.032ns, candidate−1.042ns at100MHz/1ns scalar IO; both worst paths are header[40][0]→error_code[0]/CE (19levels,9CARRY), the original32-bit validation/control cone left intact by this option. Baseline uses2436 LUT/3212 FF; candidate2464 LUT/3260 FF, both72 LUTRAM/no block RAM/no DSP. Functional qualification therefore does **not** make v001 timing-qualified. Root authorized the separate v002 validation pre-sum successor on this measurement; this source remains frozen.

No457-frame full archived rerun was performed. Full reconstructed canonical/HUD/pixel goldens require the parent's new whole-system integration replay with explicit parser module binding. Parser metadata success is not canonical SHA verification or frame publication.

## Reproduce

Run `scripts/cu66-v71/packet-prefix/derive.py` only to recreate this isolated source from the pinned parent. It fails if the parent hash changes.

Use unique output directories with `run_focused.py --output ...` and `run_controls.py --output ...`. The latter freezes actual sources, chosen byte fixtures and native metadata/qmap oracles and builds Verilator with two jobs. The two-state latency change alters random-stall RNG scheduling, so total clocks need not differ by exactly two times the accepted count under that schedule.

After functional gates, `ooc.py --output ... --work C:/<new-short-name>` performs sequential matched baseline/candidate unplaced exact-part synthesis at100MHz with1ns scalar IO budgets and private short TEMP/TMP directories. A successful report-generation marker is not a positive-slack or routed qualification claim. No timing exception, relaxed clock, speed-grade or PHY change is used. Read actual reports before selection.

No BIT, hardware, selected source change or 30fps result is claimed here.
