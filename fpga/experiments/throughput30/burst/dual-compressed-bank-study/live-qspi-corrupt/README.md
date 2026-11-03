# Post-guest QSPI corruption: explicit CRC rejection control

This separate negative test extends the `../live-qspi-banks` scenario without
changing its sources or evidence. The same emulated ESP32-S3 guest and actual
Rust receiver produce the 84-event clean-0 / guest-rejected-frame-1 / frame-2
sequence. After the guest has accepted frame 2, the Verilator testbench flips
one bit at byte offset 1,234 while shifting its payload onto the modeled QSPI
pins. It keeps the guest's original header CRC and separately computes the CRC
of the unmodified guest events, so this specifically tests corruption after
guest validation. Exactly one byte must be modified.

The test requires the dual-bank controller to reject frame 2's commit with CRC
reason 3. It checks that the accepted-frame count stays one, the rejected-frame
count includes both the prior guest abort and this CRC reject, no new decoder
pixels or framebuffer writes occur, frame 0 remains the front with every
framebuffer pixel intact, and another complete LCD canvas scan passes after
the rejection. Frame 0 was also compared pixel-for-pixel to the related C model.
The bench sends explicit negative status 5 for the final commit. The separate
negative adapter requires that NACK, records all 84 event hashes, and withholds
the guest's success ACK; it terminates the waiting guest after recording the
expected result. Therefore this is **not** a guest end-to-end success or a
recovery-after-the-NACK test. The successful clean/corrupt/recovery evidence
remains in `../live-qspi-banks`.

Reproduce by running `build.sh` with an empty `BUILD_DIR`, then this directory's
`run-multi.py` with seven arguments: new work directory, esp-emu executable,
guest ELF, guest flash image, packet trace, newly built `obj/Vtb_live_multiframe`,
and fixture directory. Source hashes for the RTL are checked by the build; the
wrapper pins guest, flash, trace and fixtures and independently audits event
hashes. Recorded scratch artifacts are `/home/lori/gamebub-tools/live-corrupt-build-v2/`
and `/home/lori/gamebub-tools/live-corrupt-run-v2/`; small logs and host-script
hashes are under `results/`. See `../live-qspi-banks/README.md` for dependencies
and port-reuse notes.

The test-only adapter, synthetic stop-and-wait bridge and digital QSPI/CDC,
SDRAM and LCD models do not establish target firmware behavior, physical bus
error rates, electrical margins, real RF performance, or 30 fps.
