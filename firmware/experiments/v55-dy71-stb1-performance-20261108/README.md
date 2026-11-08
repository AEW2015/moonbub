# V55 combined offline performance candidate

This separate source candidate combines individually qualified changes over exact frozen V54. It has not been target-built, installed or physically timed. V54 remains the first hardware control so the new transport/diagnostics can be measured without these additional performance changes.

The composition is restricted to exact sources: V49 `native/hud.hpp` canonical Huffman arrays; V50 `native/endpoint.hpp` bounded READ slicing; V51 revision2 free-only reserve callbacks and their helpers; V53 HBU1 status trait/default, actual one20-byte SPI read and unchanged four-field status validation body. The diagnostic label is V55. No other algorithm, SPI clock or native source changes are included. `composition.json` pins full input files and function fragments; `composition-delta-proof.json` reverses the selected changes and proves all remaining application logic matches V54. Six other native files remain exact V48.

V54's STB1/ABI3/caps3f, aligned1024-byte in-place source buffer, failure observer/context/checksum, DYN1/DYA1 wire, native/HBU1 state transitions, Error enum, SDK defaults,16,384-byte worker stack,98,304-byte arena,8,192-byte reserve and free/largest-block admission thresholds are preserved. Raw512/1024 bounds remain critical; no new protection against arbitrary oversized raw SPI transactions is claimed. SDK/log/DMA internal allocation/bounce behavior remains unmeasured.

## Executed combined checks

`C:/moon/builds/v55-host01` passes the full source-bound native/Rust suite:213 Rust executions, including all104 original regressions, STB1 and failure observer tests. Native allocation-budget/physical-reserve failure, rollback, stale state and original first12/253,440HUD-word checks pass. The suite does not raise the native cap. The cached12 native test retains actual accepted state and verifies the full HBU readback/commit path in the host model.

Additional source-extracted gates pass: four callback executions (control/candidate), seven actual STB Adapter SDK-shim cases and six actual HBU status Adapter SDK-shim cases. The HBU read starts at0xe0000608, reads five words in one20-byte transaction and checks the same four values at indices0/2/3/4; packed-loaded remains observational. SPI mode stays16MHz/32-bit/no-byte-swap/autoincrement. The free-only callback model preserves returned free values/minimum tracking and separate failure diagnostics while removing normal largest-block walks; its4520-query model is not an actual V55 runtime call count or elapsed-time result.

The combined native endpoint also passes the original three-frame control and twelve NEW local-video HUD sequence. Both full-frame READ and the actual256-word READ pattern match independent source goldens:316,800 unique HUD words,633,600 comparisons. Old3/new12 arena peaks are88,974/95,053 under98,304, with zero allocation failures. Thirty malformed/late-HUD checks preserve prior state and fifteen fresh-generation recovery checks pass. These host64-bit arena results do not prove ESP32 fragmentation, SRAM reserve or runtime stack margin. The new sequence is the short local motion-test sequence, not the requested120-second Mass Effect clip.

V54 diagnostic compatibility remains tested: six strict Python decoder tests and two actual Rust-emitted context/CRC vectors pass; maximum record payload remains186 bytes. Sampling is still post-failure/non-atomic/best-effort and has no normal-path SPI/log output. No new paced re-export claim is made.

## Stack and remaining gates

Individually qualified V49 Xtensa frames increased Huffman192→752bytes (+560) and channel144→160 (+16), a recorded +576-byte call-chain change. Combining it with STB1 and failure diagnostics requires a new exact target/static-frame/effective-SRAM review and physical task high-water measurement. The worker stack and reserve are deliberately not increased to conceal this risk. Host bounds and zero-allocation tests are not a proof of the complete target call stack or SDK allocation behavior.

Root review is required before the V55 target build. Preserve the exact combined source and rerun affected checks after any changes. Package only after target/SRAM/stack gates pass. Hardware must first qualify unchanged V54 with the selected timing-clean ABI3 FPGA, then compare V55 using the same original fixture and measurement setup; the new-content twelve-frame check is separate. No physical speedup, sustained streaming rate, live encoding or30fps acceptance is established here.
