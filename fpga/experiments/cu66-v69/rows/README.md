# Canonical full-grid tiles → planar bytes → SHA256 (v69)

This component serializes the fixed **720×480 YUV420 canonical hash canvas**. It is not physical LCD scanout, panel rotation or a display timing controller. The parent still owns normalization, CU66 framing, inverse/motion reconstruction, external memory, HUD validation and bank publication.

`cu66_tile_rows.sv` takes full-grid uint8 8×8 tiles and emits **D0 02 E0 01 + Y rows + Cb rows + Cr rows**, exactly 518,404 bytes. `cu66_rows_sha256.sv` is an actual SystemVerilog connection to the frozen v69 SHA core, with common transaction starts, component-error aborts and a rows-complete gate before exposing the full digest. No Python model executes in either DUT.

## Interface

There is one clock and synchronous active-high reset. `start_valid && start_ready` latches `frame_id[31:0]` and `key`. Frame ID FFFFFFFF rejects. There is no replay/epoch policy in this component; the parent owns that policy.

A tile transfers on `tile_valid && tile_ready`:

- `tile_pixels[8*i +:8]` is row-major pixel i, 0..63.
- Every accepted tile must carry the latched `tile_frame_id` and `tile_key`. Input planes are exactly Y=0, Cb=1, Cr=2. `tile_index` starts at zero in each plane and increases in full-grid tile-raster order. There are 5,400 Y tiles (90 per row), then 1,350 per chroma plane (45 per row).
- **`tile_last` is true only on plane 2 tile 1,349**, the global final tile. It is false at the Y/Cb plane ends. Wrong identity/key/plane/index, duplicate indexes and early/missing last reject immediately on acceptance. An offered tile while ready is low is not accepted.
- All 512 pixel bits are captured before returning ownership to the producer. The module then performs eight registered 64-bit row-word writes over eight clocks. Its baseline capture-plus-store interval is nine clocks per tile. Input storage is bounded; it does not keep an entire frame.

Output uses `data_valid/ready/data[7:0]/data_last`. The four geometry bytes precede all image bytes. Output valid, byte and last are stable under stalls, except when abort/reset or an error cancels the transaction. `done` means the final serialization byte was accepted. It is not frame authorization. All emitted bytes are provisional until the parent's expected hash, HUD and publication checks pass.

`abort_i` invalidates buffer ownership and output. Held abort gates ready/valid. Reset/abort do not clear strip RAM; full/cache-valid flags prevent stale data from becoming a valid output. A system reset must also flush external tile queues. The parent must propagate serialization errors to a downstream hash transaction and retain the prior published bank.

Errors are sticky until the next accepted start/reset: 01 invalid configuration ID, 02 tile identity/order/key, 03 last-marker mismatch, 04 internal final-byte-count mismatch. `accepted_tiles`, `emitted_bytes`, `strip_word_writes/reads` and stall counters expose work; successful frames have exactly 8,100 valid tiles, 64,800 writes, 64,800 reads and 518,404 bytes.

## Bounded wide storage and overlap

`STRIP_BANKS=1` uses **720×64-bit words =5,760 logical payload bytes** for one eight-row Y band. A chroma band uses only the first 360 words (2,880 B). Per-bank word counts keep stale unused chroma columns out of the stream.

`STRIP_BANKS=2` provides 11,520 payload bytes and fills one band while the other drains, including plane transitions. A separate 64 B captured tile and 8 B output word cache are additional; flags, indexes, metadata and SHA storage are also additional. These are logical payload bounds, not total BRAM/SRAM usage or device fit.

There is one 64-bit write per store clock. The output cache prefetches the next word on its prior word's last-byte handshake, so continuous draining has no per-word bubble. After `proc; opt; memory_dff; opt_clean; memory_collect`, Yosys retains the strip as **one synchronous read port and one write port**, width64, depth720/1440. Compressed generic netlists and `memory-evidence.json` retain this check. Physical primitives, port packing, clock frequency and placement remain unmeasured.

The first read-register version did not merge under the initial unoptimized memory pass; those diagnostics are retained. An unreset output register protected by valid ownership and the standard optimization pass give the registered read port. No RAM contents are reset to obtain correctness.

