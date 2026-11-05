# V33 AV restoration failure fence

V33 fixes a source-observed recovery-reporting gap: a failed AV power-save restoration could drop its guard, then a later empty cleanup could report success. The single executable production change latches global recovery failure in the existing Restore-error callback. Actual AV join/drop then supplies an unconfirmed drain and the coordinator retains ownership/quarantines. Restore-error worker exit/quarantine is intentional; successful radio calls, standalone-video behavior, pacing, queues, protocol and SDK defaults are unchanged.

This was **not observed as the cause of retained hardware losses**. No normal NoPS behavior experiment is included. Standalone video still leaves the actual radio mode untouched; accepted AV, including input-only sessions, uses the existing scoped guard. A successful AV STOP/expiry can restore power saving while video continues. The separate ownership review and future optional experiment are explicitly evidence/design rather than deployed behavior.

V33 is an uninstalled successor of sealed v32. Source export `firmware/exports/v33-av-restore-fence-source-20261105`, manifest `b1de222215958269e81164563fcb0e0cc20dfc1b5578c84b7aa54c1843f7d420`, includes587 manifest-bound files/all574 selected inputs, fonts/assets/locks and exact upstream license/attribution files. No other GameBub checkout is assumed. External toolchain/IDF/component prerequisites are documented. Original ELF/BIN/UF2 remain local, not bundled in this source export.

| Gate | Executed result |
|---|---|
| Focused SDK tests |83 cases: prior66 +7 generic guard +10 exact-production-fragment restore/join/coordinator cases |
| Other copied host checks |97 Rust suite tests,39 model cases,24 expected compiler rejections |
| Fresh target check/release | PASS5m49s/1m29s, esp193/ESP-IDF5.4.3 |
| Production application-only UF2 validation | PASS12,549 blocks |
| Static shared SRAM |130,812B, unchanged versus v32 |
| SDKconfig/ABI and17 measured PS function entry frames | Identical to v32 |
| Relocated export target build | NOT_RUN; copied host replay/preflight pass separately |
| Hardware installation/restore/query/stack/heap/streaming | NOT_RUN |

Original candidate manifest `9ff2b452aa948dd5e89c4bbe7facb00e6b9bf25236fa36b481f2c6601cb40874`; selected source snapshot `8e91bc9c2bd063ee1c2e1163dd40e6d3f6baa4250ce7af22cff5796da6655b1c`; ELF `cadae73fa2e62ad7a4b2db5983796c28d028f77a03a9b4859cdeeb6c2d17d2cf`; UF2 `a3a7cb727cf2ce4074e576f4f312e4fc8bb504757d82161cb7626a03959815f2`. No full-task stack bound or physical delivery improvement is inferred from the static frames.

Tests compile mechanically extracted actual Radio/helper/Guard::Drop text, actual AV STOP/expiry and actual coordinator/core-access logic with a fake SDK. They inject setter/getter/verification and rollback failures, verify sticky failure survives later empty cleanup, and reject false `power_restored`/clean admission. This does not execute the complete socket/audio worker or real SDK/radio timing. The first shell-status ambiguity is retained; qualifying Python subprocess captures record native Cargo return0.

Installed v30/build50 and settings are unchanged. V31 remains the proposed first legacy physical comparison, isolating trace work. V33 is a separately reviewable recovery-safety candidate. A custom CPL1 FPGA image, negotiated custom network transport and30 unique physical fps retain their independent gates.
