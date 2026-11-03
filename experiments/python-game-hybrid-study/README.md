# Bounded selective HR01/HP01 integration over temporal GM01

This new Python experiment integrates the frozen row-run patch candidate with bounded display-only selection. It emits existing **HG01** when at least one patch fits and the original **GM01 byte string** when none fits. It never alters GM01 YUV predictor planes. It does not modify any old study, installed Sunshine, ESP32 firmware, FPGA RTL, or negotiated GF02 profile.

## API and validation contract

`hybrid_codec.py` exports:

```python
config = Config(frame_cap=49152, rectangles=COMPACT,
                patch_policy="adaptive_row",  # alternatively "hp01"
                max_attempts=4, work_budget_ms=None)
decision = select_frame(base_bytes, same_capture_rgb, config,
                        spent_before_ms=measured_base_preparation)
receiver = Decoder(epoch=1, frame_cap=49152)
display_rgb, info = receiver.receive(decision.packet)
identity = base_identity(decision.packet, epoch=1)
raw_base, identity = extract_base(decision.packet, epoch=1)
```

`Decision` reports actual packet bytes/format, admission reason, identity, every attempted rectangle/candidate cost, selected exact area, rejected work, preflight and assembly costs. Up to four immutable, declared, disjoint rectangles are tried in priority order. HP01 encodes one frozen patch. Adaptive mode actually encodes HP01 and all applicable HR01 RAW/direct-row/palette-row candidates, chooses minimum complete bytes, validates the winner, and reuses those bytes during wrapping. All losing candidates and cap-rejected rectangle attempts remain in the service timer. In adaptive metadata, frozen `candidate_details.candidate_count` counts only the two or three HR01 modes; the separately encoded HP01 adds one, for three or four total actual candidates per attempted rectangle. There is no future-frame or quality oracle in selection.

Admission includes the complete 22-byte HG01 header/CRC, complete GM01 bytes, and each four-byte prefix plus full patch header/palette/payload/CRC. An over-cap GM01 base explicitly rejects. A later small priority may fit after an earlier large priority fails. “Adaptive” can send **more complete bytes** when its smaller patch encoding permits additional exact regions; compare bytes at the same selected area, or report both coverage and bytes.

The sender's cheap base preflight validates GM01 header/session fields, geometry, exact length, map syntax and whole CRC. It **does not entropy-decode coefficients**. `base_identity`/`extract_base` additionally validate HG01 envelope integrity, bounded patch slices, geometry and nonoverlap, but do not certify patch payloads or coefficient syntax. These helpers are for identity routing, not permission to publish a decoded frame or ACK success. Call `Decoder.receive` for full validation.

The receiver enforces its negotiated cap before parsing. It validates every patch and overlap before calling one atomic frozen GM01 decoder. The GM01 decoder validates coefficients and reference state and reconstructs before committing. Valid patches overwrite only display RGB565 words. Malformed patch/base, stale session/reference or oversized packet cannot commit the GM01 state. GM01 fallback and HG01 share that same state. Sender callers must bind base bytes and RGB to the same capture; packet syntax cannot prove their semantic correspondence.

Optional observed-work budgeting checks before/after patch attempts and after assembly. Late fallback does not refund any prior preparation, candidate or assembly work. This cooperative check is not a hard processing deadline. Unit tests inject late work and verify paid fallback.

## Evaluation

The fixed priorities match the earlier studies:

- Broad: `(16,48,192,80)` and `(160,352,400,80)`, total 47,360 pixels.
- Compact: `(22,54,160,24)`, `(22,82,160,24)`, `(168,360,320,24)`, `(168,390,240,24)`, total 21,120 pixels, or 44.59% of broad.

These real-image rectangles are configured priorities, not recognized or verified HUD locations. Same-frame exactness is measured against original RGB565 words. MSE compares original/displayed RGB565 expanded to RGB channels on common active/broad/background regions, so selected lossless RGB565 areas have zero error under that metric; source RGB888 quantization remains outside this exactness claim.

The campaign has two 60-native-frame temporal sequences starting at one second, 16 fixed held-out frames starting at four seconds, two separately labeled seeded noisy UI fixtures, and two deliberately flat 1-bit-glyph fixtures. Each source prepares one actual GM01 base shared across broad/compact × HP01/adaptive profiles. Temporal sequences use the frozen bounded GM01 base controller, keys at sequence 0/30, and ACK only after all matching-policy receivers decode; no loss, reordering, queue simulation or pacing is implied. The source clips are native 25/29.88 fps and related/precompressed; this does not prove 120 distinct native-30-fps game frames.

