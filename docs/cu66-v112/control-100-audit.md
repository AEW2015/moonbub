# V112 control-100 route audit

The fresh-RTL 10 ns OOC `cs88_pipeline_v91k` route completed (exit 0, 1576.6 s, signoff open). Setup timing **failed**: WNS -1.034 ns; TNS -2028.748 ns; 5,607/88,855 setup checks failed. Hold WNS +0.086 ns and pulse WNS +3.75 ns, with zero hold or pulse failures. The frozen V110 Count 100 MHz control WNS was −1.022 ns, making this result 12 ps worse.

**Worst routed setup path:** `transform/fill_bank_reg/C` → `transform/coefficient_banks[1].words[10].value_reg[12]/CE`, slack −1.034 ns, data delay 10.745 ns (2.711 ns logic, 8.034 ns routed), 10 logic levels (`CARRY4×2`, `LUT4×1`, `LUT5×2`, `LUT6×4`, `RAMD32×1`).

The report has one 10.000 ns `component_clk`; zero missing/multiple clocks and zero unconstrained internal endpoints. It counts 1,101 input ports without input delays and 12,856 output ports without output delays at the OOC boundary. No valid timing exceptions were found. All 66,205 routable nets routed with zero routing errors.

Open findings: the 52 DRC checks are warning severity (CFGBVS-1×1, DPIP-1×9, DPOP-1×27, DPOP-2×14, RTSTAT-10×1). DRC 23-814 says connectivity DRC coverage is incomplete in OOC mode. The routed methodology report has 1,029 checks: 20 RAM output-register warnings, 8 large setup violations, 1,000 missing interface-delay checks, and 1 control-set warning. The log notes `HD.CLK_SRC` is unset, so OOC clock skew is not estimated; seven BUFG candidates were skipped for placement/routing conflicts. RTSTAT-10 covers 1,027 nets with no routable loads, including top/debug/interface outputs.

The run used fresh RTL and loaded the fixed clock before synthesis; default synthesis by omission, Default opt/route, `ExtraNetDelay_high` placement, no physical optimization, and no checkpoint. All 18 source files (17 `.sv`, one `.svh`), source/tool/recipe pins, and 97 retained artifacts were independently rehashed. This is component-only evidence and does not qualify whole-parent integration, board I/O timing, physical clock integration, or hardware performance.

Audit record: [`control-100-final.json`](../../experiments/python-gamebub-v112/audit/control-100-final.json). Native receipt: [`receipt.json`](../../experiments/python-gamebub-v112/native/20261108T195804890929Z/receipt.json).
