# Next hardware window and custom 30 fps gates

Status update, 2026-11-04 after the demo: v22 is now installed with the retained
build50 FPGA. The requested window ended and streaming/control sessions were
stopped. One unexplained reboot remains open; the mixed-mode totals are not a
15 fps acceptance result. See [current progress](COORDINATED-30FPS-PROGRESS-20261104.md).
The v26 app-only successor has now completed its offline build/package gates;
it adds reset/identity reporting, bounded diagnostic pages and restricted AKD1
access. Use [the v26 regression sequence](V26-AKD1-REGRESSION-20261104.md) for the
next window. Its new worker stack and runtime behavior remain physically
unqualified. The FPGA diagnostic is still in route/report review. Custom
streaming is still unavailable. The v22 sequence below is retained as the
historical comparison plan, not a direction to reinstall it by default.

Date: 2026-11-04. This is a test plan, not a device-ready announcement. No device
probe, flash, core reload, SD change or stream was performed to write it.

## Earliest useful physical test

The prepared **v22 app-only JPEG/AV regression can run at the next coordinated
window** with the previously selected build50 FPGA unchanged. It does not need
a new FPGA build. The package is built, target-checked and validated through the
production UF2 parser. It was subsequently installed during the demo described
above; full physical qualification remains open.

Exact app: `firmware/experiments/v22-stream-service-20261104/release/moonshine-rev4.uf2`,
SHA-256 `329a47a13d01b3416e5c11ed7bbd8c4bf69f0641fe4635679c8f8df14ab14542`.
Historical selected FPGA: build50/V4,
SHA-256 `a1ca6ce6b2c333a7c2ad4d29b94a7adf683dc49669d7f87fe3f80e63ef9ef3f9`.
Those hashes identify retained artifacts, not a fresh readback of the handheld.

This window tests v22's shorter device locks, UI/USB service and audio diagnostics
against the existing MSV1/AV v1 path. It does not activate AR03 or establish its
30 fps capability. The exact candidate and method are described in
[the v22 handoff](SUNSHINE-HANDOFF-v22-20261104.md).

1. Confirm the handheld, current app/core identity, serial owner and sender
   availability; save current settings and starting counters/captures before
   changing a working session. Preserve the known recovery artifacts.
2. Install only the explicit Rev4 app UF2. The established usable updater path
   requires the physical Volume-minus/Power sequence; software-only entry did
   not provide a usable Windows updater in prior sessions. Recheck current USB
   identity and drive rather than assuming a COM number or drive letter.
3. Verify startup marker `USB_TRACE av_service schema=1 variant=v22-stream-service-20261104`,
   normal menus, physical controls and USB control. Capture heap and stack
   watermarks; a host build cannot establish those runtime measurements.
4. Restore and read back the comparable configuration: **32 video queue slots,
   overlap enabled, margin13 and timing0**. Volatile defaults may differ after
   reboot. Confirm actual receiver and accepted sender addresses; historical
   `.157` and `.47` addresses are not current readiness evidence. Keep credentials
   out of logs and chat.
5. Begin input-only and a quiet tone, then a 20-second 5 fps video control and
   five-minute video run. Compare received/decoded/presented/frame drops,
   packet-queue drops/high-water, Busy/gap reasons and core faults. Retain gain,
   quality, bitrate, host commit and frame range. Stop escalation on unexplained
   faults; preserve evidence instead of repeating flashes.
6. If those pass, repeat the established 12 fps combined audio/controller
   workload. Keep host pacing and capture settings fixed during the comparison.
   Record post-STOP audio drain/underrun/rejection and neutral input release.

## When custom AR03 testing can start

There is no honest calendar estimate yet. Current RTL pieces are experimental
components, not a complete board image. The next custom physical milestone is
one deterministic KEY frame, not a 30 fps acceptance run.

| Gate | Required evidence before first custom streaming window |
| --- | --- |
| Complete FPGA KEY path | Envelope + GM01/map/CP02 + exact reconstruction, bank writes, canonical tag, required display patches and actual scanout joined; all integrity checks precede publication |
| FPGA implementation | Exact source/XDC/board identity, combined fit, routed setup/hold, route/DRC/CDC and bitstream hash; isolated OOC timing is insufficient |
| Receiver backend | Owned buffers plus real FIFO reservation/submission/completion/read-drain integration, bounded worker service and target memory/stack checks |
| Shared live contract | Windows/receiver agreement on capability, peer/port, identity lifetime, epoch/reset/rekey, ambiguous/lost outcomes and reference publication |
| Test window | Exact host/app/FPGA versions, actual addresses, workload and frame range, starting counters, one serial owner, captures and named start/STOP/drain responsibilities |

An isolated FPGA compute diagnostic could precede full custom streaming only
after a dedicated diagnostic image meets its own simulation and routed board
gates. No such new image is claimed ready by the component source exports.

After the first KEY, qualify P/promotion/recovery, then 60 seconds each at
5/10/15/20/30 fps. Follow with five minutes and 30 minutes at 30 fps, then audio
and controller coexistence. Count unique physical presentations and reconcile
all outcomes, intervals, faults and backlog. Ingress acknowledgements and
nominal simulation clocks cannot establish physical playback rate.
