# Morning hardware handoff — 2026-11-08

The selected next hardware combination is **V028 FPGA with V54 as the first receiver control, then V55 for performance comparison**. New images are built and offline-qualified; they have not been installed or physically tested. There is no30fps result.

## Exact selected artifacts

| Role | Artifact | SHA256 |
|---|---|---|
| FPGA Rev4.1 | [V028 BIT](../../fpga/experiments/cu66-v71/stb1-release-v028-20261108/selected-image/moonbub-v028-stb1-rev4.1.bit) | `69da8c4b6ef3e9f15aa8bdca4973624b33a505e2b1116cd06b1e33aa744d527d` |
| ESP32 first control | [V54 UF2](../../firmware/experiments/v54-dy71-stb1-failure-diag-20261108/release-stb1-failure-diag-v001/moonshine-rev4.uf2) | `1f3bd4ce4a8221b57da3ac82acdbee6c5eddddb1adc66e101a8cc0e4c494fa6f` |
| ESP32 combined candidate | [V55 UF2](../../firmware/experiments/v55-dy71-stb1-performance-20261108/release-stb1-performance-v001/moonshine-rev4.uf2) | `5278b95b1ac8b73454c5f0f76771beac606ecdd135ebeca1a0a6395601b0d28d` |

V028 USERID/USR_ACCESS`44593740`, ABI`0x00030000`, caps`0x3f`. Its final routed setup/hold/pulse are+0.005/+0.020/+2.000ns,56,551/56,551nets fully routed, zero routing errors and unwaived DRC errors. Warnings and two inherited bundled-data CDC critical paths remain explicitly documented. Clocks, SDRAM PHY, I/O budgets and pins are unchanged. The [final integrity receipt](evidence/v028-final-selection-review-20261108/result.json) rechecks selected BIT/checkpoint/report and79source hashes.

V54 SDK ELF is`c7506ed07f791338fce41f2903e75081d4c7cef58b6bde6f7bae52aa6b1f19a6`. V55 SDK ELF is`ef005e82d795b3ea1bdb6248901b821a7b5e78ad753de5fe0b6d2766a663976b`. Use these exact ELFs for identity and log decoding; inherited Git metadata is not the SDK ELF identity.

## What passed

- Last physical control: V48/V027, local`.33`,12accepted/presented,253,440actual HUD comparisons, zero rejects/underruns/native allocation failures,21.923482seconds diagnostic elapsed. Corrected software reboot also passed. A genuine battery-level power cycle is not automated.
- Actual V55 Rust/native/selected V028 RTL/SDRAM/HBU/scanout passed12newvideo frames twice: [zero-start memory](../../fpga/experiments/cu66-v71/stb1-v55-video12-system-20261108/REPORT.md) and [deterministic nonzero memory](../../fpga/experiments/cu66-v71/stb1-v55-video12-poison-system-20261108/REPORT.md). Each has12accepted/presented,0rejects/underruns and zero mismatches across6,220,800canonical bytes,4,147,200video pixels and253,440displayed HUD words. HX33→HU25 predictive-envelope transition and bank0/1reuse pass; bank2 is untested here.
- Exact native code passes the existing old3/new12 oracle, fault, rollback and recovery checks under host ASan+UBSan at-Os/-O2. All candidate target builds, packaging and required host/native checks pass. Runtime ESP32 stack/fragmentation and physical throughput remain unknown; native logical arena peaks95,053/98,304bytes.

Model assumptions remain explicit: direct8cycle CSR accesses,100us modeled yields,200ms modeled Prepare, accelerated SDRAM powerup/refresh, no real radio/IDF/SPI/native-CPU timing. Source covers0.367seconds of local motion-test, not the120secondMassEffectclip. Physical margin13/porches are not certified by the simulated40pixel scanout origin.

## What is not selected

V003 LUT replication failed final setup−0.197ns. The one-line CE-factored source removed the intended feedback and improved that local path to+0.289ns, but fresh whole-design timing failed−0.382ns. Its incremental attempt reused95.01%cells but failed placement before routing. Neither produced a selected BIT. The [source-traced parser plan](STB1-PARSER-NEXT-TIMING-PLAN-20261108.md) is the next design task; no new RTL or timing exception was introduced for it.

## Current physical blocker and test order

The handheld is in software DFU, root VID1209/PIDB010/serial802C0E7A, Windows problem28/no driver. Installed factory V48 is preserved; no vendor-client erase/write has occurred. FPGA power was shut down by DFU entry. Do not treat the old`.157`IP or V027 identity as current readiness.

The narrowly scoped Microsoft signed in-box WinUSB binding is prepared, pending the one administrative step. After binding, independently qualify GET_INFO/interface/partition layout and protected backups. Only then app-only apply/readback, separate [one-shot normal reboot](../../host/lab-selftest-v1/normal-reboot-v1/README.md) (20fake-backend tests; not live-qualified), and observed USB composite/CDC/vendorMI00 return plus exact SDK ELF. Whether the updater-root driver binding persists into normal composite mode is unqualified. A control ACK alone never proves reset. The exact DFU image/source association is also a physical qualification gate.

Then verify selected FPGA DONE/USERCODE/ABI, fresh heap/largest block/worker stack/canary and actual IP/filter before local`.33`tests. Run original3/12 with V54/V028; compare V55 with unchanged fixtures/BIT, measuring native service, QSPI transfers/waits, write/readback, decode/presentation, heap/stack and errors. Then run new12. Keep full readback as the diagnostic control. Require a longer sequence/recovery contract and qualified encoder before the120second or30unique displayed frames/s acceptance test. Audio/controller coexistence remains separate.

The checked Windows CU66 branch remains`15ca3422`, providing offline qualification. [Windows preparation prompt](../SUNSHINE-NEXT-CU66-PREPARATION-PROMPT-20261108.md) requests offline readiness first, with no START. No`.47`network trial was run in this local window.

Recovery archive`D:/moon/backups/JPEG-V38-BUILD50-20261107.zip` remains intact: SHA256`14d67fc4fa489fa3f4a00e249f1782aae9b3cfe6c5815aeaaf879dfc0dcdf82f`, rechecked this window. New work remains underC:/moon; old C:/vtmp, C:/mb70 and the checked legacy root links remain absent.
