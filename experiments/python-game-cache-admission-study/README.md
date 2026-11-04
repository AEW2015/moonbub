# Exact-source cache through admission and commit

This closes the v12 memoization integration gap at the Python controller boundary.
`cache_admission.Controller(config=None)` has the frozen rate controller's public
configuration, encoder, prepare result and attempt fields. It emits the same full
GM01 packet bytes under paired input/reference histories. Normal and fallback
maps are evaluated in the same order, with the same complete 49,152-byte cap.

One immutable PC RGB source and at most two map-specific P payloads are retained.
Reuse requires exact source/map equality, epoch, geometry, motion mode and the
same immutable ACKed key object/ID. Source changes replace the one-entry source
cache. Keys conservatively invalidate it. Cached payloads retain no raw transform
or quantized coefficient arrays, and do not allocate FPGA/ESP32 memory.

A hit creates a separately typed, weak-set registered preview capability containing
the current frame header/CRC. The preview consumes no credit. `Encoder.commit()`
checks owner, generation, epoch, frame monotonicity, ACKed key identity and credit
availability before adding the ordinary pending P row. The controller calls commit
only after the complete current packet fits its cap. Fresh candidates still use
the frozen GM01 analyze/encode-candidate/commit path. This is not a shortened
packet, a new skip syntax or a more recent reference image.

Fully encoded rejected P candidates may populate the exact cache. They cannot
advance last-issued state, generation, the reference or pending credits. A repeat
can therefore reject again without repeating transform/entropy work; it still
pays lookup, packet header/CRC generation and admission. If a later cap permits
the exact candidate, it is admitted through the same commit checks. Keys cannot
use this P cache. A normal cached candidate that fails its cap does not suppress
the fallback attempt or consume the fallback's credit.

Eight tests cover complete byte equality; zero transform/entropy on hits; cached
normal/fallback admission and repeated paid rejection; no codec state mutation on
rejection; stale/foreign/forged preview rejection; two credits and key drain;
source/map/mode/epoch invalidation; P expiry versus key recovery; and random
repeated histories. The cached capability does not masquerade as a full GM01
transform `Prepared` object, so callers cannot accidentally re-quantize absent
cached transform arrays.

`benchmark.py` pairs the normal and cache controllers in alternating execution
order. It records whole preparation costs including map building, exact lookups,
source/payload copies, all losing attempts, header/CRC and commit. Independent
decode/hash verification and source acquisition/BOX scaling are outside those
stage clocks. Every accepted packet is decoded independently and compared against
both pending expectations; all paired complete bytes match. Rejected decisions
retain their paid service costs and before/after codec-state snapshots.

The campaign has 172 paired 720×480 source IDs: two 60-frame native windows,
16 held-out all-key inputs, and 36 labeled synthetic repeat/alternating/noise
controls. Native active game content is 720×405. The native samples are related,
precompressed 25/29.88 fps footage with repeated images, not native 30 distinct
fps acquisition. Host load is uncontrolled. Gain on repeated sources does not
predict gain on distinct-frame gameplay; miss costs remain paid.

## Retained paired results

| Case | Source IDs / hit decisions | Mean full prepare, normal → cache |
| --- | ---: | ---: |
| Combat temporal | 60 / 26 | 20.30 → 11.54 ms |
| Second temporal | 60 / 0 | 20.51 → 20.65 ms |
| Combat held-out keys | 8 / 0 | 27.60 → 27.94 ms |
| Second held-out keys | 8 / 0 | 26.29 → 26.66 ms |
| Synthetic flat repeat | 12 / 10 | 19.68 → 4.24 ms |
| Synthetic alternating | 12 / 0 | 18.93 → 19.28 ms |
| Synthetic repeated noise/reject | 12 / 7 | 84.20 → 30.77 ms |

The native combat mean improves 43.1%; its repeated-image cohort is not a
distinct-frame gameplay guarantee. The second native window instead has a 0.67%
miss overhead. All 172 pairs preserve complete bytes; 163 are admitted and
independently decoded, while nine repeated-noise decisions explicitly reject
before commit. There are 49 cache-hit candidate attempts across 43 hit decisions;
some rejected noise decisions try both cached normal and fallback payloads.
Every rejected decision keeps codec state unchanged and its actual work paid.

Maximum reported persistent cache storage is 1,051,342 bytes on the native second
sample and 1,424,200 bytes on the noisy synthetic control. `cache_bytes()` measures
the current source/map/header/payload collection, not process peak memory. During
source replacement, local references can briefly overlap the old and new cache;
object overhead, pending packets and temporary computation arrays are extra.

The parent execution study integrates this controller into staged finite GF02/
GA01 replay with the exact v12 fast receiver. That is separate evidence: these
immediate-ACK preparation pairs alone do not demonstrate finite pipeline FPS.
No installed sender mode, firmware, RTL, physical SDRAM service or hardware
30 fps is established. Cache bytes exclude Python object/weak-set overhead,
existing pending full packets and temporary transform/decoder workspaces.

Run using the study virtual environment from this directory:

```sh
python -m unittest -v test_cache_admission.py
python verify.py                    # retained result/source check, no timing work
python benchmark.py > run.log 2>&1   # regenerate paired costs; external media required
```

`results.json` pins executed source and media hashes. Attempt rows expose
`cache_hit`, `cache_lookup_ms`, `cache_copy_ms` and `cache_bytes_after`; these are
also available to the finite replay. `last_cache` summarizes the last call.
