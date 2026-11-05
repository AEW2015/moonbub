# V48/V49 evidence audit

Audited the integrated streaming receiver, its allocation probe, the V49 actual
tile traces, work-demand model and their test/verification logs. These studies
cover the same qualified AB38 receiver domain and make component claims; neither
establishes a physical frame rate or a fitted implementation.

## V47 context: fixed global-grid search is negative

V47 evaluates 24 frames from each of four fresh v40 cohorts through separate
fixed-zero and `global_grid` causal histories. The fixed global-grid policy
increases both complete bytes and original-source RGB565 error in all four
cohorts: bytes rise 8.42%, 12.15%, 16.31% and 2.87%; active MSE rises 23.51%,
6.78%, 3.06% and 53.63%, respectively. All 96 zero-control outputs match the
prior controls, and no frame exceeds the final cap. V47 has three producer and
six independent tests; replay checks 192 histories, 1,152 AB38 alternatives and
4,055,040 exact HUD words. Its SAD-based search proxy did not predict actual
rate/distortion outcome.

## V48 integrated streaming receiver

The receiver replays 577 causal frames, reconstructs 4,673,700 coefficient
output tiles and consumes 4,530,538 arithmetic AB38 tiles. Independent replay
confirms exact coefficients, references, HUD and display output, read-only
atomic publication and no full coefficient or prediction arrays in the subject.
It supports only AB38 arithmetic dispatches 5/6 and rejects the legacy 0–4
profiles explicitly; this is not full CS38 profile compatibility. Five producer
and three independent tests pass.

The measured mean whole-receive time is 225.769 ms for the streaming path versus
77.714 ms for the direct full-array receiver (about 2.91× slower). Streaming
removes the full coefficient array, but on this Python host it does not improve
service time. Both paths retain the external-model full reference, reconstruction
and normalized output planes; the receiver stages the frame privately and
publishes only after all late checks succeed.

The separate memory probe runs 16 fresh-process points: two frames from each of
four scenes, once per implementation. Tracemalloc starts after imports, packet
I/O and prior-reference boot; it reports tracked call current/peak bytes, not
whole-process RSS or target memory. Traced call-peak ranges are exactly
10,408,319–30,120,239 bytes for direct receive and 2,799,321–2,852,932 bytes
for streaming. Direct decode records a 1,036,800-byte coefficient array; the
streaming subject records zero. Both
record 1,036,800 normalized output bytes and 42,240 HUD-word bytes. The prior
reference is excluded on frame 1, not frame 0. These tracked allocation
increments do not prove whole process peak memory, include all native
allocations, or establish FPGA/ESP32 fit. The probe is instrumented and is not a
performance test.

## V49 observed tile work and assumed bank schedule

V49 records actual traces over 96 frames, 288 planes and 777,600 raster tiles;
752,420 tiles contain arithmetic-coded coefficients. Replay verifies unchanged
AB38 bytes and coefficients, exact per-tile counter placement, and equal final
eager/deferred arithmetic work. The aggregate traces contain 7,574,207 binary
probability products, 6,116,124 renormalization steps, 4,075,123 first-pass
products, 16,790,995 second-pass products and 1,053,307 dequantizer products.
Three reader tests and three schedule tests pass; the independent log confirms
the same totals and no encoder import.

The schedule is an assumption-based finite-bank work-demand model evaluated on
those traces, not RTL cycles. It models one or four arithmetic engines, eager or
deferred level decode, and one or two coefficient banks. Its engine profiles
assign assumed cycles per binary decision and renormalization; the four-engine
profiles take the maximum stream service and require independent compressed
reservoir refill, ports and state, none of which is demonstrated. The inverse
stage assumes specified MAC lane counts, 16 cycles of complex-block
round/control work and one or eight output pixels per cycle. It also assumes an
eight-cycle bank clear, serial nonzero writes and serial interval preload/guard
reads. Under these assumed services, the README reports component demand at
100 MHz from 14.864 ms maximum (shared conservative, one bank) down to 2.803 ms
maximum (optimistic four engines, two banks). At the assumed 50 MHz, the shared
slow one-bank scenario exceeds 33.33 ms on 17/96 frames, while its two-bank
scenario has no modeled component misses. These cycle totals and conversions
are model units derived from assumptions, not measured RTL cycles or routed
clock results.

One coefficient bank is only 128 bytes of coefficient output; two banks total
256 bytes. The model excludes reference/output memory service, CRC/SHA, HUD,
color conversion, scanout, network, ESP32, QSPI and port arbitration. Frame input
is assumed available. No whole-frame or end-to-end timing conclusion follows
from a modeled component schedule; in particular, it is not evidence of
30-fps operation.
