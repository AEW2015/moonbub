# Coordinated MoonBub checkpoint, approximately04:09 Denver

Development continues toward the approximately06:09 morning handoff. Game Bub can remain powered off. No overnight sender, device query, firmware/FPGA installation, SD/settings change or Windows pacing change has occurred. The last installed control remains v30/build50/overlap/32slots; future hardware readiness needs fresh identity/network checks.

## Published candidates

Branch `feature/overnight-30fps-20261105`, latest checkpoint02e10112. V31 remains the proposed first legacy physical comparison. V32 is a read-only CPL1 observer; v33 adds the separately reviewed AV restoration-failure fence. These are uninstalled candidates with target/UF2 checks, not new hardware results.

| Package | Selected input count | Current manifest |
|---|---:|---|
| v31 trace lock scope |568|5aac54272fcfd15f7d440dc58c669620626d37243da46d2d2b6d162960ce0607|
| v32 CPL1 observer v002 |572|c8ac02fa841e5745450219ecd2894179fdc83504cce80b09e7246318676054cc|
| v33 AV restore fence |574|b1de222215958269e81164563fcb0e0cc20dfc1b5578c84b7aa54c1843f7d420|

V32's portable source also completed a clean relocated release, preserving its SDKconfig/ABI and130812B static shared SRAM. V33 remains130812B, with all17 measured PS function frames unchanged. Its focused SDK tests total83; actual native return0 is retained. Restore failures now intentionally exit/quarantine and cannot become a false clean drain after later empty cleanup. Successful normal behavior is unchanged; this is not a measured fix for Sequence losses.

A packaging omission in the initially published v32 export was corrected in commitc59e620: exact upstream license/attribution files lay outside the selected input list and were missing. The corrected package and fresh copy verify; firmware inputs/build helper/image hashes are unchanged. The v33 export includes both notices explicitly. Git-index bytes are checked against local manifest-bound sources; a fresh archive replay is underway.

## Closed receiver correlation

Both retained controls are published with exact traces/joins and explicit gaps. Epoch2's2013421/4096 is last positive at the Windows post-send API; epoch3's2013780/10240 is last positive at outbound Npcap. Neither has a retained receiver packet observation. The SOF paths for2013422 and2013900 remain unknown;2014108 remains unmatched. Complete exports lost2376/2085 trace calls respectively. Numeric capture timestamps were not stored, so no independent three-field receiver join or RF-loss location is claimed. No streaming fix was selected.

V31 reduces hot-lock trace work and adds per-kind loss counts. A separately bound optional compact-history design would add a planned896B and numeric identities with nonblocking per-writer publication. It is not implemented or target-measured; v31 physical comparison comes first. Its trigger policy/absence boundaries must not silently replace the existing Sequence-window semantics.

## FPGA progress and failed gates

The exact restricted CP23 independent KEY/full legacy-HUD path, positive local-ROM loader, actual modeled storage/native rendering, and finite two-distinct-frame handoff have passed source-bound functional tests. Current implemented subset remains CP23/HC22/HD22 selection with HC22mode0/HR01INDEX_RUNS2 only; prediction/history/general bank reuse and custom network endpoints remain unsupported.

- The CPL1 board source passed clock/reset/platform simulations and actual ROM-core rendered CRC4c5725e5 across two native canvases. A separate guarded-read successor passed matched native/reset tests and actual synthesized active-read EN proof: two LCD read ports and one bridge read port disable under their local reset. Write-side EN remains unknown in arbitrary warm states although write strobes are zero; no blanket warm-retention or whole-board signoff follows.
- A new complete board-top simulation is running through functional PLL/ODDR/IOBUF primitives, the actual QSPI/ordered bridge/CSR and native output. Its short smoke passed; full panel/40-word query results remain pending. Primitive simulation excludes analog timing/metastability.
- Registered-byte transpose uses8RAMB36 rather than16 with cycle-equivalent outputs and its own routed component setup+0.605ns/hold+0.167ns. That leaf result does not qualify a whole board.
- Combined BRAM gather/transpose reduced the first complete composition's44912LUT to about25k while fitting101/135 BRAM tiles. Whole unplaced setup remains open. Boundary stages preserved exact full rendering/cancellation; a real CV/abort loop was found and rejected, then fixed without an inferred exception. Loop-free boundary v008 measured-3.084ns, so the stage hypothesis was not reported as a whole-timing improvement.
- Exact fixed-rectangle bounds removed an unregistered HUD DSP path, improving whole synthesis estimate to-2.367ns, with25405LUT/22047FF/99RAMB36+4RAMB18/47DSP. Full adoption checks are still running. This is unplaced synthesis, not routed timing or hardware throughput.
- The next measured path is21-level epoch/cancellation control into the base hash, also feeding memory control. A separately reviewed private-join candidate preserves immediate parent transfer masks and sends child cancellation through its existing registered CANCEL state. Its control/admission tests pass, including unchanged3299973-cycle control schedule; negative/held-HUD/final-sample adoption gates are still running. No clock/constraint relaxation is selected.

Next priorities are complete board-top evidence, functional closure of the exact timing successor, then actual source-bound board implementation if feasible in the remaining window. A negative unplaced estimate may be measured through implementation; it is never relabeled as routed PASS. Setup/hold/pulse, route/DRC, CDC/Gray/reset/IO and ROM initialization remain independent gates before any hardware image is offered.

## Hardware decision

No new custom network port/carriage has been assigned. The local fixed-ROM path and the existing JPEG/AV path are distinct.30 unique physical displayed frames/s remains unverified. The next legacy test still proposes one selected receiver change, build50 unchanged, same saved clip/settings and unused IDs2014200or newer, with camera/outbound capture covering through STOP. No hardware test starts from this checkpoint.
