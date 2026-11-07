# V43 / V027 original KEY/P comparison

Status: offline timing, native image audit and BIT generation passed. Ready for the bounded physical comparison; no new hardware has been programmed. Physical baseline remains V42/V023, holding the final native endpoint/lease.

Exact BIT: `C:/mb70/dy71-v027-20261107-v001/image01/moonbub-v027-lab.bit`, SHA-256 `9922aa617c21a03e8a31f932d45e22d905e91d4e263ef593692898d363d07dee`. The parser checked intended USERID `4459373f`; physical DONE/USERCODE still require the hardware window.

## Exact scope

Test V43's bounded bulk HUD transfer against the unchanged original CU66 KEY/P fixtures. V027 uses the V023 decoder system with the source-bound V026 idle row capture and a global buffer on the existing fourth synchronized core-reset stage. ABI is `00020000`, capabilities `1f`, HBU1 signature `48425531`, intended USERID `4459373f`.

This is a two-frame correctness and transfer-time comparison. It does not demonstrate live custom-codec streaming or 30 fps. Windows uploader, fixtures and DYN1 UDP port 5535 remain unchanged.

## Before installation

Require the exact BIT hash, positive final routed setup/hold/pulse, all nets routed, zero routing errors and DRC errors, positive timed reset-path coverage, native image audit and checked BIT identity. Preserve V42/V023 rollback images. V027 routed result is setup +0.019 ns, hold +0.012 ns, pulse +2.000 ns; 55,412/55,412 routable nets routed, zero routing errors. The native audit passed with zero unwaived DRC errors, positive LCD checks and +1.355 ns on the worst reported buffered reset path. The BIT was emitted from the same hash-bound routed checkpoint. These small positive margins do not establish physical streaming performance.

V43 app-only release: `firmware/experiments/v43-dy71-bulk-hud-20261107/release-bulk-hud-v002`. ELF SHA-256 `efd0a8650853f8d996dd22bfa4fb33d0d1b4da8678f453cb8304ac9579880fb9`; UF2 SHA-256 `476520418833411a5f712bda2193ec17ea2132cbced7804627cd494e564fd33c`. Do not install release-v001.

With Windows stopped, enter physical USB update mode to clear the held V42 lease and install the explicit app-only image. The Windows control-interface driver cannot enter the usable updater automatically. Preserve partitions, SD files and settings. Verify exact V43 ELF identity, then load only the eligible volatile V027 BIT and verify DONE/USERCODE and idle ABI/HBU probes before writes.

## Windows coordination and trial

1. Prepare the unchanged uploader at commit `cbbd85fda`, `host/dy71-lab/dy71_fixture_sender.py`, with original adjacent `packet0.cu66` and `packet1.cu66`.
2. After the handheld's boot is verified, start one invocation with `--receiver 192.168.0.157 --bind 192.168.0.47 --initial-wait-seconds 600`, using a fresh log. Report the printed session and actual source IP/port while it waits. No whole-run retry.
3. Verify actual handheld IP/filter, Wi-Fi heap/largest allocation, stack and exact image/profile. Arm the receiver only after the uploader is confirmed waiting, avoiding the idle owner-release window.
4. Send only original KEY frame 0, then dependent P frame 1. No JPEG/MSV1, video loop, audio, AV or controller injection.
5. Require matching status-2 presentation replies for both frames and independent 2 accepted/2 presented, zero rejection/underrun, all 42,240 actual HUD words read back equal, plus natural colors/expected held scene. Retain the endpoint/lease on final image or failure; do not force-release or switch FPGA images underneath it.

## Record and compare

Record firmware/FPGA/source hashes, actual session/source/destination, per-frame replies, elapsed time, HUD write/readback time, QSPI attempts, native CPU preparation time, allocation/heap/largest block and stack low-water. Keep camera/operator observations separate from counters and simulation.

V42/V023 physical baseline: 35.050912 seconds total, 28.430830 seconds HUD write/readback, 392,927 QSPI attempts; native CPU 304,230/209,963 microseconds; 42,240 words verified. Do not infer an improvement until the exact new physical trial has completed.
