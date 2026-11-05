# Optimized CPL1: routed setup FAIL

The fixed-clock Rev4.1 implementation completed on 2026-11-05 at 05:11 Denver. **No BIT was generated and this candidate must not be programmed.** Build50 remains the installed hardware path.

| Gate | Result |
|---|---|
| Routed setup | FAIL: WNS −1.618 ns, TNS −7795.573 ns, 13,015 endpoints |
| Routed hold / pulse | +0.015 ns / +2.000 ns, zero failing endpoints |
| Routing | All 50,673 routable nets routed; zero routing errors |
| Actual optimized wrapper/native replay | PASS: 691,200 pixels, two held-image canvases, CRC 4c5725e5 |
| Actual optimized board/QSPI replay | PASS separately sealed in `cpl1-optimized-board-native-observer-20261105`: all 259,200 physical words, 139 snapshot checks, 40 real QSPI words |
| Hardware / external QSPI hold / warm PLL memory retention | NOT RUN / NOT PROVEN / NOT QUALIFIED |

`source-freeze.json` (58be226c18264735705f38c4e4f606c2d6d69e7e3003e5ad1b8a4019cf2d3bcc) selects the exact optimized source. `optimized-bindings.json` and `verify_optimized.py` bind and reverse the observer-only deltas to the qualified constant-bounds v008 parent. Copied baseline `prepare_*`, `seal.py`, `verify_sources.py`, and baseline binding files are historical recipes, **not the selection or seal authority** for this successor. Use `seal_optimized.py` and the resulting manifest. Product sources remained frozen throughout simulation and implementation.

The clocks, official pins, LCD polarity, SDRAM 279° capture phase, I/O budgets, exceptions and device were preserved. The executable `build_board.py` stages actual bound `key.cp23.hex` and `quantizers.hex` in the build working directory. The final routed checkpoint is SHA256 `04a54e2316064bdf5e08bc129f40cf53064a2a4e23f72740cbdc2a16dc4dbd24`.

The default DRC report caps REQP-1839 at 20 and therefore is not a complete reset-cone inventory. The independent GM mapped-INIT review preserves the default report and produces uncapped reports separately. Active-read leaf enable proofs do not imply all RAM ports or warm retention are safe. `check_timing` also reports 17 inputs without I/O delay (buttons and asynchronous QSPI samples), partial CS delay, and two forwarded-clock outputs without output delay. The existing asynchronous crossing methodology and 10 ns max-datapath constraint do not prove board/ESP external QSPI hold.

This private one-ROM fixture has CAPS zero. It does not implement a complete CP23 network profile, arbitrary images, P prediction, host ACK semantics, audio/controller coexistence, or unique-frame 30 FPS.
