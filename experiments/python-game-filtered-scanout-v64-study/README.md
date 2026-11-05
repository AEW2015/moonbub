# Pull-driven filtered YUV scanout model (V64)

V64 applies the frozen V60 strong display filter during row delivery for 96 actual frames from later source IDs 24–47: 46,080 luma/RGB565 lines, 33,177,600 exact RGB565 words, and 2,027,520 exact HUD words. The pull model loads each source-Y row once, caches at most four vertical rows, has one pending row and at most two lookahead rows, and retains neither a full filtered Y plane nor a full RGB image. Maximum logical row-data ownership is 7,200 bytes; this excludes the static mask, HUD patches, external full YUV reference banks, Python integer temporaries, CDC/FIFOs, and metadata.

The 44.0613 ms mean scanout-plus-check time is a host model timing with assertion/hash work. Decode and oracle creation are excluded; it is not a CPU-rate advantage or end-to-end FPS result. Caller-owned YUV/HUD banks, physical ports, front-bank fences, RTL handshakes, clock, BRAM fit, and panel timing are not implemented or measured. Pull pauses validate bounded functional behavior only.

The producer and independent replay pass three and five tests respectively. Reproduce with `benchmark.py` and `verify.py`.
