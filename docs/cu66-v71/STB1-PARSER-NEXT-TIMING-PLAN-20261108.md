# Next parser timing work - source-traced proposal, no RTL change

Selected hardware candidate remains passing V028/V001. The CE-factored fresh build fails -0.382ns globally; the incremental attempt then failed placement before final STA. These attempts do not authorize new RTL, constraints or another build tonight.

## Measured path and actual source predicate

Fresh CE final setup-paths.rpt launches parser metadata_reference_tag_reg[25] and ends metadata_plane_bytes_reg[0][9]/CE. Data9.917ns:3.146ns logic,6.771ns routing(68.276%),15levels including9CARRY4. The carry chain does **not by itself prove an arithmetic bottleneck**; wide equality/validation reductions can map through carry structures. The gate-level intermediate names are state-related, so exact chain-to-expression attribution remains to be measured before choosing a rewrite.

The actual source is packet-rx-staging-v001/cu71_packet_rxstage_v001.sv, not the HUD request factor. CHECK_OUTER lines249-268 validates outer fields/reference, then latches metadata_reference_tag. CHECK_INNER lines284-310 performs two prioritized validation groups. The first includes inner128(24)!=metadata_reference_tag plus magic/version/profile/key/frame/reference/dimensions/block fields and rejects code6. Only if it passes, the length group checks qmap/vector/three plane lengths and total, rejecting code7. Only if both pass does it capture metadata_plane_bytes[i]<=16'(inner32(48+4*i))-1, prefixes/block size, then enter PREFIX_STARTS. Thus a128-bit tag comparison is legitimately in the current capture CE cone.

Packet metadata is explicitly provisional until downstream commit. However, that statement alone does not permit exposing invalid header values sooner: internal/public readers, abort behavior, qmap/plane address generation, error diagnostics and state/reset observations must be audited before speculation is accepted.

## Preferred bounded candidates for later review

1. **Explicit staged validation:** separate immutable CHECK_INNER header checks from length checks and metadata commit. Register the result/error class, binding it to the current packet generation/frame ownership. Preserve code6-before-code7 priority, full-width unsigned length comparisons, existing modular16-bit prefix/byte arithmetic, and zero/new-value visibility requirements. Abort/reset must invalidate pending validation immediately, with no later metadata_valid/rd_req/commit from stale decisions. Existing header bytes are already fully captured and no byte read outstanding at entry, which provides a concrete potential stable-operand boundary; it does not prove a new cycle is harmless.
2. **Speculative private capture with a valid fence:** only if source/netlist measurements show this avoids the CE cone and an observation audit proves speculative fields unobservable, capture derived lengths into private unqualified registers before reference validation, then publish only after the unchanged ordered validations. Do not just remove the tag or other fatal gates from existing public capture signals. Extra storage/valid logic could worsen congestion and needs actual synthesis/resource timing comparison.
3. **Pure combinational factoring:** consider specialized field capture eligibility only after proving an implication like the prior HUD factor against the exact source predicate. There is no currently established Boolean implication allowing this parser reference-tag check to be removed. Do not cut global fatal or use a false/multicycle exception to hide it.

These are different changes from optional command/HUD identity pipelining; the former HUD metadata feedback was removed, but the parser path remains independently real. No FF replication, pblock or reset rewrite is justified solely by nine carry cells or the generic incremental placement error.

## Required evidence before another route

- Extract the exact remaining gate-level cone and map the first carry chain inputs to source expressions; preserve actual endpoint/launch bindings. Compare equality, state/decode, length and CE contributions rather than guessing from names.
- Source-bound sequential tests for all KEY/P metadata, bad inner tag/frame/reference/profile/dimensions, zero/min/max/oversized lengths, unsigned total overflow,16-bit modular prefixes, simultaneous code6+code7 faults, abort/reset at each new stage, backpressure/held metadata, immediate next-packet ownership and stale validation reuse.
- Re-run actual full-system KEY/P, staging/CRC, qmap, plane dispatch, HUD and commit/presentation gates with the new source. Canonical SHA/HUD/content checks remain downstream; parser metadata_valid must never authorize malformed or canceled state.
- Reset only new valid/owner state required to prevent stale use. Leave new private data unreset only after proving no consumer can observe it without the valid fence; configuration INIT does not replace runtime abort/reset invalidation.
- Synthesis proof of expected CE/logic depth plus resource/reset/BRAM review, unchanged clock/pin/external-memory constraints and explicit CDC endpoint differences. Full route then all setup/hold/pulse/DRC/routes/coverage gates. A local improved endpoint does not establish whole-design closure, as the CE experiments demonstrated.

No source/build/hardware changes were made for this note. Source/report hashes are bound in the adjacent JSON.
