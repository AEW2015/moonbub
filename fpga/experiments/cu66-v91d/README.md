# V91d acknowledged packed scratch RTL

`packed_scratch.sv` implements the frozen V91c packed image in a single 262144-byte external memory bank. It accepts provisional decoded coefficients, waits for explicit context ends and successful packet seal, acknowledges every write, rereads the descriptor, and reconstructs dense scalar output in raster order. It is a sequential functional prototype; throughput, physical fit, timing, IDCT and frame deadlines are unproven.

## Interface and transaction ownership

`begin_valid/ready` latches `begin_blocks[16:0]`, `begin_raw`, three full-width `begin_count*` values, `begin_epoch[31:0]`, and `begin_serial_clear`. Geometry must be 1..8192 blocks; AC counts are bounded by 5/15/43 coefficients per block. RAW counts must be zero. Admission computes every 16-byte-aligned segment and rejects allocations exceeding 262144 bytes. Epochs must increase strictly over accepted transactions, including across warm reset and abort; wrapping requires a new cold instance with an empty external bus.

`coef_valid/ready` transfers band, block, raster index, signed value and epoch. Exactly one held coefficient is copied into the single 16-byte write assembler. Values must be -2048..2048. DC must cover every block in order. RAW must cover every coefficient in raster order. Nonzero AC events must belong to their band and increase strictly in `(block, zigzag rank)` order. A stale coefficient, invalid coordinate, duplicate, zero AC event or count mismatch fails closed.

`band_end_valid/ready` ends each context, including empty AC contexts. Compressed transactions end bands 0,1,2,3 in that order; RAW ends band 0 only. The handshake includes band and epoch. Partial assembler lines are zero padded and acknowledged before accepting the next context. `seal_valid/ready` is available only after all contexts and writes complete; it represents successful packet validation. The descriptor is then written as two acknowledged bursts. No dense output is available before sealing. Inputs held while ready is low have not been accepted.

`dense_valid/ready` transfers block/index/value/epoch. `done` is sticky after the last dense coefficient; `sealed` remains high. Finish/failure requires an explicit matching abort or reset before the next begin. The input and output sides do not overlap transactions.

## Memory and cancellation

The external memory interface has at most one outstanding 128-bit request. Addresses are aligned byte addresses within the admitted image. Request payload and valid are held through backpressure. Both reads and writes require a matching-epoch response; response data is relevant only to reads. The earliest supported response is an edge after request acceptance, with arbitrarily many intervening cycles. `mem_rsp_ready` is always high. Memory errors fail closed; unsolicited or mismatched responses report error 6. A mismatched response does not retire the actual pending request.

A matching `abort_valid/abort_epoch` or synchronous `reset` cancels local ownership, assembler contents, output and caches. **An accepted external write remains real.** The RTL drains its matching response before `begin_ready` permits reuse of the bank. This also holds when reset is asserted for many cycles through the delayed ACK. An abort from a previous epoch is ignored. Abort clears previous errors. The initial values of the FSM, outstanding flag, epoch-seen flag and active epoch rely on FPGA power-on register initialization; cold construction requires an empty external bus. A system that cannot guarantee this must provide an external bus recovery procedure.

Errors: 1 geometry/count budget; 2 epoch; 3 coefficient bounds/band/order; 4 premature/wrong context end; 5 memory error; 6 unsolicited or mismatched response; 7 descriptor mismatch. Failure with an outstanding request drains the real response before bank reuse.

## Exact bytes and bounded local storage

The 32-byte descriptor is `<8I`: magic `0x43393150`, blocks, raw flag, AC1/2/3 counts, used bytes, zero. Compressed data has signed16 DC values followed by three aligned segments of 32-bit AC records: block13 | raster6 | signed13. RAW stores aligned dense signed16 values. Every final partial burst is padded with zeros. External RAM is reused without clearing the full bank.

The drain uses four 16-byte line caches, at most three 32-bit AC heads, one 64-coefficient local tile, and a 64-bit validity mask. The assembler is 16 bytes and coefficient holding slot is one record. Descriptor data and control registers are additional. There is no full-frame dense scratch array. Descriptor contents and reread coefficient ranges/order are checked.

`begin_serial_clear=1` clears all 64 local tile payloads sequentially for a baseline; mask mode clears the validity mask in one cycle and emits zero for untouched positions. DC/AC writes mark validity. Both modes use the same packed bytes, independent goldens and deterministic stall policy. This comparison measures tile clearing only; the implementation still serializes cache fetches, AC merge, and scalar output.

## Reproduce and evidence

Run from the repository root:

```sh
python3 scripts/cu66-v91d/build_vectors.py
python3 scripts/cu66-v91d/run_scratch_rtl.py
```

The existing `gamebub-cu66-v69-build` container provides Verilator and C++. Compilation uses `--assert -Wall` with fatal warnings, C++ `-Wall -Wextra -Werror`, and `-j 2`. No hardware command is used. Every invocation retains an immutable attempt directory with source snapshots, SHA256 pins, independent compressed vectors, compile log, simulation output and report. `scratch-results.json` selects the most recent attempt, including failures.

`tb_scratch.cpp` models finite request stalls and delayed ACKs. Accepted writes change the backing memory when the external model produces their ACK, including after abort/reset. Each independent vector runs ready and stalled with mask and serial-clear modes, compares the entire image byte-for-byte, compares every dense scalar, and checks exact addressed read/write burst counts. Directed tests cover profile/count/budget boundaries, malformed events, early seal, stale abort, delayed-write cancellation, reset held over ACK, stale/unsolicited responses, error ACKs, memory corruption and repeated epoch rejection. The 8192-block tail case checks maximum packed position and zero defaults under reuse.

These simulations do not establish physical memory bandwidth, placement, clock frequency, hardware behavior or a complete under-10ms / 30-fps pipeline.
