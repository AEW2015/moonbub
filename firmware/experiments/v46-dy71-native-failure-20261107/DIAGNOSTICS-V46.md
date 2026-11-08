# V46 native failure diagnostic candidate

Purpose: retain actual failure context for V45 cached12 ordinal 3 / frame 3 / phase 6 Error::Hud. No cause or performance fix is selected. Phase 6 can include Prepare or subsequent native software COMMIT/ABORT validation. V027 FPGA, sequence-v3 wire, native budget 98,304 bytes, physical reserve 8,192 bytes, ingress cache, admission/decode/ownership and failure quarantine remain unchanged.

## Bounded observations

- Native getter copies 24 fixed u64 values, six existing allocator statistics, and at most 96 failure-text bytes. It reports original length and truncation; hex export is split into three 32-byte records. Getters allocate nothing, invoke no heap probes and change no native state.
- Arena last failure records kind (0 none, 1 budget, 2 physical reserve, 3 malloc, 4 element-count overflow), requested size, live bytes, free bytes and largest block at failure. `probes` bit 0 validates free and bit 1 largest. Overflow request is element count, other requests are bytes. Last failure persists across successful calls; it is not a claim about the current call.
- Optional largest-block callback is invoked only at allocation failure. Existing admission tests, reserve threshold and allocation order are preserved. Failure-only free sampling supplies diagnostic context for budget/malloc/overflow; the existing reserve failure reuses its admission sample.
- Rust stores last actual native opcode, generation/frame/reference, FFI return and written count, native response argument, driver check mask, and expected/observed Prepare tags. Explicit validity bits identify unavailable/stale identity, reply and tags.
- Wrapper stages: 1 input framing, 2 input-response rejection, 3 FFI return, 4 output length, 5 output framing, 6 response identity, 7 decoded response observed, 8 driver payload validation failed. Stage 7 with nonzero reply argument is a real native rejection, not FFI failure.
- Prepare payload mask: bit 0 length, 1 phase, 2 candidate-ready flag, 3 words, 4 generation, 5 frame, 6 reference, 7 tag. Software masks: 0x100 response argument/length (low bits 0/1); 0x200 COMMIT payload; 0x400 ABORT payload.
- On Err only, before Adapter drop, read exactly once each CSR 0x350 owner, 0x354 accepted, 0x358 presented, 0x35c rejected, 0x360 underruns, 0x110 stage error. Retain each Result including Contended/read error. No retries, selection writes, aborts or authority changes. These passive read attempts contribute to health read/QSPI counts and occur after the failed driver result.
- Snapshot remains fixed-size, immutable after publish, checksummed and paced one line per 40 ms using the existing DY45 envelope; diagnostics do not fabricate unavailable partial timing arrays. No new tasks/threads.

## Verification and limits

Host suites compile the actual C++ endpoint and Rust production driver/wire/telemetry. Added checks distinguish allocator budget/reserve/malloc, decode rejection, response-tag mismatch, input/output framing, output identity and FFI errors. Observational getters and repeat exports retain state/hash; worst-case lines and storage are bounded. Host-only injection entry points are cfg(test) and excluded from target.

Target compilation, ELF SRAM/stack review, exact binary/updater checks and physical behavior remain pending root review. Fixed native/Rust diagnostic storage and failure getter stack are additions; no claim is made that hardware cached12 is repaired. CPU-only probe, if included, is a separate explicit diagnostic and cannot establish network/FPGA throughput.
