# Exact CP02 RDO counter v26

This host Python experiment removes packet construction from the frozen v25
isolated-block RDO probes. The oracle is the actual
`python-token-entropy-study/token_coeff.py` encoder used by GM25.

`model.py` exposes `count_packets(coefficients, blocks_w) -> int` for one
general CP02 packet and `isolated_packet_bytes(coefficients) -> int64[N]` for
independent one-block packets. Input domain, row-reset DC, bounded Rice escape
costs, three AC bands, zero runs, EOB, independent DC/AC padding, all four
context bytes, 22-byte header, CRC, and RAW ties are accounted exactly. No
bitstrings, raw-byte coefficient buffers, payloads, headers or CRCs are built.
Malformed geometry/dtype/count is rejected before widened coefficient work.
The isolated path chunks at 1024 blocks, independent of overall input count.

`rdo_skip` preserves source SSE, ROI/chroma halo protection, DC16 shortcut and
v25 decision inequalities. `fast_model.py` copies only v25's two encoder
wrappers and binds this RDO function locally; it exports the normal GM25
analysis, encode, parse and decode APIs. No frozen module is monkeypatched.
Final original/pruned full-plane candidates are still constructed and compared,
so their actual context-sensitive size fallback remains unchanged.

Run with `/home/lori/gamebub-streaming-prototype/.venv/bin/python`:

```
python -m unittest discover -s experiments/python-game-rdo-counter-v26-study -v
python experiments/python-game-rdo-counter-v26-study/benchmark.py
python experiments/python-game-rdo-counter-v26-study/verify.py
```

The benchmark uses retained capped-key v25 RDO1 histories for 96 native
720x480 sources (720x405 active). Every retained candidate, including the
complex-scene key fallback, is encoded with both implementations using the
same prepared analysis and alternating order. References advance only from
retained accepted decoded GM25 packets. Source reads, reference replay, HUD,
and parity checks are outside encode clocks. Shared analysis is measured once
and charged to both variants. Standalone counting uses thousands of native
full coefficient blocks selected by recorded indices from real GM25 parsers.
Five alternating repeated measurements are retained, with medians and hashes.

`results.json`, `run.log`, `tests.log`, and `verify.log` contain measured
results and validation. These are host Python timings, not ESP32/FPGA, radio,
QSPI, mapped-resource or physical 30 fps evidence. Old codec and artifact
files remain untouched. Packet equality means existing CP25/JA25 wrappers can
continue using identical GM25 bytes; those wrappers are outside these clocks.
