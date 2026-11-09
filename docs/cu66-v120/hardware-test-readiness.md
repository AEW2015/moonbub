# 100 MHz hardware testing and 30 fps

The existing V118 source handoff is the stable 100 MHz component control. Two fresh implementations passed with +0.061 ns setup margin. V119 also passed twice at 100 MHz, but with only +0.024 ns. These are exact decoder component source/tool/recipe qualifications on xc7a100tcsg324-1, not complete Game Bub board bitstreams.

V120 Source A passed its functional suite but failed routed setup timing at both clocks: −0.045 ns on one endpoint at 100 MHz and −1.847 ns at 125 MHz. It has no positive repeat and is not a qualified replacement. Source B subsequently passed all four functional proof stages and two separate fresh 100 MHz implementations at +0.174/+0.174 ns setup and +0.028/+0.028 ns hold. Its [qualified component handoff](handoff.md) binds that exact source; its 125 MHz route still fails at -1.517 ns. Source A or an older version cannot qualify B. Use the [current measured results](../../experiments/python-gamebub-v120/results.json) and a published source-bound handoff manifest, when available, for the final selection.

For V120 testing, export the exact Source B RTL using its [qualified handoff](handoff.md). Keep [V118’s handoff](../cu66-v118/handoff.md) as a separate control. The board team still needs its real top, pin/clock/reset constraints, memory-controller arbitration, ESP32/QSPI crossing and display path, followed by complete-design timing and board measurements. No board image was programmed by this study.

The [remote hardware instructions](remote-hardware-test.md) give the source export commands, integration requirements and evidence to return. The [fresh V118 export check](../../experiments/python-gamebub-v120/audit/stable-control-export.json) verifies source preparation only; it does not qualify V120 or run hardware.

## What the current model establishes

The row-oriented parent service fixture measures final accepted outer input byte to validated commit:

| Profile | Model cycles | Conditional time at 100 MHz | Remainder of a 33.333 ms frame budget |
| --- | ---: | ---: | ---: |
| Fast row service | 1,145,104 | 11.45104 ms | 21.88229 ms |
| Bounded-stall row service | 1,553,197 | 15.53197 ms | 17.80136 ms |

Those conversions assume the complete parent runs at 100 MHz; only component timing is currently qualified. They exclude the time before the final input byte and are not measured end-to-end frame periods. The model uses one independent keyframe plus recovery, software HUD semantic decoding, and an abstract single-lease 16-bit memory service. It does not demonstrate sustained distinct gameplay frames, calibrated physical memory/scanout contention or ESP32 execution.

The byte-at-a-time service takes 3,704,705/9,484,147 cycles, conditionally 37.04705/94.84147 ms at 100 MHz, already exceeding the frame budget. Hardware should implement and measure the row batching, rather than assume byte service will sustain 30 fps. The row results make 30 fps computationally plausible, but do not establish an achieved hardware frame rate. Both row fixtures also exceed a strict 10 ms budget at 100 MHz.

## Measurements needed on the board

First replay known local fixtures at the intended clock and compare complete decoded bytes/digests against the independent goldens. Record first/last accepted input, first/last canonical byte, validated commit, presentation start, request/response conservation, FIFO high-water marks, outstanding physical owners and stall reasons. Test backpressure, cancellation and a clean retry before adding the live network source.

Then run a sustained sequence of distinct frames through the actual host→ESP32→QSPI→FPGA path while display scanout shares memory. Count received, committed, presented and dropped frames separately. Measure frame periods and latency from explicit timestamps; do not obtain an FPS claim by taking the reciprocal of the post-input processing fixture. A 30 fps frame period is 33.333 ms (about 3.333 million 100 MHz cycles). Strict under-10-ms processing requires fewer than 1,000,000 cycles at 100 MHz, or fewer than 1,250,000 at a separately validated 125 MHz clock.

The next hardware handoff must identify its exact selected source composition and independently qualified clock. A passing clock from another candidate or a modeled parent is not a substitute for that identity.
