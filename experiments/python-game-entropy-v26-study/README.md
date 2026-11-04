# Exact coefficient run coding for Gamebub

EC26 is a new laboratory coefficient syntax. It preserves all quantized int16
coefficients, their reconstructed references, displayed pixels and exact HUD.
GE26 wraps frozen GM25 maps/prediction/quantizers with an additional plane
dispatch. CP26/JA26 use the same atomic Python publication contract and60/65-byte
binding/ACK sizes as v25, with distinct protocol magic. Existing peers reject it.

Each plane tries actual EC26 bodies against its retained v25 incumbent. The
incumbent wins ties. Zero/full/DC classifications and quantized data are not
changed. EC26 codes row-reset DC deltas plus three sparse AC streams. Runs cross
block boundaries, eliminating CP02's per-block EOB/run prefixes. Each band's run
and level Rice parameters minimize exact bounded bit lengths. Headers, CRC,
padding and raw fallback all count.

Two native policies test block-major AC and the smaller of block/frequency-major
layouts. The former can conceptually decode with DC plus three AC stream cursors
and one128-byte coefficient block, given random access to the retained compressed
packet. A separate Python four-cursor iterator now proves block-by-block output
against the full-plane oracle. A hardware scheduler and memory-port timing have
not been implemented. Frequency-major needs full-plane coefficient staging
or an additional indexing/memory design; it is not automatically a small-buffer
DSP pipeline. Report these alternatives separately rather than treating stored
packet bytes as the complete memory cost.

The campaign repacks the96 v25 capped-key RDO1 source frames into192 actual
CP26 transactions, replaying each alongside its actual CP25 baseline. Every
coefficient, reconstructed plane/tag, RGB565 hash and quality statistic matches.
The same actual HU25 packets are used. Complete bytes cannot grow because each
plane has a frozen fallback and frame/envelope sizes are unchanged. This is
lossless entropy improvement, unlike v25's lossy RDO/changed reference policy.

```sh
python -m unittest -v test_model.py test_protocol.py > tests.log 2>&1
python benchmark.py > run.log
python verify.py > verify.log
```

Rates project bytes to30IDs/s on reused precompressed29.88fps footage. Host
repacking/decoder timings are measured separately; old source encoding was not
retimed here. No hardware, native target/transport, SDRAM arbitration, fitted
FPGA resource/timing or physical30fps proof is provided. The current JPEG path
and frozen v20/v25 handoffs are not modified.
