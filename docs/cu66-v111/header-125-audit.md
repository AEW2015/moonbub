# V111 Header-125 native route audit

Audit status: **PASS_V111_NATIVE_FINAL_AUDIT** for receipt, pin, and report consistency. The 8 ns target result is **negative** (`FAIL_125MHZ_COMPONENT_SETUP`).

- Receipt `experiments/python-gamebub-v111/native/20261108T185212082116Z/receipt.json` SHA-256: `f9e64cede50cb6b9b9c7ea20153aaac4c32909579180f3819267e228d158ec87`.
- Prepared gate, policy, dispatch, source/recipe/tool pins, all 72 external artifacts and all 97 retained files rehash successfully.
- Fresh RTL out-of-context synthesis and routing at 8 ns/125 MHz; default synthesis selected by omitted CLI directive. No checkpoint, hardware, or bitstream.
- Setup WNS **−3.525 ns**, TNS **−47241.035 ns**, **39,342 / 89,310** failing endpoints. Hold WHS **+0.096 ns**, no failures; pulse WPWS **+2.750 ns**, no failures. All routable nets completed with zero routing errors.
- The timing table reports TNS −47241.035 ns; the separate Setup total-violation line displays −47241.036 ns, a 0.001 ns report-rounding difference.
- Worst path: `coefficients/child/scratch/read_segment_reg[1]/C` → `coefficients/child/scratch/state_reg[0]_rep/D`, 11.401 ns over 12 logic levels.
- Actual Count-125 same-clock 8 ns control WNS is **−3.264 ns**, so Header is 0.261 ns worse. No 10 ns result is used as comparator.
- This is an out-of-context component result, not full-top I/O timing, bitstream, board, or 30 FPS qualification.

Details: `experiments/python-gamebub-v111/audit/header-125-final.json`.
