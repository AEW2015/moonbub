# Deterministic 30 Hz fixture generator

`generate.py` creates moving synthetic frames with the existing Moonbub
`host/make_fixture.py` pattern and production `moonshine.encoding.encode`.
Each output JPEG is validated for the same fixed-Huffman baseline 4:2:0 profile
used by the host. Its Pillow-decoded little-endian RGB565 image, JPEG and RGB565
SHA-256 hashes, and rational 30 Hz presentation timestamp are written alongside
it. The output directory must be new or empty; generated binary frames are not
committed here. Inputs are synthetic and are not a substitute for gameplay.

```sh
python -m pip install -r host/requirements.txt
python experiments/fixture30/generate.py /tmp/gamebub-fixture30 --frames 10
```

The reference uses Pillow's JPEG reconstruction and chroma interpolation;
the FPGA has different integer arithmetic and sampling. Do **not** require an
exact Pillow match or invent a pixel tolerance before comparing with the known
fixed-color C model and establishing valid bounds. The fixture has not yet been
run through the RTL decoder. A successful generator run does not demonstrate
firmware, transport, scanout or FPS.

`example-manifest.json` records two identical 10-frame generator runs with the
same local Pillow version. It is an environment-specific snapshot: Pillow and
libjpeg versions may affect encoded or decoded bytes. Regenerate and compare
hashes on the other machine; differences are a reproduction failure to inspect,
not automatically a hardware fault. Timestamp values indicate desired cadence,
not measured presentation times.

For the existing 64×64 pipeline fixture, an instrumented version of the RTL
bench writes the first decoded frame's coordinate-tagged pixels. Run
`fpga/experiments/throughput30/run-pipeline64-reference.sh` with Verilator and
Pillow to reproduce the comparison. The bench still checks memory against its
own decoder output; the new Python check compares that output with Pillow.
One local run recorded 1,593/4,096 exactly matching RGB565 pixels; the maximum
channel difference was two quantization units. See
`pipeline64-pillow-comparison.json`. This characterizes only that fixture and
is not a general acceptable tolerance or proof of decoded image correctness.

A separate Ubuntu container run with Python 3.12/Pillow 10.4.0 repeated the
generator twice and produced identical manifests. Its 10 JPEG hashes and 10
RGB565 hashes also matched the separate Python 3.14/Pillow 13.0.0 run. Both
version-specific manifests are included. This is a 10-frame sample, not a
cross-platform guarantee; actual libjpeg builds can differ.

`generate-small.py` produces 10 distinct synthetic 64×64 JPEGs, validates
that each uses the expected baseline 4:2:0 fixed-Huffman syntax, and records
SHA-256 values. `fpga/experiments/throughput30/run-pipeline64-multiframe.sh`
feeds them through the actual decoder and functional SDRAM controller in
Verilator. The test checks 40,960 pixel writes, each back-buffer word, front
buffer ownership, and 10 ordered frame IDs after **manually injected** display
boundaries. Memory is compared to this same RTL decoder's output; it is not an
independent image oracle. There is no LCD, QSPI, ESP32, clock-paced video input,
720×480 image or FPS result in this small component test.

The same RTL dump was also compared with the existing fixed-color C model,
compiled and run on Linux. All 4,096 RGB565 pixels matched exactly. The C model
shares the core's upstream algorithms and its color arithmetic was adapted to
the RTL, so it is a separate software implementation but not a fully independent
JPEG design. The reference runner now builds the C model and requires exact
matching for this fixture. The Pillow comparison remains independently decoded.

The separate burst experiment also checks a single full-resolution fixture;
consult `fpga/experiments/throughput30/burst/README.md` for that result and the
larger independent Pillow differences observed there. Neither one-fixture error
range is an accepted universal tolerance.
