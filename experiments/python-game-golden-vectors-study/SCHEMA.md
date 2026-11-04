# `gamebub-ar02-golden-v1`

The root JSON has `schema`, `epoch`, `source_sha256`, `cohorts`, `negative_vectors`,
`counts`, `elapsed_python_seconds`, and `scope`. Unknown major schema identifiers
must be rejected by consumers. `epoch` is 16 for this snapshot. Source pin paths
are relative to the Moonbub repository root, not absolute machine paths.

An object descriptor is:

```json
{
  "path": "objects/<raw-sha256>.<kind>.bin",
  "encoding": "raw",
  "raw_bytes": 43,
  "raw_sha256": "<64 hex digits>",
  "stored_sha256": "<64 hex digits>"
}
```

`encoding` is `raw` or `zlib`; zlib names end in `.zlib`. Consumers verify stored
SHA-256 before decompressing, then raw size/hash. Paths must be relative and may
not contain `..`. Hashes describe exact bytes, not JSON string representations.
An array descriptor adds `shape` and NumPy-compatible canonical `dtype` around
`blob`. Allowed dtypes are `|u1` (RGB888/map), `<u2` (RGB565), `<i2` (YUV). Array
storage is C-order, without NumPy headers. Source RGB shape is `[height,width,3]`;
display RGB565 is `[height,width]`; reconstructed YUV shapes are Y `[h,w]`, Cb/Cr
`[h/2,w/2]`. Scale maps follow the frozen GM ROI geometry, recorded explicitly.

A cohort has `spec` and ordered `rows`. `spec` names its coding/source modes,
width/height, UI choice and frame requests. Every cohort starts from fresh empty
encoder/receiver state. Requests carry `id`, `promote` and `force_key`. Every row
contains:

- `source_rgb888`, `scale_map`: canonical original source/map arrays.
- `ar02`: one complete sealed AR02 packet, including all original CRC fields.
- `gf02`: ordered datagram object descriptors covering that complete packet.
- `af02`: the exact expected receiver publication ACK.
- `identity`: JSON-safe parsed outer/inner routing metadata, with byte tags in
  lowercase hex; `body_crc` is an integer, independent of the packet footer bytes.
- `pre_banks`, `post_banks`: keys `"0"`/`"1"`, each null or `{id,tag,planes}`.
  `planes` are three canonical array descriptors; tag is lowercase hex.
- `decoded_yuv`: the private reconstructed Y/Cb/Cr arrays for this decode.
- `decoded_rgb888_sha256`, `base_rgb888_sha256`: exact returned and unpatched
  RGB888 hashes. Returned RGB follows the frozen RGB565-expanded UI contract.
- `display_rgb565`: the canonical final display word array.
- `selected_pixels`: count of exact source RGB565 words selected by UI patches.

A negative vector has `name`, `target`, `cohort`, `prelude_ids`, `packet` and
`expected`; encoder-feedback cases also name `pending_id`. `target` is exactly
`receiver.begin` or `encoder.ack`. The verifier must reconstruct the declared
precondition, attempt the original bytes, require rejection, and compare semantic
state/ownership afterward. Decoder work counters are allowed to increase. For
feedback negatives, the original correct ACK must remain applicable.

`counts` contains cohort/frame/negative/datagram/UI-word totals, recomputed from
rows. `elapsed_python_seconds` measures fixture export only; it is not a decoder
cycle model or achieved stream FPS. `scope` records the evidence limitation.
