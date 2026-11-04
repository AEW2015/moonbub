# v24 runtime diagnostics — unflashed ESP32 application experiment

This is the firmware experiment `v24-runtime-diagnostics-20261104`, derived only
from sealed `v22-stream-service-20261104`. It is a different namespace from the
remote host codec study `study/gamebub-codec-v24-comparison-20261104` at commit
`4025d35`; that study is not incorporated here.

The installed v22 application UF2 remains
`329a47a13d01b3416e5c11ed7bbd8c4bf69f0641fe4635679c8f8df14ab14542`.
No COM/USB connection, probe, service, flash, SD change or hardware operation is
performed. The reported spontaneous reboot remains unexplained. The old capture
missed startup details; subsequent uptime and stack watermarks do not establish
a reset cause or stack overflow. The hardware record belongs to the separate
`evidence/15fps-controller-demo-20261104T193749Z` window.

## Commands and compatibility

`?` is a new read-only runtime query. Lowercase `r` was already the CRC benchmark
and remains unchanged; uppercase `R` remains Right-button injection. The complete
USB/margin/timing command path was inspected before selecting `?`. As with other
one-byte commands, the timing `T...LF` parser must be idle: it consumes bytes
until LF while collecting or discarding an incomplete timing command.

The query reads the SDK reset reason, monotonic uptime, firmware experiment name,
internal free/largest heap block and current USB-task stack watermark. It also
reports the bounded SDK application descriptor fields and its embedded
`app_elf_sha256`. No Device lock, FPGA read, task-priority update or runtime state
write is used. `CAPTURE` is only a diagnostic sequence counter.

The embedded SDK ELF digest identifies the ELF used by `elf2image`. It is not a
self-computed BIN hash, source inventory hash or circular provenance claim.
External release metadata records separate ELF/BIN/UF2/source-inventory hashes.
Descriptor strings are SDK-supplied fields, so their version/project text need
not equal the firmware experiment name. The existing AV-service startup marker
still names its unchanged v22 service-policy ancestry; the new `USB_D24 ... boot`
marker and `?` variant/ELF pages distinguish this image.

The `s` command and its existing brief status output are unchanged. The `t`
command retains its source/clock/overlap, AV and FPGA-timing messages, replacing
the oversized completed/dropped FrameTrace and combined QueueDrop/ProducerTiming
Debug messages with explicit `USB_D24` pages. Old parsers expecting
`USB_TRACE completed=...` or `application_queue=... producer_timing=...` must
recognize the new schema. Existing AV diagnostic pages are unchanged and are not
covered by the new page-size claim.

The workspace recorder `scripts/record_gamebub_reboots.py` now accepts `?` and
retains the `USB_D24` prefix (root-owned recorder change, not firmware source).
Its raw logging/startup capture should be used for a later test. Older captures
that filter only `USB_TRACE` can silently omit these new pages.

## Page schema and sampling limits

Normal new pages start with:

`USB_D24 v=1 c=<captureSeq> g=<generation_before> e=<epoch_before> f=<frameID> p=<page>`

All counters are unsigned decimal; durations/timestamps are microseconds unless
the field denotes bytes, packets, priority or stack units. Stack values retain
the exact FreeRTOS API's watermark units; no conversion or safety margin is
invented. `c` wraps at 32 bits and restarts after reboot. Group it with a recorder
connection/boot identity, uptime and image digest rather than treating it as a
persistent globally unique ID.

`g` is the source-generation marker and `e` is the software presentation-epoch
sequence sampled before collecting the pages. The end page supplies `g_after`
and `e_after`. These are **sampled before/after markers, not an atomic snapshot**.
Matching markers do not prove atomicity. FrameTrace is copied under its own
mutex; queue, producer, epoch and runtime observations use separate getters and
times. Retained completed/dropped records can predate a source change, so the
begin page explicitly says `frame_epoch_binding=false`. No frame-origin epoch
association may be inferred from the capture-time `g/e` values.

`fc0..fc6` describe the most recent completed network frame; `fd0..fd6` describe
the most recent dropped network frame. `f` is the corresponding frame ID; the
first page includes `valid`, which must be honored. Fields preserve all original
FrameTrace observations: packet/byte counts; start/last/end timestamps;
interarrival, queue residence, consumer processing/gap maxima; QSPI/lock totals
and maxima; remaining frame bytes; and first offset gap. Remaining bytes are
not FIFO capacity. Producer gaps are socket receive timestamps, not wire times.

`q0..q3` retain all QueueDrop and queue occupancy/high-water fields; their `f` is
the recorded first-drop ID, qualified by `first_valid`. `pr0..pr1` retain all
ProducerTiming fields; their `f=0` has no frame association. Runtime, boundary
and descriptor pages also use `f=0`. One `t` produces 23 new pages in addition
to existing messages; one supported-descriptor `?` produces seven new pages.
This is bounded work, but adds serial traffic and logging time and does not run
on the packet hot path. No zero-cost instrumentation claim is made.

