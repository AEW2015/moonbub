# Actual V55 + CE receiver + parser validation-stage KEY/P replay

The original finite KEY0/P1 pair passed through the actual Rust receiver driver, native HUD FFI, selected RTL decoder, SDRAM model, HBU service, commit and scanout. This is a functional composition result, not hardware or 30fps qualification.

| Check | Result |
|---|---:|
| Accepted / presented / rejected / underruns | 2 / 2 / 0 / 0 |
| Actual new parser state19 visits | 2 |
| HUD words written and independently read back | 42,240 / 42,240 |
| Canonical byte mismatches | 0 |
| Composed video pixel mismatches | 0 across691,200 pixels |
| Displayed HUD word mismatches | 0 across42,240 words |
| Full raster samples | 384,000 per frame |
| Observed front banks | 0 then1 |
| Host replay wall time | 443.531seconds |

The new runtime witness is test-only: the wrapper counts actual `system_core.receiver.parser.state==19` clocks and the C++ server refuses success unless the count is exactly2. All canonical front-bank bytes, composed pixels, borders and displayed HUD words match independent prequalified original-pair goldens. No DUT output was used to derive the oracle.

Two production RTL modules differ from selected V028: the existing CE receiver factor SHA316123fb1db92d67a797b2a49263500314d5173561a2eff52ef451734f94deb9, and parser SHA39197a682b894f55d4a9a73ed039e58c0f3bed1aeb3a6cc24139c1c4d5325c56. The actual37-input Verilator list contains the new parser exactly once and the old parser path is absent. Remaining selected RTL is unchanged; support wrapper/CPP witness instrumentation and fresh output paths are separately bound. All executed inputs and harness hashes passed end checks.

The actual V55 Rust network_driver/local/HUD/framing/STB1 sources are preserved unchanged. The native library matches host01 DLL SHA09264044887f7d4a502b5f3eb0e75a3b2fad4e18be0a6cbb3afefda0922ba494 and its import library. Native cap98,304bytes, peak88,942bytes, maximum allocation15,360bytes,57allocation calls and zero allocation failures. The target ELF, radio path, target fragmentation/reserve behavior and app network-failure hook were not exercised.

Model assumptions remain directCSR8cycles/core100MHz, modeled yield100us (physical thread yield has no fixed sleep), explicit Prepare200ms per frame and native CPU virtual timer0. SDRAM starts at default zero, with accelerated init20/refresh750 and unchanged clocks/reset/timing model. The virtual elapsed506,918us and host wall443.531s must not be interpreted as physical speed. Bank2, nonzero-memory startup, stale/error/recovery injection, FPGA placement/routed timing, physical SPI/SDK and hardware playback are not covered by this positive pair. The separate candidate unit tests have their own scoped watchdog boundary evidence; it is not inherited into this run.

The initial compile failed before elaboration due Windows/WSL path serialization. Its command, logs, bindings and harness snapshot are preserved under compile01-path-failure. All old executable/output destinations were corrected and checked before replay; no old replay was launched. This failed preparation is retained rather than treated as FPGA failure. Corrected compile passed in45.938seconds and exact Rust host compilation passed.

Authoritative evidence: result.json, comparison.json, bindings.json, native-binary-binding.json, compile/rust/run receipts, native-run.log and rtl-stderr.log. A separate new12 replay is running independently and no result is claimed here for it. No Vivado or hardware operation was performed by this replay.