Preparation charges actual map/controller/base work once and adds it to each profile's measured complete selection, including all rejected attempts and fast preflight. Receive includes patch validation, one base entropy decode, base hash, overlay and conversion. Source decode/scale, quality/oracle checks, transport and display are excluded. Fixed-order uncontrolled host wall time is not target throughput. Packet + 59 bytes per 1,024-byte chunk and 52 reverse bytes are accounting only.

Seven unit tests cover candidate-byte reuse, complete caps, byte-identical fallback, fast preflight without entropy parsing, cheap extraction, late paid work, invalid body/patch/session/geometry, mixed key/P streams, stale/foreign encoder ownership, and exact display/predictor separation. Every executed source is pinned in `results.json`.

Run from the repository root using `/home/lori/gamebub-streaming-prototype/.venv/bin/python`:

```sh
python -m unittest discover -s experiments/python-game-hybrid-study -v
python experiments/python-game-hybrid-study/benchmark.py
python experiments/python-game-hybrid-study/verify.py
```

HG01 still requires an explicitly matching peer/transport profile. Target row-decoder resource/bandwidth verification and complete finite-service deadline/drop tests remain necessary before a hardware or 30-fps claim.

## Recorded results

The run produced **560 actual selector decisions**: **552 capped admitted packets** and eight explicit noisy-base rejections. All selected RGB565 words are exact; every unselected pixel matches its same GM01 base. All 120 temporal frames per policy decoded against the same immutable YUV references, including the key transition at sequence 30. No temporal controller base was rejected.

| 120 native temporal inputs | Mean complete bytes | Mean exact area / common broad | Mean preparation | Mean receive | Mean full service |
| --- | ---: | ---: | ---: | ---: | ---: |
| Same GM01 base control | 10,414 | 0 | — | — | 49.73 ms |
| Broad HP01 | 23,530 | 15,360 / 32.43% | 24.21 ms | 26.70 ms | 50.90 ms |
| Broad adaptive HP01/HR01 | 29,695 | 46,827 / 98.87% | 36.25 ms | 28.98 ms | 65.23 ms |
| Compact HP01 | 24,289 | 21,120 / 44.59% | 23.94 ms | 27.15 ms | 51.09 ms |
| Compact adaptive HP01/HR01 | 15,924 | 21,120 / 44.59% | 30.26 ms | 27.71 ms | 57.97 ms |

Compact adaptive saves **34.44% complete packet bytes** at identical selected area and identical displayed quality relative to compact HP01. All 120 compact adaptive frames select all four requested rectangles; maximum complete packet is 33,962 bytes. Broad adaptive admits both rectangles in **118/120** frames, versus only the first in every HP01 frame. Its higher total mean packet size buys more exact area; common broad RGB565 MSE drops from 9.679 to 0.179. Two broad second-patch attempts still fail their actual full-frame cap and remain paid.

The 16 independent held-out inputs give compact **40,048 → 31,216 mean bytes**, a **22.05% reduction** at the same exact area, with adaptive maximum 34,403 bytes. Broad adaptive provides all broad pixels on 8/16 inputs and a mean 66.22% broad exact coverage; it does not promise full-ROI losslessness on every frame. Held-out compact full service increases from 62.62 to 69.84 ms because all HR candidate work is paid.

The deliberately noisy synthetic bases exceed the cap before patch work and reject under all four policies. Flat best-case fixtures fit: compact HP01/adaptive means 14,759/14,426 bytes and broad means 18,929/16,936 bytes. Keep these artificial fixtures separate from real game evidence.

All 552 admitted packets in this dataset are HG01. Byte-identical raw GM01 fallback, late-budget fallback, mixed GM01/HG01 P decoding, and key ownership are exercised in unit tests; this main campaign does not provide native-game fallback-frequency evidence. `verify.log` confirms 140 sources, 560 decisions, exact selected/unselected behavior, caps, same-source bindings and 16 executed-source hashes.

The cheapest measured full-service means still exceed 33.3 ms. **This is not a 30-fps proof.** The useful result is a smaller explicit decoder contract and a measured coverage/byte/candidate-cost tradeoff. The next integration must carry HG01 through an explicitly matching transport, preserve decoded-state ACK ownership, account for the complete finite pipeline, and validate native row decode and physical memory service before hardware deployment.
