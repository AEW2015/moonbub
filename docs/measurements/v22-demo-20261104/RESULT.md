# 15 fps controller demo: evidence summary

**Result:** this was a diagnostic run with interruptions and configuration changes, not a clean 15 fps acceptance. The console shows an unexpected reboot, a post-reboot `Legacy`/default-four-slot interval, and later restoration of 32-slot overlap and margin 13. Final firmware counters and queue/core snapshots are useful observations, but they are sampled at different times and are not one atomic frame-accounting record.

## Image identity and reboot

- `pre-update-record.json` records the pre-update app and FPGA image hashes as unknown; it explicitly says no FPGA configuration readback was taken.
- `update-write.json` records an application-only copy of the v22 UF2 to the GAME BUB volume: source SHA-256 `329a47a13d01b3416e5c11ed7bbd8c4bf69f0641fe4635679c8f8df14ab14542`, 6,302,208 bytes, all bytes written. The updater result was `copy_complete_pending_boot_verification`.
- Later console output identifies the running app as `v22-stream-service-20261104` (`USB_TRACE av_service`, including at 19:57:44.703). This is runtime startup evidence for the v22 app, beyond the copy record. The build manifest itself still says `installed: false`; no installed UF2 readback was made.
- The running APC1 status reports `build=1296191312` (`0x4D424F50`) while supported. The v22 snapshot code reads this build register and validates it against the APC1 ABI. It matches the selected build50 manifest `usr_access` value `0x4D424F50`. The selected programming artifact is `fpga/candidates/v21-audio/build/moonshine-rev4.1.bit`, SHA-256 `a1ca6ce6b2c333a7c2ad4d29b94a7adf683dc49669d7f87fe3f80e63ef9ef3f9` (manifest SHA-256 `ab274599ef9372addb19bd2a9c15a1e74458d0e66fe55c818695ebb54b099270`). The console identity is a runtime register value, **not a readback of the full FPGA bitstream/hash or configuration memory**.
- An unexpected reboot is evident from the app uptime discontinuity and return to idle/menu. `menu-return-status.log` at 19:49:59.823 reports uptime 52,535 ms; the continuous capture resumes at 19:55:13.237 with uptime 365,959 ms. These place that boot origin at approximately 19:49:07. The captured bundle contains no reset-reason, panic, or backtrace output for the event, so its cause is **unknown**.

## Configuration intervals

The initial setup log selected queue depth 32 and overlap before connecting at 19:44:57–19:45:06. After the reboot, RAM-only settings had to be reselected. The post-reboot continuous log reports `mode=Legacy` from 19:55:13 through the disconnect at 19:57:35; the candidate’s documented default queue depth is four. Treat counters in this interval as contaminated by Legacy/default-four operation, not as results for the intended overlap configuration.

At 19:57:35.270 the sender was disconnected. The console then records queue depth 32 at 19:57:38.369, overlap requested at 19:57:39.441, and reconnect at 19:57:40.505. The later `t` snapshots report `overlap_request_active=(true, true)` and queue capacity 32. Margin began at 20; keys `[` applied 19, 18, 17, 16, 15, 14, then 13 from 19:59:29.050 through 19:59:33.763. The 19:59:34.630 status reports applied margin 13.

## Final sampled snapshots

| Capture time (UTC) | Snapshot |
|---|---|
| 19:59:36.124–19:59:36.135 (`s`) | App: received 2,664; decoded 2,663; displayed 2,663; dropped 1,517; errors 23,990. FPGA/core: completed 2,664; faults 0; drops 85; overflow 0; underruns 0. Buttons read 0. |
| 19:59:37.744–19:59:37.782 (`t`) | AV active, `audio_enabled=false`; requested/active overlap `(true, true)`. Application queue capacity 32, queued 0, drops 0, high-water 25. Producer timing is cumulative socket-receive telemetry, not wire timing. |
| 20:00:12.731–20:00:12.738 (`s`) | App: received 3,204; decoded 3,197; displayed 3,197; dropped 1,517; errors 23,990. Core completed 3,204; faults 0; drops 85; overflow/underruns 0. |
| 20:00:14.051–20:00:14.091 (`t`) | AV still active with audio disabled; overlap `(true, true)`; queue capacity 32, queued 0, drops 0, high-water 25. FPGA timing read returned `busy` for this sample. |
| 20:00:15.574–20:00:15.594 (`x`) | Disconnect; worker stopped, `recovery_failed=false`; saved Wi-Fi power-save mode restored to 1. |
| 20:00:18.671–20:00:18.678 (`s`, final) | App: `Disconnected; source stopped and remote controls released`; received 3,245; decoded 3,240; displayed 3,240; dropped 1,518; errors 23,991. Core: status 1 (idle), completed 3,245; faults 0; drops 86; overflow 0; underruns 0; transport overflow 0. Buttons read 0. AV is inactive, audio disabled, and Wi-Fi power-save is restored. |

The queue high-water and zero-drop values are the 20:00:14 pre-disconnect sample, while final application/core counters are from 20:00:18 after disconnect. These counters are independent snapshots; their values should not be reconciled as though sampled atomically. `received`, `decoded`, `displayed`, core `completed`, application drops and core drops are separate stages. The high sequence-error count, large application drop count, reboot/configuration interval, and changing settings prevent this run from serving as clean 15 fps acceptance. Audio remained off; AV audio accepted/rejected/underrun counters stayed zero.

The run ended explicitly disconnected, with remote controls released and recovery reported successful. The capture finished at 20:00:45.368.

## Source records

- `pre-update-record.json`, `update-write.json`, `post-update-status.log`, `configure-receiver.log`, `network-and-display.log`, `menu-return-status.log`, `continuous-console.log`
- `pre-update-artifacts/v22-build-manifest.json` and `pre-update-artifacts/build50-manifest.json`
- `fpga/candidates/v21-audio/manifest.json` and `firmware/experiments/v22-stream-service-20261104/handheld/src/streaming/audio_snapshot.rs` (artifact and runtime-register interpretation)
