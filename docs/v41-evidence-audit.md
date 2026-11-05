# V41 evidence audit

Audited the V41 checkpoint, raster study, HUD profile, native-cap study and
`docs/prototype-v41-native-cap-comparison.json`. The native comparison check
passes (`compare_native_cap_v41.py --check`); raster producer and independent
replay logs report 4/4 and 8/8 tests passing. Native `verify.log` reports 21
points, 2,100 independently decoded AUs, eight points with cap failures, exact
source/HUD checks, and no encoding during verification.

## Raster study

The gameplay claims match the retained results: Primary is 134,817 control
bytes versus 138,677 candidate bytes; Complex is 309,308 versus 313,076. The
strict complete-packet guard therefore selects the control in all 24 gameplay
frames. The only positive candidate is the flat synthetic fixture (3,095 to
2,683 bytes, 13.3118% saved, zero error). Directional and noise fixtures retain
control. This supports the reset-island hypothesis on that fixture only; it is
not a gameplay bitrate gain.

The replay totals agree: 27 selected frames, 162 rank trials, 843,048 candidate
recomputations and 218,700 causal frontiers. The stated 63,699 eligible exact
alternatives and 20,862 proposed nonzero modes are raster candidate counts, not
accepted gameplay modes. The 2,928-byte edge-cache figure is a logical context
sketch; it excludes frame/reference and transform storage and does not establish
an FPGA memory fit. The reported pair-clock values are host paid-work scopes,
not standalone codec latency or 30-fps evidence.

## HUD profile timing

The six-frame profile reproduces the selected HUD packet bytes. The first audit
found a mismatch: pstats keyed entries by filename, line and function name, so
multiple frozen-module code aliases overwrote each other in the old summary.
The profiler now aggregates each raw `cProfile` entry across six independent
profile instances. The corrected profile reports 2.138403 s summed self time,
2.138667 s instrumented `runcall` wall time, and 2.138306 s cumulative time for
the six `generate` calls; the self and wall totals agree within profiling
measurement overhead. The generator expression now totals 2,547,254 calls /
0.726795 s self time, `format` 2,731,615 / 0.355697 s, and `str.join` 0.166483 s.
Cumulative rows overlap and must not be added. These remain cProfile diagnostics,
not paired unprofiled performance.

## Native cap comparison

The checked comparison draws from 21 added settings across the same 100 combat
source frames: 2,100 actual AUs, independently decoded. Complete-byte accounting
includes the actual AU, exact selected HX33 HUD packet, modeled 80-byte binding,
and actual extradata on frame zero. The 80 bytes are accounting, not an
implemented wire extension. The input is precompressed 25-fps low-resolution
combat video upscaled to the canvas; nominal encoder timestamps do not establish
30-fps capture or physical throughput.

The 49,152-byte per-frame cap findings agree with the study. Eight settings
have at least one over-cap frame, and those candidates are retained as failures.
HEVC CRF22/VBV160 is 2,362,563 complete bytes, mean active MSE 23.9478, peak
33.1654, maximum packet 40,122, and zero cap failures. Its zero-failure
`every_frame_quality_ok` flag comes from comparing each of the 100 actual
active-area squared errors against the corresponding CS38 error; it is stronger
than the mean/peak summaries and is the evidence for the exact-SSE-gated result.
It uses 21.3209% fewer complete bytes than CS38's 3,002,785. This is a measured
point on this sampled combat sequence, not an exhaustive codec frontier or an
equal-hardware comparison.

The comparison correctly separates gates: HEVC CRF24/VBV160 and AV1 CBR3000/
buffer40 pass mean quality only; AV1 CBR4000/buffer40 passes mean and peak but
fails the every-frame gate. No tested AV1 point passes every-frame quality.
AV1 CBR5000/buffer40 passes its gates with only 20 bytes of maximum-packet
headroom, which is not a robust bound. The eight failing settings are three
capped-CRF34 variants (five cap failures each), three capped-CRF37 variants
(three each), HEVC CRF22/VBV240 (two), and AV1 CBR5000/buffer60 (four). These
are settings with failures, not a total of eight failed frames.

This native evidence means the V41 gameplay raster experiment does not establish
custom-codec superiority over native coding. It also does not establish a
physical 30-fps endpoint, hardware decode fit, or transport guarantee. RR41's
only measured positive remains its synthetic flat fixture.
