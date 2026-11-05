# V60–V64 evidence audit

These studies share the same four Mass Effect walkthrough cohorts and reuse source material. The native temporal work uses later windows from known clips (IDs 24–47), not unseen games. None measures deployed ESP32/network/panel throughput, FPGA cycles, BRAM fit, or physical 30 fps.

| Study | Verified scope | Boundary |
| --- | --- | --- |
| V60 display filter | 20 policy/native cases × 4 fixed presets × 24 frames = 1,920 display variants; 96 source canvases; 491,520 filter samples. Independent scalar replay confirms immutable canonical/reference inputs, exact HUD, and unchanged encoded bytes. Four producer + two independent tests. | Luma display processing only. Identity is the exact control. Error-change metrics are diagnostics, not subjective flicker or visual-quality proof. Per-frame oracle selection is not implemented. |
| V61 native temporal grid | 48 settings, 1,152 decoded AUs on four later 24-frame windows; five parameter points contain six access units that fail the complete packet cap. | Fresh parameter points, not fresh game content, globally optimal frontier, or FPGA decode. |
| V61 targeted cap | 21 rate-control settings, 504 decoded AUs; three access units over the complete packet cap across three settings. | Requested bitrate is not delivered bitrate. Targeted combat peak-rate evidence, not held-out calibration or transport capacity. |
| V63 filter frontier | All 69 archived native points (48+21), 1,656 presentations, 3,312 filtered variants, 16 custom comparisons; three gate tests plus independent verifier. | Reuses encodes; rederives post-filter quality gates. Not an optimal native frontier or subjective-quality result. |
| V64 pull scanout | 96 actual later-window frames; 46,080 lines; 33,177,600 RGB565 words and 2,027,520 HUD words. Maximum four cached vertical rows, one pending row, two lookahead rows; 7,200 logical row-data bytes. Three producer + five independent tests. | 44.0613 ms includes model assertions/hashes but excludes decode/oracle preparation. Full reference banks and Python temporaries are outside the logical row budget. No RTL ports, BRAM, clocks, or panel timing are measured. |

V60 and V64 filter only display luma; canonical reference YUV and the encoded bitstream are unchanged. The 7,200-byte V64 figure is a model's bounded row ownership, not total device memory. V60's all-case four-preset grid includes identity and stronger presets across both custom and native cases; it does not imply that a runtime can select the best preset for free.
