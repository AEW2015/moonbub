# Exact v35 source bundle

This directory contains the exact 551 selected source files of the sealed local
v35 release, plus selected review metadata and original build/check helpers.
It preserves the ordinary firmware tree elsewhere in the repository.

The original build manifest is preserved byte for byte. Its absolute producer
paths refer to the original Windows workspace, and it references additional
local logs, earlier attempts and images intentionally omitted from this source
bundle. The manifest does not imply those artifacts are present here. The
selected sealed UF2/ELF/BIN remain in that workspace; a rebuild is a new image
and must be checked and hashed again. No physical installation is established.

Build prerequisites include the recorded esp193 toolchain, ESP-IDF 5.4.3,
Windows Xtensa C++ tools and the locked Rust dependencies. Original helpers
contain historical local target/output paths; inspect them before reuse.
Do not flash a default firmware build in place of this explicitly selected
variant. See the branch CU71 development status and local control ABI.
