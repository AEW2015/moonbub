# V49 canonical Huffman offline experiment

Status: **host qualification passes; isolated candidate only**. No V48/published source changes, target build, hardware operations or network sends. Control copies the frozen V48 native source exactly; candidate differs only in native/hud.hpp's huffman function. Scope/hash evidence: scope-check.json, source-bindings-initial.json and source-bindings-final.json.

## Change

Replace the sorted pair vector and map keyed by(code length,code) with bounded canonical code counts, first-code/first-symbol arrays and ordered symbol storage. Output remains the existing Arena-tracked vector. Table lookup uses integer ranges instead of a map lookup for each input bit. Original table construction allocated map nodes; map lookup itself did not allocate per bit.

There are648 explicit table-array bytes on the stack (two256-byte arrays, two17-element u16 arrays and one17-element u32 array). No new heap allocation exists for the tables. ns remains1..min(count,maximum+1), count1..21120, symbols0..maximum<=255, lengths1..16, strictly increasing wire symbol order. Singleton retains length1/zero-bit constant semantics. Bounded raw bits, padding, completeness, oversubscription, truncated input, output count and trailing-bit checks remain mandatory.

Canonical validation computes the same sorted(length,symbol) code assignment: first_code[n]=(first_code[n-1]+count[n-1])*2. Each depth must fit its2^n space; the extended depth16 end must equal65536 for a complete tree. First-symbol offsets partition the at-most256 ordered symbols. Lookup checks code>=first and code-first<count before indexing, bounding every array access. Input validation precedes indexing by symbol/length. No mutable accepted-reference state is introduced.

## Executed semantic and rollback evidence

- Both actual C++ native variants: first12 original frames, all253440 independent golden HUD words, unchanged98304-byte arena cap and8192 reserve. Both peak88974/live84976 on this sequence.
- Both variants:457 retained golden corpus frames,9651840 HUD words,3 existing malformed packet rejections. This broad semantic harness deliberately uses a1048576-byte host cap; its100888-byte peak is not target-fit proof.
-1877 Huffman differential cases give identical accepted output bytes and identical error strings:1145 targeted/random cases plus732 mutations of valid codebooks/bitstreams. Cases include ns1 constants, ns256 full table, depth16, unsorted/duplicate symbols, invalid lengths, oversubscribed/incomplete trees, padding, truncation, trailing bits and bound violations. Harness requires Arena.live==0 after every standalone case.
- Actual-native late-component rollback test passes for invalid canonical patches0/1 after the larger outputs were decoded. Accepted identity/tag/wordCRC remains unchanged; live allocation returns to baseline; same-generation retry is Stale; newer-generation valid retry and abort preserve accepted reference. The existing negative allocation exception/stale test also passes.

Executed commands and logs are preserved by run_qualification.py/execution.json; qualification.json, RESULT.json and control-/candidate-*.log record outcomes. This is native C++ execution, not a simplified decoder simulation.

## Heap effect

| Measurement | V48 control | Canonical candidate |
|---|---:|---:|
|457-frame corpus tracked allocation calls|84765|14829|
|457-frame corpus peak bytes|100888|100888|
|First12 native peak bytes|88974|88974|
|Full256-symbol100-decode microbenchmark allocation calls|26600|100|
|Same microbenchmark peak bytes|35456|21120|

Corpus allocation calls decrease about82.5%. Unchanged full-decoder peaks show that other overlapping paths determine those maxima. This experiment has not rerun the bounded TLSF fragmentation matrix; fewer allocation calls are not proof that every target heap layout succeeds.

## Host timing only

benchmark02 alternates control/candidate ordering for five rounds, same Windows host/compiler(-Os), same corpus and full256-symbol21120-output microbenchmark. Timings below are medians of internal steady-clock measurements; complete process timings and every sample are retained separately in benchmark02/runs.json.

| Internal host work | Control | Candidate |
|---|---:|---:|
|Sum of457 native Prepare calls|971335us|919790us|
|100 standalone full256-symbol Huffman decodes|401271us|76821us|

The broad Prepare sum improves about5.3% in this small noisy host sample; whole-process medians are1.346s versus1.331s and include file I/O/golden hashing. The synthetic lookup-heavy microbenchmark improves about5.2x. Neither result predicts ESP32 speed or physical displayed FPS. benchmark01 is an earlier complete five-round process-time run; benchmark02 adds explicit Prepare timing and is the selected attribution run.

## Stack/call-chain limit

GCC Windows host -Os -fstack-usage reports Huffman352?896 bytes (+544); channel33304?320; decode_patch432, decode_hud560, HudGate.prepare336 and Endpoint.transact336 unchanged. The illustrative host HS33 chain through those functions totals2320?2880 bytes before deeper helpers/runtime; this is not a formal stack bound. The explicit additional tables stay below the preferred1KiB budget, but Xtensa code generation, C++ exception stack and actual target high-water remain unmeasured. No target stack safety claim is made.

## Recommended next gate

Independent canonical/bounds/exception review, then a separate target build and SDK stack/SRAM review before proposing a new physical app. Keep V48's bootstrap and FPGA V027 unchanged. If stack margin is tight, use a separately reviewed compact input-view table representation or Arena-tracked fixed scratch rather than silently raising stack or reserve limits. Retest actual TLSF fragmentation schedules before claiming fragmentation robustness. No merge/publication is part of this experiment.
