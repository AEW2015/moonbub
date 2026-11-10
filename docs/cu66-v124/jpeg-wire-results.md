# V124 native MSV1 file replay

**Selected qualifier status: PASS.** One bounded Verilator run completed both phases successfully. The preparation contract remains labeled `PREPARED_NOT_RUN` because it describes the prepared input/source contract; the executed result is recorded separately by the selected attempt receipt below.

## Input boundary

The selected native endpoint receipt is `experiments/python-gamebub-v124/endpoint/attempts/20261110T040425114351Z-6a1d1432/receipt.json` (SHA-256 `d7eba5bc52afc856344810bcb9ee544dc9d7a76c899520a349a4735b449fbfd5`). Its native C++ packetizer output `out/native-1024.bin` is 27,251 bytes, 26 u16-framed datagrams, and byte-exact to the shared `receiver-pattern-msv1-packets.bin` golden (SHA-256 `78c58cfcc4860761c33bcc7021e3db14e9fa66ef5e9a385ae1e4c00c82a6447f`). The actual Rust receiver separately recovered the pinned 26,159-byte JPEG exactly (SHA-256 `8cc99ea7d50d1d20255e41ff7247b0770b3349e705c27152a41817418ce5c9de`). The V124 preparation pins the endpoint selected pointer, receipt, result, actual C++ packetizer driver, packet file, Rust receiver snapshot, and recovered JPEG.

The preparation invokes the existing production Python parser/reassembler only as an additional validation of the native C++ datagrams and recovered JPEG bytes. It never uses Python packet generation. The C++ pin-driver bench reads the copied native packet bytes as its input file. This is file replay, not live Rust-to-pin driving or shared-timebase co-simulation.

## Frozen downstream bench

The source order matches the frozen V115 baseline and contains 27 RTL source files, including the unchanged `jpeg_wire.sv` wrapper/bench dependencies, actual QSPI endpoint and CDC, actual Moonshine core, and the same guarded vendor JPEG input substitution. The frozen V115 RGB565 golden is read from OLD_A and compared to the related C-model PPM conversion; it is never rewritten. The exact V115 lint review, Root approval, diagnostics, baseline VLT, and source/line rules are pinned from their original paths. The V124 qualifier retains the RAM/PSI gates and adds the combined RAM-plus-swap resource guard.

The inherited bench ran both phases with two good-frame checks, bad-CRC rejection, midreceive reset/retry, exact pixel-value/coordinate ownership checks, held-output stability, and sink-drain/frame-boundary checks. It used testbench-generated QSPI pin edges; it did not execute the Rust firmware worker or prove ESP32 timing.

## Preparation contract and launch control

`experiments/python-gamebub-v124/jpeg-wire/preparation.json` records `PREPARED_NOT_RUN`, the exact V115 source order, RTL and external input SHA-256 pins, lint scope, native packet/JPEG receipt chain, and parser comparison. That status refers to the source-bound preparation contract, not the selected execution. The V124 preparation and qualifier are reversibly derived from the frozen V115 scripts in `scripts/cu66-v124/jpeg_wire/derivation.json`; the recorded recipes replay to the candidate hashes.

The earlier preparation-only invocation and its `PREPARED_NOT_RUN` state are historical. The executed qualifier required `--root-grant ROOT_V124_JPEG_WIRE`. Its attempt receipt and command records are persisted before subprocess launches; `actual_RTL_run` records simulator invocation, including if a phase later fails. The accepted run was the single Root-granted auxiliary attempt.

## Executed auxiliary qualifier attempt

Attempt `experiments/python-gamebub-v124/jpeg-wire/attempts/20261110T050259794391Z/receipt.json` finished `PASS` (receipt SHA-256 `8669ec40a6bd86535bcc995623f6d90bafebf8171f35c4d2f8a71f3ee6c13eea`). The stable result pointer `experiments/python-gamebub-v124/jpeg-wire/results.json` reports `PASS` and pins that receipt hash. Compile and both phase commands exited 0 with strict assertion and lint settings. All 54 source snapshots in the attempt match the preparation contract. The old V115 output checksums remain unchanged, and the V124 attempt container was absent from the terminal container listing.

Both phase verdicts were `TEST_PASS` with `actual_endpoint_CDC_JPEG=true`, two good frames, 691,200 verified pixels, one bad-CRC rejection, one midreceive-reset/retry, and 79,525 accepted bus writes. Each reports 183,575 held-pixel cycles and 2,006,477 core cycles. With `tick_ps=1250`, this testbench configures endpoint and core clocks at 200 MHz and 100 MHz respectively. These are simulated clock settings and bench cycle counts, not measurements of hardware or physical timing. The host wall time was about 12 seconds.

The result is limited to the finite testbench and this file replay. It does not establish ESP32 performance, physical memory service, LCD operation, network timing, end-to-end latency, or sustained FPS. It does not exercise Rust firmware session execution or live Rust-to-pin co-simulation.
