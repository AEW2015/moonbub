# V48 local self-test bootstrap

Purpose: remove chat-relayed sender timing and routine physical reboot steps for bounded CU66 testing. The native decoder is byte-for-byte V47; V027 and sequence-v3 stay unchanged. This update does not claim better codec throughput or that the network fragmentation failure is repaired.

Selected release: `firmware/experiments/v48-dy71-selftest-control-20261107/release-selftest-control-v001`.

- ELF SHA-256: `93a389adb4e5bf88fa9eb5d28fc3d82abdb012e4fb647cd50f81196c917aab74`.
- UF2 SHA-256: `a10cd156e76c900a8f1c2f08123083dfd687d03341698ff584ae5fed530c0c98`.
- Static SRAM132,076bytes, guard163,840; production updater verified13,691application-only blocks.
- Frozen-source target build passed.104Rust host checks passed, including9parser/7descriptor/11recovery-policy checks, plus actual-native253,440HUDwords and late-patch rollback. The local Python controller's15offline tests passed separately.

The heap-free serial protocol is`!MBLAB1 <16hexnonce> ACTION\n`: PING, HOST33, HOST47, REBOOT or DFU. Responses echo nonce/action andOK/BUSY/ERROR. Invalid, timed-out or oversized frames consume through newline, preventing their contents from becoming legacy single-key controls. HOST33/47 changes only a RAM override in the custom lab Wi-Fi path; saved credentials and SD configuration are untouched.

Reboot/DFU requires quiet video/AV and either idle or completed-held custom work, with retained export finished. An atomic coordinator barrier blocks new work while the deferred reset is pending. Timer-setup failure cancels that barrier; accepted state/leases are never force-released. This is whole-system restart recovery, not a fabricated native commit. ACK means the action was queued, not that reboot completed.

USB now advertises static Microsoft OS2.0 WINUSB descriptors for vendor interface0 only. VID/PID/serial, CDC interfaces and storage layout are unchanged; USB version becomes0210 and lab USB firmware revision4800/4802/4803 invalidates stale feature caches. This lab bcdDevice is not hardware revision: GET_INFO continues reporting real hardware identity. Target ELF has strong BOS/vendor callbacks. Driver auto-binding remains a physical gate, not a host-test result. No updater/partition/bootloader image is changed.

After the one physical app update:

1. Verify exact ELF, CDC nonce PING and CPU12. Check WinUSB interface0 status and read-only GET_INFO; preserve CDC operation.
2. Prepare same V027 and camera. Use`host/lab-selftest-v1` to apply HOST33, launch the pinned local sender, check its live process/session/count/source/remainingwait and arm once. No`.47`host is required.
3. Preserve complete receiver/host results, inspect any failure, then explicitly qualify serial REBOOT and exact post-reset identity. No automatic whole-run retry.
4. Qualify installed software-DFU access and the separately reviewed protected app-only client before claiming button-free updates. If that gate fails, continue software reboot and offline work; do not risk a blind flash or modify the bootloader.

The requested six-hour work window begins with local preparation and proceeds through bounded tests, evidence-driven fixes and offline verification. Each failed run stops for analysis. Hardware availability, physical bootstrap and validated recovery determine which gates can be completed unattended. True battery-level off/on still requires an external actuator if software recovery is insufficient.

Evidence index: candidate`evidence/readiness-v001/readiness.json`. All work stays underC:/moon; preserve exact V47/JPEG recovery releases. Target V48 runtime, WinUSB binding, software reboot and local network playback remain unverified when this handoff is written.
