# Display-only luma filter and temporal diagnostics (V60)

This study applies four fixed luma display presets to 20 reused policy/native-anchor cases: 1,920 display variants over 96 source canvases. It never modifies canonical YUV, reference inputs, encoded packets, or HUD patches. All 491,520 scalar filter samples are independently rederived, HUD words remain exact, and encoded bytes are unchanged.

Identity is the exact control. The stronger presets are display-only alternatives with measured spatial and temporal error diagnostics; their values are not subjective quality or perceptual flicker scores. One fixed preset per display profile requires configuration/negotiation. An oracle that picks a preset per frame is neither implemented nor free of signaling cost. The model filters a full Y plane; line-buffer, DSP, port, and clock implementation is outside scope.

Reproduce with `calibrate.py`, `benchmark.py`, `verify.py`, and the two unittest logs (`tests.log`, `tests_verify.log`). Four producer and two independent tests pass. No encoding is called; no encoded-byte, native-frontier, hardware-fit, or FPS gain is claimed.
