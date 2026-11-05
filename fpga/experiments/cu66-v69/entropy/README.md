# CU66 v69 AB38 coefficient RTL

This is an original synthesizable SystemVerilog AB38 payload decoder with a self-checking Verilator testbench. It is a **component**, not a CU66 frame receiver or FPGA streaming demonstration. It implements actual adaptive arithmetic decoding and coefficient syntax; no Python implementation runs inside the DUT.

The supported outer coefficient dispatches are **5 (full grid)** and **6 (visible compact, width 1)**. All other dispatches reject explicitly. Both compressed AB38 flag 0 and signed raw fallback flag 1 are supported. The initial implementation has **one shared arithmetic engine**, four persistent stream interval states and four separate 88-entry probability banks. Parallel engines are future work.

## Interface and integration contract

`cu66_ab38_decoder.sv` has one clock and synchronous active-high reset. Configuration is accepted on `cfg_valid && cfg_ready`:

- `cfg_dispatch[2:0]`, `cfg_packet_bytes[15:0]`, encoded `cfg_blocks[16:0]` and encoded `cfg_blocks_w[8:0]`.
- The supplied byte bank starts at the AB38 magic and **does not include dispatch byte 5/6**. It includes AB38's trailing CRC32. Default bounds are 49,152 compressed bytes and 8,100 encoded blocks. Width is 1..256, divides the block count; dispatch 6 requires width 1. These are component bounds, not a physical memory-fit result. Parameter values must remain within the 16-bit address and 17-bit block interfaces.
- External byte reads use `rd_req_valid/ready/addr` and `rd_rsp_valid/ready/data`, with at most one accepted outstanding request. A responder holds valid/data until accepted. Responses are ordered. The compressed bank remains immutable through the transaction: the decoder first scans CRC/header, then rereads compressed stream bytes through one cache per stream.
- A tile transfers on `tile_valid && tile_ready`. `tile_coefficients[16*i +:16]` is signed row-major coefficient `i` of one 8×8 tile; `tile_index` is its **encoded** index and `tile_last` marks the last encoded tile. Valid, index, last and all coefficients stay stable during output stalls. Root integration must supply implicit hidden-zero tiles/scatter compact tiles into full-grid positions.
- `done` pulses only after all entropy/termination checks and acceptance of the final tile. `error/error_code` are sticky until the next configuration/reset. Already emitted tiles are **provisional**: a late error can occur after earlier tiles, so the parent must not publish a reconstruction/reference bank based on partial output.
- `abort_i` cancels output and prevents new configuration. An already accepted read is drained before `cfg_ready` returns. `busy` can drop before that drain completes; keep the byte-bank/read lease until `cfg_ready`. A held abort and an abort coincident with response acceptance are supported. Local reset assumes the external read responder is also reset/flushed; it is not a transaction-tag implementation.

`debug_state`, `decoded_decisions`, `renormalizations`, `memory_reads` and `output_stall_cycles` are actual RTL counters/observations. They are not throughput estimates. Configuration while busy is ignored according to valid/ready; the active parameters remain latched.

## Implemented checks

The RTL validates immutable payload length bounds, dispatch/configuration, AB38 CRC32, magic/version/flags, requested geometry, reserved fields, exact component lengths, Rice parameter bounds, declared arithmetic bit lengths and low padding bits, exact two-zero termination, DC predictor bounds, run/count limits and signed coefficient domain −2048..2048. DC prediction resets at each encoded row. AC uses three pending events, not three whole coefficient arrays. Tile values are reordered from normative zigzag to raster order.

Error codes are hexadecimal: `01` config/dispatch; `02` CRC; `03` header identity; `04` lengths; `05` raw syntax; `06` external address; `07..0b` stream parameters/bit lengths/padding; `10` AC run; `11` AC level; `12` DC range; `13` event cursor; `14` incomplete final events; `15` raw coefficient range; `20` bit exhaustion; `21..22` arithmetic interval/context; `23` exact ending length; `24` nonzero ending bit; `ff` invalid FSM state. The error is a rejected component transaction, not resynchronization or recovery by scanning for markers.

