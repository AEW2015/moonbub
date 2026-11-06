# V71 actual-controller system simulation scope

The system runner is `scripts/cu66-v71/system/run.py`. It derives a new
`cu71_system_sim` verification wrapper from frozen v70, instantiates the current
`cu71_system`, and copies every compiled RTL file into each fresh run directory.
The implementation controller is the exact SDR2 source-v004 controller, without
the `SIMULATION` define. Functional ODDR/IOBUF models supply its pin behavior.
They do not establish pad placement, electrical behavior or timing closure.

The memory clock is 100 MHz in modeled time. Read-clock edges use the selected
274.5-degree phase and posedge retiming; the panel uses the inherited native
period. Fast and slow access arguments are lumped digital STA terms, not
independent measurements of PCB flight and chip tAC.

The complete 32 MiB checked model is derived from the exact Icarus-qualified
memory component model. Verilator requires a separately disclosed scheduling
variant: the monitor's zero-delay delta step becomes 1 ps. Functional command
and DQ scheduling are unchanged. This is not byte-identical execution of the
Icarus monitor, and Verilator's two-state behavior cannot independently prove
unknown-data rejection. The strict original monitor remains executed by the
source-bound fast/slow Icarus component campaigns.

The native host bench parses original complete CU66 packets and runs the real
C++ HUD semantic endpoint. HUD words travel through guarded RTL auxiliary
requests and are functionally read back before the HUD tag/drain notification.
The independent decoder's canonical/YUV/RGB values are used only in scoreboards.
This bench uses typed processor sidebands; it is not HC70 wire-to-RTL, ESP32
CPU/SRAM or live QSPI/network evidence. Native C++ CPU service is outside HDL
time and must not be omitted from eventual hardware latency accounting.

The bounded control test precedes complete chronological KEY/P replay. Every
attempt retains producer commands, stdout/stderr, copied sources and hashes.
A printed PASS marker with a nonzero process exit remains a failed attempt.

`full-pin01` compiled successfully but aborted after its bounded control checks
printed PASS. `full-pin-asan01` identified the adapter error: renaming the native
bench's `main` to a normal namespaced function removed C++'s implicit successful
main return. Falling off that value-returning function caused undefined behavior.
Both failed attempts remain preserved; neither is a qualified control result.
The corrected driver returns zero explicitly. `full-pin02` passed the normal
control process, and `control-asan-fixed01` passed ASAN/UBSAN with no reported
runtime errors, using the original hash-bound instrumented model archive and
runtime objects with only the corrected driver rebuilt. No RTL or memory-model
behavior was changed to resolve this host-bench error.

Even a successful functional replay would not establish 30 clean unique
presentations/s. Read back canonical planes, exact HUD contents and complete
RGB buffers separately from actual line/pixel observations. Unexpected black
replacement lines and underruns remain cadence failures. RGB/painter and HUD
scalar writes still need an explicit burst-capable API before their bandwidth
can be inferred from canonical row-burst improvements.
