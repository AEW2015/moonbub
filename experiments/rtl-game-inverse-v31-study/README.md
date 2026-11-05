# V31 custom-codec inverse-transform RTL accelerator

This is an isolated Artix-7-oriented kernel, not a complete streaming decoder
or a replacement Gamebub bitstream. Existing JPEG RTL and firmware are unchanged.
The ESP32 compact-header work is documented separately in
[`docs/esp32-compact-transport-plan.md`](../../docs/esp32-compact-transport-plan.md)
and remains proposed rather than implemented/flashed.

## Arithmetic and interface contract

`inverse_q14.sv` accepts one raster-ordered 8×8 block as 64 ready/valid pairs:

- Signed 20-bit **dequantized** coefficients, legal magnitude ≤522,240.
- Unsigned 8-bit prediction samples, 0–255, in matching output-pixel order.

The eight shared signed MAC lanes calculate the frozen custom codec's inverse:

```text
mid = (coefficients × Q14 + 8192) arithmetic-shift-right 14
residual = (Q14ᵀ × mid + 8192) arithmetic-shift-right 14
pixel = clip(residual + prediction, 0, 255)
```

Rounding occurs after **each** pass, with half ties toward positive infinity.
Signed 24-bit intermediates, 38-bit products and 48-bit sums cover the declared
domain. The maximum Q14 column absolute sum is 43,284; conservative intermediate
and final bounds are 1,379,678 and 3,644,896, both within signed 24 bits.
The directed vectors attain the final bound. No silent coefficient saturation,
alternative approximate transform, or changed GM27 coefficient syntax is used.

An output block contains 64 raster-ordered ready/valid residual/pixel samples,
index and last flag. It remains stable while stalled. One block is outstanding;
the next load waits until the final output handshake. Synchronous reset discards
partial load, computation or stalled output. Arrays are filled before use;
they do not require a bulk memory reset. The upstream parser must validate the
coefficient domain and provide exact reconstructed-reference predictions.

With `BYPASS=1`, zero residual blocks bypass both passes. DC-only blocks execute
the exact two scalar products through the shared pipeline. `BYPASS=0` is the
dense arithmetic control. The shortcuts change cycles, not output pixels.

## Measured behavioral simulation cycles

Full-input/full-output-ready service counts include loading 64 samples and
emitting 64 outputs:

| Block | Dense control | Shortcut enabled |
| --- | ---: | ---: |
| Zero | 260 cycles | 128 cycles |
| DC only | 260 cycles | 132 cycles |
| General | 260 cycles | 260 cycles |

There are 33,054 block vectors: 654 directed/seeded stress blocks and
all 8,100 YUV420 blocks from each of four real 720×480 v30 strict component
frames. The real frames use IDs 0 and 12 in both retained Mass Effect windows;
Python decodes preceding accepted packets to establish the actual references.

Three full Verilator runs check dense control, shortcuts, and shortcuts with
deterministic input gaps/output backpressure. Each compares 2,115,456 residual
and pixel outputs with Python. All runs exercise reset during partial load,
partial computation and stalled output. The four-state RTL and mapped-netlist
Icarus runs each cover the 654 directed/seeded blocks with the same scoreboard.
Mapped functional testing is a subset, not all 33,054 blocks or timing simulation.

| Real frame | Dense cycles | Shortcut cycles | Projected shortcut ms if 100 MHz closes |
| --- | ---: | ---: | ---: |
| 2600 / key 0 | 2,106,000 | 1,455,796 | 14.55796 |
| 2600 / P 12 | 2,106,000 | 1,205,700 | 12.05700 |
| 7200 / key 0 | 2,106,000 | 1,643,988 | 16.43988 |
| 7200 / P 12 | 2,106,000 | 1,369,896 | 13.69896 |

The dense projection is 21.06 ms at that same assumed clock. Synthetic stalls
raise shortcut projections to 15.47–19.88 ms. These are observed cycle counts
scaled by an **assumed** clock. The stimulus can offer one dequantized sample
and prediction per cycle; real entropy, DMA and memory service are not modeled.
There is no placed/routed clock result or full-pipeline 30 fps claim.

## Generic Series-7 synthesis mapping

Yosys `synth_xilinx -family xc7` maps the default shortcut-enabled kernel to:

- 8 DSP48E1 primitives.
- 1,978 FDRE primitives.
- 1,535 LUT2–LUT6 logic cells, plus MUXF/carry and distributed memory cells.
- 32 RAM32M and 10 RAM64M distributed-memory primitives; zero RAMB18/36 cells.

