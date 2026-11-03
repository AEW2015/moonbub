# JPEG stale-marker follow-up

The existing SOF-only guard still permits a stale EOI marker to cause side
effects without an accepted input byte. `tb_stale_eoi.sv` feeds the actual
valid fixture 0006 until a 32-bit-word boundary where the last accepted byte
is `ff` (offset 8503, followed by stuffed `00` at 8504). It then deliberately
presents `d9` as unaccepted data in two scenarios:

1. Input valid is low: the existing SOF-only guard transitions from entropy
   state 14 to idle even though the byte was not accepted.
2. Input valid is high but entropy downstream is not ready: the existing
   guard asserts image-end before the marker can be accepted.

Both are self-checking, reduced directed tests. The stale EOI scenario is a
constructed stimulus, not proof that live firmware produced it or that it was
responsible for the previously observed stale-SOF failure. The actual JPEG
fixture contains legal `ff 00` byte stuffing, not an EOI at this location.

`jpeg_input_candidate.v` is an isolated follow-up to the SOF guard. It advances
parser state only when a byte is valid and accepted; it qualifies the SOI and
SOS state side effects and the EOI output with acceptance and appropriate parser
states. It does not modify the production decoder. Its other state variables,
tokens, invalid streams, reset and backpressure combinations have not been
exhaustively audited. In particular, this is not a general JPEG parser fix,
production-ready change, hardware validation or formal proof.

## Results

- Verilator 5.020: both tests **fail** with the existing SOF-only guard and
  **pass** with this candidate; the candidate also handles an accepted EOI.
  `run-marker-tests.sh` reproduces the exact expected FAIL/PASS matrix.
- Vivado XSim 2025.2 behavioral: same fail/pass matrix; candidate also passes
  the accepted EOI follow-up. XSim was run on generic `xck24-ubva530-2LV-c`
  because the installed environment lacks the Game Bub Artix-7 part. Logs
  are in `*-xsim.log`. The testbench in XSim used the same logic with the
  fixture path supplied as a default and BLOCK hardcoded per run. The first
  XSim launch attempted a plusarg with the wrong CLI option; it failed to
  launch, then the hardcoded-default approach ran successfully. The Vivado
  documentation server was unavailable when researching that launch error.
- Full 720×480 fixture 0006 passes the existing directed stale-SOF test with
  this candidate in Verilator, and all 345,600 RGB565 words exactly match the
  related fixed-color C model. `run-full.log` and `compare-full.json` record it.
- Verilator 10-frame, abstract one-frame-queue replay also passes. The same
  presentation timing (29.284 fps over 9 output intervals) is observed, and all
  ten coordinate dumps are byte-identical to the prior SOF-only guarded XSim
  run that was checked against the shared-algorithm C model. `run-ten.log` and
  `ten-frame-hashes.json` record that comparison. This is not sustained 30 fps;
  compressed arrival, ESP32 memory, QSPI and real Wi-Fi remain unmodeled.

To run the directed test, install Verilator 5.x, make, C++ and Python/Pillow,
then execute `./run-marker-tests.sh`. The script creates seven synthetic 720×480
frames and uses the seventh; it retains logs in a temporary or supplied
`BUILD_DIR`. It confirms the old candidate fails for the expected reasons and
the new candidate passes. The full replay uses the parent burst experiment's
`tb_jpeg720_queue1_burst.sv`, collector, controller, LCD, simulation model,
tile reorder, `moonshine_core.sv`, vendor JPEG source files with the original
`jpeg_input.v` excluded, and `jpeg_input_candidate.v` in its place. Inputs are
the ten generated fixtures; it is not a prebuilt device bitstream.

For the complete 10-frame reproduction run `./run-ten-candidate.sh` with the
same prerequisites plus a C++ compiler. It generates fixtures, requires the
terminal simulation PASS and checks each output against the related C model.
The individual build, simulation and hash comparisons completed; the assembled
`run-ten-candidate.sh` wrapper was syntax-checked but has not itself been run
end-to-end. The directed `run-marker-tests.sh` wrapper was run successfully.