The caller still owns CU66/GS66 envelopes, actual plane/safe-mask geometry, quantization, inverse transform, motion prediction, canonical normalization/SHA, HUD, reference identity, atomic publication and display-bank ownership. CRC and SHA are unkeyed integrity checks, not authentication. This decoder changes none of the existing JPEG firmware/RTL or frozen Python studies.

## Actual simulation evidence

`export_fixtures.py` reads frozen AB38 grammar and independent decoder plus the native-v69 manifest. It exports no new gameplay captures. The actual corpus contains 1,371 full/compact AB38 plane payloads from 457 stored frames. Expected encoded-order i16 coefficients remain in the native fixture bundle; they are not duplicated as full uncompressed frames here.

The self-checking C++ harness compares **every accepted signed coefficient**, exact tile order/count/last, read-request stability and output stability. It randomizes request ready at 80%, output ready at 75%, and byte-response delay uniformly over 0..7 cycles. Every run has a per-case 20-million-cycle watchdog and must finish with `TEST_PASS`; compile/simulator exit alone is insufficient.

Regression includes two full-corpus seeds (6901/6902), three directed seeds and three stress seeds. The 31 directed cases cover zero/DC-only, row resets, ±2048, explicit Rice escapes, sparse/dense/raw data, compact geometry, every unsupported dispatch, geometry/config limits, CRC, reserved/parameter/padding errors, exact termination and raw range. A malformed termination fixture emits seven provisional tiles before rejection, exercising the parent's late-failure requirement. The 120 stress cases combine seeded coefficient data with CRC-resealed payload mutations; each mutation is classified by the independent frozen decoder, so valid changed payloads are compared rather than incorrectly assumed invalid.

Additional functional checks interrupt a pending read, abort exactly on response acceptance, hold abort through the drain, offer configuration while busy, hold a tile under backpressure then abort, and reset during activity. Every interruption is followed by a successful valid retry. These checks do not prove a parent reconstruction-bank publication fence.

`audit_results.py` checks every actual plane's decision and renormalization counts against its frozen selected AB38 work record. External reads also match the exact two-pass count: compressed `2*packet_bytes−42`, raw `2*packet_bytes−46`. It validates expected coefficient blob hashes, all transcript totals and current source hashes. `results.json` retains actual frame/plane cycles, seeds and source pins. Cycle totals include the CRC pass, metadata, entropy, stalls and byte-service model. They exclude parent reconstruction/SHA/HUD/scanout and are **not** a routed clock, Fmax, target-fit or physical 30 fps result.

## Tools and reproduction

The recorded backend is Verilator 5.020 with g++ 13.3 in `gamebub-cu66-v69-build`. Host fixture export requires the existing NumPy Python environment; the C++ testbench links zlib. The repository is mounted at the same path inside the container and `/build` is an external build directory. Run:

```sh
TASK_PYTHON=/home/lori/gamebub-streaming-prototype/.venv/bin/python \
  fpga/experiments/cu66-v69/entropy/run_regression.sh
```

For retained-evidence verification only:

```sh
python fpga/experiments/cu66-v69/entropy/audit_results.py
```

Current Verilator `--Wall` compilation is clean without disabling RTL warnings. `lint-first.log` preserves the initial width/reserved-name warnings; explicit width/port fixes resolved them. A review also fixed abort/drain handling at simultaneous response acceptance before final directed coverage. No checks were weakened to pass.

Yosys 0.33 accepts read/process lowering and reports **0 check problems**. Its three retained warnings convert short metadata arrays to registers. `yosys-proc.log` is unmapped elaboration evidence, not a technology synthesis/BRAM/DSP report. Variable configuration arithmetic, memory mapping, cycle-critical combinational paths, resource sharing, RAM ports, CDC and target routing still need measurement and optimization.
