# V44 final native-borrowing review addendum

November 7, 2026 (America/Denver). Read-only addendum to `v44-independent-review.md`, whose source pins precede the final native allocation repair. This review explicitly covers that later change and original arena-cap restoration; the older verdict is not silently transferred. No source changes, hardware access or additional broad test run was performed for this addendum.

## Reviewed final source and verdict

Final `native/hud.hpp` SHA-256: `cd65e262b66efe5e5b70db685b8f6cc417d35c113cb34b902d23a49b6d77bd70`.

Read-only comparison against V43 found only `hud.hpp` changed among all native files. The native diff consists of the HS prediction-pointer selection and its channel reconstruction read. Native endpoint, HUD gate, arena allocator, framing/CRC, tags, commit/drain/reset authority and HD25/motion-prediction implementations are unchanged. Final native and `handheld/src/cu66` hashes were checked against `C:/moon/publish/firmware/experiments/v44-dy71-three-frame-20261107/evidence/candidate-source-freeze-final-borrow01.json` and matched.

**No borrowing lifetime, alias-mutation or transaction-authority blocker was found in this narrow change.** It supports the bounded three-frame hardware correctness trial once the root's final package/identity and hardware prerequisites pass. It does not qualify continuous video or target runtime memory fit.

## Why the reference borrow is valid

- HS `plain = mode & 7`; only plain1, i.e. allowed HS modes1/9, takes `prediction = &reference->words`. These are reference-dependent modes: the prior reference-nonnull, exact `w*hh` size and reference-tag checks run before pointer selection. Mode0 is independent and never dereferences the null prediction pointer.
- Previously `motion_prediction(...,1,...)` returned an identical reference-word copy with consumed-byte offset0, after also constructing a temporary prediction vector. The replacement uses that same immutable reference and retains offset0, so the subsequent residual parsing and component reconstruction select the same words and input bytes.
- The pointer does not escape `decode_patch`. `decode_hud` passes a pointer into the accepted cache held by `HudGate::accepted_`; the synchronous `prepare` call keeps that accepted cache alive throughout decoding. It constructs a separate output/candidate vector and does not reassign/reset accepted state while the pointer is used.
- Output words are written only into the separately allocated `out` vector; the accepted reference vector is accessed through a const pointer. Per-patch output-tag and envelope-tag checks remain. Native commit occurs later through the checked external drain/commit sequence, after decoding has returned and no borrowed pointer remains.
- On decode exception, automatic output/prediction storage unwinds while the existing accepted cache stays owned. No successful candidate publication or native commit is fabricated. Failure still follows the unchanged conservative retained/quarantine worker path.
- Native transactions are synchronous under the existing exclusive HUD worker/owner. The change adds no task, callback, asynchronous retention, allocator ownership transfer or reentrant transaction. The call's stack-scoped arena context remains unchanged.

## Other modes and guards

Allowed plain2/3 (HS modes2/3/10/11) still call the unchanged `motion_prediction` helper, move the owned result into local `pred`, set the prediction pointer to that live local vector and retain its parsed consumed-byte offset. Motion grammar/ranges, predictor construction and lifetime are unchanged. HD25 and independent HS paths are unchanged. Review of unchanged code is not exhaustive test coverage for every grammar combination; the final three-frame replay and supplied directed tests cover their declared fixtures only.

The worker cap is restored to98,304, with initial114,688free/24,576largest admission and8,192per-native-allocation physical reserve unchanged. No target guard was lowered. The peak92,379 figure is a host/modeled result, not a claim that this ESP32 has sufficient actual runtime margin. Allocation overhead/fragmentation, radio activity, stack and largest free block remain physical checks. The inherited allocator's post-malloc probe behavior noted by the main review remains a limitation.

## Exact final evidence reviewed

- `C:/moon/publish/firmware/experiments/v44-dy71-three-frame-20261107/evidence/host-final-borrow01`: final native DLL and actual production driver tests with modeled MMIO;21driver +17batch +8wire =46passed. Includes original-cap three-frame success,63,360HUD-word comparisons, missing/lost third acknowledgment and low-physical-reserve failure without false presentation. Earlier larger-cap/old-native logs are superseded, preserved controls.
- `C:/moon/maintenance/streaming-verification-20261107/system-three-frame-final/RESULTS.md` and `result.json`: fresh final-native exact V027 functional replay,3accepted/3presented/0rejected/0LCDunderruns,63,360actual HUD word comparisons, canonical output and1,036,800active pixels compared. This includes modeled memory/CSR and explicit hardware/CPU/QSPI exclusions; it is not RF delivery or throughput proof.
- `C:/moon/maintenance/streaming-verification-20261107/v44-report-export`: applied helper equals maximum-tested helper byte-for-byte.5tests passed; maximum payload161bytes +80prefix budget=241bytes. Partial stage timing onErr remains explicitly unavailable. No driver/native semantics changed for logging.
- `C:/moon/builds/v44-target-run03/result.json`: target compile returned0 in117.234seconds with no handheld/native source changes, ELF SHA-256 `f92e3df64a104657957e0d9c86e7a1b79d4f07e2febb5f6fb40a6dd11da76110`. The root owns release BIN/UF2 generation, production updater parser, effective SDK/SRAM/stack review and final package identity receipt. This addendum does not independently certify a package not yet pinned here.

Physical installation must match the final target03/package identity and unchanged V027 BIT/DONE/USERCODE/ABI, use bounded3-v2 source/session only, and start from freshly observed heap/stack/ownership/network state. Success requires independent3presentations,63,360verified words and zero rejects/underruns plus expected natural display. Final endpoint/lease remains held by design; no implicit STOP/reconnect or120-second replay is enabled by this candidate.
