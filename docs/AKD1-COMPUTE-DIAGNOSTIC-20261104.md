# Local FPGA KEY/hash diagnostic contract

Date:2026-11-04. This is a **local compute-only laboratory interface**, not a
network transport, advertised codec profile or live GM01 streaming endpoint.
There is no corresponding board image or installed ESP32 accessor yet. Current
offline work performs no programming; the user's existing hardware authorization
is retained for a later coordinated physical window.

The reference controller is
`fpga/experiments/ar03-board-diagnostic-20261104/ar03_fixture_diagnostic.sv`,
bound by manifest SHA-256
`4b1edb00c306ae8e71a003a2d6b67bff6e250c255465f5fb5f0ee400d7147a4b`.
Its functional fixture and control tests pass; its100 MHz implementation gate
fails. Later timing variants must retain this local interface or change its
schema explicitly. The current raster/GM01 experiments do not constitute a new
network or firmware release.

## Identity and isolation

Reserve **MBK1=0x4D424B31** for the first exclusive compute diagnostic. A future
board build must set both `BITSTREAM.CONFIG.USR_ACCESS` and readable core CSR
`0x184` to that exact value, and bind source/XDC/bitstream hashes in its manifest.
The inherited build50 value0x4D424F50 is a different image. The current board
core exposes its build CSR inside the JPEG module, so an exclusive diagnostic
shell must deliberately retain the readable identity independently of that
module. A register read is not a cryptographic configuration readback.

The restricted ESP32 accessor must verify all of these before a command:

- core CSR0x000 equals distinct AKD1 word0x31444B41, CSR0x004 equals
  schema0x00010000, and CSR0x008 advertises zero codec capabilities;
- core CSR0x184 equals MBK1;
- diagnostic CSR0x400 equals AKD1 word0x31444B41;
- diagnostic CSR0x404 equals schema0x00010000;
- the receiver, local video loop and AV/audio session are stopped, and the
  diagnostic worker owns its exclusive software reservation.

Normal network JPEG Connect and local video-loop entry must reject MBK1 before
calling the existing `ensure_core()` path. That function recognizes MBV1 magic
alone and can otherwise either treat a compute shell as JPEG-capable or reload
the SD-card JPEG image. Zero capability bits are necessary but insufficient as
the software guard. No fake ready state, video credit, successful video admission
or display completion is allowed. The diagnostic shell must not advertise JPEG
or custom network capability. It does **not** retain MBV1 at core0x000. Generic
framework controls, overlay and buttons remain in the separate0100xxxx region.
An old application may deliberately recover through its existing SD build50
reload path; the new diagnostic application rejects MBK1 before that path.

The current ESP32 margin/timing helpers also require MBV1 and known legacy build
IDs, so their existing USB commands do **not** work with MBK1 automatically.
Future SDK adapters must recognize either the existing exact legacy peer or the
strict AKD1+MBK1 diagnostic peer, then independently verify MRG1/TIM1 and their
schemas before allowing margin/porch controls. Do not broadly relax identity
checks. AV/audio helpers intentionally reject the distinct diagnostic peer;
retaining audio HDL and electrical outputs is not an advertised AV session or
playback capability. Shared admission must prevent a new network/local/AV
session from becoming active after the diagnostic's initial stopped-state check.

No arbitrary register address, payload size or SPI command is accepted from
USB. The allowed operation set is start, bounded status/result read, abort and
clear. A new command must be selected after checking the complete USB and margin
parser maps; lowercase `r` is already the CRC benchmark. Runtime `?` in v24 is
not this accessor. A dedicated bounded worker is required; the USB/UI thread must
not hold Device across the job or a polling sleep. Read failures retain an
unknown hardware state and the reservation until recovery, rather than enabling
a second run optimistically.

## Fixed compute workload

The first diagnostic replays one synchronous BRAM fixture through outer envelope,
GM01/map, CP02, exact KEY reconstruction, private raster ordering and canonical
tag checking. It uses full existing codec capacities; no limit is silently
reduced to fit. The observer is always ready and does not write a framebuffer.

- Packet:48,203 bytes, SHA-256
  `5a39857f436fc50daaa46fc518ab13f9c168fbdadabbe95ef8bf6eeff02c0518`.
- Geometry:720x480, epoch1/frame0;518,400 private Y/Cb/Cr samples.
- Opaque tag bytes: `c6c97dee75f2be10adddff19f0985885`.
- Tag byte0 occupies CSR0x430 bits[7:0]; words advance low to high.

Successful completion certifies this private **pre-HUD** KEY and tag only. It
does not implement HUD patch semantics, P/reference banks, AF03, framebuffer
publication, scanout, UDP reception or unique physical presentations/s.

## CSR words and state

All offsets are32-bit aligned relative to the existing E0000000 core region.

