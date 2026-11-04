# Native-source GM25 fixed-policy campaign

Run with the repository Python environment containing NumPy:

```sh
python experiments/python-game-native-motion-v25-study/benchmark.py
```

This reuses the96 retained v24 common-YUV420 and original-RGB565 source
canvases:48 frames from each Mass Effect regression window. They are
precompressed29.88fps footage,720×480 coded with720×405 active pixels, reused
across18 fixed-policy cohorts. The campaign performs864 actual GM25 encodes and
isolated decodes. It does not acquire864 independent source images.

Keys0/24 use ROI8/background32. P maps and RDO settings are fixed before each
window; no future image selects their coefficients. The `zero_period8` control
holds a decoded reference for eight frames; other policies publish every
decoded frame. Their different histories can change both quality and bits.
Neither control is a byte-identical rewrite of frozen v24's AR03 adaptive path.
The separate fine-key campaign changes keys to background16 to recover the
primary window's strict quality threshold.

Each result retains real GM25 bytes, output tags/hashes, expanded-RGB565 error
sums, host encoder/decoder times, full search/RDO work and reference writes.
RDO SKIP is lossy; coarse/large-lambda controls that miss the quality floor are
retained, rather than counted as equivalent-quality improvements. Every
reference is an actual decoded reconstructed YUV image, never original source.
Source acquisition and frozen color conversion were retained from v24; these
costs are not timed again. Named memory/work counts exclude Python heap and are
not measurements of target SRAM, BRAM, DDR service or FPGA resources.

GM25 components have a larger diagnostic bound than the streaming complete
cap. This campaign alone does not establish admission: the separate
`python-game-combined-motion-v25-study` assembles actual CP25/HU25 bytes, enforces
the49,152-byte complete cap and replays actual ACKs for every source decision.
Its standalone verifier covers every retained component through actual pairs.
The records here model reliable immediate ACKs; no live capture, link, ESP32,
FPGA decoder, display clock or physical30fps proof is supplied.
