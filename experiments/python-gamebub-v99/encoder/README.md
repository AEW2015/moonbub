Fresh RGB to current CU66
========================

`fresh_cu66.encode_sequence(frames, quant_scale=16, output_dir=None, *,
clip_id='clip', key_interval=30)` consumes fresh `(480,720,3)` uint8 RGB arrays.
Scales 8, 16 and 32 are the only values in the unchanged CU66 quantizer grammar.
It returns a report containing every input attempt in `records` and one accepted
full RGB565 raster or `None` per input in `outputs_rgb565`.

The path uses the unchanged v37 analysis Prepared implementation: fresh
`fixed_codec.rgb_to_planes`, zero motion, integer forward DCT, uniform qmap,
quantization, zero hidden coefficients, exact inverse reconstruction and
canonical normalization. Every coefficient plane is a real AB38 encoding,
choosing smaller full dispatch5 or visible dispatch6. This control does not use
the integrated sender's RDO skip selector. It does not consume old quantized
outputs, old packets, old fixtures or GM01 reconstructions.

The sender builds a genuine fresh GS38/CS38 packet and genuine GU66/CU66 packet.
For CS38 sizes at most 49152 the unchanged v66 offline adapter is also checked
byte for byte. Direct construction uses exactly that adapter's headers, CRCs
and canonical tags, allowing the entire native CU66 cap of 49152, including the
sixteen-byte range excluded by the old adapter's input bound. Oversized CU66
diagnostic bytes remain actual constructed bytes and are never admitted.

The exact HUD is generated from the fresh RGB565 source in the fixed native
rectangles. Existing HU25, HX32 and HX33 implementations choose their supported
minimum. HUD motion search is disabled. This differs from the V98 GM01 control,
which has no separate exact HUD. CU66 references advance after each successful
exact v66 receive; V98 GM01 retains an immutable key anchor instead. Source RGB
conversion and reconstruction use the same unchanged `fixed_codec` functions.

Keys are requested every 30 input IDs, beginning with zero. A candidate is
ACKed only after the unchanged v66 Receiver produces the exact fresh sender
canonical planes, HUD words and output tag. Oversized attempts are retained,
counted and rejected; both references are cleared and the next input attempts
an independent key. No input disappears from the report. No quantizer fallback
is performed. Python processing times are unpaced wall measurements, with no
hardware performance inference.

Each record exposes `packet`, `canonical_bytes`, `hud_bytes`, `rgb565_bytes`,
`rgb565`, `expected` hashes, acceptance, reference identities and source hash.
`rtl_components` provides dense post-hidden-zero coefficients, qmap and packed
338-byte qmap, HUD envelope, block size, identity and 8100 operations in Y/Cb/Cr
block-raster order: 1 fills hidden blocks with 128; 0 copies visible zero-residual
P blocks; 2 reconstructs other visible blocks. This is source material for an
independently verified downstream representation, not evidence that CU66 is an
FPGA wire format.

With `output_dir`, every actual packet and every sender golden blob is written.
Golden blobs use deterministic gzip (`mtime=0`); their paths end `.bin.gz` and
the record declares `<kind>_compression='gzip-mtime0'`. SHA256s always refer to
the decompressed exact bytes. Components use a compressed, pickle-free NPZ in
`rtl_components_path`, with dense `coefficients_y/u/v`, `plane_y/u/v`, packed
`qmap`, envelope `hud`, `operations` and scalar identities.
Rejected candidates use `.oversized-cu66`. `records.json` includes all attempts;
`ledger.jsonl` contains accepted causal packets for the independent native
checker. The native checker uses `clip_id`, `frame_id`, `packet_path`, and the
`expected` canonical/HUD/RGB565 SHA256 fields. Golden definitions are:

* canonical: concatenated Y720x480, Cb360x240, Cr360x240 uint8 raster bytes.
* HUD: little-endian `<HHB` width720,height480,count, then each rectangle's
  `<4H` x,y,width,height followed by row-major little-endian uint16 words.
* RGB565: final full 720x480 little-endian uint16 raster with HUD overlay.
* canonical tag: first 16 bytes of SHA256(`<HH`720,480 + canonical bytes).

Goldens come from the fresh sender's coefficients and prediction, before packet
receive. Native validation must compare the unchanged C++ decoder separately.
No native, RTL, FPGA resource, timing, or physical 30fps result is implied here.

Run bounded checks with:

```
/home/lori/gamebub-streaming-prototype/.venv/bin/python \
  experiments/python-gamebub-v99/encoder/test_fresh_cu66.py
```
