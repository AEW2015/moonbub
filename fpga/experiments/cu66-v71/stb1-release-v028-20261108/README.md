# V028 STB1 selected board image

This is the generated, routed Rev4.1 candidate, **not programmed or physically qualified**. The source-stage prototype README records earlier gates; `manifest.json`, `selected-image/execution.json` and final reports establish the current selected image.

Selected BIT: `selected-image/moonbub-v028-stb1-rev4.1.bit`, SHA-256 `69da8c4b6ef3e9f15aa8bdca4973624b33a505e2b1116cd06b1e33aa744d527d`, USERID/USR_ACCESS `44593740`. Requires explicit ABI3/STB1 firmware (V52/V54/V55); ABI2/V027 applications must refuse it before writes.

Final setup +0.005ns, hold +0.020ns, pulse +2.000ns. All56,551 nets routed; zero routing errors or unwaived DRC errors. Clocks, SDRAM PHY and board constraints were preserved. Margin is small. Two inherited bundled-data CDC critical paths retain their separate endpoint/token analysis; this is not a zero-critical CDC result.

`inputs/` and `build-evidence/source-freeze.json` contain the exact board sources and constraints. `rebuild/README.md` describes the standalone Vivado2025.2 flow. `selected-image/routed-image.dcp` is the checkpoint associated with the BIT and final identity. Original executed scripts and reports are retained separately from path-portable rebuild scripts. A fresh placement is not guaranteed to produce identical BIT bytes.

`verification/` preserves source, harnesses, execution records and comparisons for pin-level staging, actual Rust/full-system KEY/P, and exact-source OOC FIFO primitives. These scopes differ: direct-CSR whole-system simulation does not include physical SPI/IDF/radio/native-CPU time; OOC primitives are not a full optimized routed-cell or SDF replay. The original compile lists contain historical absolute paths; rebasing simulation runners may be required.

Supported raw alias transactions are at most1,024bytes. The driver and adapter enforce this before writes. An arbitrary longer raw transaction can wrap the inherited12bit CSR address; no hostile raw-burst hardware fail-closed claim is made. Sequential CSR spans require the documented flags/generation/ticket/prefix/CRC fences.

The manifest's overall state is INCOMPLETE because hardware/physical30fps remain unmeasured. Manual artifact/hash/source/report checks were used because `c_check_handoff` is unavailable in this session. See the [candidate index](../../../../docs/cu66-v71/OVERNIGHT-CANDIDATES-20261108.md) for firmware choices and physical test order.
