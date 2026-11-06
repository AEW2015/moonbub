# V36 exact source bundle

The 551 selected source files match the sealed producer byte for byte. Selected
build, parser, frame and provenance metadata are included. ELF/BIN/UF2, compiled
objects, full local logs and vendor tools are intentionally omitted. Absolute
producer paths and omitted-artifact references in the original build manifest
do not establish those files are present in this checkout. Rebuilding creates
a new image requiring its own hash, packaging and verification.

Explicit USB G selects CU71 (43553731, ABI 00010000, caps 7); Y selects DY71
(44593731, ABI 00010000, caps f). Wrong identities reject before writes.
The historical USB_CU71_LOCAL log prefix is shared; requested_profile and
completed_profile distinguish the selected profile. There is no CU66 network
capability or new port. The installed hardware remains separate.

Target build and packaging, eighteen native-endpoint/model tests and actual
v36/native-to-DY71 CSR KEY/P correctness co-simulation passed offline. That
co-simulation used the earlier PIPE/grouped profile; later SYNCsafe/math and
split-bus integration are separate qualifications. No physical W/G/Y, target
heap/stack high-water, local display, final BIT pairing or 30 fps claim follows.
The new ELF prologue frames are individual measurements, not a full call-stack
proof. See docs/cu66-v71 for current board timing and morning test gates.

Prerequisites: recorded esp193, ESP-IDF 5.4.3, Windows Xtensa C++ tools and
locked Rust dependencies. Original helpers contain producer-specific paths;
inspect them before reuse. Preserve the selected firmware variant.
