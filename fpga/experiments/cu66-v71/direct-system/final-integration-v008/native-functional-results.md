# Final v008 combined native functional proof

The exact final manifest SHA-256 is `15cc325a837720ae4f54dbb98b30d457d76271f416b7ef1576c198a68fde4b69`, top `cu71_system_final_v008`. All23 selected RTL hashes were verified before compilation and again after execution. The run uses the composed HUD/metadata owner, event retime, parser HUDsum, selected core codecs and unchanged SYNCsafe/grouped SDRAM/PHY/map/clocks.

`evidence/full-pin01/result.json` is **PASS_FUNCTIONAL_DY71_KEY_P_CANONICAL_HUD_AND_LCD** for actual control and chronological KEY/P/P. Each frame's518400 canonical bytes and21120 HUD words match independent native goldens. The qualified actual BL8 controller/pin model produces5452 clean lines, zero black lines,2617264 scored panel pixels, zero underruns and zero RGB traffic.

| Frame | Transaction clocks | Write beats | Read bursts | Underruns |
|---|---:|---:|---:|---:|
| KEY0 |2052736|428160|6240|0|
| P1 |3435121|428160|88104|0|
| P2 |4552093|428160|133224|0|

Every original public control/stage/presentation/fence/frame/counter log line matches the qualified core-v006 replay **exactly, including all cycles**. `core-baseline-comparison.json` records that assertion. The intentionally dropped/retried P1 software ACK remains part of the unchanged test contract.

The independent original-edge event shadow checks actual public ring data immediately after every producer/reset and its following drain edge, without advancing simulation time or changing streaming inputs. Control checks1280 ring words/six records (including abort8 and failure9); frames check3264 words/24 records (including consecutive5→6, ACK10 and presentation7). Sequence, overwrite count, captured timestamps and payload words match.

`native-runner-derivation.json` records the explicit new wrapper/runner binding. The executed wrapper, C++ tests, exact compiled DUT copies, qualified model, commands, logs and SHA pins remain in `full-pin01`. Source-freeze SHA is `2d6ca40fd60067faf6fd89eca474b9aba1b796eeaf14f05b91dc75e89cf3d2cb`; frames-log SHA is `9626475e3a0e9cdcd04c3ddca5a4c4900704b8b9859d099eb73102c59ef76bb4`.

This is native simulation, not hardware. The model retains the documented1ps Verilator monitor compatibility adjustment; native C++ HUD semantic service remains outside HDL execution time. P2 remains45.52093ms at100MHz, so this is not30fps qualification. No Vivado, hardware, clocks, IO budgets, selected RTL or manifest were modified by this test task. Root's routed setup/hold/CDC/IO/DRC/image, firmware/SDK/CSR/QSPI/network and physical playback gates remain separate.
