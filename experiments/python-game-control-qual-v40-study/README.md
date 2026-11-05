# V40 causal CS37 qualification

This study reuses the frozen fast zero-map analyzer from v37 and the integrated
CS37 sender from v38 on every archived frame in all four v40 PTS windows. For
each source frame it builds real lossless HU25 → HX32 → HX33 packets from that
frame's RGB565 pixels and the last **accepted** HUD state. It tries ROI scale 8
with background scale 16; background scale 32 is tried only if the first
complete-packet encode raises an error (including the frozen 49,152-byte cap).

One independent frozen CS37 receiver per clip validates each candidate on a
rollback-safe receiver copy. Only a packet that fits, decodes, matches all
21,120 source HUD words and passes tag/quality checks advances either base or
HUD reference state. A rejected frame remains accounted for and does not
advance state; a later frame can refer to the last accepted frame ID. The data
therefore preserves causal rejection behavior rather than assuming every
source frame was accepted.

`results.json` records all 457 inputs, PTS/time bases, media/canvas/RGB565/YUV
hashes, requested reference IDs, every attempted background, errors, archived
actual HUD/base packets, complete/HUD/base byte budgets, cap decisions, timing
scopes, quality, reference tags and source-code pins. If the frozen encoder
raises before returning an over-cap packet, the exception is recorded and no
nonexistent packet bytes are claimed. Accepted packet objects are
content-addressed in `objects/`; source canvases remain in the frozen v40
folder.

Timing is separated into source read, source conversion, HU25/HX32/HX33
construction, fast analysis and each integrated encode attempt. Receiver and
quality checks are outside sender/analysis timing. The analysis is done once per
source frame and reused across a possible second quantizer attempt. These Python
measurements do not establish native endpoint timing, transport constraints,
physical 30 fps, full-hardware fit, or HEVC/AV1 superiority.

Run with the project study Python environment:

```sh
python prepare.py > prepare.log 2>&1
python verify.py > verify.log 2>&1
```

The offline verifier checks source pins and hashes, all input IDs, key/reference
rules across acceptance and rejection, packet/cap accounting, independent
receiver output, exact HUD pixels and reported quality.

## Qualification result

All **457/457** archived frames were accepted and independently decoded: 119
frames each from `mass-effect-10000`, `mass-effect-4500`, and
`mass-effect-1600`, plus 100 from `mass-effect-combat`. There were 20 accepted
key frames (five per clip), zero rejected frames and zero background-32 retries.
Every accepted frame used ROI8/background16. Thus this run did not measure the
background-32 fallback path. Total accepted complete bytes were 8,864,829.

| Clip | Frames | Accepted | Max complete packet | Mean active MSE |
|---|---:|---:|---:|---:|
| mass-effect-10000 | 119 | 119 | 30,341 B | 17.432476 |
| mass-effect-4500 | 119 | 119 | 41,913 B | 25.944797 |
| mass-effect-1600 | 119 | 119 | 19,010 B | 11.367453 |
| mass-effect-combat | 100 | 100 | 48,540 B | 29.351515 |

The combat maximum has only 612 bytes of headroom under the complete 49,152 B
cap. That tightest example is why acceptance of four independent keys alone
would not establish full-window fit. Here the actual causal run did fit every
archived frame; this still says nothing about future frames outside these clips.

Cumulative source-read / source-conversion / HUD-generation / fast-analysis /
integrated-encode-attempt wall times in seconds were, respectively: 0.279 /
0.864 / 29.418 / 0.753 / 7.136 for 10000; 0.337 / 0.865 / 31.847 / 0.731 /
7.638 for 4500; 0.285 / 0.863 / 13.063 / 0.735 / 5.428 for 1600; and 0.230 /
0.724 / 25.713 / 0.610 / 7.389 for combat. HUD generation includes construction
of actual HU25, HX32 and HX33 packets, including all measured codec trials. The
analysis is performed once per frame and reused by a possible quantizer retry.
These separated host measurements are not a physical throughput result.
