# CPL1 source / failed-route handoff

**SETUP FAIL: do not program. No BIT, DCP, EDIF, mapped netlist or vendor primitive libraries are shipped.**
This exact Rev4.1 xc7a100tcsg324-1 source produced routed WNS -1.618ns at preserved clocks/budgets. It is a diagnostic development baseline, not hardware-ready or a complete CP23 endpoint. See ROUTED-STATUS.md and ROUTED-DIAGNOSIS.md.

The inputs/ tree is the exact implementation snapshot. key.cp23.hex and quantizers.hex are deliberately also at the working-directory root to resolve original readmemh basenames. Requires licensed Vivado2025.2 with Artix7 device support; primitive libraries remain tool-owned. Python3 verifies the manifest, stages a new directory, then launches four-thread offline synthesis/place/route with the original Tcl. Run:

    python reproduce.py verify
    python reproduce.py build NEW_ABSOLUTE_OUTPUT_DIRECTORY

Build writes reports/checkpoints locally, never BIT or hardware. It does not fix known timing failure and is not expected to reproduce bit-identical routed checkpoint bytes across machines. The source/data/clock/constraint inputs are exact. Digital board evidence is explicitly MODELED, repeated scans of one held image, not unique-frame FPS. Full original simulation benches/oracles and mapped INIT proof remain in their separately source-bound repository evidence; the included result subset is not a substitute for those complete manifests.

## Self-contained Icarus replay (v002)

Install Python3 and Icarus Verilog/vvp (tested Icarus12). No other GameBub checkout or vendor libraries are required. Set IVERILOG and VVP to executable paths if they are absent from PATH. Both modes run the actual product IO branch, with no SIMULATION define:

    python replay.py --smoke --output NEW_EXTERNAL_DIRECTORY
    python replay.py --full --output ANOTHER_NEW_EXTERNAL_DIRECTORY

The smoke runs the saved16-check platform TB with actual board clocks/reset/QSPI/SDRAM. Full runs the exact saved full01 native two-canvases/139-check test and independent40-word fixture parser. Fresh unique output directories are mandatory and must be outside this source bundle; commands, exact copied sources/runtime assets and logs are retained there. The full replay previously took about27minutes on this host. See NOTICES-SIMULATION.md and simulation-selection.json. No Vivado is invoked by replay.py.
