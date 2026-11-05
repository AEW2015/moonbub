# CU66 packet/control RTL (v69)

`cu66_packet_control.sv` is an actual byte-RAM RTL parser for the explicitly restricted CU66/GU66 capability: epoch 25, 720×480, arithmetic coefficient dispatch 5/6, canonical zero-motion wire map only. It is behavioral RTL qualified with Verilator 5.020, not a synthesized design or a complete video/HUD decoder. The target part, routed clock, CDC and external-memory implementation are not proved here.

The module scans each valid packet byte once and checks original outer, inner and HUD-envelope CRC32, fixed profile/identity/geometry, exact lengths, monotonic/prior reference binding against caller-owned snapshots, qmap codes/padding, key/no-vector or P/exact `00 00 00` motion grammar, plane dispatches and HUD envelope identities/rectangles/types/lengths. It emits each AB38 payload address **after its dispatch byte**, payload byte length, encoded block count and block width, plus HUD address/length and canonical/HUD tag fields. It does not create fake converted packets or inspect golden data at runtime.

## Frame-owner and lease interface

The root frame-bank owner is the **only** owner of accepted frame/reference history. At `cfg_valid && cfg_ready`, this parser snapshots `cfg_packet_bytes`, last-frame valid/ID and reference-bank valid/ID/previously verified canonical tag. These inputs must describe one immutable staged compressed packet and its selected reference bank. `cfg_packet_bytes` is 16 bits; the transport/owner must reject an oversized original length before narrowing it. This module also bounds the supplied value to 733–49,152 bytes.

All 128-bit digest ports put **wire byte 0 in bits 127:120** and wire byte 15 in bits 7:0. No reference-bank SHA is computed here. The snapshot/cache contract assumes the owner keeps that verified bank unchanged; it is not ECC or authentication.

The flow is:

1. Configuration acceptance acquires the local packet lease. `busy` remains high while reading and validating.
2. On complete structural/CRC success, `metadata_valid` holds all metadata stable until `metadata_ready`.
3. That handshake enters `WAIT_COMMIT`. It does **not** release the packet or advance any accepted state. Metadata registers remain stable through this wait.
4. Only `commit_valid && commit_ready` releases this parser's local lease and pulses `done`. `commit_ready` is asserted only in `WAIT_COMMIT`. A commit asserted before metadata acceptance is ignored.
5. The root must drive commit for the **current active lease** only after canonical reconstruction/hash, exact HUD semantic validation, output/reference-bank write drains and all other required gates succeed. This parser has no independent accepted-history counter and does not validate those downstream results.

The root's `frame_committed` event can drive this commit when qualified for the active frame. A local `done`/`cfg_ready` is not a global compressed-bank-reuse permission: packet, entropy and every other master must all have drained. Do not route a stale commit from an aborted generation to a new lease.

`rd_req_valid/ready` and `rd_rsp_valid/ready` implement one outstanding byte read. Addresses are relative to the active compressed packet. The arbiter adds its bank base and must preserve that bank/response routing while leased. Request address/valid hold during request backpressure. `abort_i` may withdraw an unaccepted request; an accepted request is drained in `DRAIN` before the local lease is released. Abort wins over metadata/commit. `aborted` and `error` remain visible until the next configuration; `done` is a one-cycle release/completion pulse.

Reset is active-high synchronous. Its integration contract is a shared reset/flush of the memory adapter and root lease generation; a local reset alone cannot identify a response left over from an unrelated old bus epoch. The testbench uses this reset contract at initialization and explicitly tests ordinary abort with delayed accepted responses.

## Qmap port timing

The 338 packed qmap bytes are retained in an 8-bit array. No full compressed packet is stored internally. Together, outer/inner/HUD header arrays are 242 bytes; header arrays plus qmap data total 580 logical bytes, excluding control/tag registers, routing and implementation overhead. This is not a BRAM-fit result.

The qmap port is available **only in `WAIT_COMMIT`, after the metadata handshake**. At a rising edge with `qmap_req_valid && qmap_req_ready`, it accepts an index 0–1349. `qmap_rsp_valid`, the matching index and its 2-bit code are available in the following cycle. Responses have no ready input and must be consumed in that cycle. Codes 0/1/2 represent quantizer scales 8/16/32. An out-of-range index is not accepted. Commit/abort block new lookups; consumers must be idle before root commit. Lookups do not alter accepted history or packet contents.

The row-major qmap geometry is 45×30 macroblocks of 16×16 luma / 8×8 chroma. A luma 8×8 block uses `(block_y/2)*45 + block_x/2`; chroma uses `block_y*45 + block_x`.

## Functional evidence and exclusions

Two seeded full regressions (6910, 6911) each pass:

- 457 stored full-decoder-qualified CU66 packet metadata records;
- 23 structural/CRC/profile/capability rejections;
- five metadata-valid candidates that require downstream semantic rejection, always aborted here;
- 625,050 individual one-cycle qmap results, including the retry property test;
- request stalls, variable 1–7-cycle RAM responses, held metadata and delayed commit;
- abort before request acceptance, abort/drain after request acceptance and metadata abort/retry with the same caller snapshot.

Each seed reads 8,161,002 RAM bytes including negatives/abort/retry tests. Seed 6910 takes 44,172,907 simulated cycles and seed 6911 takes 44,161,369 under the artificial RAM/stall schedule. These are behavioral test schedules, not device-clock or 30 fps results. All valid packet scans check exactly one read per packet byte. CRC scanning precedes metadata; entropy and pixel processing are not overlapped by this component.

The five deliberately deferred failures are: wrong nonzero canonical output tag, corrupted nested AB38 CRC, invalid nested AB38 geometry, hidden nonzero coefficients and a wrong reconstructed HUD output tag. Their packet-level checksums and headers can be structurally valid. Canonical hashing, AB38 semantic decode/CRC, hidden-coefficient checks and full HUD decode/tag validation must reject them downstream. The parser's successful metadata handshake is **not** a successful frame decode or publication. In particular, HUD Huffman/Rice/prediction and exact HUD reference/output matching are not implemented in this module.

Verilator lint is clean with `-Wall`; no warning waiver, disabled functional checker or vendor IP is used. The first trial found a testbench delta-evaluation error after clearing abort: it sampled gated `cfg_ready` without reevaluating combinational logic. `seed6910-initial-fail.log` is retained. The checker was corrected with `eval()` after deassertion; no DUT repair was made for that failure. Before the final two runs, qmap visibility was explicitly restricted to `WAIT_COMMIT` to match the documented handshake contract.

## Reproduce and integrate

```sh
python3 export_fixtures.py
bash run_regression.sh
python3 audit_results.py
```

The supplied script selects standalone behavioral Verilator explicitly, builds at most two jobs and uses the dedicated container's `/build/packet` by default. Set `BUILD_DIR` for another writable directory. Fixture paths are relative and copied from the frozen native CU66 corpus; source manifests and content hashes are retained. Testbench watchdogs and explicit `TEST_PASS` markers are required. No Vivado project, AMD primitive library or licensed simulator is involved in these behavioral runs; no Vivado timing/implementation result is claimed.

The frozen native C++ implementation in `experiments/cu66-native-v69/` remains the full semantic oracle. Current live Gamebub firmware/FPGA still supports JPEG; CU66 negotiation/backend integration remains new work. Physical bank fences, packet/entropy arbitration, canonical/HUD SHA, HUD semantic RTL, pixel reconstruction and display scanout must be integrated before a hardware streaming claim.