## Actual ROWS→SHA integration

The wrapper supports every combination of one/two strip banks and one/two SHA input banks. It starts both components together with the SHA byte count fixed to518404. An error aborts provisional child work; a later valid start clears sticky error state. A digest is exposed only after the serializer completed and the SHA result is valid. Backpressure is the real SHA ready signal, not a substituted Python service model.

This still does not connect entropy/inverse/DDR/HUD or enforce a reconstruction-bank fence. The SHA digest is unkeyed content binding; a correct hash alone does not authorize a displayed bank. The wrapper returns the full256-bit digest, and a CU66 caller compares its defined upper128bits with the packet tag.

## Fixtures and tests

Seven distinct full messages are checked: four retained actual canonical source keys, two full-size random/zero patterns and a coordinate-coded pattern exposing row/word/plane transpositions. These are four game-source images, not seven new captures. The exporter also feeds all **56,700 full-grid tiles** through the frozen Python v67 tile-hash model and checks the same canonical tag; full-byte/hashlib messages remain the oracle for simulation.

The C++ testbench compares every serialized byte, exact prefix/last/count, tile-store/read counts and stable stalled outputs. The integrated DUT additionally compares the entire SHA256 against the retained native/hashlib expected value. Ideal service and three random schedules (6901–6903) are run on two standalone configurations and all four integrated configurations: **168 main full-stream checks**, including **112 main full-digest checks**. Metadata/error/abort/reset suites add four valid retries per run; they do not add unique source data.

Controls cover both valid key values, wrong frame/key/plane/index, early last, duplicate indexes, Y→Cb boundary error, missing global last, invalid configuration ID, ignored busy starts, changed input bus after capture, held abort, reset, a provisional-output/backpressure abort and valid retries. Late malformed tiles may follow many correct provisional bytes, but must never expose an integrated digest. Per-frame and global watchdogs bound each test. A clean compile/exit is insufficient: `CONTROL_PASS` and final `TEST_PASS` are required.

Ideal observed service counts for a full canonical message are:

| Strip banks | SHA banks | Last serialization byte clock | First digest clock |
| --- | --- | ---: | ---: |
| 1, standalone | — |591,421 |— |
| 2, standalone | — |519,212 |— |
| 1 |1 | see `results.json` |1,126,148 |
| 2 |2 |535,410 |535,538 |

All seven payloads have the same ideal size-dependent counts. The first geometry byte transfers at clock2 and first Y byte at813. Counts include the accepted start edge and actual store/prefix/read/SHA/control work. Random schedules retain their own first/last/result and stall counts. They are not routed clocks or a physical throughput result. No LCD timing/rotation or end-to-end 30 fps proof follows from them.

## Reproduction and remaining scope

Verilator5.020/g++13.3 run in `gamebub-cu66-v69-build`; fixtures require host NumPy/zlib and the frozen hash/source bundle. The same repository path is mounted inside the container; build products are outside the repository in `/build/rows*`.

```sh
TASK_PYTHON=/home/lori/gamebub-streaming-prototype/.venv/bin/python \
  fpga/experiments/cu66-v69/rows/run_regression.sh
python fpga/experiments/cu66-v69/rows/audit_results.py
```

Current `--Wall` builds must be clean. Initial wrapper empty-output warnings were resolved by exporting telemetry rather than suppressing warnings. Before cleanup, Yosys checking after read-register merging reported64 dangling temporary read wires; the standard `opt_clean` pass removed orphaned lowering logic, with the synchronous memory port preserved and final check reporting zero problems. The before-clean logs and failed audit are retained; no check was downgraded. `memory-verify-first.log` preserves a verification-helper relative-path error, fixed before final results. Yosys generic checks must report zero problems; their retained netlists establish port shape, not physical target fit.

The next integration must preserve provisional writes, expected-tag/HUD validation, immutable reference banks, safe memory-reader lifetimes and abort/reset queue flushing. This serializer must not be substituted for a rotated physical LCD scanout path. The existing JPEG backend gains no CU66 decode capability from these standalone blocks.
