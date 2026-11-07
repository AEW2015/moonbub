# V91l native decode/display overlap

This isolated experiment retains the physical-scratch serial control and the
same key/first-delta source pair. It starts key-frame RGB after the key is
actually presented, then decodes the delta while that immutable key-frame
consumer is active. Candidate writes, scratch, accepted-reference reads and
RGB reads contend on the same unchanged timed SDRAM controller/pin model.
No memory or pixel preload and no C++ memory response actor is introduced.

`make_wrapper.py` connects `display_overlap_lease` to actual RGB start,
completion/error, reader/mux drain, candidate request backpressure and the
core's presentation drain. Existing `present_drained` remains an external hint;
the core receives the stricter lease-derived gate. Candidate alias protection
covers new handshakes. Display starts require the committed source and no
already-owned aliasing candidate write; native starts enforce candidate/scratch
closure, and the retained allocator protects accepted/front/pending banks.
The timed wrappers remain simulation verification tops, not board bitstreams.

`make_bench.py` derives the frozen all-memory-clients benchmark. An immutable
RGB descriptor preserves source ID, fid, epoch, full generation, bank and
native start/commit clocks independently of the active decode. Every canonical,
reference, coefficient, transform, write/hash and final RGB comparison remains
source-backed. A callback records RGB closure when the actual consumer lease
releases, even if the delta is still decoding. It does not wait for unrelated
candidate memory activity or defer its timestamp until a later helper returns.

Four natural modes retain the control's seeded 80% output-ready probability.
A separately labeled native guard mode (seed 912901/tAC 2 ns) holds the key's
last output pixel until delta commit plus 17 clocks while external vblank and
drained hints remain true. That trial checks real lease-protected pending
publication; its artificial hold is excluded from performance comparisons.
All modes have finite simulation and host watchdogs and strict compiler and
assertion checks. No hardware clock, PVT/SDF, full RTL HUD, fixed 30-Hz source
cadence, hardware30fps or complete validated-decode-under10ms result follows.

The runner compresses stdout online into newline-aligned chunks of at most
about 128 MiB raw each; `mode.pin_logs` defines the exact ordered stream. The
manifest retains whole-stream and per-chunk raw hashes, compressed hashes,
source/input snapshots, commands, diagnostics and actual output files. Consume
all chunks in order; no cross-chunk JSON line reconstruction is needed.

```sh
python3 fpga/experiments/cu66-v91l-overlap-live/make_wrapper.py
python3 fpga/experiments/cu66-v91l-overlap-live/make_bench.py
python3 scripts/cu66-v91l-overlap-live/run_test.py
```

`--seed 912901 --tac 2 --no-guard` runs one natural bring-up mode.
`--seed 912901 --tac 2 --only-guard` runs only the directed native guard.
The existing `gamebub-cu66-v69-build` container supplies Verilator 5.020 and
GCC 13.3.0; builds retain `--timing --assert -Wall`, C++20 and `-Werror` and
use two compilation jobs. Hardware mapping, implementation and testing remain
separate gates.
