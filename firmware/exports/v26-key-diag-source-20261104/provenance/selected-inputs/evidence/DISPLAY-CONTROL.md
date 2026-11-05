# Display calibration ABI: MRG1 + TIM1, build49

Offsets below use base0xE0000000. Discover oldcore magic/version plus buildID
0x184=0x4D424F49 before any write. Diagnostic MBD2 schema is unchanged. The
ordinary installed app remains compatible; a separate guarded USB app exposes
these controls. Settings are RAM-only; reset/reprogram returns safe defaults.

## Margin

| Offset | Read | Write |
| --- | --- | --- |
| 0x084 | Last accepted requested margin,0..80 | Full32-bit integer0..80 |
| 0x088 | Status below | Ignored |
| 0x08c | MRG1=0x4D524731 | Ignored |

Default requested/applied margin is20, with valid0/pending1 until startup
handshake applies it at a frame boundary. A margin changes scanout source-row
selection only; framebuffer/JPEG layout remains X0. Canvas covers landscape
x=margin..margin+719; left border=margin, right border=80-margin. Physical
active panel remains800x480. No pixels are rewritten/re-encoded.

## Timing

| Offset | Read | Write |
| --- | --- | --- |
| 0x090 | TIM1=0x54494D31 | Ignored |
| 0x094 | Shadow H word | Validated staging H word |
| 0x098 | Shadow V word | Validated staging V word |
| 0x09c | 0x00010003: ABI1,three apply commands | 0current,1official-derived,2custom shadows |
| 0x0a0 | Applied H word | Ignored |
| 0x0a4 | Applied V word | Ignored |
| 0x0a8 | Status below | Ignored |

Each H/V word packs SYNC[9:0],BACK[19:10],FRONT[29:20],reserved[31:30]=0.
Canonical six-value order is HSYNC,HBACK,HFRONT,VSYNC,VBACK,VFRONT. Current
preset0 is4,10,47,4,20,10: Htotal541,Vtotal834,Hstart14,Vstart24. Official-derived
v1.4 preset1 is4,119,2,4,2,3: Htotal605,Vtotal809,Hstart123,Vstart6. It is the
recorded fixed v1.4 profile, not an adaptive upstream production scheduler.
Custom preset2 uses the staged pair. Preset commands also update the shadows.

Active widths remain480native-horizontal/800native-vertical. Pclk stays nominal
29.361979167MHz, corrected ODDR D1=1/D2=0 and panel-falling timing model unchanged.
No PLL, polarity, panel SPI initialization, rotation, decoder or scaler change.

Validation uses wide sums: HSYNC>=1,HFRONT>=2;VSYNC>=1,VFRONT>=1;
VSYNC+VBACK>=2; HSYNC+HBACK+480+HFRONT<=1023;
VSYNC+VBACK+800+VFRONT<=1023. All fields are10 bits and high reserved bits must
be zero. RTL uses proven no-overflow12-bit carry-save sums (maximum3069), with equivalent threshold logic; host validators use checked/wide integer math.
These are implementation bounds, not a claim every custom profile is physically
supported by the panel. Reboot restores the default if a custom image is unusable.

Shadow writes never change display. An accepted command captures the entire
validated H/V pair and preset ID on one core edge. Invalid/busy writes leave
shadows/held pending request unchanged, except a valid H stage followed by a
rejected V stage leaves the accepted H shadow staged. There is no transactional
rollback of separate staging writes. Use one serialized writer, validate both
values before writes and verify both shadow readbacks before custom apply.
No display ever receives half of an applied H/V pair.

## Shared status encoding

Both status registers: bits6:0 applied margin or timing preset0/1/2;
bit7pending,bit8applied_valid,bit9link_online,bit10write_ready;
bits15:11zero,bits19:16last_result,bits23:20zero,bits31:24applied_seq modulo256.
Results:0RESET,1ACCEPTED,2APPLIED,3OUT_OF_RANGE,4BUSY,5LINK_RESET,6STAGED
(TIM-only). Results persist until another operation/rejection/ACK/link reset.
No clear command exists. Sequence increments on each actual apply ACK including
startup and reset replay. Pending includes the ACK-clear phase; do not overwrite
held payload until write_ready. A completion receipt requires pending0,valid1,
matching applied value(s), and sequence advanced from the accepted operation's
baseline. Last_result may describe a separate rejected interleaved write, so
sequence/value remain authoritative. Invalid requests take precedence over busy
for the reported rejection reason. No retry after an ambiguous transport write.

## Atomic application and CDC/reset contract

Independent margin/timing mailboxes use four-phase request/ACK levels. Payload
is held from request assertion through ACK deassertion. Two token synchronizer
stages precede pixel-domain payload capture. Pixel outputs change ONLY on the
LCD's real x0/y0 frame-origin edge. Margin and timing requests may apply on the
same edge or adjacent frames depending on arrival; they are not one combined
transaction. Both channels preserve whole-frame geometry. New timing fields
become visible together; x0/y0 itself is blank and valid for every allowed profile.

Each link has a core-online/pixel-armed/pixel-online rebaseline handshake.
An independently reset receiver cannot return a stale ACK as a new receipt.
A128-core-cycle ONLINE watchdog restarts a link interrupted during startup.
Reset pulses must be sampled by their respective clock domains; this matches
actual top-level four-stage reset chains. Pixel reset also resets the raster
and immediately sets margin20/current timing. Core-only reset leaves existing
pixel configuration unchanged until default20/current applies at a later frame.
Pixel-only reset automatically replays the last accepted desired configuration
once the link recovers; validity clears during recovery. No progress is promised
while a required clock/frame boundary is stopped. Firmware uses bounded polling
and reports timeout rather than assuming apply or resending blindly.

Only token first-stage D pins are exempted as asynchronous. Following recovery
stages remain timed. Held payload buses have explicit10ns max datapath bounds;
no payload-wide false paths or per-bit synchronizers are used. The existing
line-request CDC holds SOURCE rows0..719; source parity and tags are used for
odd margins. Source rows-2/-1 wrap modulo1024 to prime rows0/1 during blanking.
Prefetch window is physical y>=VSTART+margin-2 andy<VSTART+margin+718. Frame
origin invalidates line-cache epoch before the new frame's prefetch/scanout.

All defaults and runtime modes still require physical panel acceptance. No
sustained30fps, optical centering, arbitrary panel timing tolerance or electrical
pin measurement is implied by the calibration interface.

Reset-safety refinement: desired CSR values reset to defaults, but dedicated
transport_payload registers deliberately retain the old wire payload through
core reset until the pixel side acknowledges offline/cancel and ACK-low. Only
then is the next desired payload installed before link restart. A previously
captured pending operation may complete at a frame origin while cancellation
propagates; it must be a whole old payload, never a mixed configuration. Old
ACKs cannot count as fresh receipts. The stopped first draft and its failure
reason are preserved in v20-margin-build-attempt1-unsafe-reset; no hardware used it.

V3 timing-validator optimization is pure combinational equivalence: H fields
sum<=543 and V fields sum<=223 replace longer add-active-width/compare chains.
All32-bit input words including reserved/range guards were proved equivalent
with an isolated SMT solver and checked against actual old/new RTL vectors.
No command latency, interface, acceptance set or mailbox state changed.
