# Direct-display clock, reset and bundled-data constraint plan

This plan applies to the frozen PIPE display protocol and the isolated same-port `cu71_direct_scanout_syncsafe`/`cu71_lcd_lines_syncsafe` successor. It does not select a new board profile. The DY71 board top does not exist yet: its final hierarchy, generated-clock objects, reset wrapper and I/O timing must be checked after generation. No board clock, SDRAM path, reset tree or panel I/O budget is changed here.

## Clocks and reset

The observed existing `board/source-v007/moonshine_top_cu71.sv` uses a50MHz reference, a service PLL for100MHz memory, and a separate panel MMCM:50×56.375/(3×32)=29.3619791667MHz, period34.0576496674ns. The old standalone PIPE OOC used34.060ns. New leaf reports use the actual reference ratio; Icarus1ps quantization produces34.058ns. These are distinct recorded values, not a proposed clock change. Both generated clocks must keep their real clock-source relationship in the board; do not declare a broad asynchronous clock group.

The existing board reference jointly asserts platform reset on either clock-lock loss and releases each domain through its own four-stage chain. Later lock loss quarantines the diagnostic until reconfiguration. Reuse and requalify that policy in DY71; do not infer a working hot-recovery path. LCD/owner/backend/pixel state must be jointly flushed. Pixel-only reset, stopped-clock live recovery and an accepted SDRAM operation abandoned by a partial reset are outside this component proof. The standalone reset assertions flush the synthetic line worker too; they are not a physical SDRAM reset test.

## Exact crossings and capture bounds

`lcd` is the exact instance below the selected display owner. Prefix each object with the eventual selected display hierarchy, for example `system_core/scanout` only if the generated netlist proves that path. The leaf OOC prefix is empty. All selectors fail if a required exact register/pin is missing or duplicated.

| Crossing | Source Q | Destination D | Protocol and candidate bound |
|---|---|---|---|
| Request token0/1 | `lcd/request{0,1}_reg` | `lcd/request_sync{0,1}_reg[0]` | Only first stage asynchronous; bound10ns. Stage0?stage1 stays normally timed at100MHz. |
| Held request line0/1 | `lcd/request_line{0,1}_reg[0..9]` | `lcd/captured_line_reg[0..9]` | Payload changes with request toggle and stays held until completion. Capture uses the old second-stage token on the third memory edge: earliest20ns after launch. Bound each bank separately to10ns and5ns bus skew. |
| Frame token | `lcd/frame_toggle_reg` | `lcd/frame_sync_reg[0]` | Two-stage token chain; first-stage route bounded10ns. |
| Done token0/1 | `lcd/done{0,1}_reg` | `lcd/done_sync{0,1}_reg[0]` | First stage bounded one actual pixel period; stage0?stage1 remains normally pixel-clock timed. |
| Held completion error0/1 | `lcd/completed_bad{0,1}_reg` | `lcd/loaded{0,1}_reg` | Written with done toggle at final480th word. Pixel logic uses old second-stage done on third pixel edge: earliest2P˜68.1153ns. Bound one actual pixel period˜34.05765ns. Payload remains held through acknowledgment and until the next completed line in that bank. |
| Front-valid level | `front_valid_reg` | `lcd/valid_sync_reg[0]` | Stable memory-domain level; first-stage route bounded one pixel period. |
| Gray underrun counter | `lcd/underrun_gray_reg[0..31]` | `lcd/underrun_sync1_reg[0..31]` | One changed source bit per increment, source update at most once per active line. Bound10ns and5ns bus skew; `underrun_sync1?underrun_sync2` stays normally100MHz timed. Binary decode uses stage2 only. |

`pattern_enable` is tied0 in the selected owner; its retained ASYNC_REG chain is audited as a constant, not treated as a new asynchronous input. `request_epoch0/1` stays in the pixel domain. Cache context is captured locally from memory-domain `front_cache_slot`; generation/frame IDs stay wholly in the memory domain. Do not add false paths or bus exceptions to generation/context descriptors: there is no such multi-bit pixel crossing in this implementation.

The dual-clock line RAMs are vendor BRAM read/write ports. All480 words and the held completion flag precede done publication. The pixel path displays an entire black line when its tag/epoch/completion is not good. A bank may only be reused after its displayed line ends; a late writer must not touch a bank currently used for a good line. The protocol bench asserts that exclusion under bubbles, errors and held work. Do not replace this RAM ownership argument with a broad data-bus false path.

## First-stage functional fanout and the isolated successor

The frozen endpoint also reads `request_sync0/1[0]` in `requests_idle`. Native Vivado correctly reports those tokens as CDC-1 because first-stage outputs feed functional logic. That is not waived by this plan.

The legal source has a large quiet window: last request is raw(x494,y781); the next frame toggle is raw(x0,y0),28179 pixel clocks later (about959.710us at the actual board ratio). The assertion bench checks source launch location, payload hold, minimum bundle-capture age, held requests across vblank and reset recovery. This quiet behavior explains the old functional guard but does not turn first-stage fanout into a generic safe synchronizer or establish MTBF.

The new `syncsafe` endpoint removes every functional use of request stage0. `requests_idle` uses qualified stage1 tokens plus idle state and two quiet memory clocks. A frame observation is delayed four memory clocks and emitted only in that fixed qualified window; if busy, it is skipped until the next frame rather than delayed into active scanout. Descriptor/lease switching still requires the owner's complete drain fence. Panel timing/data and public ports remain unchanged. This is a separate candidate, never an in-place edit to the active grouped/PIPE source.

Native synthesis must prove each first-stage token output has only its second-stage D endpoint. Request payload and completed-error crossings remain manual bundled-data structures; expected CDC classifications are recorded individually, not globally waived. Real metastability behavior and MTBF are not simulated here.

## Applying and auditing constraints

`direct_cdc_candidate.tcl` selects exact source FF C timing startpoints and destination D pins (including C_Q), validates inherited ASYNC_REG attributes, reads the selected generated clock periods and rejects unexpected clock values. It creates no clocks and changes no I/O/reset/SDRAM constraints. Q-pin starts were rejected because Vivado reported path segmentation and empty bus-skew coverage. The corrected candidate uses legal source-register C startpoints; any segmentation warning or zero bus-skew endpoint count is a failed gate. Its bounds apply only to the listed paths; it does not cut clock domains or stage1?stage2 paths. Run it after the existing board clocks/I/O constraints, with an explicitly verified `DIRECT_DISPLAY_ROOT`.

`set_max_delay -datapath_only` also suppresses hold analysis on those exact paths; that side effect is explicit and relies on the held-data handshake, not on an added blanket hold exception. AMD documents this behavior in [UG903](https://docs.amd.com/r/2024.2-English/ug903-vivado-using-constraints/Consequences-of-Setting-Maximum-Delay-or-Minimum-Delay-Constraints-on-a-Path). The source-bound observed20ns/2P capture bounds and payload hold justify those endpoint-specific budgets. They do not justify cutting other paths.

Before any board selection, archive exact object counts, clocks, exception coverage/overrides, CDC classification, bus-skew results, normal intra-clock timing and routed physical reports. Keep required BRAM-clock and panel/SDRAM I/O budgets. A green synthesis summary after targeted CDC constraints is a leaf result, not board closure or hardware readiness. Unsupported crossings, object mismatches, clock/reset policy changes and remaining manual CDC items must stay explicit.
