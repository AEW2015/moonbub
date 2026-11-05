# V39 full48-frame AB38/CS38 qualification

Frozen adaptive binary coding is extended from v38's12-frame prefixes to both
complete48-frame histories, including keyframe24. There is no parameter retuning,
new coefficient transform, source preprocessing or syntax change.

| Window | CS37 complete bytes | CS38 complete bytes | Saving | Active MSE, unchanged |
| --- | ---: | ---: | ---: | ---: |
| Primary | 434,875 | 382,756 | 11.9848% | 14.383661 |
| Complex | 1,057,390 | 950,940 | 10.0672% | 26.544696 |

Complete maxima are19,413 /36,397 bytes. All288 selected plane payloads use
arithmetic; both actual full/compact alternatives are paid and archived for
each plane:576 AB38 components. Old CS37 fallback retains strict no-growth
semantics. These are96 causal frame cases on the same reused clips, not new
captures or held-out content. Relative to the matched fixed legacy histories,
complete reductions are16.87% /14.07%, at their identical displayed pixels.

Independent replay imports no arithmetic encoder. It decodes all576 alternatives,
checks exact winner/fallback ties, whole causal references, coefficients, HUD,
display tags, byte accounting and key24 behavior. The six inherited frozen AB38
component/frame tests qualify unchanged syntax; no additional unit-test count is
invented for a larger dataset. The new driver and all retained artifacts are
source-pinned and included in the outer v39 inventory.

The driver reuses already encoded CS37 input. Six binary candidate encodes cost
42.85 /108.31ms per frame on this host; input encoding is externally paid and
these are candidate-only clocks. Frame validation still uses the frozen full-array
proof adapter. This is not integrated sender/receiver timing or a native FPGA
decoder, and no physical30fps follows. The original-input native anchors remain
smaller at better MSE; see the v39 comparison.

```sh
cd experiments/python-game-binary-full-v39-study
python verify.py
```

The different generic import names in `bridge.py` deliberately keep the frozen
AB38 helper namespace separate from this driver's output directory. No frozen
globals are patched. Source arrays are read from inherited content-addressed
objects; no original media download is required for replay.
