# V91k provisional canonical YUV420 to RGB565

`canonical_rgb565_v91k` reads an actual provisional 720×480 canonical frame
through a ready/valid byte-addressed memory interface. Memory layout is raster
Y (345,600 bytes), Cb (86,400 bytes), Cr (86,400 bytes). It emits 345,600 held
RGB565 words in raster order. No HUD, integrity validation or publication occurs.

Chroma interpolation follows the frozen native renderer exactly: horizontal
rounded averages on odd x, then vertical rounded averages on odd y, with edge
replication. Subtract 128 from interpolated chroma. RGB uses signed floor shifts
of the fixed 359/88/183/454 coefficients, clamps to [0,255], then truncates to
5/6/5 bits. The Python golden is independently derived from retained canonical
frames, not the converter outputs.

This first integration deliberately issues **nine separate byte reads per
pixel**, including duplicated edge/even-coordinate samples: Y, four Cb and four
Cr samples. It charges 3,110,400 accepted and acknowledged reads per frame.
There is one physical read owner, with no zero-time gathered pixel service.
A matching response releases that owner. An unexpected epoch fails the active
conversion but cannot release the real pending request; its matching response
must still drain. A bus-error response with matching identity ends its request
and fails the conversion. Request fields and output words remain stable under
legal backpressure.

`reset` is a local warm reset. It drops provisional computation/output but
retains a physical pending read. `cancel` does the same. Both block replacement
until the matching response drains. The pending register has configuration INIT
zero, explicitly separating FPGA power-on empty state from local warm reset.
A zero start epoch rejects before any read. The accepted memory lease must
remain immutable until completion or drain; the bench checks its bytes.

The runner first saves the **actual canonical bytes accepted from the BR88
reconstruction RTL**. This converter's separate RTL simulation replays that
candidate memory through the byte bus and compares every accepted RGB word to
independent goldens. This is a component join through exact memory replay;
it is not one monolithic simultaneous memory-controller/scanout implementation.
Canonical and conversion cycles are reported separately and as a sequential
replay-service sum. No physical clock or board bandwidth is inferred.

The finite FAST bus acknowledges a byte two edges after acceptance; SLOW
acknowledges after two through six edges with seeded request/output stalls.
The eight directed checks exercise pending-read abort/reset and blocked
replacement, held-word abort/reset, epoch/bus faults, invalid start identity
and clean retries. Earlier successful output on a failed conversion remains
provisional. `done` means every RGB word was accepted, not validated publication.

The uncached nine-read schedule is a correctness baseline and a measured cost
for the subsequent line-buffer/tile-cache optimization. Physical RAM, DSP/LUT
mapping, routing and frame-rate qualification remain open.
