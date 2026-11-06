# FPGA versions and firmware numbers

Updated November 6, 2026, about 06:00 Denver. These names identify different
layers; a source revision or successful simulation does not identify an
installed, qualified bitstream.

Use the **BIT SHA-256 plus selected-source manifest hash** to identify an exact
FPGA build. CU71/DY71 magic values identify compatible interfaces, not unique
build fingerprints. "Last verified installed" below is historical evidence,
not a fresh device query.

There are four numbering schemes: **build50** names an image build;
**v70/v71** name integration/development revisions; **board-source-v008**
names one frozen source selection inside that work; **v32/v36** name ESP32
application revisions. Suffixes such as `cache-readpipe-v001` name individual
experiments and do not identify a complete FPGA image.

| Name | Purpose | Evidence/state |
|---|---|---|
| v19/v20-era builds | Earlier JPEG overlap and LCD timing/margin development | Historical versions; use exact build/image hashes for comparisons |
| build50 | Established JPEG video plus AV/controller path | Last physically verified installed FPGA; retain for separate 25 fps test |
| CP23/CPL1 diagnostic | Earlier custom-codec hardware/control diagnostic | Locally tested; build50 restored afterward; not the CU66 decoder |
| CU66 v70 | Linked custom-codec integration source baseline | Pinned source `fcc02c58d46f96a26790ce02826a0bf937c2478b`; not an installed image |
| CU71 | Successor custom-codec path with RGB framebuffer | Earlier diagnostic path; local profile magic `43553731` |
| DY71 | Direct YUV/HUD scanout successor avoiding RGB surface traffic | Current target; incompatible local profile magic `44593731` |
| DY71 board-source-v008 | Exact latest completed full-board implementation | Model gates pass; routed setup fails; no qualified BIT |

The v008 complete implementation is `C:/mb70/dy71i03`: setup **-0.834 ns**,
hold **+0.023 ns**, pulse **+2.000 ns**, all **49,051/49,051** nets routed.
It also retains three native console directory-creation errors. Both issues
block image qualification; zero process exit status does not override them.
Selection SHA-256 is
`3e5760ca6da2d593febe00655cb0a343d6d675f02db2ea8d1e9623df0fef6ba8`.

The packet-arbiter, entropy read-address, cache read-address, SHA payload-enable
and event-counter experiments are isolated candidate improvements. They are
not released or installed FPGA versions. Each needs its own proof and the
final selected composition needs full routed signoff.

ESP32 **v32** and **v36** are application versions, independent of FPGA names.
V32 is last physically verified installed with build50. V36 is packaged but
not installed; USB `G` selects CU71 and `Y` selects DY71. Its local fixture
does not advertise a new network port or establish 30 fps streaming.

Morning order remains: existing build50 25 fps test, then the qualified new
local custom-codec fixture when a reviewed bitstream is available.
