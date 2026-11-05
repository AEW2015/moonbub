# Prepared v26 / AKD1 hardware window

Status: the first limited hardware window is complete; see
[the measured results](V26-AKD1-HARDWARE-RESULT-20261104.md). The installed app
is now v26. Build50 was restored/tested and the handheld returned to its normal
menu. This is the repeat procedure; establish fresh readiness for another run.

| Purpose | Exact artifact / identity |
| --- | --- |
| Target app | v26-key-diag-access-20261104, app-only UF2 `80003d79887976d8a49889a0e0bcda2905cb58763ff21d720169c3a87432bc63` |
| Expected runtime ELF digest | `521f529ed99e587cfbd47e63be0de99f4a5f9a13fbf099752a24065655ed49e6` |
| Target private FPGA | guarded-ROM BIT `b1ca685e457446838b9d6c78b86f02c4b793dad42eccb3b5c50075d17e20e260` |
| FPGA part / IDs | xc7a100tcsg324-1; USERID B0100004; USR_ACCESS 4D424B31 |
| App recovery | retained v22 UF2 `329a47a13d01b3416e5c11ed7bbd8c4bf69f0641fe4635679c8f8df14ab14542` |
| Normal FPGA recovery | retained build50 BIT `a1ca6ce6b2c333a7c2ad4d29b94a7adf683dc49669d7f87fe3f80e63ef9ef3f9` |

Target paths and detailed checks are in
[the v26 regression sequence](V26-AKD1-REGRESSION-20261104.md). The normal SD
files and default FPGA selection stay intact; this window uses application-only
updating and volatile FPGA programming.

1. Confirm the actual USB/board identity, quiet sender state and one serial
   owner. Preserve settings and reset/startup logs. Recheck the updater drive
   rather than assuming a drive letter. The usable Windows updater still needs
   the physical Volume-minus/Power sequence.
2. Install only the verified v26 app. Check its unique variant and runtime ELF
   digest, normal menus/controls and bounded diagnostics against unchanged
   build50. Its new 4096-byte worker stack remains provisional until measured.
   Coordinate any legacy JPEG/AV test separately with actual addresses and
   starting counters; do not infer `.157`/`.47` readiness from old sessions.
3. Disconnect and prove receiver/AV drain. Verify the JTAG target is the intended
   Game Bub, then load the exact guarded-ROM BIT into volatile configuration.
   Preserve file hash, programming result, DONE and expected runtime identity;
   family ID readback is not full configuration hash readback.
4. Keep audio off, QSPI at or below 16 MHz and the PLL configuration unchanged.
   No external reset or reprogramming may occur while a diagnostic owns the core.
   Read `b`, then `d` for one fixture. Record owner/sequence, 48,203 ingress bytes,
   518,400 samples, exact opaque tag, hardware elapsed cycles and faults. The
   simulation comparand is 3,000,322 cycles, nominally 30.00322 ms at 100 MHz.
5. Record `key_resource` after reporting and again after later logger activity:
   its own stack minimum in bytes, declared allocation and internal free/largest
   heap. `?` measures the USB task separately. Observe actual line framing,
   synchronous SPI duration, teardown and query/no-query overhead.
6. Use guarded `y`/exit proof before reuse; then separately test `d`/`a`
   cancellation. Any ambiguous or unowned state retains quarantine and logs;
   restart with fresh qualified configuration rather than guessing a drain.
7. Restore the retained normal FPGA and verify identity/menu/controls. Leave
   normal SD boot/recovery selection intact and report all physical checks
   separately from prior simulation.

The FPGA image contains ROM-fed private KEY decode/hash plus independent native
bars/overlay. It has no network decoder capability and no SDRAM controller.
Normal JPEG/local/AV admission is deliberately refused under AKD1. The new
elastic YUV store, owned-read service and RGB arithmetic kernel are separate
simulation experiments; they are **not** present in this BIT. Visible bars do
not prove decoded-frame presentation, and this window cannot qualify 30 fps.
