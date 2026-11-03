# JPEG end-of-image output backpressure follow-up

The preceding `marker-audit/jpeg_input_candidate.v` prevents parser state and
`img_end_o` from changing on an unaccepted EOI. It still asserts the distinct
`data_last_o` signal without checking that the EOI byte was accepted. The actual
`jpeg_core` connects that signal to `jpeg_bitbuffer.inport_last_i`, which sets
its internal drain flag independently of `inport_valid_i`. A premature last
pulse can therefore request drain while downstream is blocked. This is a
component-level hazard; no actual hardware failure has been attributed to it.

`tb_real_eoi_last.sv` uses the unchanged valid synthetic 720×480 `0006.jpg`
from the previous fixture generator (SHA-256
`013dc842ef06b249da968c009c57bff4905728d40c6166f22147302a37af6e38`). It
feeds the whole file and holds the actual final 32-bit word `40 1f ff d9`
stable. It accepts the first three bytes, then deasserts downstream ready while
the real EOI `d9` is waiting. No JPEG bytes or source-valid rules are altered.
The existing broader parser candidate emits `data_last_o=1` despite no EOI
acceptance; the directed checker fails at 335.692 µs in both XSim 2025.2 and
Verilator 5.020. It resumes ready afterward only in a passing run.

`jpeg_input_followup.v` is an isolated copy that adds valid, accepted and
entropy-state qualification to that `data_last_o` expression. It passes the
same test in both simulators and asserts `data_last_o` when the genuine EOI is
accepted. These are component-level checks; the full buffering/bitbuffer drain
interactions and other marker paths still require stress and audit. The change
has **not** been integrated into production or FPGA hardware and is not a
complete JPEG parser fix.

The follow-up also passed a ten-frame full-resolution behavioral Verilator run
with the existing abstract one-frame queue and burst/LCD model. All ten decoded
RGB565 dumps matched the earlier guarded run byte-for-byte and each matched the
related fixed-color C model. Presentation results were unchanged: 29.284 fps
over nine intervals, not sustained 30 fps. The test did not force EOI stalls
and omits physical Wi-Fi, QSPI, panel, FPGA timing and hardware validation.
The fixed-color C model shares algorithms with the RTL and is not a fully
independent decoder.

Run `./run-eoi-tests.sh` for a bounded Verilator previous-FAIL/followup-PASS
matrix. `./run-ten-followup.sh` rebuilds and runs the ten-frame regression and
checks all ten against the related C model. Both require Verilator 5.x, C++,
make, timeout and Python/Pillow. For XSim, compile `tb_real_eoi_last.sv` and
one candidate in a behavioral project and point `+JPEG_FILE` at fixture 0006;
set a 2 ms test duration. XSim runs here used generic `xck24-ubva530-2LV-c`
because the installed Vivado lacks the actual Artix-7 part. The fixture path
was provided as a testbench default, with all stimulus and checks otherwise
unchanged. XSim `$fread` reports an insufficient-data warning because its
oversized destination is longer than the fixture; this is expected, and all
fixture length and EOI checks passed. XSim simulation exit code alone can be
zero after a `$fatal`, so check the log for the first fatal or terminal PASS.

Evidence:

- `real-eoi-previous-{verilator,xsim}-fail.log`: prior candidate fails.
- `real-eoi-followup-{verilator,xsim}-pass.log`: follow-up passes.
- `ten-frame-verilator.log` and `ten-frame-hashes.json`: ten-frame regression.
- `tb_eoi_last.sv` and `previous-candidate-xsim-fail.log` are the original
  reduced diagnostic; the real-file EOI scenario above is the stronger test.
