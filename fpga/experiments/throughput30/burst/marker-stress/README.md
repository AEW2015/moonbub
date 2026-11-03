# JPEG entropy source-gap and backpressure regression

This test exercises only the experimental `jpeg_input_followup.v` parser from
`../marker-followup/`, **not** the entire JPEG decoder, FPS path or hardware.
It feeds ten distinct synthetic 720×480 JPEGs. The source holds each 32-bit
word stable while valid until the word is accepted. During invalid source gaps,
the driver cycles marker-like data (`d8`, `d9`, `da`, `c0`), which hardware
must ignore. A deterministic xorshift pattern stalls entropy output, while
source gaps and final-word strobes exercise byte alignment. The checker requires
exactly one data-last and forbids a last pulse while the downstream is blocked.

A separate Python oracle parses JPEG markers, extracts the entropy-coded scan,
unstuffs `ff 00` and requires byte-for-byte equality with the RTL's accepted
entropy stream. This tests parser byte/marker handshaking, not image decode.
Verilator 5.020 passed 300 runs (10 fixtures × 30 deterministic seeds) with no
entropy byte differences; `entropy-noise-results.json` records fixture and
entropy hashes and the simulator binary hash, and `entropy-noise-verilator.log`
contains the PASS summary. The oracle handles the repository's one-scan,
no-restart fixture profile; it deliberately rejects unsupported scan markers.
It does not cover malformed or arbitrary JPEGs, all seeds, all stall schedules,
all marker side effects, integration with the real output FIFO, or timing/fit.

A Vivado XSim 2025.2 behavioral cross-check ran fixture 0006 at seed 42 with
source-gap noise. It produced exactly the same 25,595 entropy bytes and 46,516
cycles as Verilator for this case. The XSim run used a generic `xck24` part
because the installed tool lacks the real Artix-7; it does not establish
hardware timing. XSim reports an expected short `$fread` warning because the
byte array is larger than the input fixture. See `entropy-noise-seed42-xsim.log`.

Reproduce Verilator with `./run-entropy-tests.sh`, requiring Verilator 5.x,
make, C++, timeout, and Python/Pillow. It generates fixtures under a fresh build
folder; set `SEEDS` to expand the deterministic seed set or `BUILD_DIR` to
retain data. For XSim compile the testbench and `jpeg_input_followup.v` in a
behavioral project, use `+JPEG_FILE`, `+OUT_FILE`, `+RANDOM=1`,
`+NOISE_GAPS=1`, and `+SEED=42`, with the 20 ms watchdog. The saved XSim run
used testbench defaults for those values and paths due the local launch setup;
its data and seed contract are otherwise the same.

An initial XSim elaboration rejected a testbench statement with `XSIM 43-3209`
(unsupported construct); the Vivado documentation search server was unavailable
and official UG900 search did not identify a specific applicable answer record.
A testbench-only rewrite renamed the `randomize` variable and moved its chained
xorshift expression into a function, preserving the algorithm. It then ran and
matched Verilator as described. No vendor patch or DUT change was applied for
that simulator workaround; the exact unsupported subexpression was not isolated.
