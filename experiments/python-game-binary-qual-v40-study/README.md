# V40 causal AB38/CS38 qualification

This extends the frozen AB38/CS38 coefficient syntax to all accepted frames in
the v40 control qualification, reusing the actual CS37 packets. For each of the
three coefficient planes, it encodes and archives both full-grid and compact
AB38 alternatives, then compares each dispatch payload against the old CS37
plane payload. The old payload wins ties. The selected three payloads are
wrapped into a complete CS38 packet with the same actual HUD, IDs, maps, and
reference/output tags.

The sequence resets per source clip. Input key frames follow fid%24; each P
frame uses the last accepted CS37 normalized reference and exact HUD state from
the input qualification. Both the independent CS38 frame adapter/receiver and
an old CS37 receiver replay the sequence, and their reconstructed base planes,
HUD words, source display quality and hashes must match exactly.

`results.json` contains all 457 selected CS38 packets and 2,742 archived AB38
alternatives, with old/new byte counts, exact winner, per-alternative candidate
encode time, source hashes, IDs/PTS/reference IDs, tags, quality and code/input
pins. Candidate clocks include only each `AB38.encode` call; CS37 input encoding
is externally paid, and decode assertions, frame wrapping, reception, source
loading, quality and archive I/O are outside those clocks. No FPS conclusion is
made.

The code tests no new algorithm or parameter setting. It extends a frozen codec
on previously qualified source windows; it does not establish held-out content,
native/FPGA implementation, ESP32 transport performance, or a standards
comparison. The input clips and their 457-frame qualification are source-pinned.
The independent verifier imports no AB38 encoder and checks all alternatives,
actual winner/tie decisions, causal CS38 and CS37 receiver state, exact HUD,
source display hashes, MSE and byte/cap accounting.

```sh
python benchmark.py > benchmark.log 2>&1
python verify.py > verify.log 2>&1
```

## Results

All 457 accepted CS37 frames transcode to smaller complete CS38 frames, with
unchanged exact references, HUD pixels and displayed quality. Across the cohort,
complete bytes fall from 8,864,829 to 7,954,123, a saving of 910,706 bytes
(10.2732%). All 1,371 selected plane payloads use arithmetic; no old-plane
fallbacks or complete-byte ties occurred. The 2,742 full/compact alternatives
were both encoded and retained for every frame/plane.

| Clip | Frames | CS37 bytes | CS38 bytes | Saved | Full / compact selected | Max CS38 | Min cap headroom | Active MSE | Six candidate encodes/frame |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| mass-effect-10000 | 119 | 2,279,340 | 2,062,089 | 9.5313% | 42 / 315 | 27,063 B | 22,089 B | 17.432476 | 107.077 ms |
| mass-effect-4500 | 119 | 2,679,319 | 2,424,218 | 9.5211% | 42 / 315 | 38,504 B | 10,648 B | 25.944797 | 132.323 ms |
| mass-effect-1600 | 119 | 584,524 | 465,031 | 20.4428% | 18 / 339 | 16,249 B | 32,903 B | 11.367453 | 33.305 ms |
| mass-effect-combat | 100 | 3,321,646 | 3,002,785 | 9.5995% | 43 / 257 | 44,032 B | 5,120 B | 29.351515 | 189.917 ms |

The rate reduction is measured only against the actual accepted CS37 control
packets for these same source frames, with the same exact HU25/HX33 sidecars.
This is a transcoder qualification: CS37 input encoding was externally paid.
The six alternative AB38 encode calls per frame are timed; arithmetic decoding,
CS38 wrapping, source access, independent causal replay and display scoring are
not included. These are not integrated sender clocks or frame-rate claims. The
results do not qualify future/held-out content, native endpoints, FPGA cycles,
ESP32 transport, HEVC/AV1 superiority or a complete capture-to-display service.
