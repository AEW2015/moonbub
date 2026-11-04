# v26 and AKD1 physical regression sequence

Status: prepared offline, not executed. Installed v22/build50 remains the recovery
comparand. No current address, connection or hardware readiness is inferred.

The target is a useful private compute measurement before a custom network
receiver exists. This does not qualify 30 fps playback. AKD1's native LCD bars
are independent of its private decoded samples.

## Bound candidates

- ESP32: `firmware/experiments/v26-key-diag-access-20261104/release-key-resource/`.
  UF2 SHA-256 `80003d79887976d8a49889a0e0bcda2905cb58763ff21d720169c3a87432bc63`.
  Manifest `00b3d4a4bd6190646d72b817dc22d3802e6f70b87cfec35d9d5b2547cf8c4a66`.
- FPGA: `fpga/candidates/akd1-compute-cancel-boundary-20261104` is the next
  candidate. Its `akd1-compute-lcd-prune-20261104` parent failed routed setup;
  the successor still needs full simulation and route/report gates. There is
  no qualified bitstream hash in this checklist yet.
- Contract: [AKD1 local diagnostic](AKD1-COMPUTE-DIAGNOSTIC-20261104.md).
  Exact identity pair is AKD1/MBK1, schema 1, zero network capabilities.

## Before a physical window

1. Verify the sealed v26 manifest and preserved app/FPGA recovery images.
   Preserve the normal SD files and settings. Keep app updates application-only.
2. Complete routed setup, hold, pulse, route, DRC, clock, CDC and active-interface
   review for the exact FPGA checkpoint. Bind reports, bitstream and source hashes.
   A passed internal OOC report does not replace these board checks.
3. Coordinate a quiet window with Windows. Stop video/AV and release injected
   controls; do not send packets during a diagnostic job.
4. Start one reconnecting serial recorder with fresh output/control paths. Its
   whitelist includes `d/a/b/y`; it never sends commands automatically on reconnect.
   Record reset/startup lines, not only status pages. Credential lines stay redacted.

## App-only regression against unchanged build50

Use the physical USB updater step once: the Windows vendor update driver does
not provide the usable software-triggered updater. Verify the exact app-only
image after writing and wait for its runtime marker before other actions.

Record `?` and bounded `t` pages, app identity, reset reason, uptime, heap/largest
block and USB stack minimum. Re-establish actual DHCP/source addresses and selected
32-slot/overlap settings explicitly; do not infer them across reboot.

Check normal menus and existing MSV1/AV behavior in separate short sessions:
known-good JPEG decode/presentation, input-only Connected/TestReady session,
then quiet audio. Record starting/final video, queue and audio counters and compare
query versus no-query operation. The existing connected receiver owns the core
even with no video frames; this candidate does not add cold-boot standalone AV.
No reboot fix or stack-safety claim follows from a successful host build.

## Volatile FPGA-only AKD1 check

After successful app regression, disconnect and prove receiver/AV workers drained.
Program only the qualified volatile FPGA image; retain normal SD build50 for
recovery. Record selected bitstream hash, programming result and FPGA identity.
No other operator/JTAG reset may occur while a diagnostic owns the core.

- `b`: read-only status. Verify all eight identity words and no unowned RUN or
  terminal record. An unowned record is quarantined; do not adopt or clear it.
- `d`: start one private fixture. Record full owner, result sequence, epoch,
  tag, cycles, bytes, samples and explicit fault/status from bounded pages.
  Compare 48,203 ingress bytes, 518,400 samples and exact expected tag. The
  simulation's 3,000,322 cycles is a comparand, not a physical measurement.
- `b`: retain the held result and `key_resource` page. It must name KeyDiag,
  measure its own stack minimum in bytes, and report internal free/largest heap.
  `?` measures the USB task separately. Check later samples after logger activity.
- `y`: guarded clear and confirmed worker exit. Confirm subsequent status and
  heap/task reclamation before another job; detached reclamation is not assumed
  instantaneous. Exercise a separate `d`/`a` cancellation and clean restart only
  after the completed-job path passes.

Do not issue arbitrary CSR writes or automatic reset/reprogram recovery.
Ambiguous start/read/stop, unowned state or lost ownership requires retaining
logs/reservation and explicit restart with fresh qualified configuration.
Measure synchronous SPI duration, query overhead, stack and heap across repeated
jobs. The new 4,096-byte worker allocation is provisional until measured.

## After the diagnostic

Restore the known normal FPGA through the existing controlled path, verify its
identity, then repeat one known-good JPEG and controller session. Custom network
streaming remains blocked on production identity/recovery agreement, a real
bounded FIFO backend, reference/HUD composition and real memory/scanout service.
Only the complete path can enter the 5/10/15/20/30 fps physical acceptance ladder.
