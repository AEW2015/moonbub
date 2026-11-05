# V31: custom-codec RTL acceleration and ESP32 transport notes

The isolated [RTL experiment](../experiments/rtl-game-inverse-v31-study/README.md)
implements the custom codec's exact two-pass signed Q14 inverse transform,
prediction add and clipping. Its zero/DC shortcuts preserve all output pixels.
Generic Series-7 synthesis maps eight shared MAC lanes to **8 DSP48E1s**, using
distributed storage and **zero block RAM primitives** for this kernel.
The eight DSPs implement registered multipliers; the current mapping leaves
accumulation/rounding in fabric (`MREG=1`, `PREG=0`). A DSP P-accumulator variant
is a concrete next comparison, rather than an assumed optimization already done.

Three full Verilator cases each check **33,054 blocks / 2,115,456 samples**:
dense control, shortcuts, and shortcuts with deterministic input gaps/output
backpressure. Directed reset tests cover partial load, partial computation and
stalled output. Four-state RTL and Series-7 mapped functional Icarus runs each
check 654 directed/seeded blocks. The mapped test is a subset and has no SDF.

The corpus includes all 8,100 YUV420 blocks from each of four real 720×480 v30
strict frames, plus 654 scalar-checked directed/seeded cases. Inputs are actual
dequantized coefficients and reconstructed-reference predictions; entropy parsing,
dequantization and reference-memory fetching are outside the hardware kernel.

| Component frame | Dense cycles | Shortcut cycles | Shortcut projection at assumed 100 MHz |
| --- | ---: | ---: | ---: |
| 2600 key | 2,106,000 | 1,455,796 | 14.56 ms |
| 2600 P | 2,106,000 | 1,205,700 | 12.06 ms |
| 7200 key | 2,106,000 | 1,643,988 | 16.44 ms |
| 7200 P | 2,106,000 | 1,369,896 | 13.70 ms |

The dense projection is 21.06 ms. Shortcut blocks take 128 cycles for zero and
132 for DC, compared with 260 for general blocks. Synthetic stalls raise real
component projections to 15.47–19.88 ms. These counts include block input/output
handshakes. They do not establish a 100 MHz routed design or real producer/memory
service. Native decoder, SDRAM, color/HUD, network/QSPI and display timing remain
unqualified; physical 30 fps is unproven.

RTL was selected first to make signed widths, stage rounding, handshake/reset
behavior and DSP mapping explicit. An HLS implementation can later use the same
vectors and contract. No HLS or XSim run is claimed: this environment's configured
Vivado bridge/path did not provide a working session, so this experiment explicitly
uses Verilator 5.020, Icarus 12.0 and Yosys 0.33 in a separate Docker image.

The first Icarus checker failure was reduced to an inline `$isunknown` concatenation
quirk; named vectors preserve the full X/Z checks, with an X/Z-injection reproducer.
The mapped netlist's eliminated parameter needs a parameter-free testbench instance.
The earlier 240-second mapped timeout is inconclusive; the final bounded mapped
test uses the same 654 cases with a 600-second wall limit. See retained diagnostics
and passing transcripts, rather than treating the earlier failures as passes.

The [ESP32 firmware notes](esp32-compact-transport-plan.md) now specify proposed
session/frame/continuation framing: 12 common bytes per fragment plus 16 once
per frame, around 1,400 payload bytes subject to MTU/credits, conservative byte
credit reservations, and bounded DMA handling. They distinguish current MSV1
behavior from proposed changes and include arithmetic savings, compatibility and
loss/reset/CRC/commit tests. **This is documentation only; firmware is not changed
or flashed.** Consolidating inner codec metadata remains a separate parser change.

Next integrate a bounded EC26 coefficient reader and dequantizer, then the exact
fractional predictor with real memory arbitration, block-buffer overlap, color/
HUD composition and publication fences. Reuse these bit-exact vectors before
place/route and hardware testing. Preserve the current JPEG path and v20 handoff.

```sh
python experiments/verify_prototype_v31.py
```

Offline verification checks arithmetic, compressed vector hashes, source closure,
cycle ledgers, simulator PASS/reset markers and mapped resource counts. It needs
the inherited Python/NumPy environment and no original video or hardware.
