# V47 bounded actual-TLSF fragmentation comparison

Final result, 2026-11-07. No hardware, network, target build or production-source changes were performed by this harness task. All harness work is under this directory; source/fixture pins are in `bindings.json`.

## Qualified result

The final bounded matrix is **60 deterministic schedules**, one128,000-byte backing region, original V46 versus V47 largest-first decoder, same fixed holes/pins, same per-frame HU input allocation, same98,304 native cap and8,192 free reserve. Both variants use the unmodified local ESP-IDF5.4.3 `components/heap/tlsf/tlsf.c` allocator compiled for the Windows64-bit host. Native arena malloc/free calls are redirected only in preserved header copies to that real TLSF pool. No synthetic request-size rejection is used.

| Outcome | Schedules |
|---|---:|
| Both fail allocation |57|
| Original fails; candidate passes all12 |2|
| Both pass all12 |1|
| Original passes; candidate fails |0|
| Integrity-invalid final schedules |0|

Every completed frame is compared word-for-word against its independent42,240-byte golden HUD; a complete12-frame pass verifies253,440words. Every original/candidate run checks TLSF free-list and physical-block integrity immediately after creation, on native failure, and on final success. All recorded native failures in this matrix are real malloc failures (kind3), not cap/reserve refusal. These severe synthetic fragmentation patterns are intentionally not representative failure-rate samples.

The candidate advances farther in13 schedules, the same distance in46, and less far in1. Thus **no successful-control regression was found**, but **progress is not uniformly better**. Seed15 original presents6 before failure; candidate presents4 before failure. Both still fail cleanly.57/60 candidate failures means this change is not a robust cure for arbitrary fragmented heaps.

## Two integrity-qualified improvements

| Seed | Original V46 | Candidate V47 |
|---|---|---|
|3|Fails frame6, request15,360; live73,800; free42,936; largest11,904; peak92,544|12 golden frames pass; peak88,974|
|4|Fails frame4, request15,360; live73,800; free41,344; largest14,320; peak92,379|12 golden frames pass; peak88,974|

Seed3 initial free125,064/largest67,080; seed4 initial free123,192/largest56,840. Both meet the existing network preflight total/largest thresholds. Inputs/pins/order are identical between variants within each seed. Integrity checks passed for both the original failure state and candidate success state. Traces `seed3-v46-trace.csv` and `seed3-v47-trace.csv` retain actual native allocation/free IDs, sizes, frame, success, pre-call total free and largest block. The RESULT row is followed by destructor releases of the retained accepted cache; these are host teardown, not additional target recovery.

This confirms a mechanism by which largest-first decoding reduces allocation pressure and changes physical fit on a real bounded allocator. It does **not** reproduce exact physical frame3/11,520 failure timing, prove target network success, or prove sustained codec speed.

## What the model includes and omits

The pool is consumed into deterministic variable-sized freeable holes separated by persistent64–512-byte pins, then the holes are freed. The pins represent long-lived surrounding allocations. Each frame allocates its actual HU Prepare wire from the same pool and frees it after successful Prepare. Actual native temporary and accepted/candidate allocations use this pool. Standard host I/O, test vectors, native Endpoint object and tracing-map overhead remain outside it. Fixture files and golden comparisons are host test mechanisms, not target file access.

Target32-bit ABI, exact SDK/Wi-Fi heap regions, concurrent allocation timing, malloc metadata and live physical topology differ from this64-bit host model. The actual ESP-IDF TLSF algorithm is exercised, but this is neither the full heap_caps allocator selection nor the target's exact heap. Fixed pins are plausible stress topologies, not a reconstruction of which real target object occupied each hole.

## Preserved failed exploratory harness

`sweep.json` is the original **unqualified480-configuration exploration**. It must not be reported as477 both-fail/2 improvements/1 both-pass. It lacked initial/failure-path integrity gates.196 terminal runs returned TLSF list-check error12 after completing golden words; subsequent investigation reproduced a free-list check error **immediately after TLSF creation**, before any native decode or pin allocation, for a136,000-byte host64 pool. Physical-block integrity returned0 while list integrity returned−1 (the failed condition is an empty free-list head expected to equal the null-block pointer).

The failure correlates with host64 control-table alignment/size layout for that configuration; its exact library-port cause was not fixed or attributed to production. `tlsf-debug.c` adds assertion-site printing only, preserving the exploratory diagnostic separately. The final evidence uses only128,000-byte pools whose initial and terminal integrity checks pass. The old exploration is explicitly INVALID for comparative conclusions; no integrity error has been hidden or silently counted as a normal decoder failure.

## Reproduce

From PowerShell, with all temporary/compiler output paths under C:/moon:

```powershell
$env:PATH='C:\msys64\ucrt64\bin;'+$env:PATH
$env:TEMP='C:\moon\tmp'
$env:TMP='C:\moon\tmp'
$lab='C:/moon/maintenance/v47-fragmentation'
$idf='C:/Users/lavat/.espressif/esp-idf/v5.4.3/components/heap/tlsf'
gcc -O2 -I "$idf/include" -c "$idf/tlsf.c" -o "$lab/tlsf.o"
foreach($version in 'v46','v47') {
  g++ -std=c++17 -O2 -I "$lab/$version" -I "$idf/include" "$lab/fragmentation.cpp" "$lab/tlsf.o" -o "$lab/$version.exe"
}
python "$lab/run_matrix.py"
```

Single qualified improvement, with optional final `trace` argument for the allocation/free history:

```powershell
& "$lab/v46.exe" 3 128000 C:/moon/publish/firmware/experiments/v46-dy71-native-failure-20261107/handheld/src/cu66/fixtures/prepare12 trace
& "$lab/v47.exe" 3 128000 C:/moon/publish/firmware/experiments/v46-dy71-native-failure-20261107/handheld/src/cu66/fixtures/prepare12 trace
```

`qualified-matrix.json` retains every result, exit code and stderr. Tests hard-code the preserved independent HUD reference directory `C:/moon/maintenance/v45-sequence/qualification`; those inputs are hashed in bindings. The copied V46/V47 native header trees preserve this exact run. Their `bounded.hpp` substitutions are only `std::malloc(n?n:1)`→`lab_alloc(n?n:1)` and `std::free(p)`→`lab_free(p)`; production sources are untouched. The final harness source itself is hashed.

No more seed search is required for this candidate. The next evidence must be the bounded target CPU12/network cached12 comparison, preserving the existing guards and rollback. Treat successful offline fit as justification for that experiment, not hardware qualification.
