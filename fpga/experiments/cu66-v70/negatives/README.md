# CU70 native negative-packet replay

This directory reuses the existing full-receiver `Sim` harness by including
`../receiver/tb_receiver.cpp` with its `main` temporarily renamed. It does not
edit that bench or the receiver RTL. `prepare_cases.py` validates the original
v69 negative manifest and fixture sizes/SHA-256 pins, then exports TSV so the
C++ runner has no JSON dependency.

For each of the 28 manifest cases, a fresh simulator instance accepts the
manifest key packet using the native decoder only as a scoreboard, then feeds
the negative packet with mode 8 (no injected fault), requires rejection while
preserving accepted canonical/HUD state, and accepts independent key frame 24
for recovery. The root packet parser, base decoder and native HUD endpoint are
active in this path. The RAM is the bench's transactional model; painter and
scanout are completion/descriptor models. This does not prove physical SDRAM,
RTL painter pixels, physical scanout, target timing, or frame rate.

Run `python3 fpga/experiments/cu66-v70/negatives/run_negatives.py`. Build and
per-case logs plus before/after source hashes are retained in `results/`.
