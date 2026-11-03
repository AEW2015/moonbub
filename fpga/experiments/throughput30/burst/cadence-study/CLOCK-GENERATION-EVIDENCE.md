# Hypothetical display clock and existing MMCM

The 27.0709258 MHz simulation clock is **not the existing routed clock or a runtime-selectable setting**. It requires a new clock configuration and implementation; numerical candidates below are not a Vivado legality, jitter, timing-closure, panel, or hardware result. No design, bitstream, configuration, or hardware was changed in this assessment.

## Existing source and constraints

Study `fpga/rtl/moonshine_top.sv` instantiates a dedicated `MMCME2_BASE` for the panel: input `clk50`, `CLKIN1_PERIOD=20.0 ns`, `CLKFBOUT_MULT_F=56.375`, `DIVCLK_DIVIDE=3`, `CLKOUT0_DIVIDE_F=32.0`. Hence, with an exactly 50 MHz input, PFD = 16.666667 MHz, VCO = 939.583333 MHz and pixel clock = **29.361979 MHz**, not 27.070926 MHz. There is no runtime MMCM reconfiguration interface in this instance. A separate `PLLE2_BASE` generates the study's service/memory clocks, so its ratios are not numerically changed by adjusting this dedicated panel MMCM; all crossings and implementation nevertheless need review.

`fpga/evidence/lcd_pins_rev4.xdc` constrains input pin P17 to 20.000 ns; `fpga/build-final/utilization.rpt` identifies `xc7a100tcsg324-1`. The corresponding routed `fpga/build-final/timing_summary.rpt` reports `praw` and the forwarded LCD clock at **29.362 MHz, 34.058 ns**. It reports overall WNS +0.031 ns and WHS +0.014 ns, and LCD output setup slack +10.260 ns, under that routed design and its constraints. `fpga/scripts/timing-reviewed.tcl` uses provisional LCD output delays of +2.0/-1.0 ns and specific CDC exceptions. Those figures neither qualify the board's actual electrical delays nor establish closure for another clock setting or another RTL build.

The original Game Bub source also uses a 50 MHz input and MMCM VCO `50 MHz / 3 × 56.375`, but its [Game Boy core clock generator](https://github.com/elipsitz/gamebub/blob/ce607713c7dcd87fe42d5c0de5d4be040e61a47f/fpga/src/main/scala/net/gamebub/core/gameboy/HandheldGameboy.scala) shares that MMCM among system, SDRAM, display and SPI outputs. Its framework chooses an integer display divider based on the selected revision. Changing that shared VCO or divider is a separate implementation problem; the study's dedicated-MMCM candidates must not be transplanted as if other clocks were unaffected.

## Arithmetic candidates only

At exactly 50 MHz in, `fVCO = 50 MHz × M / D` and `fout = fVCO / O`. The testbench half-period 18.470 ns gives target `1 / 36.940 ns = 27.070925826 MHz`; its 541×834 raster gives approximately 59.9984 Hz.

| Case | M | D | O | VCO MHz | PFD MHz | Output MHz | Raster Hz |
|---|---:|---:|---:|---:|---:|---:|---:|
| Routed study baseline | 56.375 | 3 | 32 | 939.583333 | 16.666667 | 29.361979 | 65.076174 |
| Retain baseline VCO, change O | 56.375 | 3 | 34.75 | 939.583333 | 16.666667 | 27.038369 | 59.926261 |
| Closer frequency candidate | 22.875 | 1 | 42.25 | 1143.750000 | 50.000000 | 27.071006 | 59.998595 |

The closer candidate is approximately **+80.09 Hz (+2.96 ppm)** relative to the testbench clock, before oscillator tolerance. These are arithmetic examples, not asserted realizable bitstreams. [AMD UG472](https://docs.amd.com/api/khub/documents/1kFbRqzm2fhwGy~cLQG2yA/content) documents MMCM feedback multiplier and CLKOUT0 fractional increments of 0.125 and integer input division. [AMD DS181](https://docs.amd.com/api/khub/documents/iAkxxTOk96ANLJqYf2hgrQ/content), Table 37, gives the Artix-7 -1 MMCM VCO range **600–1200 MHz**, PFD **10–450 MHz**, and output **4.69–800 MHz**. Both examples meet these basic numeric ranges and attribute increments. These checks do not establish all primitive, fractional-mode, duty-cycle, input-jitter or other configuration requirements.

Changing M/D/O changes clock uncertainty, VCO jitter, fractional-divider waveform, phase, duty cycle and reset/lock behavior; actual input oscillator tolerance and jitter have not been verified. An implementation would need tool-validated primitive/clock configuration, regenerated clock constraints, independent CDC and external IO delay review, synthesis/place-and-route with full timing and pulse-width checks, and panel/module specifications before any board experiment. No 30 fps, timing-closure or physical display claim follows from this calculation.

## Local source and report hashes

Paths below are relative to the study's `fpga` directory. SHA-256 values document the exact inspected files:

```text
0475af1af47d1bdc59945e63e785aac5804acbc2f0956afe314150dbfce551be  rtl/moonshine_top.sv
e5ac4f3c8e1e55726920b297e1a451b1b6427b94b9d16ff1d414da90a97103a3  evidence/lcd_pins_rev4.xdc
376ddf38edfd817758b8893765fcdfb4a5f94d35baf18659a56a7cf69b2fdf49  scripts/timing-reviewed.tcl
efdfca968636ec534fb705a33237c7cca05617b31e7a518dcaf36c12195fa953  build-final/timing_summary.rpt
55f43b5d0bfe8492b31b8efb100e42ecf4950eea0c62f028f6c7eb5837d13c16  build-final/utilization.rpt
```
