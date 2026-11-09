# V117 measured validated-parent cycle results

The terminal guarded B run is
`experiments/python-gamebub-v117/throughput-study/live-guard/attempts/20261109T123743862126Z/receipt.json`.
It uses actual RTL clocks, independent canonical/HUD data, actual C2/root/seal
hash jobs, finite memory service, wrong-ACK debt drain and clean retry.
The exact-cycle A control matches selected V116C in all four records.
The four profiles use the same `actual_001` keyframe and recovery fixture. They
do not establish worst-case latency across all frames or a sustained frame rate.

| Profile | V116C/A cycles | B cycles | B conditional125 MHz | B conditional100 MHz |
| --- | ---: | ---: | ---: | ---: |
| Byte fast |4,166,111|3,704,690|29.637520 ms|37.046900 ms|
| Byte stalled |9,873,327|9,484,122|75.872976 ms|94.841220 ms|
| Row fast |1,416,449|1,126,533|9.012264 ms|11.265330 ms|
| Row stalled |1,844,338|1,553,878|12.431024 ms|15.538780 ms|

The interval starts at the final accepted outer byte and ends at validated
commit. Presentation is a separate fence. Fast row saves 289,916 cycles,
approximately 20.47%; its margin against the strict 1,250,000cycle target is
123,467 cycles. Stalled row still misses that conditional target. Neither row
profile is below the strict 1,000,000cycle threshold for10 ms at 100 MHz.

Each profile validates 518,400 canonical and 42,240 HUD bytes through 1,025
actual hash jobs. Each guard witness has one parent-fault gap edge and one
exact-golden private residual handshake, with 33,384 actual local reads and
matching responses and no final local owner. No private local read or revoked
local response occurred in these four wrong-ACK fixtures; those guard cases
are not advertised as exercised. Existing full-component peer suites retain
their separate accepted physical write/read/replay cancellation tests.

Actual source B125 routed WNS is −2.202 ns. These millisecond values are conditional
normalizations, not achieved clocks. The full parent, SDRAM, ESP32 endpoint,
network and display have no routed-system/board latency qualification here.
Sustained distinct-frame hardware 30 fps and hardware-validated under 10 ms remain
open. Final C is intended to preserve the measured B schedule while changing
physical arithmetic/storage/control structure, and must prove that with its
own fresh parent execution and an exact B-record comparison.
