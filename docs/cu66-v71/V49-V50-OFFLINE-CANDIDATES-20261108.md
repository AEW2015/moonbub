# Separate ESP32 performance candidates after V48

V48/V027 passed the local twelve-frame test and remains the physical reference. Two separate firmware candidates now pass offline and target-build gates; neither is installed. The handheld is in software DFU with a separate unbound vendor node, pending a one-time signed in-box driver binding. No flash write has occurred through the new vendor client.

## V49: canonical Huffman tables

Source: `firmware/experiments/v49-dy71-canonical-huffman-20261107`, release `release-canonical-huffman-v001`.

- ELF: `64a7243f2331b0e4b6d4731d7a814d491e9fb3b08bc4e16085d6c643ff99cda1`.
- UF2: `a6b2d30b88570353a0ff924ee4b1f6f4f239272e416ba9fc4e22d74f66c9e691`.
- Native delta against V48: only Huffman construction/lookup in `hud.hpp`. Bounded canonical arrays replace heap-backed tables and vectors; output allocation, validation and wire behavior remain unchanged.
- 1,877 differential cases, twelve golden frames/253,440 words, a 457-frame semantic corpus, malformed inputs and rollback pass. Tracked corpus allocations fall from 84,765 to 14,829; whole-decoder peak is unchanged. The broad corpus uses a 1 MiB semantic-only cap and does not establish target fit.
- Host Prepare improves about 5.3%; the lookup-heavy microbenchmark improves about 5.2 times. These are host measurements, not ESP32 or display rates.
- Actual Xtensa static frames: Huffman increases from 192 to 752 bytes; channel increases from 144 to 160 bytes. The combined increase is 576 bytes. Runtime stack headroom remains a physical gate.

104 Rust host tests, target build, static SRAM of 132,076 bytes and the production UF2 parser pass. Require cold CPU12 and network stack measurements before accepting the candidate; do not silently increase stack or relax reserves.

## V50: bounded HUD READ slicing

Source: `firmware/experiments/v50-dy71-hud-read-slice-20261108`, release `release-hud-read-slice-v001`.

- ELF: `8dc3788fe6461fbfb0559cd4accbc8879d5c978b4de3bc8e2f5b5bfa29d5fbcf`.
- UF2: `748036c95182315d58819cc68e0f51ffa83632b2fb92d5ccaec2f3970f941c68`.
- Native delta against V48: only READ in `endpoint.hpp`. Skip whole canonical patch ranges and copy requested words instead of scanning all 21,120 words for every small READ. V49's Huffman change is absent.
- 262,669 differential requests cover every word offset, patch crossings, zero/full/final ranges, malformed framing, capacity/identity/stale cases and unchanged accepted state. Complete HR70 responses, including CRCs, match. Coverage includes 261,852 valid golden reads, 636 expected C ABI errors and 181 status rejections.
- One 83-command burst reduces inner word-loop visits from 1,752,960 to 21,120, plus bounded patch checks. The host benchmark is about 12.16 times faster, with no new READ allocations. This does not predict the speedup of the enclosing physical HUD-write phase.
- Xtensa Endpoint and C-wrapper frames remain 224 and 48 bytes respectively.

104 Rust host tests, twelve native golden frames, target build, static SRAM of 132,076 bytes and the production updater parser pass.

## Hardware sequence and limits

Both preserve V027, sequence-v3, the 98,304-byte native arena, the 8,192-byte physical reserve and worker stack settings. USB descriptors retain revision 4800 because the control ABI is unchanged; use the exact SDK ELF hash and variant label for firmware identity. Each candidate has source-bound evidence in `evidence/readiness-v001/readiness.json`.

Qualify driver access, read-only updater behavior, installed partition layout and exact V48 backup first. Then test one candidate at a time using the same local fixtures and FPGA, with cold CPU12 followed by network cached12. V50 is the first transfer-phase comparison; V49 separately measures CPU/allocation effects. Combine only after individual correctness and runtime gates pass.

The [HBU audit](V48-HBU-THROUGHPUT-AUDIT-20261107.md) establishes that HBU1 already has a 512-byte window. Compressed ingress still uses per-word credit/write/count transactions and dominates transaction count. A versioned burst-ingress RTL prototype is being verified offline; it is not a selected bitstream or hardware-ready result. Software results do not justify timing exceptions or clock changes.
