# RM01: actual-rate GM01/BM01 choice from one ACKed key

The primary goal remains **720×480 at 30 fps**. This experiment does not reduce resolution or frame rate. It implements actual complete-byte choice between GM01 zero motion and BM01 bounded block motion, with an optional GM01 global candidate. It does not assert that Python or hardware achieves the goal.

## One canonical owner, pure previews, selected commit

`rate_motion.py` imports frozen v11 arithmetic/format helpers; it never constructs GM01/BM01 shadow encoders. One new `Encoder` owns one immutable reconstructed **ACKed** YUV key, up to two P credits and monotonically issued selected frame identities.

```python
encoder = Encoder(epoch=1, window=2, modes=("gm_zero", "bm_block"))
preview = encoder.preview(rgb, frame_id, scale_map=declared_map)
candidate = select(preview, frame_cap=49152)
if candidate is not None:
    packet = encoder.commit(preview, candidate)
# Convenience: decision = encoder.prepare(rgb, frame_id, scale_map=declared_map)
receiver = Decoder(epoch=1, frame_cap=49152)
rgb, info = receiver.receive(packet)
encoder.ack(info["frame_id"], epoch=info["epoch"], frame_crc=info["body_tag"])
```

Preview computation cannot install a reference, consume a credit, or advance `last_issued`. It builds every actual candidate against the same source/map/canonical reconstructed key. Selection uses complete packet lengths only; declared mode order breaks ties. It sees no quality oracle or future frame. Only a registered, fresh preview/candidate pair from the owning encoder can commit. All-cap rejection leaves reference, issued identity and credits unchanged. Pure-preview registries are ownership metadata, not transmitted state.

The selected key remains pending and blocks P preparation until its matching ACK. Wrong epoch/frame/body tag, an inner-only CRC, expired keys and late ACKs cannot install a losing reference. A new key requires all P credits to drain. ACK/expiry of P packets releases a credit without replacing the immutable key. Expiring a pending key requires independent-key recovery. Logical `read_pins` count outstanding P credits; this is **not physical reference-read drain, DMA or CDC ownership**.

GM01 zero/global and BM01 keys have the same source, constant-128 prediction, quantization and reconstructed pixels. The implementation therefore shares one actual key transform, entropy pass and reconstruction, charges those stages once, then builds each complete candidate header/CRC. It does not pretend to perform or pay multiple reconstructions that it never executes. `shared_key_reconstruction_count` is exactly one for keys. For P frames, each attempted predictor's SAD/search, prediction, transforms, quantization and entropy actually run and are all charged even when that candidate loses.

Source conversion and map encoding are also shared once per preview. BM01 uses the frozen ±4 even-vector full-block SAD search by default. `gm_global` is an explicit optional mode; the paired campaign uses zero/block because the prior real-source global control chose zero throughout. Global search is unit-tested and never assumed to be a free candidate. Key/P arithmetic retains frozen Q14/ROI/CP02 behavior and exact whole-P zero-residual semantics.

## New complete RM01 contract

RM01 is an experimental mixed peer envelope, **not an installed GF02/GA01 adapter or standard HEVC/AV1 format**. Its 26-byte little-endian header declares magic/version, inner codec kind, epoch/frame/reference IDs, canvas and exact inner length. A four-byte whole-envelope CRC follows. All reported packet sizes charge this 30-byte overhead, plus complete inner GM01/BM01 headers, maps, vectors, coefficient payloads and nested CRCs.

The receiver owns one independent canonical YUV key and dispatches complete inner parsing according to the declared codec. It binds outer identity/canvas/reference to the inner header and parsed syntax; checks caps, CRCs, vectors/maps/coefficients, reference and replay constraints; reconstructs independently; and only then publishes key/last-frame state. It never reads encoder pending arrays. `identity(packet)` is cheap header/CRC preflight for identity routing, not a coefficient-decode certificate.

The key-output tests compare every candidate to frozen GM01 pixels. Mixed GM01/BM01 P candidates are also checked against separate frozen receivers initialized with the same accepted key. Forged/stale previews, wrong ownership, two-credit drain, malformed inner/outer bodies, bad session/tag, key loss and full-cap rejection have explicit negative tests. Source/coeff/prediction arrays, preview candidates and temporary packets are Python allocations beyond the two logical credits; no target BRAM/DSP/SDRAM fit is established.

## Paired campaign and service boundaries

All new real and synthetic inputs are **720×480**. The campaign uses two 60-native-frame windows starting at one second with keys at frame IDs 0/30, plus eight predeclared causal indices `(0,2,4,6,8,10,12,14)` starting at four seconds from each clip with a key at 0. The held-out indices form sparse causal sequences; they are not 16 independent key frames. Source clips remain native 25/29.88fps, related/precompressed, and may repeat content. Scheduling or byte-rate multiplication cannot turn them into native 30-distinct-frame game capture.

Three profiles see the same source IDs/maps/keys: GM01-zero only, BM01-block only, and actual-rate zero/block. They each have their own independently measured encoder/receiver as comparison controls. Within actual-rate there is only one key owner. For every source ID, the benchmark asserts that the canonical reference hash matches across controls and selector, and that each actual-rate candidate packet hashes **identically** to its corresponding single-mode control. This catches hidden mismatched key histories, not just matching nominal frame IDs.