| Offset | Read / write meaning |
| --- | --- |
| 0x000 / 0x004 / 0x008 | Future shell AKD1 / schema0x00010000 / zero codec capabilities |
| 0x184 | Reserved diagnostic build ID MBK1 in the future shell |
| 0x400 | AKD1 magic0x31444B41 |
| 0x404 | Schema0x00010000 |
| 0x408 | Exact write1 START,2 ABORT,4 CLEAR; other values reject |
| 0x40c | State[2:0], busy bit3, DONE bit4, FAIL bit5, ABORTED bit6 |
| 0x410 | Accepted pipeline-start to terminal-event cycles |
| 0x414 / 0x418 | Observed samples / accepted fixture ingress bytes |
| 0x41c | Error stage[11:8], code[7:0] |
| 0x420 / 0x424 | Owner64 low/high |
| 0x428 / 0x42c | Completed epoch/frame |
| 0x430..0x43c | Tag128, low word first |
| 0x440 / 0x444 | Rejected commands / compute result sequence |
| 0x448 / 0x44c | Fixture byte length / watchdog cycle limit |

States are0 IDLE,1 START,2 RUN,3 DONE,4 FAIL,5 CANCEL,6 ABORTED. Busy means START,
RUN or CANCEL. START is accepted only when not busy and the next owner has not
exhausted its64-bit space. Owners increase monotonically until FPGA reset; reset
begins a new local ownership generation. Unknown commands and START while busy
increment the command-rejection count and cannot replace the current owner.

An accepted START clears previous counts/tag/fault/result identity. START waits
for the internal codec handshake, then resets elapsed to zero and enters RUN.
The elapsed count is independently checked against actual simulated posedges.
DONE and FAIL hold their results until another command. The result sequence
increments only for completion, child error or watchdog; it does **not** increment
on START, ABORT or CLEAR. It is a sampling counter, not a lifetime frame identity.

Stage15 is local:code1 completion owner/epoch mismatch, code2 RUN watchdog,
code3 START-admission watchdog. Other stage/code values retain the joined codec's
meaning. Read failure, missing completion or a watchdog cannot establish a frame
presentation.

## Snapshot and recovery rules

RUN counters are sampled live, not an atomic snapshot. To report a terminal
multiword result, the worker reads state/result-sequence/owner before and after
the payload and accepts the record only when both sets match a stable DONE or
FAIL state and the expected current owner. Retain the software capture sequence
and boot/diagnostic generation in logs. The worker reservation prevents another
local operator from restarting the job during those reads. A reset or mismatch
invalidates the record; do not splice words from different runs.
This is not reset-proof identity: an unseen external FPGA reset can restart the
owner and result counters and create an ABA observation. ESP32 program-epoch
tracking covers its own programming attempts, not external JTAG/reset. The lab
window therefore requires an exclusive operator and no external programming or
reset during a job; known reset/program events invalidate the software generation.

ABORT has priority over the job. It immediately masks/cancels the private child
path, enters CANCEL, then ABORTED one core edge later. It clears tag/fault but
retains owner, elapsed/sample/byte counts and result sequence. Consequently a
STOP receipt requires observing stable ABORTED and owner, not a sequence increase.
Completion can race between the pre-STOP read and the ABORT write, so ABORTED may
retain either the earlier sequence or an incremented completion sequence for the
same owner. Do not require the sequence to stay unchanged as the STOP condition.
There is no external SDRAM/DMA in this diagnostic; this cancellation is not proof
of a future external memory drain. CLEAR only returns a terminal state to IDLE;
it does not clear retained payload fields. The next accepted START resets them.

Both START admission and RUN execution have separate10,000,000-clock watchdogs.
At a physically qualified100 MHz those would each be100 ms; current failing OOC
timing does not establish that physical service rate. A proposed ESP32 one-second
job/poll deadline is a software policy pending implementation and target testing,
not an implemented bound. On timeout or ambiguous START, retain unknown state,
issue ABORT when transport is usable, and confirm ABORTED before clearing or
starting again. If ABORT cannot be confirmed, keep the worker reserved and report
recovery required. Do not erase evidence or flash repeatedly as recovery.

## Before any physical compute test

1. Complete source-bound timing variants and the exact joined fixture/control
   simulations; close all internal100 MHz paths without changing capacities.
2. Choose and synthesize the explicit decoder-exclusive board variant. Build50
   already uses120.5/135 BRAM tiles; the standalone diagnostic uses53 more.
   Replacing the70.5-tile JPEG core makes fit plausible, but arithmetic addition
   is not a measured combined implementation.
3. Preserve board clocks, pins, overlay, LCD margins/porches, button/IRQ path,
   audio and reset behavior. Simulate the actual QSPI endpoint/CDC and diagnostic
   command/read/reset transactions. Close routed setup/hold, routes, DRC/CDC and
   required external timing coverage; preserve any provisional electrical limits.
   Derive constraints from the actual exclusive design. If unused SDRAM/LCD
   read datapaths are pruned, record their absence and exclude those inactive
   datapaths from qualification while keeping physical pins/clocks electrically
   safe and constraining every remaining live interface. Review this explicitly;
   do not add dummy clients, dont_touch or broad exceptions to satisfy stale
   baseline cell-count checks.
4. Implement and target-validate the restricted ESP32 worker, identity/capability
   guards, bounded logging, STOP/recovery and normal-Connect rejection. Verify
   its exact BIN/ELF/UF2/source binding and app-only recovery workflow.
5. Coordinate one physical window with one serial owner, exact versions and
   starting counters. Initially use volatile FPGA JTAG only, retaining normal
   SD-card build50 and recovery artifacts. No persistent FPGA replacement is
   implied. Measure physical fixture cycles/tag/error behavior before considering
   a networked custom test or30fps acceptance.
