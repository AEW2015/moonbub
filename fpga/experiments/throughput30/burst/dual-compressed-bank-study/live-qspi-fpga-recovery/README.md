# FPGA-model recovery after post-guest CRC rejection

This isolated continuation of `../live-qspi-corrupt` tests the FPGA/display
model after it rejects a frame with a CRC mismatch and sends negative status 5.
Frame 0 arrives from the actual emulated guest and is presented. Frame 1 is
aborted after guest-detected corruption. Frame 2 is accepted by the guest but
has one bit flipped on the simulated QSPI link, so the two-bank controller
rejects it. Frame 0 stays intact through the rejection and a complete LCD scan.

The existing experimental guest accepts only a `K` success acknowledgment:
it has no NACK handling or next-frame recovery policy. Therefore the separate
negative adapter verifies the NACK, withholds success and terminates the guest.
Only then, the **testbench's synthetic sender**, not the guest or production
firmware, sends distinct fixture 0003 over the same QSPI endpoint, using credit
checks and ordered fences. The controller accepts and presents that 27,300-byte
frame. All 345,600 frame-3 RGB565 pixels match the related C model and modeled
framebuffer, and its complete LCD canvas scan matches. The frame-0 buffer stays
intact until and after frame-3 presentation; model underruns and FIFO overflow
remain zero. Frame 0 also matches its own C model. The first 84 guest event
hashes are audited; 83 receive success ACKs, and the final commit gets NACK 5.
This proves a bounded **FPGA-model-only** recovery sequence, not guest, network
or end-to-end recovery.

Run `build.sh` with an empty `BUILD_DIR`, then this directory's `run-multi.py`
with the seven documented arguments from `../live-qspi-corrupt/README.md`.
The wrapper pins the existing guest and fixture hashes plus fixture 0003; the
build verifies `sources.sha256`. Recorded artifacts are
`/home/lori/gamebub-tools/fpga-recovery-build-v1/` and
`/home/lori/gamebub-tools/fpga-recovery-run-v1/`; short evidence and host-script
hashes are in `results/`. Existing live and corruption evidence is unchanged.

The test uses a synthetic stop-and-wait bridge, test-only register adapter,
and digital QSPI/CDC, SDRAM and LCD models. It does not establish actual guest
NACK behavior, hardware timing, RF operation, physical signal integrity or
30 fps.