Full-size synthetic static, opposite-moving block texture and noise/cut cases remain separately labeled. Noise cap failures are charged and must not advance credits/references. All candidate sizes, including rejected ones, remain retained; only admitted packets decode. Quality on admitted outputs uses the same active/ROI/background RGB888-versus-RGB565 metrics as the previous block study. Equal quantizer maps do not guarantee equal distortion under different predictors. Minimum bytes is not rate-distortion optimization.

Preparation includes actual map construction, source conversion, every losing search/transform/entropy pass, envelope and metadata hashes, selected commit and key reconstruction. The measured outer preparation timer includes the map; internal stage timings make shared work explicit. Receive includes full parsing/prediction/inverse/color conversion. Source file decode/BOX scaling, expected-P oracle, quality/comparison checks, transport and presentation are excluded. Host load is uncontrolled and profile order fixed. Immediate in-process outer-tag ACK follows decode/hash verification; there is no paced finite transport, benchmark packet loss or native concurrency here.

Forward `packet + 59 × ceil(packet/1024)` and reverse 52 bytes are accounting only. The 30fps field is a byte-rate multiplier, not an executed frame schedule. No lower-resolution or lower-fps cases are substituted for the primary goal.

## Reproduce

Use the prototype virtual environment and run from the repository root:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest discover -s experiments/python-game-rate-motion-study -v
/home/lori/gamebub-streaming-prototype/.venv/bin/python experiments/python-game-rate-motion-study/benchmark.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python experiments/python-game-rate-motion-study/verify.py
```

The benchmark pins every executed source before/after timing. `results.json`, `benchmark.log`, `tests.log` and `verify.log` retain packet/control hashes, actual attempts, ownership/reference checks, quality and full paid host costs. All older iteration11 sources remain unchanged.

## Recorded results

The run produced **462 decisions and 616 actual candidate packets over 154 source IDs**: 453 packets admitted under the complete 49,152-byte cap, and nine paid cap rejections. All canvases are 720×480. Every actual-rate candidate hashes identically to its independent control with the same canonical key. Nine tests and the 13-source-pin persisted verifier pass.

|60-frame real window|GM01-zero /BM01 /actual-rate mean complete bytes|Actual-rate choices GM /BM|GM01-zero →actual-rate preparation|Active PSNR GM01-zero →actual-rate|
|---|---:|---:|---:|---:|
|Combat|8,832 /9,167 /8,832|60 /0|22.34 →70.16 ms|34.020 →34.020 dB|
|Second clip|12,056 /11,802 /11,741|22 /38|19.47 →63.69 ms|35.203 →35.132 dB|

Actual-rate avoids BM01's combat byte regression, but still pays every losing search/transform. Combat full service rises from 44.39 to 92.43 ms with **no byte saving**. The second clip saves 2.61% versus GM01-zero and 0.51% versus BM01-only, with a small distortion change; full service rises from 43.36 to 91.10 ms. It is not free rate-distortion optimization and is not a Python 30fps candidate.

Held-out combat again chooses GM01-zero on all eight causal IDs, without byte gain. Held-out second chooses BM01 once: 12,530.5 →12,522.25 mean bytes, only 0.066% lower, with a 0.009 dB active-PSNR decrease. This discourages assuming the main-window BM01 gain generalizes to every gameplay segment. All 120 main real and 16 held-out IDs fit each control and selector; their maximum selected packet is 31,522 bytes.

The separately labeled full 720×480 opposite-motion fixture favors block prediction: GM01-zero 19,808.5 →actual-rate 6,547.25 mean bytes (−66.95%), with active PSNR 25.371 →26.034 dB. It uses contrived block-aligned texture and opposing integer motion, so it is not representative gameplay evidence. Static128 selects BM01 zero-residual P syntax on three frames and GM01 for the key, reducing mean 3,547 →1,328.5 bytes; source/search/transform work still runs.

Full720×480 noise/cut input supplies the important negative admission case. Three high-entropy frames exceed the cap under both predictors and reject without advancing reference or issued state; later valid frames continue from the old ACKed key. Across the three profiles these are nine rejections. Actual-rate alone spends **466.30 ms on its three rejected preparations**. Its accepted-frame mean packet is 2,677.7 bytes, but that number describes only the three admitted flat/cut frames and must not characterize the rejected noise. The all-six-source actual-rate preparation mean is 101.04 ms. Rejected costs are retained separately rather than erased by accepted-frame full-service averages.

Actual packet bytes include the same 30-byte RM01 overhead for both controls and the selector. Comparisons are therefore within one explicit mixed format; unwrapped installed GM01 would not carry those 30 bytes. These are independent paired encoder/decoder calls with immediate in-process feedback, not a finite-link or hardware test.

The next useful step is a bounded **causal low-cost search gate** or rate-aware vector objective, evaluated against the unconditional GM01 baseline with every gate/search/candidate cost included. Preserve a safe GM01 option, hold reconstruction/quality and actual complete side bytes together, and do not claim a skipped search was evaluated. Integrating RM01 into a finite transport and physical read-drain contract remains separate work. The primary target stays 720×480 at 30fps; this experiment reports a negative compute tradeoff instead of substituting lower resolution.