## Host and target evidence

`python -u run_checks.py` checks the parent guards, unchanged policy/wire/default
sources, exact intended source deltas and all inherited host harnesses. It also
tests the actual production pure formatter at worst-width values. The initial
executed result is 371 test executions (inherited tests repeat across harnesses,
not 371 unique tests), including 28 new page shapes. Maximum tested payload is
161 bytes, with zero formatter allocations. Descriptor arrays are bounded and
sanitize control/non-ASCII bytes. Overflow, non-ASCII and newline injection fail
explicitly instead of silently truncating a page.

The helper caps payloads at 192 bytes and reserves 64 bytes for logging/framing.
The host maximum of 161+64=225 bytes is a **modeled full-line bound**. The host
test does not execute ESP logging, prove actual logger framing or establish
runtime stack safety. Independent Luna review found no concrete dispatch/page/
descriptor issue by source inspection; it is not SDK ABI or runtime evidence.

Target stages passed using esp193 and ESP-IDF 5.4.3 in isolated short target
`C:/mv24`: `check.ps1`, then `build.ps1`, then `package.ps1`. Packaging uses
ESP32-S3 `elf2image` (DIO/80 MHz/8 MB), application-only UF2 and the copied
production DFU parser. All 12301 blocks pass Rev4 identity, application-address
and binary round-trip checks. The compiled SDK configuration is byte-identical
to v22. Static shared SRAM is 121780 bytes; the BIN is 3148832 bytes, leaving
2094048 bytes in the unchanged 5 MiB factory partition. No target `cargo run`
or flashing command is used.

The 553-input source inventory SHA-256 is
`b605ac94e39aa3cbe93e9f57a79fad8527318f4ea3dc40a6d6e150f444d80188`.
The app-only UF2 SHA-256 is
`c13c4f4183092fdf9c897fdf083e492e66ea6112c84c8412f5930ae250488c20`.
The binary's embedded SDK ELF digest exactly matches the external ELF SHA-256:
`0c1a431538b504bfad62912ccd1ecc85b271eecdc0d20012325c02e024e7107a`.
Full ELF/BIN/UF2 metadata and source/artifact hashes are in
`release/moonshine-rev4.json` and `evidence/build-manifest.json`.

Selected ELF prologues show USB command shrinking from 720 to 384 bytes, but the
new nested helpers have their own frames: video 768, runtime 320, emit 272,
log_frame 272, page 288, frame formatter 128, app/runtime formatters 80 and queue
formatter 64 bytes. The SDK logger log frame is 128 bytes. V22's old FrameTrace,
QueueDrop and ProducerTiming Debug formatters have 240, 160 and 112-byte frames.
Formatting and emission are separate paths, so summing every listed function
would overcount some paths; omitted formatting/libc/interrupt frames also mean
these are not complete upper bounds. The new persistent caller/helper frames
can increase stack demand despite shorter lines. AV run changes from a selected
2432 to 2480-byte prologue despite its source being byte-identical, so no stack
margin is inferred from unchanged source either. All task stack declarations
remain unchanged. `evidence/stack-comparison.json` and the individual old/new
disassemblies retain the selected evidence. The prior raw USB watermark 716
belongs to v22, not v24. Runtime stack acceptance remains **NOT_RUN**.

SDK configuration, BLE, task priorities/stacks, pools, queue/overlap defaults,
UI/calibration variant, MSV1 and AV v1 wire formats are unchanged. No AR03 runtime
or new port is added. Source deltas are limited to main module/startup wiring,
USB dispatch/diagnostic routing, one read-only generation accessor, and the two
new diagnostic modules; a host harness is added. Parent source/release guards
and external artifact hashes remain separate from runtime identity.

## Later hardware gate — not run

At an explicitly coordinated future window, retain unfiltered panic/startup
output through reconnect and query `?` after boot. Record query cadence, bytes
logged and durations. Establish a no-query control, then a stated sparse query
cadence (`?` on startup/reconnect, `s` every five seconds and `t` every thirty
seconds initially) under the
same stream/controller workload. Measure USB/AV/producer/consumer stack
watermarks, heap/largest block, frame timing and logging overhead. Change one
cadence at a time and retain the exact image/FPGA/source identities. These are
proposed tests, not a claim that the example cadence is safe or that v24 fixes
the unexplained reboot. Installed v22 and build50 remain recovery references.
The root-owned [regression window](../../../docs/V24-DIAGNOSTIC-REGRESSION-20261104.md)
is the coordinated operator checklist; this document does not authorize running
it. Run `python verify.py` to recheck the sealed source/artifact hashes and all
five parent guard maps. Overall readiness remains **INCOMPLETE** because physical
runtime, stack, framing and logging-overhead qualification has not run.
