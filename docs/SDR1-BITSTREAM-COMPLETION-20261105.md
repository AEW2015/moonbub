# SDR1 bitstream completion

The distinct SDR1 local memory diagnostic is built, with BIT/LTX generation
complete. It has not been programmed. This is a small raw-memory probe, not
the full CPL1 design or a Sunshine receiver.

## Selected artifacts

- Source: `fpga/diagnostics/sdr1-20261105/implementation03/inputs` (source-v005).
- Routed checkpoint: `postroute03-alternate01/routed.dcp` under that diagnostic.
- BIT: `image03-alternate01/moonbub-sdr1.bit`.
- LTX: `image03-alternate01/moonbub-sdr1.ltx`.
- Hash-bound evidence: `image03-alternate01/completion-manifest.json`.
- Part: `xc7a100tcsg324-1`; Vivado 2025.2.
- Intended USERID/USR_ACCESS: `53445231` (SDR1).

BIT SHA-256:
`6e6169edf630f63a878cda8da184c7a1176fc9deb13482d46a4887d4aa281be8`.

LTX SHA-256:
`4bef6abc9b4cc0f09ece6730800028ca00dfaf3d141adb0180931437c98d5977`.

## Executed build gates

Routed setup +0.059 ns, hold +0.053 ns, pulse +2.000 ns. All routable nets
are routed with zero routing errors. Native pre-image DRC has zero errors;
four vendor debug-IP warnings remain. The selected CDC report has no critical
or warning entries. Known input/output timing coverage gaps remain explicitly
recorded in `gate.json`; none were added to repair timing.

Source-v005 native-pad simulations04/05 both pass with the fast and slow
implementation-derived digital timing assumptions. Each checks 32 written
and read words, a literal first response, raw trace retention, rejected busy
GO, stable results and held-GO reset admission. These are modeled digital
timing points, not measured board delays or a complete SDRAM margin sweep.

The initial corrected source route missed setup by 0.107 ns on four endpoint
control paths. Physical-only AlternateReplication and rerouting repaired it
without changing RTL, clocks, pins or numeric I/O timing budgets. The selected
checkpoint remains hash-bound to that source build. The earlier failing route
and blocked image attempt are retained.

## Physical test scope

Use volatile JTAG, the reserved exact cable/device and a retained build50
rollback. No ESP32 reflash, persistent FPGA flash or SD write is required.
The VIO GO handshake starts four aligned eight-word bursts on the first SDRAM
chip. Capture the 16 raw samples, response-valid mask, first response, first
error, run ID and write/read/timeout counters. Use fresh run IDs and stable
done snapshots. Do not use the CPL1 USB `P` snapshot command on SDR1.

Expected first response, high word first:
`17071606150514041303120211011000`.

A model pass or a green status raster cannot establish physical memory
correctness. Save raw readback even on failure; restore build50 after the
diagnostic as appropriate. Full CPL1 CRC and network-streaming qualification
remain separate.
