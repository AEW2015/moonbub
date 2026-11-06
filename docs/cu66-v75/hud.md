# V75 guarded full-BL8 processor HUD transfers

V75 extends the processor-facing HUD auxiliary port with full eight-word reads
and writes. The existing scalar path remains available. The receiver, CU66
packet syntax, native HUD semantics, canonical memory layout, painter transfer
interface and global commit protocol are unchanged. New code lives in V75
paths; V74 sources and evidence remain frozen.

## Request and completion contract

Addresses count x16 words. A full BL8 transfers eight adjacent words (16 bytes),
with the lowest-address word in payload bits 15:0. New ports are
`hud_aux_req_burst`, `hud_aux_req_read_burst`,
`hud_aux_req_burst_data[127:0]`, `hud_aux_req_byte_enable[15:0]` and
`hud_aux_rsp_burst_data[127:0]`. Existing scalar data and response ports retain
their low-word compatibility behavior.

| Request | write | write-burst | read-burst | byte-enable |
|---|---:|---:|---:|---:|
| Scalar read/write | 0/1 | 0 | 0 | `0000` |
| Full BL8 write | 1 | 1 | 0 | `ffff` |
| Full BL8 read | 0 | 0 | 1 | `0000` |

Other flag/mask combinations are rejected locally. This interface intentionally
accepts full eight-word writes only; partial byte masks are not a processor HUD
feature. Wide addresses must be aligned to eight words and the entire block
must remain in the selected candidate's 21,120-word HUD allocation. All
requests require the active generation/frame identity and current candidate
permission. Writes additionally require exactly the next uncompleted word
address; skips, duplicates, wrong banks and overflow are rejected before a
physical SDRAM command is issued.

The arbiter captures address, data, flags and mask at request acceptance.
Producer changes after acceptance cannot change the operation. One auxiliary
request is outstanding at a time. Responses hold their identity and payload
until accepted; the wide memory bridge snapshots all eight returned words for
both a miss and a cache hit. The arbiter routes response validity and ready to
the accepted owner. The output payload has no meaning when response valid is
low.

`hud_completed_words` advances by eight after a successful physical wide-write
acknowledgment and by one for a successful scalar write. Queue admission is not
completion. A claimed external HUD drain still requires exactly 21,120
completed words, no recorded physical transfer fault, and no outstanding HUD
operation. Accepted physical blocks drain through every beat even when the
receiver aborts or rejects an early drain claim. Pending operations and candidate
leases are not released early.

The hardware coverage counter does not independently validate the content's
semantic hash. The existing processor HUD endpoint must prepare the actual
patches, upload them, read back and hash the actual returned words in their
logical order, then supply the matching generation/frame/bank/tag drain
acknowledgment. The integrated positive-system test exercises that separate
semantic gate; the directed control bench deliberately uses diagnostic words
and makes no successful frame/commit claim.

## Traffic budget

A complete HUD upload changes from 21,120 scalar requests/physical BL8 commands
to 2,640 full-write commands. Active writes remain 21,120 x16 words; physical
write beats change from 168,960 to 21,120, saving 147,840 masked beats per frame.
Readback similarly changes 21,120 scalar API requests into 2,640 wide requests;
the old physical cache already combined adjacent scalar reads, so this is not
an eightfold reduction in physical read bursts. Root's scalar/burst full-system
ablation measures actual controller cycles and preserves exact output. These
request/beat counts alone are not target-frame-rate or CPU-time evidence.

## Directed control regression

`python3 fpga/experiments/cu66-v75/system/run_control.py` compiles the actual
integrated RTL with the frozen V72 SDRAM controller/model, strict Verilator
warnings and a bounded watchdog. `control-results.json` records source and
command-log hashes. Model peeks are read-only checks; no test data is preloaded
through a model backdoor.

The bench retains the V74 scalar guard/partial-abort/early-drain cases. In the
new burst suite, the testbench legally backpressures additional packet fetches
immediately after the actual HUD-prepare handshake. Metadata parsing and
candidate ownership are real, while compressed-base execution is stalled so
physical controller counters isolate HUD traffic. The separate full-system
scalar/burst replay covers concurrent base/HUD service. Added
cases use real packet metadata to obtain candidate permission, transfer and
read back a complete 21,120-word diagnostic HUD through actual BL8 commands,
reject malformed flags, partial masks, bad generation/frame/bank, misalignment,
range crossing, duplicates and skipped write addresses. It mutates producer
payloads after acceptance and stalls full write, read-miss and read-hit
responses. Another candidate raises a false full-drain claim after the first
physical write beat, then checks that all eight accepted beats drain before
candidate release. No complete video frame is accepted in this directed test.

The final source-stable regression passes with these finite counts:

| Check | Result |
|---|---:|
| Actual candidate metadata parses | 4 |
| Physical HUD words written, including discarded candidates | 21,130 |
| Preserved denied scalar writes | 7 |
| Additional denied burst/shape/range/identity requests | 21 |
| Candidate abort drains | 4 |
| Early full-drain claims rejected | 2 |
| Stalled wide responses / accepted producer mutations | 3 / 3 |
| Accepted complete frames | 0 |

The isolated complete upload issues exactly **2,640 physical write commands /
21,120 physical x16 beats**, followed by complete wide readback. The separate
first-beat abort probe issues one more command and drains eight beats. The new
suite's 202,339 model clocks include metadata, negative requests, response
stalls, readback and aborts; this is not a pure HUD-transfer or frame-decode
latency. The preserved legacy suite uses 99,261 clocks. All raw counts and
command/log/source hashes are in `control-results.json`.

`control-attempt1-hang.log` and `control-attempt2-hang.log` preserve incomplete
harness attempts that left two independently clocked VerilatedContext instances
alive; explicit single-thread configuration alone did not resolve the observed
sleeping futex. Scoping the first model/context to end before creating the
second allowed normal termination. `control-attempt3.log` and
`control-attempt4.log` retain an initially overstrict aggregate-counter check:
2,640 HUD commands ran alongside 233 additional canonical-memory BL8 commands. The final directed
suite isolates HUD traffic through legal packet-source backpressure instead of
mistaking aggregate activity for a HUD defect. No production RTL repair was
required, and these attempts are not passing qualification records.

Full canonical/RGB correctness, complete HUD semantic decoding, real CPU
service, physical SDRAM behavior, target fit/Fmax/CDC, 30 fps and under-10-ms
target decoding remain separate qualification gates.
