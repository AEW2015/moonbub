# SDR1 physical readback: response alignment failure

The qualified SDR1 BIT was loaded by volatile JTAG on November 5, 2026.
DONE=1 and USERID/USR_ACCESS both matched `53445231`. The app remained v32,
ELF `5bbb988144eeee7fcd96fb442573171f25912168fa94586a6a6fb2ce36e3e8fd`.
No ESP32, SD or persistent FPGA flash writes were made.

Private capture directory: `evidence/hardware-sdr1-20261106T003119Z` (UTC date).
BIT SHA-256: `6e6169edf630f63a878cda8da184c7a1176fc9deb13482d46a4887d4aa281be8`.

Three independently triggered runs (IDs 1, 2, 3) returned the same failure:

| Measurement | Each run |
|---|---:|
| Written words | 32 |
| Returned words | 32 |
| Word mismatches | 28 |
| Timeout | 0 |
| Busy GO rejections | 0 |
| First error word address | `0x100000` |
| First expected / observed | `1000` / `1101` |
| Response-valid mask | `7f80` (samples 7–14) |

Expected first burst, in returned-word order:
`1000 1101 1202 1303 1404 1505 1606 1707`.

Actual returned burst:
`1101 1202 1303 1404 1505 1606 1707 1707`.

The raw retimed input trace is:

| Sample | Raw word |
|---:|---|
| 0–4 | `1707` |
| 5 | `1000` |
| 6 | `1101` |
| 7 | `1202` |
| 8 | `1303` |
| 9 | `1404` |
| 10 | `1505` |
| 11 | `1606` |
| 12–15 | `1707` |

LTX mapping matters: logical probe `raw_trace_1` is physical port 3, the low
128 bits (samples 0–7); logical `raw_trace` is physical port 4, the upper
128 bits (samples 8–15). The analysis uses that actual mapping.

All eight expected words exist consecutively at raw samples 5–12. The first
response matches raw sample 6, consistent with the additional registered
response stage. Thus the response path omits the first available word. The
digital models previously placed the first word at sample 6 and did not
reproduce this physical timing point. This is a model/physical alignment gap;
it does not establish the fitted chip's CAS timing or measured PCB delays.

The camera showed the red failure raster. The full CPL1 BIT was not loaded
after this failed gate. Build50 was restored and verified DONE=1,
USERCODE `b0100004`, USR_ACCESS `4d424f50`, rollback BIT SHA-256
`a1ca6ce6b2c333a7c2ad4d29b94a7adf683dc49669d7f87fe3f80e63ef9ef3f9`.

## Known-good tester comparison and next repair

The operator reports the Godot SDRAM tester passed large read/write windows.
Its local SERDES4 reference is present under
`C:/Users/lavat/codex/gamebub/gamebub-source/fpga/vivado/sdram_serdes4`.
`rtl/serdes4_read_align.sv` explicitly takes capture delay and capture slot;
it does not infer alignment from pixel contents. Its model schedules CAS3
reads with `read_due=cycle+3`; do not change our CAS model merely to fit this
failure. The tester's different PHY cannot supply an interchangeable delay
number for this controller.

The next focused experiment should expose a latched response-start setting
in the small probe, compare waits 4 and 5 at unchanged frequency/phase, and
retain raw samples, configuration and fresh run IDs. Extend simulation with
the observed earlier first-word timing and require both positive and negative
alignment cases. Wait 4 is a candidate suggested by this trace, not yet a
hardware-proven repair. Do not rewrite the PHY or load the full CPL1 image
until literal burst readback passes. No 30 fps or memory-window sweep result
is claimed by these four-burst runs.
