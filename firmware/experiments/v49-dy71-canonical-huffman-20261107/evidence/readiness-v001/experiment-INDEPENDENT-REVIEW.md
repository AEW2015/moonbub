# Independent canonical Huffman review

November7,2026. Read-only review of the isolated V49 native experiment. No candidate, V48, target or hardware state was changed.

## Decision

No blocking functional or bounds defect found in the canonical-table replacement. It is suitable for a separate target build and bounded qualification. This is not approval to claim target stack safety, physical speed, reliable fragmented-heap fit or30fps.

I independently compared the native trees: only`hud.hpp` differs, and its prefix before`huffman` and suffix from`plain_rice` onward are identical. Control HUD SHA256`8880d403231579ce32c548c9994796e6cf9cec468470b7dc2f95b9227e2b184e`; candidate`0f0da550675b7574ddf78697b9dea7305887c85ab7368a3eb780dcca0e79c602`.

## Canonical assignment and integer bounds

The initial guards constrain count to1..21120, maximum to0..255, ns to1..min(count,maximum+1), and bit count to16*count. Therefore maximum+1,16*count and nb+7 cannot overflow unsigned32. Every symbol and code length is validated before indexing: symbols are0..maximum, wire symbol IDs strictly increase, and lengths are1..16. No duplicate or absent symbol can create an extra ordered-symbol insertion.

`counts` and`first_symbol` use16-bit entries, sufficient for at most256symbols/offset256. `first_code` correctly uses32bits: an already complete shorter tree extends to65536 at depth16, a value that would not fit16bits. The recurrence`(code+counts[n-1])<<1` is bounded by2^n at every successful previous depth; n never exceeds16. Oversubscription is rejected when the complete code range at any depth exceeds2^n.

The ordered-symbol pass visits code lengths ascending and symbol IDs ascending, exactly matching the original sorted(length,symbol) pairs. Each declared symbol is inserted once; the final offset is ns<=256. An array write uses the old offset, at most255. For lookup, `c>=first` prevents unsigned underflow, and `c-first<counts[n]` bounds the index inside that depth's assigned symbol interval. If counts[n]==0, first_symbol may equal256 but the lookup condition cannot succeed, so no out-of-range read occurs. `c` receives at most16bits and does not overflow.

The depth16end==65536 completeness test is equivalent to the old longest-depth end==2^prior check: extending a complete shorter tree through empty depths preserves full occupancy. Incomplete and oversubscribed tables still fail closed. Validation may discover an invalid table before the old implementation would have allocated its map nodes; that is an intended allocator-lifetime change, not altered acceptance.

## Edge and exception behavior

The singleton path still requires one-bit declared length and zero encoded bits, returning count copies of its symbol. ns>=1 guarantees`last` is valid before conversion/indexing. Empty streams, invalid constant syntax and invalid bounds remain rejected.

The same`Bits` implementation validates exact byte count and zero padding, bounds every bit read, and requires exactly nb consumed at completion. Output remains the same Arena-tracked reserved vector. It emits exactly count symbols and then checks trailing bits. No accepted reference cache, HUD tag, candidate publication, commit or abort code changed. Local arrays unwind automatically; output allocation failure still uses the existing bounded allocator/exception path.

## Evidence reviewed and correct interpretation

The actual-native differential harness compares outputs and error strings and verifies Arena.live returns to0 after each standalone case. Executed evidence records1877 differential cases, first12independent HUD goldens/253440words,457golden semantic corpus frames/9651840words, existing malformed inputs and late-component rollback. The broad corpus's1MiB cap remains semantic-only; its100888peak does not qualify target98,304fit for every corpus input.

Corpus tracked allocations decrease84765→14829, but first12peak stays88974 and broad corpus peak stays100888. Thus this removes table-allocation churn without reducing those measured full-decoder maxima. No TLSF fragmentation matrix has yet been rerun for this change. Fewer allocation calls alone do not prove the physical allocation failure is resolved.

The report correctly distinguishes selected benchmark02internal medians from earlier benchmark results: full Prepare sum971335→919790us, while the synthetic table-heavy microbenchmark401271→76821us. These are host/compiler/workload observations, not ESP32 latency or displayed frame rate. Whole-process timing includes I/O and golden hashing and should not be substituted for Prepare-only timing.

## Stack gate before hardware

The explicit arrays total648bytes. Host GCC reports Huffman frame352→896bytes, an increase544. This does not establish the Xtensa frame or full call chain. A historical network low-water near2904bytes makes this worth measuring, not ignoring: naïvely subtracting544would leave2360bytes, but that arithmetic is not a target proof because optimizer/inlining, deeper helpers and C++ exceptions differ.

Before proposing a physical V49 image, inspect the selected Xtensa`-fstack-usage` output for Huffman and its channel/decode/gate/endpoint callers, preserve exact source/image bindings and effective SDK/SRAM evidence, and confirm the worker stack allocation remains unchanged. Then run the bounded cold CPU12 and actual network cached12 with measured low-water/heap and complete diagnostics. Do not silently raise the stack, arena or physical reserve to compensate. If margin is inadequate, independently evaluate a compact immutable input-view table or explicitly accounted reusable scratch and rerun semantics/rollback tests.

The current change introduces no FPGA requirement. Retain the qualified V027 and keep target build, allocator-model behavior, host timings and physical playback as separate evidence.