The logic LUT count excludes distributed RAM and is not a complete physical
LUT utilization count. This is isolated generic mapping, not Vivado utilization,
placement/routing, timing closure, or fit alongside the existing JPEG design.
The signed 24×14 lane arithmetic is chosen to fit Series-7 DSP multiplication;
see [AMD UG479](https://docs.amd.com/api/khub/documents/gu4oRPFEh_Pm2uaAlfY6Kg/content).
The mapped cells use `MREG=1`, `PREG=0`, multiply-only OPMODE and zero C/PCIN.
The DSP multipliers are used; accumulation and rounding remain in fabric.
This is not a fully absorbed DSP48 accumulator implementation. Moving the
feedback accumulation into the P stage is a specific next architecture test.

## Reproduction

Build dependencies in a dedicated Docker image, separate from the ESP32 tools:

```sh
docker build -t gamebub-codec-sim:v31 \
  -f experiments/rtl-game-inverse-v31-study/Dockerfile \
  experiments/rtl-game-inverse-v31-study
python experiments/rtl-game-inverse-v31-study/run_sim.py --work /tmp/my-v31-run
```

The runner uses two CPUs and a 4 GiB container memory cap. It validates and
expands retained compressed text vectors, requires clean Verilator lint, builds
and runs the three full behavioral cases, runs four-state directed RTL, maps
the actual kernel to Series-7 cells and tests that mapped netlist functionally.
It requires explicit `TEST_PASS` and `RESET_ABORT_PASS` markers and bounded
timeouts. Do not infer PASS from successful compilation or an empty log.

The retained image provides Verilator 5.020, Icarus 12.0 and Yosys 0.33; exact
version output and image identity are retained. Rebuilding the unpinned Ubuntu
package image later can install newer tools: rerun validation rather than
assuming identical binaries. The runner uses the calling Linux account's UID/GID
for build-directory ownership.

Offline arithmetic/log/source checking without rebuilding tools:

```sh
python experiments/verify_prototype_v31.py
```

Python/NumPy and the inherited frozen source closure are required. Original
video downloads and physical hardware are not needed for retained replay.

## Simulator diagnosis

The initial Icarus12 checker falsely flagged known handshake bits when
`$isunknown` received an inline concatenation. The standalone source/log in
`diagnostics/unknown_repro.*` reproduces inline=1 versus named=0 with known bits,
and explicitly checks that the named-vector expression detects X and Z.
The testbench uses named vectors with the **same** complete handshake/payload
checks. No DUT behavior or acceptance criterion was relaxed. An upstream search
found general SVA discussion but no verified issue matching this exact failure;
the local reproducer is the evidence, not an asserted vendor workaround.

The mapped default design has no remaining `BYPASS` parameter. `MAPPED` removes
that elaboration override from the testbench; it still uses the same interface
and scoreboard. An earlier parameter-not-found elaboration failure is not a
functional DUT failure. Only the later explicit passing run qualifies mapping.
The first mapped runtime exceeded its 240-second wall limit after block 529;
it was inconclusive. The final runner allows 600 seconds for the unchanged
654-block mapped test. Its cycle watchdog and functional checks stay active.

Vivado/XSim and Vitis HLS were not available through the configured local tool
paths; initial bridge discovery did not complete. This experiment explicitly
uses Verilator/Icarus/Yosys. It does not claim an XSim or HLS run. The AMD RTL
simulation skill supplied the bounded-test and evidence methodology.

## Next acceleration work

1. Add a validated EC26 block-major coefficient reader and bounded dequantizer.
   Feed this kernel through a small block FIFO; preserve malformed-packet and
   frame-abort checks before bank publication.
2. Add the exact v28 fractional predictor with measured reference-memory service.
   Model SDRAM arbitration, reconstructed-bank hazards and DMA backpressure.
3. Compare DSP P-register accumulation, ping-pong block buffers and sparse MAC scheduling against these
   goldens. Charge zero discovery, transfers and output costs explicitly.
4. Compare an HLS implementation against the same integer vectors and interface
   after the HLS toolchain is available. Measure synthesis/implementation;
   pragma intent alone does not prove DSP mapping or throughput.
5. Integrate color conversion, exact HUD composition and publication fences,
   then place/route and exercise real hardware. Keep the JPEG profile available.

This kernel does not implement EC26 parsing, dequantization, reference fetch,
bilinear prediction, color conversion, HUD composition, network/QSPI ingress,
SDRAM scheduling, CDC, frame tags/CRC, atomic bank commit or LCD scanout.
