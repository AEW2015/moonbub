# Qualified 120-frame DYN1 v3 fixture

This package contains 120 distinct CU66 frames from the first 19.8532 seconds of the retained local portrait rendering-breakdown clip. Source targets are sampled at 6 frames/second; this describes source selection only and makes no sender or display FPS claim. The source is not Mass Effect or live capture. Geometry uses the same 608x342 crop at (0,369), Pillow bilinear resize to 720x405, viewport at (0,37), RGB444 channel mapping, and uniform q32 codec map as the qualified 40-frame parent fixture.

Sequence is KEY frame 0 followed by 119 dependent P frames, each referencing its immediate predecessor. The unchanged CU66 packet cap is 49,152 bytes and HUD cap is 20,000 bytes. The pinned native-v69 oracle passed canonical YUV, HUD-word and composed RGB565 hash checks on all 120 packets. The V59 bounded native endpoint processed 2,534,400 HUD words at a 98,304-byte arena cap (peak 88,962), with zero allocation failures, 240 malformed/late-failure checks, and 120 recovery checks.

This is software/native-host qualification only: no handheld hardware or network transmission was used. See `manifest.json` for per-frame source/oracle hashes and `qualification/` for execution receipts and source bindings. Existing loader: `dy71-sequence-v3`; call with explicit count 120.
