# V111 Header-100 native route audit

Audit status: **PASS_V111_NATIVE_FINAL_AUDIT** for receipt, pin, and report consistency. The 10 ns target result is **negative** (`FAIL_100MHZ_COMPONENT_SETUP`).

- Receipt `experiments/python-gamebub-v111/native/20261108T184908625174Z/receipt.json` SHA-256: `a5ee61027e88414d27867875be6d5dc50ca2356a45e6ef958ee7f6723b944704`.
- The run used the independently accepted secondary prepared gate `experiments/python-gamebub-v111/audit/header-100-secondary.json` (SHA-256 `ca0128dc5a6f69cdf3bdc57ee2e8f9d1dac4f98af4dd0e44eb03b2dd34748633`).
- Fresh RTL out-of-context synthesis and routing at 10 ns/100 MHz; default synthesis selected by omitted CLI directive. No checkpoint, hardware, or bitstream.
- All 18 source snapshots, recipes/tool pins, 72 external reports and 97 retained files match their recorded hashes.
- Route completed with zero routing errors. Parsed setup is WNS **−1.526 ns**, TNS **−3066.815 ns**, **8,110 / 89,297** failing endpoints. Hold WHS **+0.101 ns**, no hold failures; pulse WPWS **+3.750 ns**, no pulse failures.
- Frozen V110 Count control at the same 10 ns target has WNS **−1.022 ns**. Header is 0.504 ns worse and also fails. The separate 8 ns Count-125 result is not used for this comparison.
- This component route does not qualify full-top I/O timing, board hardware, bitstream, or 30 FPS.

Detailed pins and checks: `experiments/python-gamebub-v111/audit/header-100-final.json`.
