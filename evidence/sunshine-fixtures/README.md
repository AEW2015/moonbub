# Sunshine JPEG fixture verification

`fixture-review.json` records SHA-256 and host-profile validation for all 15
JPEG fixtures in Sunshine commit `027c59412f19674616a3c31af346320a82e75207`.
`rtl-420.log` and `rtl-444.log` are the actual `tb_core.sv` transcripts for the
frame-0 4:2:0 and 4:4:4 fixtures. The testbench injected FPGA frame ID 7.
For each run, the JSON records the SHA-256 of the generated RGB565 dump, the
fixed-color C-model reference, the core RTL and the testbench. All 345,600
pixels matched the fixed-color reference exactly. The C model shares upstream
JPEG algorithms with the RTL and is not an independent implementation.

Total cycles in those logs include input, deliberately truncated/bad-CRC cases,
backpressure and other testbench work. They are not per-frame decode or display
times. The test does not instantiate the physical SDRAM/panel pipeline.

To repeat without replacing the original golden fixture, use separate checkouts
or copies. Obtain MoonBub commit `d6212c8f79964be2a7e007429d3c8048593267d9`
and the Sunshine commit above; for each mode:

1. In the isolated MoonBub copy, replace
   `host/fixtures/pattern-720x480-420-q65.jpg` with Sunshine's
   `tools/gamebub/fixtures/frame-00000000-420-r0.jpg` or
   `frame-00000000-444-r0.jpg`. Check its SHA-256 against this report.
2. Run `powershell -NoProfile -ExecutionPolicy Bypass -File fpga/scripts/test.ps1`.
   The exact RTL testbench writes `fpga/sim/decoded-rgb565.txt` and `core.log`.
3. Run `python host/build_cmodel.py` and then
   `python host/compare_decoder.py --require-fixed-exact`. These create reference
   images and comparison output inside the isolated copy.

The original test uses 100 MHz RTL clocks and a synthetic memory-ready pattern.
It checks the physical-target decoder source, frame ownership and backpressure;
it does not emulate the complete SDRAM/panel path for these two fixtures.
