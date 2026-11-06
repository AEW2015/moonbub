# CU71 implementation status

## November 6 update — supersedes the historical checkpoint below

Latest checkpoint (about 01:10 Denver): implementation03 completed with **WNS -9.606 ns**, hold +0.028 ns and pulse +2.000 ns. The worst measured path is upstream command selection through row-major tile division/address arithmetic to `tile_base`, not the already repaired entropy modulo. A separately derived address micro-pipeline is being verified. Implementation04 uses reset-light payload successors and is still running; it is not a qualified BIT.

Reset-light successors remove reset from 6,603 payload bits that are fully overwritten before valid publication. Four-state tests deliberately retain unknown startup payload and pass 3,471 IDCT tiles under two seeds, 7,081 dequant goldens, 78 reset/abort replays and 1,536 reconstruction tiles. Independent review and complete key/P/P canonical/HUD/RGB readback pass. The whole-system replay retains exactly the same cycles and 2,599 underruns as timing-v001; reset reduction is a timing/resource change, not a cadence result.

The direct-YUV successor now has a distinct **DY71 / 0x44593731, ABI 1.0, capability 0x0f** profile. Existing v35 must reject it. Native fast/slow actual-controller key/P integrity passes, but the P run has 596 LCD underruns. Its first missed line is a Y-page refill during BASE_RUN with PREPARE inactive. Matched reference-copy and bank-locality controls are in progress; no scheduler/PHY fix is selected.

The separate CP23/CPL1 reset-replica diagnostic has now passed a controlled physical fixture: exact canvas CRC `4c5725e5`, zero reported LCD underruns/coordinate errors/lost bridge writes in two live snapshots of one fixed ROM frame. Its routed setup/hold are +0.020/+0.012 ns. Build50 was restored and DONE/USERCODE/USR_ACCESS verified afterward; v32 firmware and SD files were unchanged. Evidence remains in the original workspace under `evidence/hardware-resetreplica-20261106T074932Z`. This is not CU71/DY71 playback or a unique-frame/FPS qualification.

ESP32 v35 is built and packaged, but has not been installed. The selected app-only UF2 SHA-256 is `ba43fc807a6d37d37fb89945708cbe60d920e2552077892bd55a5d737c5c3b5c`. Its source, effective SDK configuration and images are bound by the manifest in the original workspace at `firmware/experiments/v35-cu71-local-fixture-20261105/evidence/build-manifest.json`. Static shared SRAM is 130,924 bytes and the local worker stack is 12,288 bytes; physical heap/stack and first-exception checks remain open.

The actual Rust local key/P worker and bounded native C++ HUD implementation passed against the actual CU71 CSR, owner, decoder and SDRAM pin model: two accepted frames, two presentation acknowledgments, zero rejects, 42,240 HUD writes and 42,240 actual readback comparisons. See `fpga/experiments/cu66-v71/platform-sim/evidence/integration01/audit.json`. Physical SPI, PLL/CDC, FreeRTOS scheduling and target CPU latency are outside this co-simulation. There were **1,313 LCD underruns**; correct reconstruction does not close the clean-display or cadence gate.

The first complete CU71 board synthesis now fits the Artix-7 at roughly 29,000 LUTs and 28,000 FFs; use the native utilization report for exact counts. Its routed implementation **fails setup timing**, WNS −22.710 ns, with positive hold and pulse checks. Measured critical paths include entropy variable modulo/arithmetic, global reset distribution and dequantization coefficient selection/multiplication. Isolated pipeline and distribution successors are in development with unchanged board clocks and external timing budgets. No timing-ineligible BIT will be called hardware-ready.

Canonical storage now infers BRAM with exact-cycle and complete-stream proofs. Pipelined-color and BL8 painter successors pass their declared native pixel and abort/reset checks. Complete key/P/P simulations show that burst output and independent cache responses reduce execution time, but LCD underruns remain. Moving RGB banks helps some conflicts and worsens others; it is not a universal fix. A separate direct-YUV display prototype removes the RGB framebuffer copy: cache/pixel components pass millions of exact pixel comparisons, while full DMA/ownership/native-raster integration remains open.

Morning order: retain the existing JPEG/build50 configuration for the separately coordinated 25 fps test; finish exact-source functional and whole-board timing/route/CDC/DRC gates; bind the selected BIT hash; then install reviewed app-only v35 through the known physical USB update step and run one local actual key/P fixture with fresh recorder/camera evidence. The worker intentionally retains accepted native state and its maintenance lease; paired reconfiguration/restart is required after completion. CU66 network transport is **not implemented**. No 30 unique clean displayed frames/s result is claimed.

## Historical checkpoint

This integration is an isolated successor of pinned CU66v70 commit fcc02c58d46f96a26790ce02826a0bf937c2478b. It is not installed or qualified for30fps.

- Exact-device original v70 resource baseline:96,841LUTs,209,508FFs,44DSPs,2RAMB18. It does not fit the selected Artix-7. Preserve build/baseline-synth01.
- Qualified physical SDR2 controller bytes reused without change; local adapter now supports masked canonical row bursts and dedicated LCD BL8 service. Functional abort/mask/refresh tests pass.
- Actual-controller/model and LCD full-raster tests pass both selected corners:384,000pixels per fixture,0underruns, maxlinefill1,771cycles17.71us under declared synthetic background. This is not wholecodec30fps.
- Canonical rows BRAM successor: same-cycle comparisons for1/2banks plus independent518,404byte oracle each pass. Exact-device native synthesis:373LUTs,809FFs,4RAMB36; synthesized100MHz setup+3.418ns/hold+0.269ns. This is leaf synthesis, not routed board timing.
- Actual local CSR/staging/read-arbiter:74typed identity/side-effect/completion checks pass; max49,152byte staging test245,785checks pass. Board QSPl/SDK integration pending.
- First complete CU66 key against real pin model passed canonical/HUD/RGB readback:136.10ms modeled, painter112.38ms. It still uses scalar RGB/HUD aux operations and fails30fps budget. Dependent P replay is active.
- Full-system C++ adapter missing-return UB was found by ASAN/UBSAN and corrected; original failed exit134 retained. Corrected control tests and sanitized control pass. No RTL failure was hidden.
- Painter BRAM functional successor passes native26rasters and fault/reset cases; inferred resource cut is large, but100MHz combinational color path fails timing. An isolated pipelined/narrow-width color variant is in development; do not build hardware from the failing leaf.
- ESP32 v34CPU-only native HUD probe:457actual histories/21,511encoded transactions plus158recovery cases match native oracle. Exception-enabled SDK target/release/UF2 gates passed offline. Nothing installed. SDKexception-disabled attempt retained and ineligible.
- Next firmware v35 will connect real native HUD service to local CU71 typedCSR link; no CU66 network capability until that transport is agreed and implemented.

Morning sequence: complete target fit/routed timing and actual full key/P tests; retain existing JPEG/B50 for the separately coordinated25fps demo; install reviewed app-only CU66 diagnostic firmware when the operator can provide the known USBupdate button step; then verify actual key/P on CU71 hardware. No fake HUD/drain/presentation acknowledgement is allowed to close a gate.

Existing CP23 physical-candidate stream is separate: balanced candidate and alternate physical optimization both failed strict positive setup (latest-0.113ns). No BIT from those candidates was programmed. B50 remains the last verified installed FPGA image.
