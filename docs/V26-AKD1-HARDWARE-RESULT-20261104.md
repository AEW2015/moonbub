# v26 / AKD1 controlled hardware result

Executed 2026-11-05 01:38-01:55 UTC (November 4 in Denver). The app-only v26
update, private FPGA compute check and recovery completed. The handheld was left
on its normal Game Bub menu, confirmed by camera. This was not a CP23/CP25 or
30 fps streaming trial.

## Exact images

| Artifact | SHA-256 |
| --- | --- |
| Installed v26 app-only UF2 | `80003d79887976d8a49889a0e0bcda2905cb58763ff21d720169c3a87432bc63` |
| Runtime SDK ELF digest, observed | `521f529ed99e587cfbd47e63be0de99f4a5f9a13fbf099752a24065655ed49e6` |
| Volatile guarded-ROM AKD1 BIT | `b1ca685e457446838b9d6c78b86f02c4b793dad42eccb3b5c50075d17e20e260` |
| Restored/tested build50 BIT | `a1ca6ce6b2c333a7c2ad4d29b94a7adf683dc49669d7f87fe3f80e63ef9ef3f9` |

The intended Digilent cable was `210249AE796F`, with one XC7A100T. JTAG reported
DONE=1, USERCODE `b0100004`, and USR_ACCESS `4d424b31` after AKD1 programming;
recovery reported DONE=1 and `4d424f50`. These identify the family/version; they
are not a full configuration-hash readback. All 257 selected FPGA artifact
hashes and 12,419 application-only UF2 blocks were checked before programming.
Normal SD contents, partitions, bootloader and settings were not rewritten.
Recovery release artifacts were preserved; the MSC updater provides no live
flash-image backup/readback.

## Physical results

| Job / check | Observed result |
| --- | --- |
| Private KEY, owner 1 / sequence 1 | Completed; 3,000,322 cycles; 518,400 samples; 48,203 bytes; fault 0 |
| Opaque canonical tag | `c6c97dee75f2be10adddff19f0985885`, exact expected bytes |
| Guarded clear | Cleared, then inactive worker status |
| STOP path, owner 2 / sequence 2 | Aborted status, zero exposed tag, then guarded clear |
| Restart, owner 3 / sequence 3 | Completed with identical exact counts/tag and fault 0; clear/inactive confirmed |
| Local JPEG loop before AKD1 | 122 submitted / decoded / presented; clean stop |
| Local JPEG loop after build50 restore | 69 submitted / decoded / presented; clean stop and menu restore |
| Camera | Independent AKD1 native bars; changing square positions in restored local JPEG loop; final normal menu |

At configured nominal 100 MHz, the completed KEY count corresponds to
**30.00322 ms**. Both successful jobs use the same embedded fixture, epoch 1 /
frame 0. They are not unique video frames. The core performs private pre-HUD
AR03/GM01/CP02 reconstruction/hash with no SDRAM, predictor banks, HUD application,
decoded LCD presentation, AF03 or network receiver. Bars are independent of its
decoded samples. These results do not establish 30 displayed frames/s.

The STOP result retained the full 3,000,322 cycles and all 518,400 samples.
Therefore it establishes the abort/clear/restart handshake, **not mid-compute
interruption**. A future cancellation test needs observed partial work and clean
reuse before that coverage can be claimed.

The local JPEG counters are device-reported loop counters, separate from network
ingress. Camera stills show the moving square at different positions; they are
not calibrated optical frame-rate measurements. No new network sender was used.

## ESP32 resource and observability followup

- Minimum own-task stack remaining: KeyDiag **796 bytes of 4096**; UsbTest
  **636 bytes of 4096** for the exercised command mix. No stack overflow or
  reboot was captured, but these measurements are not a proof for other paths.
  Review headroom before broader diagnostic/stress workloads; do not reduce stacks.
- After successive clears, internal-free samples were 120,000, 119,812 and
  119,632 bytes; largest block stayed 31,744 bytes. The small drift is unexplained.
  IDF's detached pthread path is intended to free its bookkeeping; self-deleted
  task stack/TCB reclamation occurs later through idle cleanup. Worker exit flags
  and in-worker samples are not heap-reclamation barriers. Compare warmed-up,
  settled states before diagnosing a leak.
- A `t` diagnostic burst had concatenated/missing serial page text. The capture
  filters/redacts decoded lines; it is not a raw-byte capture. Preserve raw bytes
  and reconcile complete page markers next. No formatting-overflow cause is proven.
- AKD1 CSR accesses use the code's 16 MHz maximum. No electrical QSPI clock,
  external hold, maximum bandwidth or per-operation SPI latency was measured.
- Wi-Fi association, legacy Test MJPEG readiness and a valid idle AV snapshot
  were observed. Network video, live audio, controller injection and physical
  button-response regressions were not run in this window.

Two host-harness errors are preserved locally: a byte offset applied to
newline-normalized text caused a false wait timeout despite an explicit inactive
line; the first recovery launcher used the wrong working directory and found no
Tcl file. Corrected raw-byte inspection and the verified absolute-path retry
passed. Neither error is a receiver failure or a successful programming event.

## Next development gate

[CP23/HC22/HD22 remains the first complete-fixture target](CP23-FIRST-HARDWARE-FIXTURE-20261104.md).
No matching complete decoder image or arbitrary-payload local loader exists yet;
CP25/GM25/HD25 is incompatible and unselected. Keep Windows on its tested CP23
baseline and do not send either profile to AKD1.

Finish actual codec-to-transpose-to-memory/scanout integration, then validated
frame publication, exact HUD and P/reference service. Keep the direct-YUV read
reservation and bank-locality results as simulation evidence. The full receiver
must pass its own implementation and hardware gates before the rate ladder.

Full local evidence: `evidence/hardware-v26-akd1-20261105T013803Z/`.
Published selected logs, analysis and camera observations are under
`docs/measurements/v26-akd1-hardware-20261104/`.
