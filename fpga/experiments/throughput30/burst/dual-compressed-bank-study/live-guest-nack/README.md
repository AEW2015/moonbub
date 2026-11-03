# NACK-aware guest-harness recovery experiment

This isolated candidate modifies the **test harness**, not the production
firmware worker, to recognize a test-only `N` + sequence acknowledgment from
the host adapter. It permits NACK only for frame 2's commit, records that
frame as rejected, then continues with a distinct increasing frame ID. The
`firmware/handheld/src/streaming/protocol.rs` Receiver remains unchanged (SHA-256
`32a91ffaf0b39a82f11036be7e501765cd3f9fed6905c27b6efc01f358d79e64`); it
validates guest datagrams and their CRC before forwarding. The NACK protocol and
continuation policy are candidate test harness behavior, not implemented
production behavior.

The clean live run used four pinned synthetic JPEG fixtures. Frame 0 was
presented; frame 1's final datagram was corrupted before the guest and caused a
receiver abort; frame 2 passed guest validation, but one bit at byte 1,234 was
flipped during its simulated QSPI transmission. The modeled bank controller
rejected its CRC and returned status 5. The adapter converted that into `N` for
sequence 83, and the modified emulated guest recorded the NACK, then sent frame
3 through the unchanged Receiver and the same live event/QSPI path. Frame 3 was
committed and displayed. The prior front remained intact through the reject and
recovery, and a full scan passed after rejection. Frame 0 and frame 3 each
matched all 345,600 RGB565 pixels in the related C model and functional
framebuffer, and complete LCD canvas scans passed. The auditor checked 113
guest-emitted event hashes: 112 success acknowledgments and one NACK.

The guest executable/flash are pinned by `run-multi.py`. Existing artifacts are
`/home/lori/gamebub-tools/guest-nack-study/guest.elf`, `guest-flash.bin`, and
`fixture.trace`; RTL executable is
`/home/lori/gamebub-tools/guest-nack-study/rtl-build/obj/Vtb_live_multiframe`.
The clean live output is `/home/lori/gamebub-tools/guest-nack-study/live-run-v1/`.
Short logs, comparison JSON and source hashes are under `results/`.

To independently replay from repository root (all paths are host paths):

```sh
python3 fpga/experiments/throughput30/burst/dual-compressed-bank-study/live-guest-nack/run-multi.py \
  NEW_EMPTY_WORK_DIR \
  /home/lori/gamebub-tools/esp-emu-study-0510/esp-emu-0.51.0-x86_64-unknown-linux-gnu/esp-emu \
  /home/lori/gamebub-tools/guest-nack-study/guest.elf \
  /home/lori/gamebub-tools/guest-nack-study/guest-flash.bin \
  /home/lori/gamebub-tools/guest-nack-study/fixture.trace \
  /home/lori/gamebub-tools/guest-nack-study/rtl-build/obj/Vtb_live_multiframe \
  /home/lori/gamebub-tools/network-rtl-repro-v1/fixtures
```

The host wrapper expects a nonexistent output directory, loopback TCP 15536
and UDP 15533 free, Python with Pillow, and the pre-existing C model alongside
the fixture directory. The testbench can be independently rebuilt with
`build.sh` and an empty `BUILD_DIR`, Verilator 5.x, make and a C++ compiler;
it checks `sources.sha256`. `make-trace.py FIXTURE_DIR OUTPUT_TRACE OLD_TRACE`
checks all fixture hashes and requires the new trace to extend the previous
hash-pinned three-frame trace. The guest was built from a copied handheld tree
with `src/main.rs` replaced by `guest.rs`, fixtures 0000–0003 copied to `src`,
unchanged `protocol.rs`, and `cargo +esp193 build --locked --release --features
rev4 -j 2` using an isolated ESP-IDF 5.4.3 target directory. Conversion used
`esptool.py --chip esp32s3 elf2image --flash_mode dio --flash_freq 80m
--flash_size 8MB`; the app was inserted into a copied 8 MiB test image at
0x100000 after erasing the app partition. Rebuilding the guest may change
binary hashes; the wrapper's guest pins must be updated deliberately after
review. An earlier copied CMake cache failed because its file-api directory was
missing; the clean scratch ESP-IDF rebuild passed.

This is a stop-and-wait synthetic virtual-network and QSPI model with no shared
emulator/RTL clock. It does not establish production NACK handling, real Wi-Fi,
physical QSPI/CDC/SDRAM behavior, device fit, latency or 30 fps. The related C
model shares algorithms with the RTL; it is not an independent JPEG decoder.
