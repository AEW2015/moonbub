# CPL1 reset/pipeline bitstream completion

The full CPL1 fixed-ROM fixture BIT is complete. This is build and digital
fixture qualification, not physical SDRAM or 30 fps playback qualification.
No hardware was programmed during this work; the ESP32 image was not changed.

## Selected build

- Candidate: `cp23-reset-tags-bytewrite-20261105-v001`.
- Source: `fpga/candidates/cp23-reset-tags-bytewrite-20261105-v001/inputs`.
- Selected route: that candidate's `implementation02/routed.dcp`.
- BIT: `image-reset01/moonbub-cpl1-timing-rev4.1.bit` under the candidate.
- Source/report/image binding: `image-reset01/completion-manifest.json`.
- Part/tool: `xc7a100tcsg324-1`, Vivado 2025.2.
- Intended JTAG USERID/USR_ACCESS: `c2310001` / `43505231`.

BIT SHA-256: `6f88b65557171575dc7a647e182d61458431057df118b54095c545880da85884`.

The source retains the capture274.5 candidate's positive-edge read retiming
and 274.5-degree 100 MHz receive phase. It includes carry-save final SHA sums,
removes runtime reset from 256 private expected-tag bits initialized at job
start, and registers private SHA byte writes. The byte reservation adds one
flush cycle per 64-byte compression block. Control, ownership, valid and
recovery resets remain. The reset/pipeline work does not relax clocks, pins,
I/O budgets, timing coverage or the protocol.

## Executed gates

- Routed setup **+0.022 ns**, hold **+0.018 ns**,
  pulse **+2.000 ns**, zero violating endpoints.
- All **49,156** routable nets routed; zero route errors.
- All four bus-skew constraints pass; timing coverage matches the original
  recorded 17 input / 2 output / 1 partial-input gaps, with zero unconstrained
  internal endpoints or clock/loop errors.
- Native pre-image DRC has zero errors; retained warning counts are recorded
  in the completion manifest and uncapped native inventory.
- CDC summary retains the baseline's four multi-bit synchronizer warnings and
  54 clock-enable-controlled crossings, with no critical findings. These are
  reported, not claimed to be physical CDC proof.
- Both fast/slow full-board digital fixtures pass **139 checks**, **40 actual
  QSPI observer reads**, **259,200 modeled pad writes**, and original canvas
  CRC **`4c5725e5`**. Two held scans do not establish two unique frames.
- Envelope public-output comparison passes **479,238 cycles**, nine complete
  fixtures, error reasons 1 through 6 and reset/abort recovery.
- Combined SHA passes 27 known-answer/boundary cases, four negatives and 295
  reset/abort cases. Targeted pending-write/flush cancellation passes another
  four cases with two recovery hashes.
- The checked synthesized `outer/base_sha` storage cone changes from 185
  remote sequential sources to zero, with 15 local pending-write sources.

Matched synthesis of the isolated reset-only change removes 256 direct reset
loads and 133 LUTs. The reset-only route still failed after bounded repair
(-0.482 ns); it is retained as rejected evidence. The selected pipeline build
has its own complete simulation and implementation evidence.

The margins are narrow; the proposed +0.250 ns multi-build margin target has
not been achieved. The two memory timing-model points are implementation-
derived assumptions, not measured fitted-memory delays or a margin sweep.

## Next physical gate

First use the [completed SDR1 probe](SDR1-BITSTREAM-COMPLETION-20261105.md) for raw
burst readback. Then load this CPL1 image using volatile JTAG and a quiet UI,
capture fresh observer cookies/generations, and require the physical canvas
CRC `4c5725e5`. Keep the verified build50 rollback available and preserve the
microSD and ESP32 flash. The earlier shifted-burst CRC `dec6d87d` is a failure,
not an alternative expected result.

This profile remains fixed-ROM **CAPS0**, with no custom UDP loader or network
port. Do not announce Sunshine/MSV1 readiness from this build. Restore the
compatible JPEG/AV image before those tests, or separately qualify a versioned
custom loader. Audio/controller coexistence and 30 unique displayed fps remain
separate physical acceptance gates.


## Subsequent physical evidence

The SDR1 hardware test failed burst response alignment: all expected words
were present in the raw samples, but the selected response omitted word zero.
See [retained readback](SDR1-HARDWARE-READBACK-20261105.md). The separate
[reference BL8 window characterization](SDRAM-WINDOW-MEASUREMENTS-20261105.md)
passed full-memory interior controls and identified a marginal phase boundary.
These later measurements do not change the archived build/simulation gates;
the full CPL1 candidate remains gated on physical readback and CRC. Build50
was restored after testing.
