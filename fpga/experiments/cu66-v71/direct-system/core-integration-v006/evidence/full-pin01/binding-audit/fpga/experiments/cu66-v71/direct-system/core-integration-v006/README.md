# Explicit combined core integration v006

This isolated source set combines reviewed codec/parser successors before the separate final owner/HUD/event cleanup. It is not a selected board image or hardware release.

Baseline manifest: `syncsafe-math-v002/sources.json`, SHA-256 `8451653672247a3bad012c3bb90b0d76fdee4802768b5964d6a0a0bf61783b9f`. New manifest: `sources.json`, SHA-256 `826c979a19ad460090636453c1fd2ba239df61ee55d61fe55569bd3ed96055c3`.

New module names are `cu71_system_core_v006`, `cu71_receiver_core_v006` and `cu71_base_core_v006`. Only these binding changes are made in fresh copies:

- Base parent is frozen tag-phase-cut-v003 SHA `4159cb208180f94245ed451118aa034e84ba0895f040562aa4df114a8f47f55d`; replace dequant_resetlight with dequant_validpipe and entropy_arithpipe_v4 with entropy_dcpipe_v6. Retain its current IDCTvalidpipe and all base control/math/error logic.
- Receiver parent is frozen board-math-v001 SHA `7991bfc59ddf2942080185196b103e9af0b72b94857460f5570b92d035bd71d3`; bind parser HUDsumv003 and the explicitly named new base. No owner control, event/HUD cleanup or error-order redesign is included.
- System parent is frozen SYNCsafe-math-v002; bind the explicitly named new receiver. Memory, grouped quota/grace, PHY, physical map, clock/reset and SYNCsafe display are unchanged.

`derivation.json` records all pinned parent/child hashes, exact module-token replacements and textual reverse-equality checks. Interface declarations are checked equal for dequant, entropy and parser before preparing the manifest. All23 selected RTL files are individually hash-bound; no native golden bytes enter the DUT.

`scripts/cu66-v71/direct-system/board-math/prepare_core_v006.py` creates this source set only when every required source SHA matches. `run_core_v006.py` derives the existing source-frozen native pin-model/timeline/fence harness with the new explicit manifest and top binding; it uses Verilator two jobs, actual qualified BL8 controller/model and unchanged PHY timing parameters.

The control run and chronological KEY/P/P replay score native canonical/HUD memory goldens, exact panel pixels or whole-black underrun lines, ownership/presentation fences and zero RGB traffic. Physical SDRAM timing is represented by the qualified pin model, not a latency-only memory mock. The model's documented1ps monitor compatibility replacement is retained for Verilator. Native C++ HUD semantic service remains outside HDL execution time, so these results cannot establish full RTL HUD throughput, hardware or30fps.

Execution is under `evidence/full-pin01`; inspect its completed result/logs and source-freeze manifest. Final owner-source integration, whole-board routed timing/CDC/IO/DRC, firmware/CSR/QSPI/network and physical playback are separate gates. No Vivado or hardware operation is performed by this task.

## Completed native result

Actual control and chronological KEY/P/P pass:518,400 canonical bytes/frame and21,120 HUD readback words/frame match native goldens;5,452 clean panel lines, zero whole-black lines,2,617,264 scored pixels, zero underruns and zero RGB traffic. Control tests retain seven denied writes, two accepted-read abort drains and early-HUD-drain rejection. All selected-source hashes remain unchanged after execution.

| Frame | Transaction clocks | Physical write beats | Read bursts | Underruns |
|---|---:|---:|---:|---:|
| KEY0 |2,052,736|428,160|6,240|0|
| P1 |3,435,121|428,160|88,104|0|
| P2 |4,552,093|428,160|133,224|0|

P2 is45.52093ms at the model's100MHz memory clock; this is not a30fps result. The intentionally retried P1 software ACK and native C++ HUD service remain part of the unchanged harness contract.

Source-freeze SHA-256 is `7995a0560dbbba2a4fd555641e2b86e60a91db7ce07bd05d51cc93350e311cda`; frames-log SHA is `4093c62adde38902a9da44f79c1bc1e978a9edc41bbb1a33fb216e1204e0b84c`.

`binding-summary.json` and `handoff.json` retain the exact counters and manually checked source bindings. The component is PASS; overall release remains INCOMPLETE for future owner changes and routed/hardware gates. `c_check_handoff` was unavailable and is not claimed. Full1371-fixture entropy qualification is separate from this actual three-frame integration result.
