# V91l Python validation fixture contract

This Python checkpoint supplies an independent expected-hash oracle and real
frame inputs for the V91l RTL/C++ integration. It does not claim a full-frame
RTL publication pass. The current design uses a heterogeneous path: RTL checks
the actual CS88 packet and computes C2 hashes over actual canonical bytes; the
frozen native C++ HUD decoder parses the current HUD component and compares its
semantic output with the retained accepted-history words. Publication must wait
for those checks and all writes to drain.

## Retained inputs

[`validation.tsv.gz`](../../experiments/python-gamebub-v91l/vectors/validation.tsv.gz)
has ten tab-separated columns:

1. `id`
2. `cohort`
3. `role` (`primary` or `historical_reference_bootstrap`)
4. `packet_hex` — complete actual CS88 packet bytes
5. `canonical_tiles_hex` — 8,100 actual 64-byte tiles in plane/tile order
6. `hud_words_le_hex` — 21,120 actual semantic HUD RGB565 words in little-endian order
7. `canonical_raster_sha256`
8. `hud_semantic_sha256`
9. `computed_root_hex`
10. `computed_seal_hex`

Rows `c0_f0`, `c0_f1`, `c0_f3`, and `c3_f50` preserve the V91k primary frame
identities. `c0_f2` bridges the c0 publication chain. The c3 bootstrap starts at
the actual key frame `c3_f48`, then accepts `c3_f49` before the primary `c3_f50`.
Bootstrap rows are history/validation inputs; they do not claim V91k BR88,
transform, or RGB output coverage for those frames.

CS88 packets are the retained V90 `proxy_LOW` native selections. Where the V90
runner kept only its primary packets, the c0-f2/c3-f48/c3-f49 packets were
recreated from the retained V90 selection masks and V88 packet producer; their
SHA-256 values match the corresponding rows in the complete V90 accepted
history. The packet and actual HUD history words are also retained separately
under `vectors/packets/` and `vectors/hud-history/` for bounded TSV consumption.

Canonical pixels come from the digest-verified V82 native archive. The HUD
word files are semantic outputs from the accepted V69 native decoder over the
full source history. For every fixture, the Python model checks the semantic
HUD SHA against the V82 frame record and V90 accepted history, then checks that
the current CS88 HUD component is byte-identical to the corresponding accepted
V69 source packet. `vectors/source-export/` retains the packet regeneration
and HUD history export source used to prepare the binary inputs.

## Hash computation

The independent Python model uses only `hashlib`, `struct`, and actual packet
and archive bytes for its expected values. It rasterizes the retained tiles to
Y, Cb, Cr byte planes for the canonical SHA-256. The content root is the C2
SHA-256 tree from the frozen V88 receiver: 508 16-tile leaves, four indexed
empty leaves, then nine binary node levels in a 512-leaf tree. The pinned
context hash is
`286386153d5fd535a7aabf60493040f99831315d6e107d7242bc39872b18d6b0`.

For each history row, the model derives the root from canonical tiles and the
seal from the packet's fid, refid, key flag, generation, actual semantic HUD
word SHA, previous accepted root, and computed content root. It compares both
results with the commitment bytes in the actual CS88 header and with the
accepted V90 native history. A delta row cannot be computed until its actual
predecessor root is present in that cohort's replay chain.

## Negative vectors and limits

[`negative/index.json`](../../experiments/python-gamebub-v91l/vectors/negative/index.json)
indexes actual packet mutations for HUD payload CRC, HUD epoch, packet fid,
refid, generation, expected root, and expected seal. It also includes changed
canonical-tile and semantic-HUD word files. The Python generator confirms that
the modified canonical bytes change the computed root, modified semantic HUD
words change the computed seal, the altered root/seal fields differ from the
computed values, and byte flips break the relevant packet checks. These cases
must reject before publication.

The model does not model the RTL transaction controller, physical SRAM/SDRAM,
display scanout, continuous 30-Hz service, or sub-10-ms completion. V91l
promotion still requires the integrated runner and independent audit to show
late-error rollback, retry, accepted-reference integrity, publication fencing,
and held-scanout behavior.

## Reproduce the oracle artifacts

From the repository root, run:

```sh
python3 experiments/python-gamebub-v91l/model.py
```

The run writes `model-results.json`, the compressed ten-column fixture, and
the directed negative-vector index. It reports the source and fixture SHA-256
pins and checks its hashes directly against retained input bytes.
