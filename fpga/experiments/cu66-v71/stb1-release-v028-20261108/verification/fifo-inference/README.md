# STB1 black-box inference verification

Completed: `result.json` and `REPORT.md` record a PASS for exact RTL OOC functional-netlist behavior plus structural checks of the selected routed FIFO RAM. The final common testbench is `tb_stb1_blackbox.sv`; final runs are `rtl04` and `ooc-netlist09`.

The selected routed cell was exported, but cross-boundary optimization changed its interface. It was not connected to the original-port harness by guessing. Instead, one authorized Vivado invocation queried the immutable selected RAM configuration/connectivity and synthesized the exact FIFO RTL OOC with original ports and hierarchy preserved. The source and selected DCP stayed unchanged. All OOC artifacts, command receipts and mapping comparison are under `C:/moon/builds/stb1-inference-ooc-v001`.

Reproduce in fresh output directories:

```powershell
python C:/moon/dev/experiments/stb1-netlist-verify-20261108/run.py --output C:/moon/dev/experiments/stb1-netlist-verify-20261108/fresh-rtl
python C:/moon/dev/experiments/stb1-netlist-verify-20261108/run.py --netlist C:/moon/builds/stb1-inference-ooc-v001/burst-ooc-funcsim.v --module cu71_staging_burst_v1 --output C:/moon/dev/experiments/stb1-netlist-verify-20261108/fresh-ooc
```

The same black-box suite checks 10 scenarios, eight full-capacity FIFO events and 13,329 actual native staging packet-port bytes, with stream-order/CRC comparators. It never names internal DUT pointers/RAM. Official Xilinx UNISIM/glbl models are loaded and hashed through the compiler dependency list. No SDF or physical timing is claimed.

Initial failures and the precise LUT6 startup reproducer are retained. The final harness initializes external pins after primitive initialization, waits for GSR and retains stronger unknown-state assertions; it does not change/force DUT state or weaken checks. See REPORT.md for exact assumptions and caveats, including the separate maximum 1,024-byte raw staging contract and the unqualified optimized full routed cell boundary.
