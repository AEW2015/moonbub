# V24 independent audit checklist

Scope: independently audit the native HEVC/AV1 comparison against pinned v23
source frames and actual serialized codec packets. This is a host software
reference study, not a Game Bub standards decoder or hardware qualification.

## Source and native stream evidence

- [x] Pin campaign source code, v23 results, original input RGB hashes, and the
  exact 96 RGB565 source canvases and common YUV420 tags.
- [x] Verify each retained HC22 sidecar is the exact sidecar from its matching
  v23 CP23 packet and restores the source HUD words.
- [x] Reopen every bounded packet/extradata object, independently decode the
  complete native stream, and verify PTS/DTS, key IDs, emission timing, and
  output association for all 48 IDs per case.
- [x] Recompute bare and exact-HUD hybrid active RGB565 channel SSE, HUD word
  errors, per-frame bytes, complete packet cap fit, and projected wire math.
- [x] Recompute case summaries and sampled at-least-quality operating points;
  distinguish selected points from interpolation or BD-rate claims.

## Claim boundary

- [x] Keep HEVC and AV1 numerical quality parameters codec-specific and avoid
  claiming equal CRF settings or equivalent subjective quality.
- [x] State that the native-plus-HUD hybrid uses actual native decoding and
  actual HC22 bytes, while its CP23 binding/ACK/transport bytes are modeled.
- [x] Do not claim standards interoperability, bounded target decoder cost,
  RF behavior, or physical/sustained 30-fps performance.

## Freeze evidence

- [x] After root requests final freeze, run `python audit.py --check`, retain
  the audit test log (at least six tests), `audit.json`, and independent audit
  verifier output in this study directory.
