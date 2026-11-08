# V57/V029 40-frame run: frame 17 allocation failure

## Outcome

The physical V57/V029 run presented frames 0–16. Frame 17 was fully stored (22,953 bytes), then Native Prepare failed with reply 4 (`HUD allocation unavailable`). The sender stopped without a whole-run retry; frames 18–39 were withheld.

Frame 17’s allocator event was kind 3, request 7,680 bytes, live 77,064 bytes, free 27,476 bytes, and largest block 7,168 bytes. The allocator diagnostic maximum was 15,360 bytes. This shows the observed run did not make the earlier 16,384-byte growth request; it does not show that all future allocations will succeed. The APP remained on V57 ELF SHA-256 `c2f4fbef591d85409aed7908e90ab132f1b4348c72379881fd1067dc66fc8ae0`, with `native/hud.hpp` exact-reserve source SHA-256 `92171e1573dc78173b12f5739dc632d09d473daefa3186e286344bdd57b784e0`.

## Sender and telemetry

The sender log records 17 presented frames (0–16) in a count-40 DYN1 v3 session, followed by `frame 17: receiver failed/retained`; it did not retry the run. The recorded sender elapsed time was 25.328 seconds and includes the initial Wi-Fi wait. It does not represent a successful 20-second clip or a frame-rate measurement. The source is identified as local portrait rendering-breakdown footage, not Mass Effect or a live/performance comparison.

Two telemetry re-exports validated, each with 23 rows and checksum `6acef56c`. The device marks underlying transmit loss as unknown.

At the failure snapshot, passive FPGA registers were `0x350=11`, `0x354=17`, `0x358=17`, `0x35c=0`, `0x360=0`, and `0x110=0`. These are time-local passive reads; they do not establish a final whole-core fault state.

V029 remains held in quarantine. This report makes no claim that the image is suitable for release or that the allocation failure is fully resolved.

The raw serial file was readable for this summary but remained open by its recorder, so a stable SHA-256 could not be calculated. Its observed size was 15,067 bytes at the last write time. Sender and telemetry validation hashes are in the JSON companion.

JSON summary: `C:/moon/maintenance/V57-CLIP40-FAILURE-20261108.json`.
