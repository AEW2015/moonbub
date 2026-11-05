# CU66 v69 iterative SHA-256 RTL

`cu66_sha256_bytes.sv` is an original SHA-256 implementation and bounded byte adapter. It computes full **256-bit** digests; a CU66 caller uses the upper 128 bits (`digest[255:128]`) and performs its own expected-tag comparison. It does not validate CU66 framing, CRC, reference identity, canonical geometry/order, HUD or reconstruction-bank publication.

The algorithm and known-answer checks follow [NIST FIPS 180-4](https://csrc.nist.gov/pubs/fips/180-4/upd1/final) and [NIST SHA-256 worked examples](https://csrc.nist.gov/CSRC/media/Projects/Cryptographic-Standards-and-Guidelines/documents/examples/SHA256.pdf). No external RTL core was copied. Passing these functional vectors is not FIPS validation or an authentication/security certification.

## Interface

There is one clock and synchronous active-high `rst`. `abort_i` discards the active message/result. A transaction starts on `start_valid && start_ready`, latching the 32-bit `total_bytes` count. Byte transfers occur on `data_valid && data_ready`:

- `data[7:0]` carries bytes in message order. `data_last` must be true exactly on the declared final accepted byte. Early last, missing final last and a longer stream whose last arrives beyond the declared count reject with `error_code=01`, no result. `error` stays set until reset or another accepted start.
- `total_bytes=0` accepts no bytes and hashes the empty message directly. Pauses are allowed indefinitely; an incomplete source without a last marker cannot be distinguished from a pause. The parent owns timeout/abort policy.
- Bytes offered while ready is low are not consumed. In particular, an extra offered byte after the correct final transfer cannot alter the digest and is not another accepted transaction. The upstream frame controller must preserve byte ownership across starts.
- `result_valid` holds the entire digest stable until `result_ready` or abort/reset. `digest[255:224]` is the first standard SHA word, followed by the remaining words in standard digest order. A result is a completed hash, not authority to publish a frame before all other integrity/HUD checks pass.
- `start_ready` remains low while a message or unconsumed result is active. Start parameters offered while busy do not replace the current transaction. Held abort gates all ready/valid interfaces; reset/abort invalidate provisional work and allow a later valid retry.

The CU66 serialization caller supplies geometry bytes **D0 02 E0 01**, then normalized uint8 Y, Cb, Cr in planar row-major order. That message is 518,404 bytes. The SHA module itself is geometry/profile agnostic; it does not normalize or truncate pixel samples. Canonical input ownership and live profile negotiation remain outside it. SHA is unkeyed content binding, not traffic authentication or DDR ECC.

## One core, selectable bounded buffering

`BUFFER_BLOCKS` supports **1 or 2**:

- One bank uses 16×32-bit words (64 B) for both input packing and the rolling message schedule. Input pauses during compression.
- Two banks use 128 B of input/schedule data. Input fills one bank while the same single chained SHA core processes the other. Bank-full/order/final flags prevent overwrite or out-of-order chaining. There is no full-frame buffer and no second independent SHA context.

The core performs one compression round on every active `C_ROUND` clock, 64 per padded block, with separate prepare/add control cycles. Rotates, choices, majorities, modular additions and schedule updates are actual RTL. Input/schedule bank bytes are not total memory: hash chaining words, working words, counters, flags, constants and implementation mapping are additional. Multiple schedule reads/register updates still need target port/resource/timing evaluation.

`accepted_bytes`, `compressed_blocks`, `round_cycles`, `padding_bytes`, `input_stall_cycles` and `output_stall_cycles` are actual RTL counters. Debug fill/core state outputs support bounded simulation diagnostics.

## Functional and cycle evidence

`export_fixtures.py` provides 98 independently expected messages using Python `hashlib` outside the DUT: empty, `abc`, the 56-byte two-block vector, million `a`, lengths surrounding 55/56/63/64/65 and later block boundaries, 64 seeded random messages, four actual source40 canonical keys and two additional full-size patterns. All six full-size messages contain 518,404 bytes; only four are real retained canonical images. No new gameplay capture is represented.

Both buffer configurations pass all 98 full-256-bit digest comparisons under ideal service and three seeded randomized source/result-ready schedules (6901–6903): **784 fixture digest checks**. Each run additionally checks framing failures and eight valid retries, indefinite partial-message pause followed by abort, held abort, abort during rounds, reset, a stalled stable result, ignored busy starts and an extra unaccepted byte. Tests have per-message and global watchdogs, explicit `CONTROL_PASS` and terminal `TEST_PASS`. Compile/simulator exit is not the verdict.

For a full canonical-size message under always-valid input and always-ready result service:

| Configuration | First-result clock count | Accepted-result clock count | Padded blocks | Active round clocks | Input backpressure clocks |
| --- | ---: | ---: | ---: | ---: | ---: |
| One 64 B bank | 1,053,132 | 1,053,133 | 8,101 | 518,464 | 534,600 |
| Two 64 B banks | 534,731 | 534,732 | 8,101 | 518,464 | 16,198 |

Counts are observed RTL/testbench edges from the cycle offering/accepting start, inclusive of that start edge. First valid is reported separately from its later consumer acceptance; source and output stall counts remain in every transcript. The dual-bank gain comes from overlapping byte fill with compression, not deleting required work. A random source can become the limiting stage; randomized traces record its bubbles too.

At an **assumed** 100 MHz these first-result counts correspond to 10.53132 / 5.34731 ms. No routed 100 MHz clock has been established. The 5.18464 ms round-only arithmetic from earlier Python work excludes fill/control; this RTL explicitly measures those costs. These are component service counts, not complete decoder or physical 30 fps evidence.

## Reproduction and remaining work

The recorded backend is Verilator 5.020 / g++13.3 in `gamebub-cu66-v69-build`, linking zlib for fixtures. Host export requires NumPy and the frozen source bundle. Container paths match the host repository; `/build/hash1` and `/build/hash2` hold compiled products outside the repository.

```sh
TASK_PYTHON=/home/lori/gamebub-streaming-prototype/.venv/bin/python \
  fpga/experiments/cu66-v69/hash/run_regression.sh
python fpga/experiments/cu66-v69/hash/audit_results.py
```

The audit validates fixture hashes and expected digests, exact padding/block/round counts, all terminal markers, source pins and ideal-service cycle relations for both configurations. Logs and `results.json` preserve randomized timing and control outcomes. Current Verilator `--Wall` builds are clean; `lint-first.log` retains the initial explicit-width warnings resolved before simulation. No checker was weakened.

Yosys 0.33 read/process/check succeeds for both configurations with **0 check problems**. The retained warning lowers hash-state metadata to registers; memory totals also include the constant table and are not payload-bank sizes or mapped BRAM counts. This is unmapped elaboration evidence. FPGA synthesis, RAM/DSP/logic mapping, routed timing, reset/CDC integration, shared memory and decoder/hash/scanout overlap remain to be measured. The current JPEG firmware backend does not gain CU66 support from this module.
