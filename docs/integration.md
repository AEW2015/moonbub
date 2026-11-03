# Moonshine prototype integration

The requested implementation is recorded in `requested-prototype.txt`. The original
Linux paths in that brief do not exist in this Windows workspace. Sources are
being derived from the separately inspected `C:/Users/lavat/codex/gamebub`
workspace; that workspace has local changes and is preserved in place.

## Architecture decisions

The first transport is a standalone test sender, UDP MSV1 compressed-frame
chunks, the existing Rust/ESP-IDF application and Slint UI, the existing quad SPI
framing, core-owned registers, FPGA JPEG decode, and external SDRAM. It is not a
Sunshine-compatible video protocol. No codec identifier is borrowed from H.264.
Audio capture and transmission are absent in the standalone sender.

The physical Rev4 source configuration is 480x800 portrait scanout viewed as
800x480 landscape with the established rotation and offset. It is not a native
720x480 panel. The requested transmitted canvas is 720x480, containing 720x405
16:9 content and 37/38 black rows, centered in the panel's landscape extent.
The existing dock resolution remains a separate interface.

The framework routes the top address nibble E to the active core. Addresses in
the 01/02/03/04/05/8 windows remain framework owned. MSV1 protocol and register
definitions are documented alongside the components and checked for agreement.

## Evidence boundaries

Only the coordinator owns hardware access. This build request is being verified
offline first. Existing persistent firmware and current FPGA configuration are
preserved. A generated bitstream, successful simulator exit, or estimated link
budget does not establish LCD appearance, Wi-Fi/QSPI throughput or sustained FPS.

Build, behavioral simulation, post-route timing, physical display, and sustained
gameplay are separate gates. The final evidence manifest records each gate and
the actual source/artifact hashes. A required gate with no executed evidence
remains incomplete.

For physical testing, first identify the actual board revision, current image,
matching recovery files and their hashes, then use the established programming
helper. Do not use another development session's FPGA or serial connection.
