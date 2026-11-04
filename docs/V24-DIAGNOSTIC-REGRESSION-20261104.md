# Firmware v24 diagnostic regression window

This is a future test checklist. The application build/package gates passed;
v24 is unflashed, v22 remains installed and the demo is stopped. Firmware v24 here means the local
`v24-runtime-diagnostics-20261104` experiment, not the host-codec comparison study.
No FPGA update is needed for this application-only regression against build50.

Candidate UF2 SHA-256:
`c13c4f4183092fdf9c897fdf083e492e66ea6112c84c8412f5930ae250488c20`.
Sealed build manifest SHA-256:
`8c5d2792da22742ba087fc404ae5580cae2625b9a926a5334190b776778125d8`.
Physical stack/logging/framing and reboot qualification remain NOT_RUN.

1. Bind the exact source inventory, ELF, BIN and app-only UF2 after successful
   target build and production updater-parser verification. Preserve the installed
   v22 package and existing recovery artifacts. Record the selected FPGA artifact
   and live build register separately from any configuration readback.
2. Start one reconnecting serial owner before the update. Its filter must retain
   `USB_D24`, startup reset/panic text and existing `USB_TRACE` records. Use
   `scripts/record_gamebub_reboots.py`; choose fresh output/query/stop paths.
3. After the physical update, verify menus and physical controls, then issue `?`.
   Retain reset reason, uptime, variant, SDK descriptor identity, embedded ELF
   SHA and memory/USB stack values. The embedded SDK ELF field is not a source
   inventory hash or a readback of the entire installed BIN.
4. Confirm actual receiver/peer addresses and read back queue32, overlap,
   margin13 and timing0. Do this again after any reboot: RAM defaults are not
   evidence that the intended settings survived. Leave audio off initially.
5. Check `s` and bounded `t` output. Record query cadence and full observed line
   lengths, truncation/format errors and stack watermarks. Start conservatively
   with `s` every five seconds and `t` every thirty seconds; issue `?` on startup
   or after reconnect. Host payload bounds and static stack analysis do not
   qualify actual logger framing, scheduling overhead or stack safety.
6. Coordinate a 20-second 5 fps video control, then a short 15 fps video run with
   fixed host quality/bitrate/pacing and new frame IDs. Preserve sent/partial/
   suppressed counts and receiver received/decoded/presented/frame-drop counters,
   packet drops/high-water, Busy/gap reasons, core faults and stage timing.
   Compare a stated low-polling interval if instrumentation affects service.
7. Add input-only AV/controller coexistence after video passes. Confirm sequence
   continuity and neutral release on STOP. Keep audio as a separate regression;
   neither the previous interrupted demo nor bounded diagnostics establishes
   audio or 30 fps qualification.

On another reset, retain the raw pre-reset tail and startup reason/backtrace,
query runtime identity after reconnect, and record the new configuration. Do not
silently merge pre/post-reset counters. End with explicit disconnect, input
release and a final sampled snapshot. Treat matching diagnostic capture/generation/
epoch markers as sampled observations, not an atomic cross-task transaction.

The FPGA KEY/hash diagnostic needs a different image, a checked restricted CSR
control and routed board gates. This application regression does not enable a
custom UDP endpoint or custom-codec playback.
