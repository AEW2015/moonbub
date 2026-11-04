# Game Bub v20 hardware-development kit

Start hardware/software development from the paired
`handoff/gamebub-app-codec-v20-20261103` branches. The target is 720×480 coded,
720×405 active game content and 30 scheduled source IDs/s. This kit supplies
executable arithmetic references, binary fixtures, wire offsets and acceptance
criteria. It supplies no replacement FPGA bitstream or installed AR03 receiver.

## Run the acceptance checks

From the Moonbub repository root:

```sh
python3 hardware/gamebub-v20/verify.py
python3 experiments/verify_prototype_v20.py
```

Use the project Python environment, or install Python 3.10+, NumPy, Pillow and
PyAV. The complete repository aggregate also replays the two new Python studies.
The retained-vector checker does not need the original video downloads.
The C reference requires a C11 compiler (tested with Linux GCC 13.3) and undefined-behavior sanitizer.
On Linux, install the distribution's build toolchain and sanitizer runtime.
When no host compiler is found, the runner uses an **already running**
`gamebub-esp32-dev` container; override its name with
`GB_V20_COMPILER_CONTAINER`. It copies two source files into a fresh container
`/tmp` directory, compiles, copies the library back, and removes that directory.
It does not install packages, pull an image or change the container's project.
The compiled library runs on the Linux host and must match its architecture and libc ABI.
Container builds statically link UBSan so the host needs no matching runtime.

To export a bounded slice for a Verilator/RTL testbench:

```sh
python3 hardware/gamebub-v20/export_mem.py \
  --dataset signed-edges --start 0 --count 6 --outdir /tmp/gamebub-v20-vectors
```

A small signed-edge smoke set is also retained under `vectors/rtl-smoke/`.
Run all datasets for acceptance; this smoke set is not complete coverage.
Each `.mem` file has one signed two's-complement 32-bit hexadecimal word per
line, 64 row-major words per block. `slice.json` binds the exact golden index and
slice. Feed complete blocks through the DUT, apply randomized ready/valid stalls,
and compare every output word. A successful vector replay does not prove timing.

## What is executable

| Item | Implementation and evidence | Hardware work still required |
| --- | --- | --- |
| Q14 inverse | Portable C11 scalar kernel, ZERO/DC bypass and sparse GENERAL products; complete golden replay with UBSan | RTL scheduling, DSP decomposition, valid/ready, reset, synthesis, timing |
| Mandatory HUD | Python bounded map search, complete cap and all requested exact RGB565 patches; 20 isolated packet/YUV/display/AF03 vectors | Native host encoder, paid search budget, packet negotiation |
| Compact banks and inline tags | Python reconstruction-fed uint8 stripe tagger; actual generated tile vectors and canonical reference checks | Compact bank controller, streaming SHA, ordering/backpressure, atomic publication |
| GF03/PC18/QC18/FG19/AF03 | Exact byte offsets, generated C constants, actual control sequences and epoch-1 packet example | ESP/FPGA endpoints, true FIFO credits, capability negotiation and reset/recovery |
| Full streaming system | Component proofs and explicit service/bandwidth assumptions | Joint calibrated host/ESP/FPGA/memory/scanout implementation and board tests |

`src/gb_inverse.c` and `include/gb_inverse.h` are the arithmetic oracle, not an
ESP32 decoder or an HLS component. Input is a row-major **dequantized** signed
int32 block; output is the signed residual before prediction/clipping. Both Q14
rounding boundaries use floor((sum+8192)/16384), including negative sums. The
kernel validates its ±522,240 input contract before touching output, has no heap,
and uses fixed arrays. Preserve intermediate width; compact YUV8 applies only
**after** prediction addition and clipping to 0–255.

`golden-index.json` retains real AR03 blocks plus exhaustive DC, seeded legal
random and signed-edge cases. Arrays are little-endian int32 compressed with
zlib; descriptors carry raw/stored hashes, shape and byte count. They retain
large legal residuals without int16 truncation. The basis and conservative legal
bounds come from the frozen codec: 20-bit dequantized input, 22-bit intermediate,
and 38-bit biased accumulator bound. A 40-bit accumulator is a planning choice;
actual DSP decomposition and Fmax must be established by implementation.

`wire-contract.json` gives endianness and byte offsets. Generated
`include/gb_wire.h` exposes constants; **decode bytes explicitly**, rather than
casting packed C structs. AR03 has a 61-byte fixed header, a variable inner/UI
body and a final four-byte CRC; the CRC is not immediately after the header.
AR03's 65 fixed envelope bytes are not a 65-byte contiguous header. GF03 is a
31-byte fragment header; the packet-token prefix adds 16 bytes. A 1,008-byte
payload therefore makes a 1,055-byte UDP datagram. PC18 is 29 bytes, QC18 28,
FG19 36 and AF03 43, before 28-byte IPv4/UDP overhead.

## Ownership contract

Keep three permissions separate:

1. FG19 GRANT reserves an exact receiver frame slot before AR03 commit.
2. PC18 returns packet-buffer capacity. FINISHED confirms that the FINISH drain
   barrier arrived; RELEASE follows receiver ingress/read/decode drain.
3. AF03 confirms a fully validated decoded reference bank and canonical tag.

At most two receiver frame owners, five data tokens and one control occupy the
six-entry mailbox contract. Wrong epoch/frame/nonce/slot/body identity or reply
kind must not change another owner's state. Loss with unknown ownership stops
with bounded retained state; elapsed time never invents a credit. The laboratory
model fixes epoch 1. Production reset/rekey, reconnect, capability negotiation and
unknown-outcome recovery remain explicit work packages. CRC detects corruption;
it does not authenticate a peer. Preserve the working negotiated JPEG baseline
while implementing and testing a separate AR03 capability.

## Handoff data and entry points

- [Implementation tasks and copyable agent prompts](TASKS.md).
- [Hardware acceptance gates](ACCEPTANCE.md).
- [Mandatory HUD vectors](../../experiments/python-game-mandatory-hud-study/SCHEMA.md):
  every fixture includes its source and reference-bank preconditions; do not
  replay a P packet against an arbitrary bank.
- [Generated reconstruction-tile vectors](../../experiments/python-game-inline-reconstruction-study/SCHEMA.md):
  use canonical plane/raster ordering, last-tile finalization and expected tags.
- [v20 results and development plan](../../docs/custom-codec-prototype-v20-2026-11-03.md).

Hardware-independent tests can begin immediately. Release qualification remains
open: FPGA resource/Fmax and scanline timing, mapped external-memory arbitration,
ESP32 CPU/heap/DMA and Wi-Fi service have not been calibrated by these Python/C
proofs. The complex mandatory-HUD source projects to 11.376 Mb/s of forward data
at 30 fps, before control/reverse/radio overhead; the old assumed 8 Mb/s link is
insufficient for that case. No sustained physical 30 fps claim is made.
